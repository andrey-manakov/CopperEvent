from telebot import TeleBot, types

from app.config import settings
from app.db import engine
from app.models import Base
from app.utils.logging import setup_logging
from app.bot.handlers import browse, callbacks, friends, my, new_event, settings as settings_handler, start


def main() -> None:
    setup_logging(settings.log_level)
    Base.metadata.create_all(engine)
    bot = TeleBot(settings.bot_token, parse_mode="HTML")

    for handler in [
        start,
        new_event,
        browse,
        my,
        friends,
        settings_handler,
        callbacks,
    ]:
        handler.register(bot)

    bot.set_my_commands(
        [
            types.BotCommand("start", "Start the bot"),
            types.BotCommand("new", "Create a new plan"),
            types.BotCommand("my", "My events"),
            types.BotCommand("browse", "Browse friends' events"),
            types.BotCommand("friends", "Friends list"),
            types.BotCommand("settings", "Change timezone"),
            types.BotCommand("help", "Help"),
            types.BotCommand("cancel", "Cancel current action"),
        ]
    )

    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
