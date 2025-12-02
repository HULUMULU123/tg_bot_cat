from telebot import types


def main_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Create the main inline keyboard for game navigation."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="🎮 Играть", callback_data="game_play"),
        types.InlineKeyboardButton(text="📜 Правила", callback_data="game_rules"),
        types.InlineKeyboardButton(text="📖 Лор", callback_data="game_lore"),
    )
    return keyboard
