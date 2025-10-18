from __future__ import annotations

from typing import Dict

from telebot import TeleBot, types

from ...config import settings
from ...db import session_scope
from ...models import User
from ...repositories import UserRepository
from ...services.events import EventService, event_summary
from ...utils.dates import TIME_SLOTS
from .. import keyboards, texts

_user_states: Dict[int, Dict[str, object]] = {}


def _reset_state(user_id: int) -> None:
    _user_states.pop(user_id, None)


def cancel_flow(user_id: int) -> None:
    _reset_state(user_id)


def register(bot: TeleBot) -> None:
    @bot.message_handler(commands=["new"])
    def handle_new(message: types.Message) -> None:
        _begin_flow(bot, message)

    @bot.message_handler(func=lambda m: m.text and m.text.lower() == "new")
    def handle_new_button(message: types.Message) -> None:
        _begin_flow(bot, message)

    @bot.message_handler(func=lambda m: _user_states.get(m.from_user.id, {}).get("step") == "type")
    def handle_type(message: types.Message) -> None:
        text = (message.text or "").strip()
        if not text:
            bot.reply_to(message, "Please send a short description.")
            return
        if len(text) > 120:
            bot.reply_to(message, "Keep it short (max 120 characters).")
            return
        state = _user_states.get(message.from_user.id)
        if not state:
            return
        state["data"] = {"title": text}
        state["step"] = "location"
        bot.send_message(message.chat.id, texts.PROMPT_LOCATION)

    @bot.message_handler(
        content_types=["location"],
        func=lambda m: _user_states.get(m.from_user.id, {}).get("step") == "location",
    )
    def handle_location(message: types.Message) -> None:
        if not message.location:
            bot.reply_to(message, texts.INVALID_LOCATION)
            return
        state = _user_states.get(message.from_user.id)
        if not state:
            return
        state.setdefault("data", {})
        state["data"].update({"lat": message.location.latitude, "lon": message.location.longitude})
        state["step"] = "time"
        bot.send_message(message.chat.id, texts.PROMPT_TIME, reply_markup=keyboards.time_slot_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("TIME:"))
    def handle_time(call: types.CallbackQuery) -> None:
        slot = call.data.split(":", maxsplit=1)[1]
        user_id = call.from_user.id
        state = _user_states.get(user_id)
        if not state or state.get("step") != "time":
            bot.answer_callback_query(call.id)
            return
        if slot not in TIME_SLOTS:
            bot.answer_callback_query(call.id, "Invalid time")
            return
        data = state.get("data", {})
        title = data.get("title")
        lat = data.get("lat")
        lon = data.get("lon")
        if not title or lat is None or lon is None:
            bot.answer_callback_query(call.id, "Missing data")
            _reset_state(user_id)
            return
        with session_scope() as session:
            user_repo = UserRepository(session)
            display_name = " ".join(filter(None, [call.from_user.first_name, call.from_user.last_name])) or None
            username = call.from_user.username
            tz_name = settings.default_tz
            user = user_repo.get_or_create(user_id, username, display_name, tz_name)
            event_service = EventService(session)
            event = event_service.create_event(user, title, lat, lon, slot, user.tz)
            summary = event_summary(event, user, user.tz, joined=True)
            bot.answer_callback_query(call.id, texts.EVENT_CREATED)
            bot.send_message(
                call.message.chat.id,
                summary,
                reply_markup=keyboards.event_action_keyboard(event.id, joined=True, is_owner=True),
            )
            share_link = event_service.share_link(event)
            bot.send_message(
                call.message.chat.id,
                f"Share this link with friends:\n{share_link}",
            )
        _reset_state(user_id)


def _begin_flow(bot: TeleBot, message: types.Message) -> None:
    user_id = message.from_user.id
    _user_states[user_id] = {"step": "type", "data": {}}
    bot.send_message(message.chat.id, texts.PROMPT_EVENT_TYPE)
