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
        show_browse(bot, message)


def show_browse(bot: TeleBot, message: types.Message) -> None:
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
        friend_ids = friend_service.list_friend_ids(user.id)
        if not friend_ids:
            bot.send_message(message.chat.id, texts.NO_FRIENDS)
            return
        event_service = EventService(session)
        displays = event_service.friends_tomorrow_events(user.id, friend_ids, user.tz)
        if not displays:
            bot.send_message(message.chat.id, texts.NO_EVENTS)
            return
        for display in displays[:5]:
            summary = event_summary(display.event, display.owner, user.tz, joined=display.joined)
            bot.send_message(
                message.chat.id,
                summary,
                reply_markup=keyboards.event_action_keyboard(
                    display.event.id, joined=display.joined, is_owner=False
                ),
            )
        if len(displays) > 5:
            bot.send_message(message.chat.id, "Showing first 5 events. Use Share links for more.")
