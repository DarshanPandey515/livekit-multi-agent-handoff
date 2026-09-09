function fmtDuration(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

export default function Summary({ messages, duration, onNewCall }) {
  return (
    <div className="summary">
      <h2>Call ended</h2>
      <p className="hint">Duration: {fmtDuration(duration)}</p>

      {messages.length === 0 ? (
        <p className="muted">No transcript captured for this call.</p>
      ) : (
        <div className="transcript">
          {messages.map((m) => (
            <div key={m.id} className={`msg ${m.role}`}>
              <span className="who">{m.role === "user" ? "You" : "Agent"}</span>
              <span className="text">{m.text}</span>
            </div>
          ))}
        </div>
      )}

      <button onClick={onNewCall}>Start new call</button>
    </div>
  );
}