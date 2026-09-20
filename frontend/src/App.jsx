import { useState } from "react";

import { ApiClientError, processVideo, sendChat } from "./api/client";
import ChatPanel from "./components/ChatPanel";
import StatusBanner from "./components/StatusBanner";
import VideoProcessor from "./components/VideoProcessor";
import "./styles.css";

export default function App() {
  const [source, setSource] = useState("");
  const [videoId, setVideoId] = useState(null);
  const [chunkCount, setChunkCount] = useState(null);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState(null);

  async function handleProcess() {
    if (!source.trim()) return;
    setError(null);
    setIsProcessing(true);
    setVideoId(null);
    setChunkCount(null);
    setMessages([]);

    try {
      const result = await processVideo({ source: source.trim() });
      setVideoId(result.video_id);
      setChunkCount(result.chunk_count);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsProcessing(false);
    }
  }

  async function handleAsk() {
    if (!videoId || !question.trim()) return;
    const submittedQuestion = question.trim();
    setError(null);
    setQuestion("");
    setMessages((current) => [
      ...current,
      { role: "user", content: submittedQuestion },
    ]);
    setIsAsking(true);

    try {
      const result = await sendChat({
        video_id: videoId,
        question: submittedQuestion,
      });
      setMessages((current) => [
        ...current,
        { role: "assistant", content: result.answer, sources: result.sources },
      ]);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="/"
          aria-label="YouTube Learning Assistant home"
        >
          <span className="brand-mark" aria-hidden="true">
            YL
          </span>
          <span>YouTube Learning Assistant</span>
        </a>
        <div className="topbar-meta">
          <span className="workspace-name">Study workspace</span>
          <span className="topbar-status">
            <span aria-hidden="true" />{" "}
            {videoId ? "Video ready" : "No video loaded"}
          </span>
        </div>
      </header>

      <div className="workspace-frame">
        <nav className="side-nav" aria-label="Workspace navigation">
          <div className="nav-logo" aria-hidden="true">
            YL
          </div>
          <a className="nav-item is-active" href="#video-source">
            <span aria-hidden="true">+</span>
            <span>New lesson</span>
          </a>
          <a className="nav-item" href="#chat-heading">
            <span aria-hidden="true">O</span>
            <span>Conversation</span>
          </a>
          <a className="nav-item" href="#study-tools">
            <span aria-hidden="true">◇</span>
            <span>Study tools</span>
          </a>
          <div className="nav-spacer" />
          <span className="nav-caption">Local session</span>
        </nav>

        <aside className="materials-column">
          <VideoProcessor
            source={source}
            isProcessing={isProcessing}
            disabled={isProcessing}
            onSourceChange={setSource}
            onProcess={handleProcess}
          />
          <div className="material-status" aria-live="polite">
            <div className="panel-label">Current lesson</div>
            <strong>
              {videoId ? "Transcript indexed" : "Nothing indexed yet"}
            </strong>
            <p>
              {videoId
                ? `${chunkCount} searchable chunks ready for questions.`
                : "Add a YouTube video to start a focused study session."}
            </p>
          </div>
        </aside>

        <section
          className="conversation-column"
          aria-label="Learning conversation"
        >
          {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
          {isProcessing ? (
            <StatusBanner tone="info">
              Reading the transcript and building your study index...
            </StatusBanner>
          ) : null}
          {videoId && !isProcessing ? (
            <StatusBanner tone="success">
              Your lesson is ready for questions.
            </StatusBanner>
          ) : null}
          <ChatPanel
            messages={messages}
            question={question}
            isAsking={isAsking}
            disabled={!videoId || isProcessing}
            onQuestionChange={setQuestion}
            onAsk={handleAsk}
            onQuickQuestion={setQuestion}
          />
        </section>

        <aside className="tools-column" id="study-tools">
          <div className="tools-heading">
            <span aria-hidden="true">✦</span>
            <h2>Study tools</h2>
          </div>
          <div className="tool-list">
            <div className="tool-item">
              <span className="tool-icon tool-icon-coral" aria-hidden="true">
                ↗
              </span>
              <div>
                <strong>Instant answers</strong>
                <p>Ask about any idea in the transcript.</p>
              </div>
            </div>
            <div className="tool-item">
              <span className="tool-icon tool-icon-green" aria-hidden="true">
                ✓
              </span>
              <div>
                <strong>Source grounded</strong>
                <p>Every answer shows where it came from.</p>
              </div>
            </div>
            <div className="tool-item">
              <span className="tool-icon tool-icon-lilac" aria-hidden="true">
                ◇
              </span>
              <div>
                <strong>Learn at your pace</strong>
                <p>Keep the conversation focused on one lesson.</p>
              </div>
            </div>
          </div>
          <div className="quick-questions">
            <div className="panel-label">Try asking</div>
            <button
              type="button"
              onClick={() =>
                setQuestion("What is the main idea of this video?")
              }
              disabled={!videoId || isProcessing}
            >
              What is the main idea?
            </button>
            <button
              type="button"
              onClick={() => setQuestion("Can you summarize the key points?")}
              disabled={!videoId || isProcessing}
            >
              Summarize the key points
            </button>
            <button
              type="button"
              onClick={() =>
                setQuestion("What should I remember from this lesson?")
              }
              disabled={!videoId || isProcessing}
            >
              What should I remember?
            </button>
          </div>
        </aside>
      </div>
      <footer className="footer">
        Answers are generated from retrieved transcript excerpts. Indexes remain
        in memory for this session.
      </footer>
    </main>
  );
}

function getErrorMessage(error) {
  if (error instanceof ApiClientError) return error.message;
  return "Something went wrong. Please try again.";
}
