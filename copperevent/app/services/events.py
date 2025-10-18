from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from sqlalchemy.orm import Session

from ..models import Event, RSVP, User
from ..repositories import EventRepository, RSVPRepository
from ..utils import dates
from .invites import generate_invite_token


@dataclass
class EventDisplay:
    event: Event
    owner: User
    joined: bool = False


class EventService:
    def __init__(self, session: Session):
        self.session = session
        self.event_repo = EventRepository(session)
        self.rsvp_repo = RSVPRepository(session)

    def create_event(
        self,
        owner: User,
        title: str,
        lat: float,
        lon: float,
        time_slot: str,
        tz_name: str,
    ) -> Event:
        tomorrow = dates.tomorrow_date(tz_name)
        start_dt_utc = dates.slot_to_utc_datetime(tomorrow, time_slot, tz_name)
        event = Event(
            owner_id=owner.id,
            title=title.strip(),
            date_utc=start_dt_utc.date(),
            start_time_utc=start_dt_utc,
            loc_lat=lat,
            loc_lon=lon,
            privacy="friends",
        )
        self.event_repo.create(event, owner)
        self.session.flush()
        self.rsvp_repo.join(event.id, owner.id)
        return event

    def delete_event(self, event: Event) -> None:
        self.event_repo.delete(event)

    def join_event(self, event_id: int, user_id: int) -> Optional[RSVP]:
        return self.rsvp_repo.join(event_id, user_id)

    def leave_event(self, event_id: int, user_id: int) -> None:
        self.rsvp_repo.leave(event_id, user_id)

    def is_joined(self, event_id: int, user_id: int) -> bool:
        return self.rsvp_repo.is_joined(event_id, user_id)

    def get_event(self, event_id: int) -> Optional[Event]:
        return self.event_repo.get(event_id)

    def attendees(self, event_id: int) -> Iterable[RSVP]:
        return self.rsvp_repo.attendees(event_id)

    def friends_tomorrow_events(
        self, user_id: int, friend_ids: Sequence[int], tz_name: str
    ) -> List[EventDisplay]:
        tomorrow_range = dates.tomorrow_range_utc(tz_name)
        rows = self.event_repo.friends_events_with_join_status(user_id, friend_ids, tomorrow_range)
        displays: List[EventDisplay] = []
        for event, joined in rows:
            owner = self.session.get(User, event.owner_id)
            if not owner:
                continue
            displays.append(EventDisplay(event=event, owner=owner, joined=joined))
        return displays

    def my_tomorrow_events(self, user_id: int, tz_name: str) -> tuple[List[Event], List[Event]]:
        tomorrow_range = dates.tomorrow_range_utc(tz_name)
        created = self.event_repo.list_for_user(user_id, tomorrow_range)
        joined = self.event_repo.list_joined(user_id, tomorrow_range)
        return created, [event for event in joined if event.owner_id != user_id]

    def share_link(self, event: Event) -> str:
        token = generate_invite_token(event.owner_id, event.id)
        return f"https://t.me/CopperEventUser?start={token}"


def event_summary(event: Event, owner: User, viewer_tz: str, joined: bool = False) -> str:
    time_str = dates.format_event_time_local(event.start_time_utc, viewer_tz)
    owner_name = owner.display_name or owner.username or f"User {owner.id}"
    status = "✅ Joined" if joined else ""
    pieces = [f"{event.title.strip()} • {time_str}"]
    pieces.append(f"Host: {owner_name}")
    pieces.append(f"Location: {event.loc_lat:.5f}, {event.loc_lon:.5f}")
    if status:
        pieces.append(status)
    return "\n".join(pieces)


def event_compact(event: Event, viewer_tz: str) -> str:
    time_str = dates.format_event_time_local(event.start_time_utc, viewer_tz)
    return f"{event.title.strip()} • {time_str}"
