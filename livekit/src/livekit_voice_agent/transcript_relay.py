from __future__ import annotations

import asyncio
import logging
import uuid

from livekit import rtc
from livekit.agents import AgentSession
from livekit.agents.voice.events import UserInputTranscribedEvent

logger = logging.getLogger(__name__)


class TranscriptRelay:
    """Publish the caller's final transcripts attributed to the caller."""

    def __init__(self, session: AgentSession, room: rtc.Room) -> None:
        self._session = session
        self._room = room
        self._mic_sid: str | None = None

        room.on("track_published", self.on_track_published)
        session.on("user_input_transcribed", self.on_user_transcript)

    def on_track_published(
        self,
        track: rtc.RemoteTrackPublication,
        _participant: rtc.RemoteParticipant,
    ) -> None:
        if track.source == rtc.TrackSource.SOURCE_MICROPHONE and self._mic_sid is None:
            self._mic_sid = track.sid

    def on_user_transcript(self, ev: UserInputTranscribedEvent) -> None:
        if not ev.is_final or not ev.transcript.strip():
            return

        asyncio.create_task(self.publish(ev))

    async def publish(self, ev: UserInputTranscribedEvent) -> None:
        user = next(
            (p for p in self._room.remote_participants.values() if not p.is_local),
            None,
        )
        if user is None or not self._room.isconnected():
            return

        try:
            await self._room.local_participant.publish_transcription(
                rtc.Transcription(
                    participant_identity=user.identity,
                    track_sid=self._mic_sid or "",
                    segments=[
                        rtc.TranscriptionSegment(
                            id=ev.item_id or uuid.uuid4().hex,
                            text=ev.transcript,
                            start_time=0,
                            end_time=0,
                            language="",
                            final=True,
                        )
                    ],
                )
            )
        except Exception:
            logger.warning("failed to publish user transcript to room", exc_info=True)