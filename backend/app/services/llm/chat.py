# llm/chat.py

import logging
from typing import List, AsyncIterator
import json

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from retrieval.base import RetrievedChunk

logger = logging.getLogger(__name__)


def create_openai_client(model_name: str, api_key: str) -> OpenAIModel:
    """
    Create an OpenAI model client with a direct API key.
    
    Args:
        model_name: The OpenAI model name (e.g., 'gpt-4o-mini')
        api_key: The OpenAI API key
        
    Returns:
        A configured OpenAIModel instance
    """
    # Create OpenAI client with the API key
    openai_client = AsyncOpenAI(api_key=api_key)
    
    # Try to use provider if available, otherwise fall back to environment variable approach
    try:
        from pydantic_ai.providers.openai import OpenAIProvider
        provider = OpenAIProvider(openai_client=openai_client)
        return OpenAIModel(model_name, provider=provider)
    except ImportError:
        # Fallback: Use environment variable (less ideal but works)
        import os
        original_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = api_key
        try:
            model = OpenAIModel(model_name)
            return model
        finally:
            # Restore original key if it existed
            if original_key is not None:
                os.environ["OPENAI_API_KEY"] = original_key
            elif "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]


def create_anthropic_client(model_name: str, api_key: str) -> AnthropicModel:
    """
    Create an Anthropic model client with a direct API key.
    
    Args:
        model_name: The Anthropic model name (e.g., 'claude-3-5-sonnet-20241022')
        api_key: The Anthropic API key
        
    Returns:
        A configured AnthropicModel instance
    """
    # Create Anthropic client with the API key
    anthropic_client = AsyncAnthropic(api_key=api_key)
    
    # Try to use provider if available, otherwise fall back to environment variable approach
    try:
        from pydantic_ai.providers.anthropic import AnthropicProvider
        provider = AnthropicProvider(anthropic_client=anthropic_client)
        return AnthropicModel(model_name, provider=provider)
    except ImportError:
        # Fallback: Use environment variable (less ideal but works)
        import os
        original_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = api_key
        try:
            model = AnthropicModel(model_name)
            return model
        finally:
            # Restore original key if it existed
            if original_key is not None:
                os.environ["ANTHROPIC_API_KEY"] = original_key
            elif "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]


def create_chat_agent(model_family: str, model_name: str, api_key: str) -> Agent:
    """
    Create a PydanticAI agent for the specified model family and model.
    
    Args:
        model_family: Either 'openai' or 'anthropic'
        model_name: The specific model name (e.g., 'gpt-4o-mini', 'claude-3-5-sonnet-20241022')
        api_key: The API key for the model provider
        
    Returns:
        A configured PydanticAI Agent
    """
    if model_family == "openai":
        model = create_openai_client(model_name, api_key)
    elif model_family == "anthropic":
        model = create_anthropic_client(model_name, api_key)
    else:
        raise ValueError(f"Unsupported model family: {model_family}")
    
    system_prompt = build_system_prompt()
    return Agent(model, system_prompt=system_prompt)


def build_context_prompt(chunks: List[RetrievedChunk]) -> str:
    """
    Build a context prompt with chunks labeled A, B, C, etc.
    
    Args:
        chunks: List of retrieved chunks
        
    Returns:
        Formatted context string with labeled chunks
    """
    if not chunks:
        return "No context provided."
    
    context_parts = []
    labels = [chr(65 + i) for i in range(len(chunks))]  # A, B, C, ...
    
    for label, chunk in zip(labels, chunks):
        context_parts.append(f"[{label}] {chunk.text}")
    
    return "\n\n".join(context_parts)


def build_system_prompt() -> str:
    """
    Build the system prompt that forces the LLM to only answer from context
    and use citations with markdown formatting.
    """
    return """You are a helpful assistant that answers questions based ONLY on the provided context.

CRITICAL RULES - STRICTLY ENFORCED:
1. You MUST ONLY use information from the provided context to answer the question.
2. If the context does NOT contain enough information to answer the question, you MUST respond with: "I cannot answer this question based on the provided context."
3. DO NOT use any knowledge outside the provided context, even if you know the answer.
4. DO NOT make up, infer, or guess information that is not explicitly stated in the context.
5. If asked about something not in the context, you MUST decline and state: "I cannot answer this question based on the provided context."

CITATION REQUIREMENTS:
6. You MUST cite your sources using the format [[X]] where X is the letter label (A, B, C, etc.) of the chunk you are referencing.
7. Include citations immediately after each sentence or claim that uses information from a specific chunk.
8. You can cite multiple chunks if relevant: [[A]][[B]]
9. The context chunks are labeled with letters (A, B, C, etc.). Use these labels in your citations.

FORMATTING REQUIREMENTS:
10. Use basic Markdown formatting to structure your response:
    - Use **bold** for emphasis on important terms
    - Use *italic* for subtle emphasis
    - Use bullet points (- or *) for lists
    - Use numbered lists (1., 2., 3.) for sequential information
    - Use `code` formatting for technical terms, code snippets, or specific values
    - Use ## for section headings if organizing a longer response
    - Keep paragraphs concise and well-structured

Remember: If you cannot answer from the context, you MUST say "I cannot answer this question based on the provided context." Do not attempt to answer using outside knowledge."""


def _extract_text_from_event(event) -> str:
    """
    Helper function to extract incremental text deltas from streaming events.
    Prioritizes delta content (incremental) over full content (accumulated).
    """
    # Priority 1: Check for delta content (incremental text chunks)
    if hasattr(event, 'delta'):
        delta = event.delta
        if hasattr(delta, 'content') and delta.content:
            return str(delta.content)
        elif hasattr(delta, 'text') and delta.text:
            return str(delta.text)
        elif isinstance(delta, str):
            return delta
    
    # Priority 2: Check event.data for delta
    if hasattr(event, 'data'):
        data = event.data
        # Check for delta in data
        if hasattr(data, 'delta'):
            delta = data.delta
            if hasattr(delta, 'content') and delta.content:
                return str(delta.content)
            elif hasattr(delta, 'text') and delta.text:
                return str(delta.text)
        # If no delta, check for direct text content (but this might be accumulated)
        if isinstance(data, str):
            return data
        elif hasattr(data, 'content'):
            content = data.content
            if isinstance(content, str):
                return content
            elif hasattr(content, 'text'):
                return str(content.text)
        elif hasattr(data, 'text'):
            return str(data.text)
    
    # Priority 3: Check event directly (fallback)
    if isinstance(event, str):
        return event
    elif hasattr(event, 'content'):
        content = event.content
        if isinstance(content, str):
            return content
        elif hasattr(content, 'text'):
            return str(content.text)
    elif hasattr(event, 'text'):
        return str(event.text)
    
    return None


async def stream_chat_response(
    model_family: str,
    model_name: str,
    api_key: str,
    query: str,
    chunks: List[RetrievedChunk],
) -> AsyncIterator[str]:
    """
    Stream a chat response from the LLM based on retrieved chunks.
    
    Args:
        model_family: Either 'openai' or 'anthropic'
        model_name: The specific model name
        api_key: The API key for the model provider
        query: The user's question
        chunks: List of retrieved chunks to use as context
        
    Yields:
        Chunks of the response text as they are generated
    """
    try:
        # Create agent with system prompt
        agent = create_chat_agent(model_family, model_name, api_key)
        
        # Build context with labeled chunks
        context = build_context_prompt(chunks)
        
        # Build user message
        user_message = f"""Context:
{context}

Question: {query}

Please answer the question based ONLY on the context provided above. Use citations like [[A]], [[B]], etc. to reference the specific chunks you use."""

        # Stream the response using PydanticAI
        # PydanticAI's run_stream returns an async context manager that yields StreamedRunResult
        async with agent.run_stream(user_message) as stream_result:
            # StreamedRunResult has stream_output() method to get the async iterator
            # Track accumulated content to extract only incremental deltas
            accumulated_text = ""
            
            async for event in stream_result.stream_output():
                text_content = _extract_text_from_event(event)
                if text_content:
                    # If the extracted content is longer than accumulated, it's the new accumulated text
                    # Extract only the new delta portion
                    if len(text_content) > len(accumulated_text) and text_content.startswith(accumulated_text):
                        # New incremental delta
                        delta = text_content[len(accumulated_text):]
                        if delta:
                            yield delta
                            accumulated_text = text_content
                    elif text_content != accumulated_text:
                        # Different content (might be a delta that doesn't start with accumulated)
                        # Yield it and update accumulated
                        yield text_content
                        accumulated_text = text_content
            
    except Exception as e:
        logger.error(f"Error streaming chat response: {str(e)}", exc_info=True)
        yield f"Error: {str(e)}"
