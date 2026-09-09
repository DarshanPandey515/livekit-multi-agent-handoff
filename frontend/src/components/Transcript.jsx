import { useEffect, useRef } from "react";

export default function Transcript({ messages }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length]);

  if (messages.length === 0) {
    return <p className="muted">Start speaking — the conversation transcript will appear here.</p>;
  }

  return (
    <div className="transcript">
      {messages.map((m) => (
        <div key={m.id} className={`msg ${m.role}`}>
          <span className="who">{m.speaker || (m.role === "user" ? "You" : "Agent")}</span>
          <span className="bubble">{m.text}</span>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}