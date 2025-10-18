from __future__ import annotations

from typing import Set

from telebot import TeleBot, types

from ...config import settings as app_settings
from ...db import session_scope
from ...repositories import UserRepository
from ...services.timezone import is_valid_timezone
from .. import texts

_waiting_timezone: Set[int] = set()


def register(bot: TeleBot) -> None:
    @bot.message_handler(commands=["settings"])
    def handle_settings(message: types.Message) -> None:
        prompt_timezone(bot, message.chat.id, message.from_user)

    @bot.message_handler(func=lambda m: m.from_user.id in _waiting_timezone)
    def receive_timezone(message: types.Message) -> None:
        tz_value = (message.text or "").strip()
        if not is_valid_timezone(tz_value):
            bot.send_message(message.chat.id, texts.INVALID_TIMEZONE)
            return
        with session_scope() as session:
            user_repo = UserRepository(session)
            display_name = " ".join(filter(None, [message.from_user.first_name, message.from_user.last_name])) or None
            user = user_repo.get_or_create(
                message.from_user.id,
                message.from_user.username,
                display_name,
                app_settings.default_tz,
            )
            user_repo.update_timezone(user, tz_value)
            bot.send_message(message.chat.id, texts.TIMEZONE_UPDATED)
        _waiting_timezone.discard(message.from_user.id)


def prompt_timezone(bot: TeleBot, chat_id: int, user: types.User) -> None:
    with session_scope() as session:
        user_repo = UserRepository(session)
        display_name = " ".join(filter(None, [user.first_name, user.last_name])) or None
        db_user = user_repo.get_or_create(
            user.id,
            user.username,
            display_name,
            app_settings.default_tz,
        )
        bot.send_message(chat_id, f"Current timezone: {db_user.tz}\n{texts.ASK_TIMEZONE}")
    _waiting_timezone.add(user.id)


def cancel_waiting(user_id: int) -> None:
    _waiting_timezone.discard(user_id)
