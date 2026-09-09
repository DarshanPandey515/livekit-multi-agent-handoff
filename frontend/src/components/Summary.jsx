import Transcript from "./Transcript.jsx";
import { HeadsetIcon } from "./Icons.jsx";

function fmtDuration(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

export default function Summary({ messages, duration, onNewCall }) {
  return (
    <div className="call-grid">
      <section className="call-panel">
        <div className="agent-stage">
          <div className="avatar ended">
            <HeadsetIcon />
          </div>
          <p className="stage-label">Call ended</p>
        </div>
        <p className="call-duration">Duration: {fmtDuration(duration)}</p>
        <button className="primary-btn" onClick={onNewCall}>
          Start new call
        </button>
      </section>

      <section className="call-panel transcript-panel">
        <h3 className="panel-title">Transcript</h3>
        {messages.length === 0 ? (
          <p className="muted">No transcript captured for this call.</p>
        ) : (
          <Transcript messages={messages} />
        )}
      </section>
    </div>
  );
}