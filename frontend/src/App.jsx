import React, { useEffect, useRef, useState } from "react";
import { Room, RoomEvent } from "livekit-client";
import Visualizer from "./components/Visualizer.jsx";
import Transcript from "./components/Transcript.jsx";
import Summary from "./components/Summary.jsx";
import { AgentIcon, EndCallIcon, HeadsetIcon, MicIcon, MicOffIcon } from "./components/Icons.jsx";

const ROLE_LABELS = {
  receptionist: "Receptionist",
  hr: "HR",
  manager: "Manager",
  team_lead: "Team Lead",
};

function App() {
  const [identity, setIdentity] = useState("");
  const [status, setStatus] = useState("idle"); // idle | connecting | connected | ended | error
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState(null);
  const [audioBlocked, setAudioBlocked] = useState(false);
  const [role, setRole] = useState(null);
  const [audioStream, setAudioStream] = useState(null);
  const [messages, setMessages] = useState([]);
  const [duration, setDuration] = useState(0);

  const roomRef = useRef(null);
  const audioCtxRef = useRef(null);
  const segmentsRef = useRef(new Map());
  const roleRef = useRef(null);
  const callStartRef = useRef(0);
  const timerRef = useRef(null);

  useEffect(
    () => () => {
      clearInterval(timerRef.current);
      roomRef.current?.disconnect();
      audioCtxRef.current?.close();
    },
    []
  );

  function applyRole(metadata, participant) {
    // The agent is the only remote participant in a support call, so any
    // participant metadata carrying a known role is the agent's.
    if (!metadata) return;
    try {
      const { role: parsed } = JSON.parse(metadata);
      if (ROLE_LABELS[parsed]) {
        setRole(ROLE_LABELS[parsed]);
        roleRef.current = ROLE_LABELS[parsed];
      }
    } catch {
      /* ignore malformed metadata */
    }
  }

  function handleTranscription(segments, participant) {
    const isUser =
      !!participant &&
      participant.identity === roomRef.current?.localParticipant.identity;
    const who = isUser ? "user" : "agent";
    const speaker = isUser ? "You" : roleRef.current || "Agent";

    let changed = false;
    segments.forEach((s) => {
      const existing = segmentsRef.current.get(s.id);
      if (existing) {
        if (existing.text !== s.text || existing.final !== s.final) {
          existing.text = s.text;
          existing.final = s.final;
          changed = true;
        }
      } else {
        segmentsRef.current.set(s.id, {
          id: s.id,
          text: s.text,
          final: s.final,
          role: who,
          speaker,
          ts: Date.now(),
        });
        changed = true;
      }
    });

    if (changed) {
      const finalized = [...segmentsRef.current.values()]
        .filter((s) => s.final)
        .sort((a, b) => a.ts - b.ts);
      setMessages(finalized);
    }
  }

  async function startCall() {
    setStatus("connecting");
    setError(null);
    setRole(null);
    setMessages([]);
    segmentsRef.current = new Map();

    try {
      // Created inside the click gesture so autoplay lets it run.
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();

      const res = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identity }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "failed to get token");

      const room = new Room();
      room
        .on(RoomEvent.ParticipantConnected, (p) => applyRole(p.metadata, p))
        .on(RoomEvent.ParticipantMetadataChanged, (metadata, p) =>
          applyRole(metadata, p)
        )
        .on(RoomEvent.TrackSubscribed, (track) => {
          if (track.kind !== "audio") return;

          const element = track.attach();
          element.autoplay = true;
          element.muted = false;
          element.volume = 1;
          element.setAttribute("playsinline", "true");
          element.className = "remote-audio";
          document.body.appendChild(element);
          element.play().catch(() => setAudioBlocked(true));

          setAudioStream(new MediaStream([track.mediaStreamTrack]));
        })
        .on(RoomEvent.TrackUnsubscribed, (track) => {
          track.detach().forEach((element) => element.remove());
        })
        .on(RoomEvent.TranscriptionReceived, (segments, participant) =>
          handleTranscription(segments, participant)
        )
        .on(RoomEvent.AudioPlaybackStatusChanged, (hasAudio) =>
          setAudioBlocked(!hasAudio)
        )
        .on(RoomEvent.Disconnected, () => {
          clearInterval(timerRef.current);
          roomRef.current = null;
          setStatus("ended");
        });
      roomRef.current = room;

      callStartRef.current = Date.now();
      setDuration(0);
      timerRef.current = setInterval(
        () => setDuration(Date.now() - callStartRef.current),
        1000
      );

      await room.connect(data.url, data.token);
      await room.startAudio();
      await room.localParticipant.setMicrophoneEnabled(true);
      room.remoteParticipants.forEach((p) => applyRole(p.metadata, p));
      setStatus("connected");
    } catch (err) {
      setStatus("error");
      setError(String(err.message || err));
    }
  }

  function endCall() {
    clearInterval(timerRef.current);
    roomRef.current?.disconnect();
  }

  async function toggleMute() {
    const next = !muted;
    await roomRef.current?.localParticipant.setMicrophoneEnabled(!next);
    setMuted(next);
  }

  async function enableAudio() {
    try {
      await roomRef.current?.startAudio();
      document.querySelectorAll(".remote-audio").forEach((element) => {
        element.play().catch(() => {});
      });
      setAudioBlocked(false);
    } catch (err) {
      setError(`Audio playback is blocked: ${err.message || err}`);
    }
  }

  function newCall() {
    setStatus("idle");
    setDuration(0);
    setAudioStream(null);
  }

  return (
    <div className={`app ${status === "idle" ? "app--idle" : "app--call"}`}>
      <header className="app-header">
        <div className="brand">
          <div className="eq" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
            <i />
          </div>
          <span className="brand-name">Support Line</span>
        </div>

        {status === "connected" && (
          <div className="header-status">
            <span className="role-pill">
              <span className="pulse-dot" />
              {role ? `Speaking with ${role}` : "Connecting to agent…"}
            </span>
            <span className="muted">{fmtDuration(duration)}</span>
          </div>
        )}
      </header>

      <main className="screen">
        {status === "idle" && (
          <div className="idle">
            <div className="logo-badge">
              <HeadsetIcon />
            </div>
            <h2>Talk to our support team</h2>
            <p className="hint">
              Speak with the receptionist — they will route you to HR, the
              manager, or your team lead.
            </p>
            <input
              placeholder="Your name (optional)"
              value={identity}
              onChange={(e) => setIdentity(e.target.value)}
            />
            <button className="primary-btn" onClick={startCall}>
              Start call
            </button>
          </div>
        )}

        {status === "error" && <p className="status error">{error}</p>}

        {(status === "connecting" || status === "connected") && (
          <div className="call-grid">
            <section className="call-panel">
              <div className="agent-stage">
                <div className={`avatar ${status === "connecting" ? "pulse-avatar" : ""}`}>
                  <AgentIcon />
                </div>
                <p className="stage-label">
                  {status === "connecting"
                    ? "Connecting to the support agent…"
                    : muted
                    ? "You are muted"
                    : "Agent speaking…"}
                </p>
              </div>

              <Visualizer stream={audioStream} audioCtx={audioCtxRef.current} />

              {status === "connected" && audioBlocked && (
                <button className="primary-btn" onClick={enableAudio}>
                  Tap to enable audio
                </button>
              )}

              {status === "connected" && (
                <div className="call-actions">
                  <button
                    className={`icon-btn ${muted ? "active" : ""}`}
                    onClick={toggleMute}
                    title={muted ? "Unmute" : "Mute"}
                  >
                    {muted ? <MicOffIcon /> : <MicIcon />}
                  </button>
                  <button className="icon-btn danger" onClick={endCall} title="End call">
                    <EndCallIcon />
                  </button>
                </div>
              )}
            </section>

            <section className="call-panel transcript-panel">
              <h3 className="panel-title">Transcript</h3>
              {status === "connecting" ? (
                <p className="muted">Waiting for the agent to join…</p>
              ) : (
                <Transcript messages={messages} />
              )}
            </section>
          </div>
        )}

        {status === "ended" && (
          <Summary messages={messages} duration={duration} onNewCall={newCall} />
        )}
      </main>
    </div>
  );
}

function fmtDuration(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

export default App;