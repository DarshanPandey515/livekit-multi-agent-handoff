import os
import uuid

from adrf.decorators import api_view
from livekit.api import AccessToken, ListRoomsRequest, LiveKitAPI, VideoGrants
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["POST"])
@permission_classes([AllowAny])
async def get_token(request):
    identity = str(request.data.get("identity") or f"caller-{uuid.uuid4().hex[:8]}")
    room = str(request.data.get("room") or f"support-{uuid.uuid4().hex[:8]}")

    token = (
        AccessToken()
        .with_identity(identity)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )

    return Response(
        {
            "token": token,
            "url": os.getenv("LIVEKIT_URL"),
            "room": room,
            "identity": identity,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
async def list_rooms(request):
    async with LiveKitAPI() as lkapi:
        resp = await lkapi.room.list_rooms(ListRoomsRequest())
    
    return Response(
        {
            "rooms": [
                {"name": r.name, "num_participants": r.num_participants}
                for r in resp.rooms
            ]
        }
    )