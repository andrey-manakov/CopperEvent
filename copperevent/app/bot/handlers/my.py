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
        show_my_events(bot, message.chat.id, message.from_user)


def show_my_events(bot: TeleBot, chat_id: int, user: types.User) -> None:
    with session_scope() as session:
        user_repo = UserRepository(session)
        display_name = " ".join(filter(None, [user.first_name, user.last_name])) or None
        db_user = user_repo.get_or_create(
            user.id,
            user.username,
            display_name,
            settings.default_tz,
        )
        event_service = EventService(session)
        created, joined = event_service.my_tomorrow_events(db_user.id, db_user.tz)
        if not created and not joined:
            bot.send_message(chat_id, texts.NO_EVENTS)
            return
        if created:
            bot.send_message(chat_id, "Created by you:")
            for event in created:
                summary = event_summary(event, db_user, db_user.tz, joined=True)
                bot.send_message(
                    chat_id,
                    summary,
                    reply_markup=keyboards.event_action_keyboard(event.id, joined=True, is_owner=True),
                )
        if joined:
            bot.send_message(chat_id, "Joined events:")
            for event in joined:
                owner = session.get(User, event.owner_id)
                if not owner:
                    continue
                summary = event_summary(event, owner, db_user.tz, joined=True)
                bot.send_message(
                    chat_id,
                    summary,
                    reply_markup=keyboards.event_action_keyboard(event.id, joined=True, is_owner=False),
                )
