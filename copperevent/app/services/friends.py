from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..models import User
from ..repositories import FriendshipRepository
from ..utils import dates


class FriendService:
    def __init__(self, session: Session):
        self.session = session
        self.friend_repo = FriendshipRepository(session)

    def befriend(self, user_id: int, friend_id: int) -> None:
        self.friend_repo.befriend(user_id, friend_id)
        self.friend_repo.befriend(friend_id, user_id)

    def list_friend_ids(self, user_id: int) -> List[int]:
        return self.friend_repo.list_friend_ids(user_id)

    def friends_with_counts(self, user_id: int, tz_name: str) -> List[tuple[User, int]]:
        tomorrow_range = dates.tomorrow_range_utc(tz_name)
        return self.friend_repo.friends_with_counts(user_id, tomorrow_range)
