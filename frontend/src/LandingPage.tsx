import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Layers, MessageSquare, Search } from "lucide-react";

const LandingPage: React.FC = () => {
  const year = new Date().getFullYear();

  return (
    <div className="landing">
      <div className="landing-bg" aria-hidden />
      <header className="landing-header">
        <div className="landing-container landing-header-inner">
          <span className="landing-logo">Hybrid RAG</span>
          <nav className="landing-nav" aria-label="Primary">
            <Link to="/playground" className="landing-header-cta">
              Open playground
            </Link>
          </nav>
        </div>
      </header>

      <main className="landing-main" id="main-content">
        <div className="landing-container">
          <section className="landing-hero" aria-labelledby="landing-heading">
            <div className="landing-hero-accent" aria-hidden />
            <div className="landing-hero-copy">
              <p className="landing-eyebrow">Retrieval · grounding · chat</p>
              <h1 id="landing-heading" className="landing-title">
                Grounded answers from your documents, with hybrid search.
              </h1>
              <p className="landing-lede">
                Pair dense embeddings with lexical BM25, review retrieved
                chunks, and converse with your corpus in a single workspace.
              </p>
              <div className="landing-actions">
                <Link
                  to="/playground"
                  className="landing-btn landing-btn-primary"
                >
                  Get started
                  <ArrowRight
                    className="landing-btn-icon"
                    strokeWidth={2}
                    aria-hidden
                  />
                </Link>
                <p className="landing-actions-note">
                  Configure models and provider keys in the playground when you
                  enable chat.
                </p>
              </div>
            </div>
          </section>

          <section
            className="landing-capabilities"
            aria-labelledby="capabilities-heading"
          >
            <h2 id="capabilities-heading" className="landing-section-title">
              Capabilities
            </h2>
            <ul className="landing-features">
              <li className="landing-feature">
                <span className="landing-feature-icon" aria-hidden>
                  <Layers size={20} strokeWidth={1.75} />
                </span>
                <div className="landing-feature-body">
                  <h3 className="landing-feature-title">Hybrid retrieval</h3>
                  <p className="landing-feature-text">
                    Combine semantic and keyword signals to improve recall on
                    real-world queries.
                  </p>
                </div>
              </li>
              <li className="landing-feature">
                <span className="landing-feature-icon" aria-hidden>
                  <Search size={20} strokeWidth={1.75} />
                </span>
                <div className="landing-feature-body">
                  <h3 className="landing-feature-title">Traceable chunks</h3>
                  <p className="landing-feature-text">
                    Inspect what was retrieved before you rely on the generated
                    answer.
                  </p>
                </div>
              </li>
              <li className="landing-feature">
                <span className="landing-feature-icon" aria-hidden>
                  <MessageSquare size={20} strokeWidth={1.75} />
                </span>
                <div className="landing-feature-body">
                  <h3 className="landing-feature-title">Optional chat</h3>
                  <p className="landing-feature-text">
                    Add your model provider and API key when you want
                    conversational responses.
                  </p>
                </div>
              </li>
            </ul>
          </section>
        </div>
      </main>

      <footer className="landing-footer">
        <div className="landing-container landing-footer-inner">
          <span>© {year} Hybrid RAG</span>
          <span className="landing-footer-meta">Playground</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
