import threading

import uvicorn
from telebot import TeleBot

from api_server import create_api_app
from config import load_settings
from handlers.user_game import register_user_game_handlers
from reminders import ReminderService
from storage import Database



def start_api_server(app) -> threading.Thread:
    """Run the FastAPI server in a separate thread."""
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info"),
        daemon=True,
    )
    server_thread.start()
    return server_thread


def main() -> None:
    settings = load_settings()
    bot = TeleBot(settings.bot_token, parse_mode="HTML")

    db = Database(settings.db_path)
    db.init()
    reminder_service = ReminderService(bot, db, game_url=settings.game_url)
    reminder_service.start()

    register_user_game_handlers(bot, db)

    app = create_api_app(bot, settings.api_secret, db, reminder_service)
    start_api_server(app)

    bot.infinity_polling(skip_pending=True, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
