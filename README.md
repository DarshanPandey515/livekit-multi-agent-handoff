# livekit-voice-agent

Personal learning files for the [LiveKit Agents](https://docs.livekit.io/agents/) framework (voice agents using Groq STT/LLM/TTS).

## Multi-agent support line

A company support receptionist that hands off calls to HR, the manager, or the
team lead. Repo is split into three layers:

```
livekit-voice-agent/
├── livekit/     # LiveKit voice agent worker(s)
├── backend/     # Django + DRF (async) API
└── frontend/    # Vite + React web caller
```

- `livekit/src/livekit_voice_agent/multi_agent.py` — the support-line worker
  (receptionist ⇄ HR / manager / team lead).
- `livekit/src/livekit_voice_agent/agents.py` — standalone weather-assistant
  example.
- `backend/` mints caller tokens and lists rooms.
- `frontend/` is the browser caller.

The repo-root `.env` holds the shared credentials (`LIVEKIT_*`, `GROQ_API_KEY`);
each layer reads it.

### Run it

1. Start the voice agent worker (registers to your LiveKit cloud project and
   picks up call dispatches):

   ```
   cd livekit
   uv sync
   uv run python -m livekit_voice_agent.multi_agent dev
   ```

2. Start the backend:

   ```
   cd backend
   uv sync
   uv run uvicorn config.asgi:application --port 8000
   ```

   Endpoints:

   - `POST /api/token` — body `{"identity": "name"}`, returns
     `{token, url, room, identity}`. The worker's automatic dispatch joins the
     agent to the room when the caller connects.
   - `GET /api/rooms` — lists active rooms and participant counts.

3. Start the frontend:

   ```
   cd frontend
   npm install
   npm run dev   # http://localhost:5173, proxies /api to :8000
   ```

   Click **Start call** (mic permission), and the receptionist greets you.