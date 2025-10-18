from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Optional

INVITE_PREFIX = "inv_"


@dataclass
class InvitePayload:
    inviter_id: int
    event_id: Optional[int] = None


def _encode_payload(payload: InvitePayload) -> str:
    event_part = str(payload.event_id) if payload.event_id is not None else ""
    raw = f"{payload.inviter_id}:{event_part}".encode()
    token = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    return token


def _decode_payload(token: str) -> Optional[InvitePayload]:
    padding = '=' * (-len(token) % 4)
    try:
        decoded = base64.urlsafe_b64decode(token + padding).decode()
    except Exception:
        return None
    parts = decoded.split(":", maxsplit=1)
    if not parts or not parts[0].isdigit():
        return None
    inviter_id = int(parts[0])
    event_id = None
    if len(parts) == 2 and parts[1].isdigit():
        event_id = int(parts[1])
    return InvitePayload(inviter_id=inviter_id, event_id=event_id)


def generate_invite_token(inviter_id: int, event_id: Optional[int] = None) -> str:
    payload = InvitePayload(inviter_id=inviter_id, event_id=event_id)
    token = _encode_payload(payload)
    return f"{INVITE_PREFIX}{token}"


def parse_invite_token(start_param: str) -> Optional[InvitePayload]:
    if not start_param or not start_param.startswith(INVITE_PREFIX):
        return None
    token = start_param[len(INVITE_PREFIX) :]
    return _decode_payload(token)
