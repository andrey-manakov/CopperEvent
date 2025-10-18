from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional, Sequence

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from .models import Event, Friendship, RSVP, User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create(self, user_id: int, username: Optional[str], display_name: Optional[str], tz: str) -> User:
        user = self.session.get(User, user_id)
        if user:
            updated = False
            if username is not None and user.username != username:
                user.username = username
                updated = True
            if display_name is not None and user.display_name != display_name:
                user.display_name = display_name
                updated = True
            if tz and user.tz != tz:
                user.tz = tz
                updated = True
            if updated:
                self.session.add(user)
            return user
        user = User(id=user_id, username=username, display_name=display_name, tz=tz)
        self.session.add(user)
        return user

    def update_timezone(self, user: User, tz: str) -> None:
        user.tz = tz
        self.session.add(user)


class FriendshipRepository:
    def __init__(self, session: Session):
        self.session = session

    def befriend(self, user_id: int, friend_id: int) -> None:
        if user_id == friend_id:
            return
        existing = self.session.execute(
            select(Friendship).where(Friendship.user_id == user_id, Friendship.friend_id == friend_id)
        ).scalar_one_or_none()
        if existing:
            return
        friendship = Friendship(user_id=user_id, friend_id=friend_id, status="accepted")
        self.session.add(friendship)

    def list_friend_ids(self, user_id: int) -> List[int]:
        result = self.session.execute(
            select(Friendship.friend_id).where(Friendship.user_id == user_id, Friendship.status == "accepted")
        )
        return [row[0] for row in result]

    def friends_with_counts(self, user_id: int, tomorrow_range: tuple[datetime, datetime]) -> List[tuple[User, int]]:
        start_utc, end_utc = tomorrow_range
        subquery = (
            select(Event.owner_id.label("uid"), func.count(Event.id).label("cnt"))
            .where(and_(Event.start_time_utc >= start_utc, Event.start_time_utc < end_utc))
            .group_by(Event.owner_id)
            .subquery()
        )
        stmt = (
            select(User, func.coalesce(subquery.c.cnt, 0))
            .join(Friendship, Friendship.friend_id == User.id)
            .join(subquery, subquery.c.uid == User.id, isouter=True)
            .where(Friendship.user_id == user_id, Friendship.status == "accepted")
            .order_by(User.display_name.nullslast(), User.username.nullslast())
        )
        result = self.session.execute(stmt).all()
        return [(row[0], row[1]) for row in result]


class EventRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, event: Event, owner: User) -> Event:
        event.owner = owner
        self.session.add(event)
        return event

    def get(self, event_id: int) -> Optional[Event]:
        return self.session.get(Event, event_id)

    def delete(self, event: Event) -> None:
        self.session.delete(event)

    def list_for_user(self, user_id: int, tomorrow_range: tuple[datetime, datetime]) -> List[Event]:
        start_utc, end_utc = tomorrow_range
        stmt = select(Event).where(
            and_(
                Event.owner_id == user_id,
                Event.start_time_utc >= start_utc,
                Event.start_time_utc < end_utc,
            )
        ).order_by(Event.start_time_utc.asc())
        return list(self.session.execute(stmt).scalars())

    def list_joined(self, user_id: int, tomorrow_range: tuple[datetime, datetime]) -> List[Event]:
        start_utc, end_utc = tomorrow_range
        stmt = (
            select(Event)
            .join(RSVP, RSVP.event_id == Event.id)
            .where(
                and_(
                    RSVP.user_id == user_id,
                    Event.start_time_utc >= start_utc,
                    Event.start_time_utc < end_utc,
                )
            )
            .order_by(Event.start_time_utc.asc())
        )
        return list(self.session.execute(stmt).scalars())

    def list_friends_events(
        self,
        user_id: int,
        friend_ids: Sequence[int],
        tomorrow_range: tuple[datetime, datetime],
    ) -> List[Event]:
        if not friend_ids:
            return []
        start_utc, end_utc = tomorrow_range
        stmt = (
            select(Event)
            .where(
                and_(
                    Event.owner_id.in_(friend_ids),
                    Event.start_time_utc >= start_utc,
                    Event.start_time_utc < end_utc,
                )
            )
            .order_by(Event.start_time_utc.asc())
        )
        events = list(self.session.execute(stmt).scalars())
        return [event for event in events if event.owner_id != user_id]

    def friends_events_with_join_status(
        self,
        user_id: int,
        friend_ids: Sequence[int],
        tomorrow_range: tuple[datetime, datetime],
    ) -> List[tuple[Event, bool]]:
        if not friend_ids:
            return []
        start_utc, end_utc = tomorrow_range
        stmt = (
            select(Event, RSVP.user_id)
            .join(RSVP, and_(RSVP.event_id == Event.id, RSVP.user_id == user_id), isouter=True)
            .where(
                and_(
                    Event.owner_id.in_(friend_ids),
                    Event.start_time_utc >= start_utc,
                    Event.start_time_utc < end_utc,
                )
            )
            .order_by(Event.start_time_utc.asc())
        )
        rows = self.session.execute(stmt).all()
        return [(row[0], row[1] is not None) for row in rows if row[0].owner_id != user_id]


class RSVPRepository:
    def __init__(self, session: Session):
        self.session = session

    def join(self, event_id: int, user_id: int) -> RSVP:
        existing = self.session.execute(
            select(RSVP).where(RSVP.event_id == event_id, RSVP.user_id == user_id)
        ).scalar_one_or_none()
        if existing:
            return existing
        rsvp = RSVP(event_id=event_id, user_id=user_id, status="joined")
        self.session.add(rsvp)
        return rsvp

    def leave(self, event_id: int, user_id: int) -> None:
        stmt = delete(RSVP).where(RSVP.event_id == event_id, RSVP.user_id == user_id)
        self.session.execute(stmt)

    def is_joined(self, event_id: int, user_id: int) -> bool:
        stmt = select(func.count()).select_from(RSVP).where(RSVP.event_id == event_id, RSVP.user_id == user_id)
        count = self.session.execute(stmt).scalar_one()
        return count > 0

    def attendees(self, event_id: int) -> Iterable[RSVP]:
        stmt = select(RSVP).where(RSVP.event_id == event_id)
        return list(self.session.execute(stmt).scalars())
