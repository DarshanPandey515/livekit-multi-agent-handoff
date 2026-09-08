# livekit-voice-agent

Personal learning files for the [LiveKit Agents](https://docs.livekit.io/agents/) framework (voice agents using Groq STT/LLM/TTS). Not a finished project.

## Files

- `src/livekit_voice_agent/agents.py` — single voice agent with a `get_weather` function tool.
- `src/livekit_voice_agent/multi_agent.py` — multi-agent example: receptionist / HR / manager / team-lead personas that hand off to each other.

## Run

```bash
uv run python src/livekit_voice_agent/agents.py
uv run python src/livekit_voice_agent/multi_agent.py
```

Each module runs its own `AgentServer` entrypoint when executed directly.

Requires a LiveKit project and a Groq API key. Credentials live in `.env` (gitignored):

```
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
GROQ_API_KEY=...
```

Built with Python 3.12+ and [uv](https://docs.astral.sh/uv/).
