from telebot import TeleBot
from telebot.types import CallbackQuery, Message

from keyboards.game_kb import main_menu_keyboard

WELCOME_TEXT = (
    "Привет! Это игра-миниприложение. Здесь ты можешь узнать лор, правила и выполнять игровые задания."
)

GAME_RULES_TEXT = (
    "Правила игры:\n"
    "1. Выполняй задания, чтобы продвигаться по сюжету.\n"
    "2. Собирай награды и открывай новые главы.\n"
    "3. Следи за подсказками и не пропускай уведомления."
)

GAME_LORE_TEXT = (
    "Лор мира:\n"
    "Давным-давно мир был расколот на две фракции. Герои ищут древние артефакты, чтобы восстановить баланс.\n"
    "Твои решения будут определять судьбу королевств."
)

GAME_PLAY_PLACEHOLDER = (
    "Здесь будет игровой процесс. Подписка на каналы проверяется через мини-приложение."
)


MENU_CONTENT = {
    "game_play": GAME_PLAY_PLACEHOLDER,
    "game_rules": GAME_RULES_TEXT,
    "game_lore": GAME_LORE_TEXT,
}


def register_user_game_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def start_command(message: Message) -> None:
        bot.send_message(
            chat_id=message.chat.id,
            text=WELCOME_TEXT,
            reply_markup=main_menu_keyboard(),
        )

    @bot.callback_query_handler(func=lambda call: call.data in MENU_CONTENT)
    def menu_callback(call: CallbackQuery) -> None:
        bot.answer_callback_query(call.id)
        content = MENU_CONTENT.get(call.data, WELCOME_TEXT)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=content,
            reply_markup=main_menu_keyboard(),
        )
