export default function VideoProcessor({
  source,
  isProcessing,
  disabled,
  onSourceChange,
  onProcess,
}) {
  return (
    <section className="processor-panel" aria-labelledby="processor-heading">
      <div className="panel-title-row">
        <div className="panel-label">Study material</div>
        <span className="panel-count">01</span>
      </div>
      <h2 id="processor-heading">Add a YouTube lesson</h2>
      <p className="section-copy">
        Bring one video into the workspace and ask questions directly against
        its transcript.
      </p>
      <form
        className="process-form"
        onSubmit={(event) => {
          event.preventDefault();
          onProcess();
        }}
      >
        <label htmlFor="youtube-source">Video URL or ID</label>
        <input
          id="youtube-source"
          name="youtube-source"
          type="text"
          value={source}
          onChange={(event) => onSourceChange(event.target.value)}
          placeholder="Paste a YouTube URL"
          autoComplete="url"
          disabled={isProcessing}
          required
        />
        <button
          className="process-button"
          type="submit"
          disabled={disabled || !source.trim()}
        >
          {isProcessing ? "Indexing lesson..." : "Add to workspace"}
          <span aria-hidden="true">↗</span>
        </button>
      </form>
      <p className="field-hint">
        English transcript by default. Your index stays private to this session.
      </p>
    </section>
  );
}
