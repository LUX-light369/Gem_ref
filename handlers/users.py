import logging
import random
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from loader import bot
from models.database import bot_data
from models.settings import LotoUserData, SeaBattleUserData
from models.states import LotoRegistration, SeaBattleRegistration
from services.game_logic import now_novosibirsk, generate_random_sea_battle_cells, parse_cells, validate_ships, parse_list
from services.image_generator import generate_loto_card, generate_sea_battle_card
from keyboards.reply import common_reply_keyboard
from keyboards.inline import main_menu_keyboard

user_router = Router()

async def check_subscription(user_id: int, channel_id: int | None) -> bool:
    if not channel_id: return True
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in ("member", "administrator", "creator", "restricted")
    except: return False

@user_router.message(Command("start"), F.chat.type == "private")
async def cmd_start(message: Message, state: FSMContext):
    user = message.from_user
    if user.id in bot_data.admins: return await message.answer("🤖 Главное меню управления", reply_markup=main_menu_keyboard())
    chat_id = bot_data.default_chat_id
    if not chat_id or not bot_data.chats.get(chat_id): return await message.answer("⛔ Чат для проведения игры еще не настроен администратором.")
    settings = bot_data.chats[chat_id]
    if bot_data.check_subscription and bot_data.default_channel_id and not await check_subscription(user.id, bot_data.default_channel_id):
        kb = InlineKeyboardBuilder().button(text="📢 Подписаться", url=bot_data.channel_invite_link or "https://t.me/your_channel").button(text="✅ Проверить подписку", callback_data="check_sub").adjust(1)
        return await message.answer("❗ Для участия подпишитесь на канал и нажмите кнопку проверки.", reply_markup=kb.as_markup())
    if not user.username: return await message.answer("❌ У вас не установлен публичный @username в настройках аккаунта Telegram. Пожалуйста, установите его и повторите команду /start.")
    if settings.loto_enabled: await start_loto_registration(message, state)
    elif settings.sea_battle_enabled: await start_sea_battle_registration(message, state)
    else: await message.answer("📭 На данный момент активные регистрации на игры закрыты.")

@user_router.message(F.text == "🟢 ЗАПИСЬ НА ИГРУ 🟢", F.chat.type == "private")
async def restart_registration(message: Message, state: FSMContext): await cmd_start(message, state)

@user_router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user.username: return await callback.answer("Сначала установите @username", show_alert=True)
    if await check_subscription(callback.from_user.id, bot_data.default_channel_id):
        await callback.answer("✅ Подписка подтверждена!", show_alert=True); await callback.message.delete(); await cmd_start(callback.message, state)
    else: await callback.answer("❌ Вы ещё не подписались.", show_alert=True)

async def start_loto_registration(message: Message, state: FSMContext):
    if bot_data.loto_deadline and now_novosibirsk() > bot_data.loto_deadline: return await message.answer("⏰ Прием карточек окончен ⛔")
    uname = message.from_user.username
    if uname in bot_data.banned_users:
        if now_novosibirsk() < bot_data.banned_users[uname]:
            diff = bot_data.banned_users[uname] - now_novosibirsk()
            return await message.answer(f"Вы временно ограничены в играх. Ограничение снимется через {diff.days + 1} дн.")
    await message.answer(bot_data.loto_start_message or "🎫 Отправьте 15 уникальных чисел от 1 до 99 или напишите «Да» для случайной генерации карточки.", reply_markup=common_reply_keyboard())
    await state.set_state(LotoRegistration.waiting_for_numbers)

@user_router.message(StateFilter(LotoRegistration.waiting_for_numbers), F.chat.type == "private")
async def loto_numbers(message: Message, state: FSMContext):
    if not message.from_user.username or not message.text: return
    if message.text in bot_data.loto_user_buttons: return await message.answer(bot_data.loto_user_buttons[message.text])
    if message.text.strip().lower() == "да": nums = [str(n) for n in random.sample(range(1, 100), 15)]
    else:
        try: nums = [int(p) for p in parse_list(message.text) if p.isdigit()]
        except ValueError: return await message.answer("Используйте только целые числа.")
        if len(nums) != 15 or any(n < 1 or n > 99 for n in nums) or len(set(nums)) != 15: return await message.answer("Нужно отправить ровно 15 уникальных чисел в диапазоне от 1 до 99.")
        nums = [str(n) for n in nums]
    user_data = LotoUserData(message.from_user.username, nums)
    bot_data.loto_users[message.from_user.id] = user_data; bot_data.registered_ever.add(message.from_user.id)
    if bot_data.loto_target_chat:
        try:
            msg = await bot.send_photo(bot_data.loto_target_chat, photo=generate_loto_card(user_data.username, nums, user_data.registered_at), caption=", ".join(sorted(nums, key=lambda x: int(x))) + f" @{user_data.username}")
            user_data.photo_file_id = msg.photo[-1].file_id; user_data.card_message_id = msg.message_id; bot_data.save()
            await bot.copy_message(chat_id=message.from_user.id, from_chat_id=bot_data.loto_target_chat, message_id=msg.message_id)
        except Exception as e: logging.error(f"Loto registration media routing error: {e}")
    await message.answer("✅ Ваша карточка Лото успешно принята. Желаем удачи!"); await state.clear()

async def start_sea_battle_registration(message: Message, state: FSMContext):
    if bot_data.sea_battle_deadline and now_novosibirsk() > bot_data.sea_battle_deadline: return await message.answer("⏰ Прием карточек окончен ⛔")
    uname = message.from_user.username
    if uname in bot_data.banned_users:
        if now_novosibirsk() < bot_data.banned_users[uname]:
            diff = bot_data.banned_users[uname] - now_novosibirsk()
            return await message.answer(f"Вы временно ограничены в играх. Ограничение снимется через {diff.days + 1} дн.")
    await message.answer(bot_data.sea_battle_start_message or "⚓ Отправьте список из 15 координат клеток (например: А1, Б2) или напишите «Да» для авто-расстановки флота.", reply_markup=common_reply_keyboard())
    await state.set_state(SeaBattleRegistration.waiting_for_cells)

@user_router.message(StateFilter(SeaBattleRegistration.waiting_for_cells), F.chat.type == "private")
async def sb_cells(message: Message, state: FSMContext):
    if not message.from_user.username or not message.text: return
    if message.text in bot_data.sea_battle_user_buttons: return await message.answer(bot_data.sea_battle_user_buttons[message.text])
    text = message.text.strip()
    if text.lower() == "да":
        try: raw_cells = generate_random_sea_battle_cells()
        except: return await message.answer("❌ Ошибка случайной генерации.")
    else:
        raw_cells = parse_list(text)
        if len(raw_cells) != 15 or len(parse_cells(raw_cells)) != 15 or not validate_ships(parse_cells(raw_cells)):
            return await message.answer("❌ Неверная расстановка кораблей. На поле должны быть: один 4-палубный, один 3-палубный, два 2-палубных и четыре 1-палубных корабля (всего 15 клеток, не касающихся друг друга сторонами и углами).")
    user_data = SeaBattleUserData(message.from_user.username, raw_cells)
    bot_data.sea_battle_users[message.from_user.id] = user_data; bot_data.registered_ever.add(message.from_user.id)
    if bot_data.sea_battle_target_chat:
        try:
            msg = await bot.send_photo(bot_data.sea_battle_target_chat, photo=generate_sea_battle_card(user_data.username, raw_cells, user_data.registered_at), caption=", ".join(sorted(raw_cells, key=lambda x: (x[0], int(x[1:])))) + f" @{user_data.username}")
            user_data.photo_file_id = msg.photo[-1].file_id; user_data.card_message_id = msg.message_id; bot_data.save()
            await bot.copy_message(chat_id=message.from_user.id, from_chat_id=bot_data.sea_battle_target_chat, message_id=msg.message_id)
        except Exception as e: logging.error(f"Sea Battle registration media routing error: {e}")
    await message.answer("✅ Ваша карточка Морского боя успешно принята. Желаем удачи!"); await state.clear()
