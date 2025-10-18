from __future__ import annotations

from telebot import TeleBot, types

from ...config import settings
from ...db import session_scope
from ...models import User
from ...repositories import UserRepository
from ...services.events import EventService, event_summary
from ...services.friends import FriendService
from ...services.invites import parse_invite_token
from .. import keyboards, texts
from . import new_event
from . import settings as settings_handler


def register(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def handle_start(message: types.Message) -> None:
        start_param = ""
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) == 2:
            start_param = parts[1]
        with session_scope() as session:
            user_repo = UserRepository(session)
            display_name = " ".join(filter(None, [message.from_user.first_name, message.from_user.last_name])) or None
            username = message.from_user.username
            user = user_repo.get_or_create(
                message.from_user.id,
                username,
                display_name,
                settings.default_tz,
            )
            invite = parse_invite_token(start_param)
            event_to_show = None
            if invite:
                friend_service = FriendService(session)
                friend_service.befriend(user.id, invite.inviter_id)
                if invite.event_id:
                    event_service = EventService(session)
                    event_to_show = event_service.get_event(invite.event_id)
            greeting = texts.WELCOME
            bot.send_message(
                message.chat.id,
                greeting,
                reply_markup=keyboards.main_menu_keyboard(),
            )
            if invite and invite.inviter_id != user.id:
                bot.send_message(message.chat.id, "Friendship established!")
            if event_to_show:
                event_service = EventService(session)
                owner = session.get(User, event_to_show.owner_id)
                if owner:
                    joined = event_service.is_joined(event_to_show.id, user.id)
                    summary = event_summary(event_to_show, owner, user.tz, joined=joined)
                    bot.send_message(
                        message.chat.id,
                        summary,
                        reply_markup=keyboards.event_action_keyboard(
                            event_to_show.id, joined=joined, is_owner=(owner.id == user.id)
                        ),
                    )

    @bot.message_handler(commands=["help"])
    def handle_help(message: types.Message) -> None:
        bot.send_message(message.chat.id, texts.HELP)

    @bot.message_handler(commands=["cancel"])
    def handle_cancel(message: types.Message) -> None:
        new_event.cancel_flow(message.from_user.id)
        settings_handler.cancel_waiting(message.from_user.id)
        bot.send_message(message.chat.id, texts.CANCELLED)

    @bot.message_handler(func=lambda m: m.text and m.text.lower() == "help")
    def handle_help_button(message: types.Message) -> None:
        bot.send_message(message.chat.id, texts.HELP)

    @bot.message_handler(func=lambda m: m.text and m.text.lower() == "browse")
    def browse_button(message: types.Message) -> None:
        from . import browse as browse_handler

        browse_handler.show_browse(bot, message.chat.id, message.from_user)

    @bot.message_handler(func=lambda m: m.text and m.text.lower() == "my")
    def my_button(message: types.Message) -> None:
        from . import my as my_handler

        my_handler.show_my_events(bot, message.chat.id, message.from_user)

    @bot.message_handler(func=lambda m: m.text and m.text.lower() == "friends")
    def friends_button(message: types.Message) -> None:
        from . import friends as friends_handler

        friends_handler.show_friends(bot, message.chat.id, message.from_user)

    @bot.message_handler(func=lambda m: m.text and m.text.lower() == "settings")
    def settings_button(message: types.Message) -> None:
        settings_handler.prompt_timezone(bot, message.chat.id, message.from_user)

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("NAV:"))
    def handle_navigation(call: types.CallbackQuery) -> None:
        action = call.data.split(":", maxsplit=1)[1].upper()
        chat_id = call.message.chat.id if call.message else None
        if not chat_id:
            bot.answer_callback_query(call.id)
            return
        bot.answer_callback_query(call.id)
        if action == "NEW":
            new_event.begin_flow(bot, chat_id, call.from_user)
            return
        if action == "MY":
            from . import my as my_handler

            my_handler.show_my_events(bot, chat_id, call.from_user)
            return
        if action == "BROWSE":
            from . import browse as browse_handler

            browse_handler.show_browse(bot, chat_id, call.from_user)
            return
        if action == "FRIENDS":
            from . import friends as friends_handler

            friends_handler.show_friends(bot, chat_id, call.from_user)
            return
        if action == "SETTINGS":
            settings_handler.prompt_timezone(bot, chat_id, call.from_user)
            return
        if action == "HELP":
            bot.send_message(chat_id, texts.HELP)
