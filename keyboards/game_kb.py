from telebot import types


def main_menu_keyboard(notify_on: bool) -> types.InlineKeyboardMarkup:
    """Create the main inline keyboard for game navigation."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        # types.InlineKeyboardButton(text="🎮 Играть", callback_data="game_play"),
        types.InlineKeyboardButton(text="📜 Правила", callback_data="game_rules"),
        types.InlineKeyboardButton(text="📖 Лор", callback_data="game_lore"),
        types.InlineKeyboardButton(
            text="🔕 Не уведомлять о Сбое" if notify_on else "🔔 Уведомлять о Сбое",
            callback_data="notify_toggle",
        ),
    )
    return keyboard


def legal_accept_keyboard() -> types.InlineKeyboardMarkup:
    """Create inline keyboard for legal acceptance."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="✅ Принимаю правила", callback_data="legal_accept"),
    )
    return keyboard


def notification_keyboard(notify_on: bool, show_enter: bool, enter_url: str | None) -> types.InlineKeyboardMarkup:
    """Create inline keyboard for notifications."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if show_enter and enter_url:
        keyboard.add(
            types.InlineKeyboardButton(text="➡️ Войти в Сбой", url=enter_url),
        )
    keyboard.add(
        types.InlineKeyboardButton(
            text="🔕 Не уведомлять о Сбое" if notify_on else "🔔 Уведомлять о Сбое",
            callback_data="notify_toggle",
        ),
    )
    return keyboard
