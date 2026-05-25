from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from models.database import bot_data

def common_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🟢 ЗАПИСЬ НА ИГРУ 🟢")
    settings = bot_data.chats.get(bot_data.default_chat_id) if bot_data.default_chat_id else None
    if settings:
        if settings.loto_enabled:
            for text in bot_data.loto_user_buttons: builder.button(text=text)
        elif settings.sea_battle_enabled:
            for text in bot_data.sea_battle_user_buttons: builder.button(text=text)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
