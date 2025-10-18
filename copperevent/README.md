# CopperEvent Telegram Bot

CopperEvent is a lightweight Telegram bot that helps friends create and join tomorrow-only plans. The bot keeps everything simple: events are private to friends, invitations happen through deep links, and everyone sees what their friends are up to tomorrow.

## Features

- Create tomorrow-only events with a type, location pin, and time slot.
- Discover friends' plans and join or leave with inline buttons.
- Manage events you created or joined, including delete and share links.
- Establish friendships automatically through deep-link invites.
- Store data in a local SQLite database (`copperevent.db`).
- Simple timezone handling with user-configurable IANA timezones.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the environment template and fill in the values:
   ```bash
   cp .env.example .env
   ```
   - `BOT_TOKEN`: Telegram bot token for `@CopperEventUser` (placeholder username).
   - `TZ`: Default timezone (IANA string) applied when users register, e.g., `Europe/Amsterdam`.
   - `LOG_LEVEL`: Logging level (e.g., `INFO`).
4. Run the bot:
   ```bash
   python run.py
   ```

The bot starts polling and automatically initializes the SQLite database on first run.

## Usage

- `/start` – Register the user, greet them, and show the main menu.
- `/new` – Create a new tomorrow event (type → location pin → time slot).
- `/my` – List events you created or joined tomorrow, with actions.
- `/friends` – Show your friends and how many events they have tomorrow.
- `/browse` – See tomorrow's events from your friends and join/leave.
- `/settings` – View or change your timezone (IANA string).
- `/help` – Display short help information.
- `/cancel` – Cancel any ongoing flow.

Events are always scheduled for “tomorrow” in the creator's timezone. Selected local time slots are converted to UTC for storage. When browsing, times are shown in the viewer's timezone.

Share an event via the **Share** button. The generated deep-link invitation (`https://t.me/CopperEventUser?start=inv_<token>`) automatically establishes mutual friendship when a new user starts the bot with it, and optionally previews the shared event.

## Notes

- No background jobs, reminders, or recurring events.
- All data lives in `copperevent.db` in the project root.
- The project uses polling and the [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) library for the bot.
- SQLAlchemy ORM provides simple persistence without migrations.

Enjoy planning tomorrow with your friends!
