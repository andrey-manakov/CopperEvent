from __future__ import annotations

from telebot import TeleBot, types

from ...config import settings
from ...db import session_scope
from ...repositories import UserRepository
from ...services.events import EventService, event_summary
from ...services.friends import FriendService
from .. import keyboards, texts


def register(bot: TeleBot) -> None:
    @bot.message_handler(commands=["browse"])
    def handle_browse(message: types.Message) -> None:
        show_browse(bot, message.chat.id, message.from_user)


def show_browse(bot: TeleBot, chat_id: int, user: types.User) -> None:
    with session_scope() as session:
        user_repo = UserRepository(session)
        display_name = " ".join(filter(None, [user.first_name, user.last_name])) or None
        db_user = user_repo.get_or_create(
            user.id,
            user.username,
            display_name,
            settings.default_tz,
        )
        friend_service = FriendService(session)
        friend_ids = friend_service.list_friend_ids(db_user.id)
        if not friend_ids:
            bot.send_message(chat_id, texts.NO_FRIENDS)
            return
        event_service = EventService(session)
        displays = event_service.friends_tomorrow_events(db_user.id, friend_ids, db_user.tz)
        if not displays:
            bot.send_message(chat_id, texts.NO_EVENTS)
            return
        for display in displays[:5]:
            summary = event_summary(display.event, display.owner, db_user.tz, joined=display.joined)
            bot.send_message(
                chat_id,
                summary,
                reply_markup=keyboards.event_action_keyboard(
                    display.event.id, joined=display.joined, is_owner=False
                ),
            )
        if len(displays) > 5:
            bot.send_message(chat_id, "Showing first 5 events. Use Share links for more.")
