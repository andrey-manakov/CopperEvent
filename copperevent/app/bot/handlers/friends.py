from __future__ import annotations

from telebot import TeleBot, types

from ...config import settings
from ...db import session_scope
from ...repositories import UserRepository
from ...services.friends import FriendService
from .. import texts


def register(bot: TeleBot) -> None:
    @bot.message_handler(commands=["friends"])
    def handle_friends(message: types.Message) -> None:
        show_friends(bot, message)


def show_friends(bot: TeleBot, message: types.Message) -> None:
    with session_scope() as session:
        user_repo = UserRepository(session)
        display_name = " ".join(filter(None, [message.from_user.first_name, message.from_user.last_name])) or None
        user = user_repo.get_or_create(
            message.from_user.id,
            message.from_user.username,
            display_name,
            settings.default_tz,
        )
        friend_service = FriendService(session)
        friends = friend_service.friends_with_counts(user.id, user.tz)
        if not friends:
            bot.send_message(message.chat.id, texts.NO_FRIENDS)
            return
        lines = ["Friends and their plans for tomorrow:"]
        for friend, count in friends:
            name = friend.display_name or friend.username or f"User {friend.id}"
            lines.append(f"• {name} – {count} event(s)")
        lines.append("Use /browse to see details.")
        bot.send_message(message.chat.id, "\n".join(lines))
