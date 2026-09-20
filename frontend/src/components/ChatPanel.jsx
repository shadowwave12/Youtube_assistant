export default function ChatPanel({
  messages,
  question,
  isAsking,
  disabled,
  onQuestionChange,
  onAsk,
  onQuickQuestion,
}) {
  return (
    <section className="chat-panel" aria-labelledby="chat-heading">
      <div className="chat-header">
        <div>
          <div className="panel-label">Conversation</div>
          <h2 id="chat-heading">Ask about your lesson</h2>
        </div>
        <span className={`availability ${disabled ? "is-muted" : ""}`}>
          <span className="availability-dot" aria-hidden="true" />
          {disabled ? "Waiting for video" : "Ready to answer"}
        </span>
      </div>

      <div className="conversation-intro">
        <span className="intro-dot" aria-hidden="true" />
        {disabled
          ? "Add a lesson to begin"
          : "Your questions stay grounded in the transcript"}
      </div>
      <div
        className="message-list"
        aria-live="polite"
        aria-label="Conversation"
      >
        {messages.length === 0 ? (
          <div className="empty-chat">
            <span className="empty-mark" aria-hidden="true">
              +
            </span>
            <p>
              {disabled
                ? "Your conversation will appear here once a video has been indexed."
                : "Ask about an idea, example, or key moment from the lesson."}
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <article
              className={`message message-${message.role}`}
              key={`${message.role}-${index}`}
            >
              <div className="message-label">
                {message.role === "user" ? "You" : "Assistant"}
              </div>
              <p>{message.content}</p>
              {message.sources && message.sources.length > 0 ? (
                <div className="sources">
                  <div className="sources-heading">Source excerpts</div>
                  {message.sources.map((source) => (
                    <blockquote
                      key={`${source.video_id}-${source.chunk_index}`}
                    >
                      <span>Chunk {source.chunk_index + 1}</span>
                      {source.text}
                    </blockquote>
                  ))}
                </div>
              ) : null}
            </article>
          ))
        )}
      </div>

      <form
        className="question-form"
        onSubmit={(event) => {
          event.preventDefault();
          onAsk();
        }}
      >
        <label htmlFor="question">Your question</label>
        <div className="question-row">
          <input
            id="question"
            name="question"
            type="text"
            value={question}
            onChange={(event) => onQuestionChange(event.target.value)}
            placeholder={
              disabled ? "Process a video first" : "What is the main idea?"
            }
            disabled={disabled || isAsking}
            required
          />
          <button
            type="submit"
            className="send-button"
            disabled={disabled || isAsking || !question.trim()}
          >
            {isAsking ? "Thinking..." : "Send"}
            <span aria-hidden="true">↗</span>
          </button>
        </div>
      </form>
    </section>
  );
}
