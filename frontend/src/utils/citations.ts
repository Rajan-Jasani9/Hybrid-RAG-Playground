/**
 * Citation parsing utilities
 */

export interface Citation {
  label: string; // A, B, C, etc.
  startIndex: number;
  endIndex: number;
}

export interface TextSegment {
  text: string;
  citations?: string[]; // Array of citation labels
  isCitation: boolean;
}

/**
 * Parse text with citations like [[A]], [[B]], etc.
 * Returns segments with citation information
 */
export function parseCitations(text: string): TextSegment[] {
  const segments: TextSegment[] = [];
  const citationRegex = /\[\[([A-Z])\]\]/g;
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    // Add text before citation
    if (match.index > lastIndex) {
      segments.push({
        text: text.substring(lastIndex, match.index),
        isCitation: false,
      });
    }

    // Add citation
    segments.push({
      text: match[0], // [[A]]
      citations: [match[1]], // A
      isCitation: true,
    });

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    segments.push({
      text: text.substring(lastIndex),
      isCitation: false,
    });
  }

  // If no citations found, return the whole text as one segment
  if (segments.length === 0) {
    segments.push({
      text,
      isCitation: false,
    });
  }

  return segments;
}

/**
 * Extract all unique citation labels from text
 */
export function extractCitationLabels(text: string): string[] {
  const labels = new Set<string>();
  const citationRegex = /\[\[([A-Z])\]\]/g;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    labels.add(match[1]);
  }

  return Array.from(labels).sort();
}
