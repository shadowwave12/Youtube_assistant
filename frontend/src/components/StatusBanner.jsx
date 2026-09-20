export default function StatusBanner({ tone, children }) {
  return (
    <div
      className={`status-banner status-${tone}`}
      role={tone === "error" ? "alert" : "status"}
      aria-live="polite"
    >
      <span className="status-dot" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}
