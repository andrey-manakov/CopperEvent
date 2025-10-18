from __future__ import annotations

from telebot import TeleBot, types

from ...config import settings
from ...db import session_scope
from ...models import User
from ...repositories import UserRepository
from ...services.events import EventService, event_summary
from .. import keyboards, texts


def register(bot: TeleBot) -> None:
    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("JOIN:"))
    def handle_join(call: types.CallbackQuery) -> None:
        event_id = int(call.data.split(":", 1)[1])
        with session_scope() as session:
            user_repo = UserRepository(session)
            display_name = " ".join(filter(None, [call.from_user.first_name, call.from_user.last_name])) or None
            user = user_repo.get_or_create(
                call.from_user.id,
                call.from_user.username,
                display_name,
                settings.default_tz,
            )
            event_service = EventService(session)
            event = event_service.get_event(event_id)
            if not event:
                bot.answer_callback_query(call.id, texts.MISSING_EVENT)
                return
            if event_service.is_joined(event_id, user.id):
                bot.answer_callback_query(call.id, texts.ALREADY_JOINED)
                return
            event_service.join_event(event_id, user.id)
            bot.answer_callback_query(call.id, texts.JOINED_EVENT)
            markup = keyboards.event_action_keyboard(event_id, joined=True, is_owner=(event.owner_id == user.id))
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("LEAVE:"))
    def handle_leave(call: types.CallbackQuery) -> None:
        event_id = int(call.data.split(":", 1)[1])
        with session_scope() as session:
            user_repo = UserRepository(session)
            display_name = " ".join(filter(None, [call.from_user.first_name, call.from_user.last_name])) or None
            user = user_repo.get_or_create(
                call.from_user.id,
                call.from_user.username,
                display_name,
                settings.default_tz,
            )
            event_service = EventService(session)
            event = event_service.get_event(event_id)
            if not event:
                bot.answer_callback_query(call.id, texts.MISSING_EVENT)
                return
            if not event_service.is_joined(event_id, user.id):
                bot.answer_callback_query(call.id, texts.NOT_JOINED)
                return
            event_service.leave_event(event_id, user.id)
            bot.answer_callback_query(call.id, texts.LEFT_EVENT)
            markup = keyboards.event_action_keyboard(event_id, joined=False, is_owner=(event.owner_id == user.id))
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("DELETE:"))
    def handle_delete(call: types.CallbackQuery) -> None:
        event_id = int(call.data.split(":", 1)[1])
        with session_scope() as session:
            user_repo = UserRepository(session)
            display_name = " ".join(filter(None, [call.from_user.first_name, call.from_user.last_name])) or None
            user = user_repo.get_or_create(
                call.from_user.id,
                call.from_user.username,
                display_name,
                settings.default_tz,
            )
            event_service = EventService(session)
            event = event_service.get_event(event_id)
            if not event:
                bot.answer_callback_query(call.id, texts.MISSING_EVENT)
                return
            if event.owner_id != user.id:
                bot.answer_callback_query(call.id, texts.NOT_OWNER)
                return
            event_service.delete_event(event)
            bot.answer_callback_query(call.id, texts.EVENT_DELETED)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("VIEW:"))
    def handle_view(call: types.CallbackQuery) -> None:
        event_id = int(call.data.split(":", 1)[1])
        with session_scope() as session:
            user_repo = UserRepository(session)
            display_name = " ".join(filter(None, [call.from_user.first_name, call.from_user.last_name])) or None
            user = user_repo.get_or_create(
                call.from_user.id,
                call.from_user.username,
                display_name,
                settings.default_tz,
            )
            event_service = EventService(session)
            event = event_service.get_event(event_id)
            if not event:
                bot.answer_callback_query(call.id, texts.MISSING_EVENT)
                return
            owner = session.get(User, event.owner_id)
            if not owner:
                bot.answer_callback_query(call.id, texts.MISSING_EVENT)
                return
            joined = event_service.is_joined(event_id, user.id)
            summary = event_summary(event, owner, user.tz, joined=joined)
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, summary)

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("SHARE:"))
    def handle_share(call: types.CallbackQuery) -> None:
        event_id = int(call.data.split(":", 1)[1])
        with session_scope() as session:
            user_repo = UserRepository(session)
            display_name = " ".join(filter(None, [call.from_user.first_name, call.from_user.last_name])) or None
            user = user_repo.get_or_create(
                call.from_user.id,
                call.from_user.username,
                display_name,
                settings.default_tz,
            )
            event_service = EventService(session)
            event = event_service.get_event(event_id)
            if not event:
                bot.answer_callback_query(call.id, texts.MISSING_EVENT)
                return
            if event.owner_id != user.id and not event_service.is_joined(event_id, user.id):
                bot.answer_callback_query(call.id, "Join before sharing!")
                return
            link = event_service.share_link(event)
            bot.answer_callback_query(call.id, "Share link sent")
            bot.send_message(call.message.chat.id, f"Share this link:\n{link}")
