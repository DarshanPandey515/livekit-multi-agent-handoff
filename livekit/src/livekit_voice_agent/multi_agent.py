"""Support-line voice worker: composition root (server + entrypoint wiring).

Business components live in this package:
    prompts.py          role instructions
    session.py          shared session state
    roles.py            agent classes, transfer tools, role registry
    transcript_relay.py caller speech relay for the web transcript
"""

from __future__ import annotations

import json

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    AgentServer,
    AgentSession,
    APIConnectOptions,
    JobContext,
    TurnHandlingOptions,
    inference,
)
from livekit.agents.voice.agent_session import SessionConnectOptions
from livekit.plugins import groq

from .roles import build_agents
from .session import SessionState
from .transcript_relay import TranscriptRelay

load_dotenv()

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    """
    LiveKit RTC entrypoint.
    """

    agent_registry = build_agents()

    state = SessionState(
        current_role="receptionist",
        agents=agent_registry,
    )

    session = AgentSession[SessionState](
        userdata=state,

        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),

        llm=groq.LLM(
            model="openai/gpt-oss-20b",
        ),

        tts=inference.TTS(
            model="inworld/inworld-tts-2",
            voice="Ashley",
            language="en",
        ),

        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
            interruption={
                "mode": "adaptive",
                "min_duration": 0.4,
            },
            endpointing={
                "mode": "dynamic",
                "min_delay": 0.65,
                "max_delay": 2.0,
                "alpha": 0.9,
            },
            preemptive_generation={
                "preemptive_tts": False,
            },
        ),

        conn_options=SessionConnectOptions(
            tts_conn_options=APIConnectOptions(
                max_retry=5,
                retry_interval=2,
            ),
        ),
    )

    
    TranscriptRelay(session=session, room=ctx.room)

    await session.start(
        room=ctx.room,
        agent=agent_registry["receptionist"],
    )

    await ctx.room.local_participant.set_metadata(json.dumps({"role": "receptionist"}))

    await session.generate_reply(
        instructions=(
            "Greet the employee as the company receptionist and ask "
            "how you can help."
        ),
    )


if __name__ == "__main__":
    agents.cli.run_app(server=server)