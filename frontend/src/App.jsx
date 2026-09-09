import React, { useEffect, useRef, useState } from "react";
import { Room, RoomEvent } from "livekit-client";

function App() {
  const [identity, setIdentity] = useState("");
  const [status, setStatus] = useState("idle"); // idle | connecting | connected | error
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [audioBlocked, setAudioBlocked] = useState(false);
  const roomRef = useRef(null);

  useEffect(() => () => roomRef.current?.disconnect(), []);

  async function startCall() {
    setStatus("connecting");
    setError(null);
    setInfo(null);
    try {
      const res = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identity }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "failed to get token");

      const room = new Room();
      room
        .on(RoomEvent.ParticipantConnected, (p) => {
          setInfo(`Connected to: ${p.name || p.identity}`);
        })
        .on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
          if (track.kind !== "audio") return;

          const element = track.attach();
          element.autoplay = true;
          element.muted = false;
          element.volume = 1;
          element.setAttribute("playsinline", "true");
          element.className = "remote-audio";
          element.dataset.participant = participant.identity;
          document.body.appendChild(element);

          element.play().catch(() => setAudioBlocked(true));
          setInfo(`Audio connected: ${participant.name || participant.identity}`);
          console.debug("LiveKit remote audio subscribed", {
            participant: participant.identity,
            publication: publication.trackSid,
          });
        })
        .on(RoomEvent.TrackUnsubscribed, (track) => {
          track.detach().forEach((element) => element.remove());
        })
        .on(RoomEvent.AudioPlaybackStatusChanged, (hasAudio) => {
          setAudioBlocked(!hasAudio);
        })
        .on(RoomEvent.Disconnected, () => {
          setStatus("idle");
          setInfo(null);
          setAudioBlocked(false);
        });
      roomRef.current = room;

      await room.connect(data.url, data.token);
      await room.startAudio();
      await room.localParticipant.setMicrophoneEnabled(true);
      setStatus("connected");
    } catch (err) {
      setStatus("error");
      setError(String(err.message || err));
    }
  }

  async function endCall() {
    roomRef.current?.disconnect();
    roomRef.current = null;
    setStatus("idle");
    setMuted(false);
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

  return (
    <div className="app">
      <h1>Support Line</h1>
      <p className="hint">Speak with the receptionist — they will route you to HR, the manager, or your team lead.</p>

      {status === "idle" && (
        <div className="controls">
          <input
            placeholder="Your name (optional)"
            value={identity}
            onChange={(e) => setIdentity(e.target.value)}
          />
          <button onClick={startCall}>Start call</button>
        </div>
      )}

      {status === "connecting" && <p className="status">Connecting…</p>}
      {status === "error" && <p className="status error">{error}</p>}

      {status === "connected" && (
        <div className="controls">
          <p className="status ok">{info || "Connected"}</p>
          {audioBlocked && (
            <button onClick={enableAudio}>Tap to enable audio</button>
          )}
          <button onClick={toggleMute}>{muted ? "Unmute" : "Mute"}</button>
          <button onClick={endCall} className="danger">
            End call
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
