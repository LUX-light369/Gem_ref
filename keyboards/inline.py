from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models.database import bot_data

def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ /play", callback_data="menu_play"); builder.button(text="⏸ /pause", callback_data="menu_pause")
    builder.button(text="⏹ /stop", callback_data="menu_stop"); builder.button(text="📂 /upload", callback_data="menu_upload")
    builder.button(text="✅ РУЧНАЯ ПРОВЕРКА ✅", callback_data="menu_verify")
    settings = bot_data.chats.get(bot_data.default_chat_id) if bot_data.default_chat_id else None
    builder.button(text=f"🎲 Кубики: {'ВКЛ' if settings and settings.dice_enabled else 'ВЫКЛ'}", callback_data="menu_dice_toggle")
    builder.button(text=f"🎰 Слот: {'ВКЛ' if settings and settings.slot_enabled else 'ВЫКЛ'}", callback_data="menu_slot_toggle")
    builder.button(text=f"🎫 Лото: {'ВКЛ' if settings and settings.loto_enabled else 'ВЫКЛ'}", callback_data="menu_loto_toggle")
    builder.button(text=f"⚓ Морской бой: {'ВКЛ' if settings and settings.sea_battle_enabled else 'ВЫКЛ'}", callback_data="menu_sea_battle_toggle")
    builder.button(text="⚙️ Настройки", callback_data="menu_settings")
    builder.adjust(2, 2, 1, 2, 2, 1); return builder.as_markup()

def settings_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📌 Мой чат", callback_data="settings_my_chat"); builder.button(text="📢 Мой канал", callback_data="settings_my_channel")
    builder.button(text="⏱ Интервал", callback_data="settings_my_interval"); builder.button(text="🔗 Ссылка приглашения", callback_data="settings_invite_link")
    builder.button(text="🔔 Проверка подписки", callback_data="settings_sub_check")
    builder.button(text="💬 Стартовое сообщение", callback_data="settings_start_msg")
    builder.button(text="🎫 Настройки ЛОТО", callback_data="settings_loto"); builder.button(text="⚓ Настройки Морского боя", callback_data="settings_sea_battle")
    builder.button(text="📋 Все чаты", callback_data="settings_chats")
    builder.button(text="📋 Список финалистов Лото", callback_data="settings_finalists_loto"); builder.button(text="📋 Список финалистов МБ", callback_data="settings_finalists_sea")
    if bot_data.admins: builder.button(text="👑 Администрирование", callback_data="settings_admin")
    builder.button(text="↩️ Назад", callback_data="settings_back")
    builder.adjust(1); return builder.as_markup()

def loto_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Чат для карточек", callback_data="loto_chat"); builder.button(text="📅 Дедлайн", callback_data="loto_deadline")
    builder.button(text="💬 Стартовое сообщение", callback_data="loto_start_msg"); builder.button(text="🔘 Кнопки участников", callback_data="loto_buttons")
    builder.button(text="🏆 Ограничения", callback_data="loto_bans"); builder.button(text="🎫 Кол-во финалистов", callback_data="loto_finalists")
    settings = bot_data.chats.get(bot_data.default_chat_id) if bot_data.default_chat_id else None
    builder.button(text=f"⚡ Триггер: {'ВКЛ' if settings and settings.loto_trigger_enabled else 'ВЫКЛ'}", callback_data="loto_toggle_trigger")
    builder.button(text="⚙️ Слова-триггеры", callback_data="loto_triggers"); builder.button(text="ℹ️ Текущие настройки", callback_data="loto_current")
    builder.button(text="📊 Статистика", callback_data="loto_stats"); builder.button(text="📢 Рассылка", callback_data="loto_broadcast")
    builder.button(text="↩️ Назад", callback_data="loto_back")
    builder.adjust(1); return builder.as_markup()

def sea_battle_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Чат для карточек", callback_data="sb_chat"); builder.button(text="📅 Дедлайн", callback_data="sb_deadline")
    builder.button(text="💬 Стартовое сообщение", callback_data="sb_start_msg"); builder.button(text="🔘 Кнопки участников", callback_data="sb_buttons")
    builder.button(text="🏆 Ограничения", callback_data="sb_bans"); builder.button(text="🎫 Кол-во финалистов", callback_data="sb_finalists")
    settings = bot_data.chats.get(bot_data.default_chat_id) if bot_data.default_chat_id else None
    builder.button(text=f"⚡ Триггер: {'ВКЛ' if settings and settings.sea_battle_trigger_enabled else 'ВЫКЛ'}", callback_data="sb_toggle_trigger")
    builder.button(text="⚙️ Слова-триггеры", callback_data="sb_triggers"); builder.button(text="ℹ️ Текущие настройки", callback_data="sb_current")
    builder.button(text="📊 Статистика", callback_data="sb_stats"); builder.button(text="📢 Рассылка", callback_data="sb_broadcast")
    builder.button(text="↩️ Назад", callback_data="sb_back")
    builder.adjust(1); return builder.as_markup()

def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить админа", callback_data="admin_add"); builder.button(text="➖ Удалить админа", callback_data="admin_remove")
    builder.button(text="👥 Список админов", callback_data="admin_list"); builder.button(text="🏆 Ограничения победителей", callback_data="admin_bans")
    builder.button(text="↩️ Назад", callback_data="admin_back")
    builder.adjust(1); return builder.as_markup()
