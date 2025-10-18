from __future__ import annotations

from telebot import TeleBot, types

from ...config import settings
from ...db import session_scope
from ...repositories import UserRepository
from ...models import User
from ...services.events import EventService, event_summary
from .. import keyboards, texts


def register(bot: TeleBot) -> None:
    @bot.message_handler(commands=["my"])
    def handle_my(message: types.Message) -> None:
        show_my_events(bot, message)


def show_my_events(bot: TeleBot, message: types.Message) -> None:
    with session_scope() as session:
        user_repo = UserRepository(session)
        display_name = " ".join(filter(None, [message.from_user.first_name, message.from_user.last_name])) or None
        user = user_repo.get_or_create(
            message.from_user.id,
            message.from_user.username,
            display_name,
            settings.default_tz,
        )
        event_service = EventService(session)
        created, joined = event_service.my_tomorrow_events(user.id, user.tz)
        if not created and not joined:
            bot.send_message(message.chat.id, texts.NO_EVENTS)
            return
        if created:
            bot.send_message(message.chat.id, "Created by you:")
            for event in created:
                summary = event_summary(event, user, user.tz, joined=True)
                bot.send_message(
                    message.chat.id,
                    summary,
                    reply_markup=keyboards.event_action_keyboard(event.id, joined=True, is_owner=True),
                )
        if joined:
            bot.send_message(message.chat.id, "Joined events:")
            for event in joined:
                owner = session.get(User, event.owner_id)
                if not owner:
                    continue
                summary = event_summary(event, owner, user.tz, joined=True)
                bot.send_message(
                    message.chat.id,
                    summary,
                    reply_markup=keyboards.event_action_keyboard(event.id, joined=True, is_owner=False),
                )
