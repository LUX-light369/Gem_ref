import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from loader import bot, queue_manager
from models.database import bot_data, MAIN_ADMIN_ID
from models.states import *
from keyboards.inline import *
from services.game_logic import parse_list, now_novosibirsk
from handlers.shared import send_finalists_list, check_chat_access

admin_router = Router()

async def dictation_loop(chat_id: int, settings):
    while settings.status == "playing" and settings.index < len(settings.items):
        queue_manager.enqueue_message(chat_id, settings.items[settings.index])
        settings.index += 1; bot_data.save()
        if settings.index >= len(settings.items):
            settings.status = "paused"; bot_data.save()
            queue_manager.enqueue_message(chat_id, "✅ Весь список рандома продиктован!")
            if settings.loto_enabled and len(settings.loto_finalists) < settings.loto_finalists_count:
                for a in bot_data.admins:
                    try: await bot.send_message(a, "Лото: диктовка завершена, но лимит финалистов не набран. Выдать текущий список?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Да, выдать", callback_data=f"give_finalists_loto_{chat_id}")]]))
                    except: pass
            elif settings.sea_battle_enabled and len(settings.sea_battle_finalists) < settings.sea_battle_finalists_count:
                for a in bot_data.admins:
                    try: await bot.send_message(a, "Морской бой: диктовка завершена, но лимит финалистов не набран. Выдать текущий список?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Да, выдать", callback_data=f"give_finalists_sea_{chat_id}")]]))
                    except: pass
            return
        await asyncio.sleep(settings.interval)

@admin_router.callback_query(F.data.startswith("menu_"))
async def menu_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in bot_data.admins: return await callback.answer("⛔ Доступ запрещен.", show_alert=True)
    cmd, chat_id = callback.data[5:], bot_data.default_chat_id; await callback.answer()
    if cmd == "play":
        if not chat_id: return await callback.message.answer("❌ Рабочий чат не выбран в настройках.")
        settings = bot_data.chats.get(chat_id)
        if not settings or not settings.items: return await callback.message.answer("❌ Текущий список диктовки пуст. Сначала загрузите список через /upload.")
        if settings.status == "playing": return await callback.message.answer("⚠️ Диктовка уже запущена.")
        await callback.message.answer("▶️ Подтвердите запуск диктовки списка:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_play_{chat_id}"), InlineKeyboardButton(text="❌ Нет", callback_data="cancel")]]))
    elif cmd == "pause":
        settings = bot_data.chats.get(chat_id)
        if settings and settings.status == "playing": settings.status = "paused"; bot_data.save(); await callback.message.answer("⏸ Диктовка приостановлена. Автопроверки продолжают работу.")
    elif cmd == "stop":
        settings = bot_data.chats.get(chat_id)
        if settings and settings.status in ("playing", "paused"): settings.status = "stopped"; settings.index = 0; bot_data.save(); await callback.message.answer("⏹ Игра остановлена. Индекс диктовки сброшен.")
    elif cmd == "upload": await callback.message.answer("📂 Отправьте текстовое сообщение со списком элементов (разделители: пробел, запятая или новая строка)."); await state.set_state(UploadList.waiting_for_list)
    elif cmd == "verify": await callback.message.answer("📝 Введите 15 элементов для ручной проверки карточки. Если хотите добавить пользователя в финалисты при успехе, укажите его @username в сообщении."); await state.set_state(VerifyList.waiting_for_verify)
    elif cmd == "dice_toggle" and chat_id: s = bot_data.chats.setdefault(chat_id, bot_data.chats.get(chat_id)); s.dice_enabled = not s.dice_enabled; bot_data.save(); await callback.message.edit_reply_markup(reply_markup=main_menu_keyboard())
    elif cmd == "slot_toggle" and chat_id: s = bot_data.chats.setdefault(chat_id, bot_data.chats.get(chat_id)); s.slot_enabled = not s.slot_enabled; bot_data.save(); await callback.message.edit_reply_markup(reply_markup=main_menu_keyboard())
    elif cmd == "loto_toggle" and chat_id: s = bot_data.chats.setdefault(chat_id, bot_data.chats.get(chat_id)); s.loto_enabled = not s.loto_enabled; bot_data.save(); await callback.message.edit_reply_markup(reply_markup=main_menu_keyboard())
    elif cmd == "sea_battle_toggle" and chat_id: s = bot_data.chats.setdefault(chat_id, bot_data.chats.get(chat_id)); s.sea_battle_enabled = not s.sea_battle_enabled; bot_data.save(); await callback.message.edit_reply_markup(reply_markup=main_menu_keyboard())
    elif cmd == "settings": await callback.message.answer("⚙️ Меню настроек конфигурации:", reply_markup=settings_menu_keyboard())

@admin_router.callback_query(F.data.startswith("confirm_play_"))
async def confirm_play_callback(callback: CallbackQuery):
    if callback.from_user.id not in bot_data.admins: return
    chat_id = int(callback.data.split("_")[2]); settings = bot_data.chats.get(chat_id)
    was_paused = settings.status == "paused"; settings.status = "playing"; bot_data.check_subscription = True
    if not was_paused: settings.index = 0; settings.loto_finalists = []; settings.sea_battle_finalists = []; settings.loto_finalists_disabled = False; settings.sea_battle_finalists_disabled = False
    bot_data.save(); await callback.message.delete(); await callback.message.answer("▶️ Диктовка элементов запущена в целевой чат.")
    asyncio.create_task(dictation_loop(chat_id, settings)); await callback.answer()

@admin_router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery): await callback.message.delete(); await callback.message.answer("❌ Операция отменена.", reply_markup=main_menu_keyboard())

@admin_router.callback_query(F.data.startswith("give_finalists_"))
async def give_finalists(callback: CallbackQuery):
    if callback.from_user.id not in bot_data.admins: return
    chat_id = int(callback.data.split("_")[-1]); settings = bot_data.chats.get(chat_id)
    if settings: await send_finalists_list(chat_id, settings, "loto" if "loto" in callback.data else "sea_battle")
    await callback.answer("Список выдан."); await callback.message.delete()

@admin_router.message(StateFilter(UploadList.waiting_for_list), F.chat.type == "private")
async def process_upload(message: Message, state: FSMContext):
    if message.from_user.id not in bot_data.admins: return await state.clear()
    items = parse_list(message.text); chat_id = bot_data.default_chat_id
    if not chat_id: return await message.answer("❌ Сначала выберите рабочий чат в настройках бота.", reply_markup=main_menu_keyboard())
    if not items or len(items) != len(set(items)): return await message.answer("❌ Ошибка парсинга. Список пуст или содержит дублирующиеся элементы.")
    settings = bot_data.chats.setdefault(chat_id, bot_data.chats.get(chat_id))
    settings.items = items; settings.index = 0; bot_data.save()
    await message.answer(f"✅ Список успешно загружен и сохранен. Всего элементов: {len(items)}", reply_markup=main_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(VerifyList.waiting_for_verify), F.chat.type == "private")
async def process_verify(message: Message, state: FSMContext):
    if message.from_user.id not in bot_data.admins: return await state.clear()
    settings = bot_data.chats.get(bot_data.default_chat_id)
    if not settings: return await message.answer("❌ Активный чат не выбран.")
    parts, nums, uname = parse_list(message.text.strip()), [], None
    for p in parts:
        if p.startswith('@'): uname = p.lstrip('@')
        else: nums.append(p)
    if len(nums) != 15: return await message.answer(f"❌ Должно быть ровно 15 элементов для проверки. Вы прислали: {len(nums)}")
    dictated = [item.upper() for item in settings.items[:settings.index]]
    missing = [n for n in nums if str(n).upper() not in dictated]
    res = "✅ Все элементы присутствуют в истории диктовки!" if not missing else f"❌ Обнаружены невыпавшие элементы: {', '.join(missing)}"
    if not missing and uname:
        if settings.loto_enabled and not settings.loto_finalists_disabled and uname not in settings.loto_finalists:
            settings.loto_finalists.append(uname); res += f"\n👉 Пользователь @{uname} занесен в список финалистов Лото (№{len(settings.loto_finalists)})."
            if len(settings.loto_finalists) >= settings.loto_finalists_count: settings.loto_finalists_disabled = True
        elif settings.sea_battle_enabled and not settings.sea_battle_finalists_disabled and uname not in settings.sea_battle_finalists:
            settings.sea_battle_finalists.append(uname); res += f"\n👉 Пользователь @{uname} занесен в список финалистов Морского боя (№{len(settings.sea_battle_finalists)})."
            if len(settings.sea_battle_finalists) >= settings.sea_battle_finalists_count: settings.sea_battle_finalists_disabled = True
        bot_data.save()
    await message.answer(res, reply_markup=main_menu_keyboard()); await state.clear()

# Полная реализация всех веток подкнопок настроек во избежание Update is not handled
@admin_router.callback_query(F.data.startswith("settings_"))
async def settings_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in bot_data.admins: return await callback.answer("⛔")
    cmd = callback.data[9:]; await callback.answer()
    if cmd == "my_chat": await callback.message.answer("Введите ID чата для проведения игр или перешлите сообщение из него:"); await state.set_state(SetChatIdState.waiting_for_chat_id)
    elif cmd == "my_channel": await callback.message.answer("Введите ID новостного канала для проверки обязательной подписки:"); await state.set_state(SetChannelIdState.waiting_for_channel_id)
    elif cmd == "my_interval": await callback.message.answer("Введите задержку отправки элементов диктовки в секундах (например, 2.5):"); await state.set_state(SetIntervalState.waiting_for_interval)
    elif cmd == "invite_link": await callback.message.answer("Отправьте URL-ссылку на канал для кнопки подписки участников:"); await state.set_state(SetInviteLinkState.waiting_for_link)
    elif cmd == "sub_check": bot_data.check_subscription = not bot_data.check_subscription; bot_data.save(); await callback.message.answer(f"Проверка подписки установлена в статус: {'ВКЛ' if bot_data.check_subscription else 'ВЫКЛ'}", reply_markup=settings_menu_keyboard())
    elif cmd == "start_msg": await callback.message.answer("Отправьте текст стартового сообщения, которое сохраняет форматирование:"); await state.set_state(DictationStartMessage.waiting_for_start_message)
    elif cmd == "loto": await callback.message.answer("🎫 Тонкие настройки игры ЛОТО:", reply_markup=loto_menu_keyboard())
    elif cmd == "sea_battle": await callback.message.answer("⚓ Тонкие настройки игры МОРСКОЙ БОЙ:", reply_markup=sea_battle_menu_keyboard())
    elif cmd == "chats":
        if not bot_data.chats: return await callback.message.answer("Список зарегистрированных чатов пуст.")
        builder = InlineKeyboardBuilder()
        for cid in bot_data.chats.keys():
            try: chat = await bot.get_chat(cid); title = chat.title or str(cid)
            except: title = f"Чат {cid}"
            builder.button(text=title, callback_data=f"selectchat_{cid}")
        builder.adjust(1); builder.button(text="↩️ Назад", callback_data="settings_back")
        await callback.message.answer("📋 Выберите активный рабочий чат бота:", reply_markup=builder.as_markup())
    elif cmd == "finalists_loto":
        settings = bot_data.chats.get(bot_data.default_chat_id)
        if settings: await send_finalists_list(callback.from_user.id, settings, "loto")
    elif cmd == "finalists_sea":
        settings = bot_data.chats.get(bot_data.default_chat_id)
        if settings: await send_finalists_list(callback.from_user.id, settings, "sea_battle")
    elif cmd == "admin": await callback.message.answer("👑 Настройки администрирования бота:", reply_markup=admin_menu_keyboard())
    elif cmd == "back": await callback.message.answer("🤖 Главное меню управления", reply_markup=main_menu_keyboard())

@admin_router.callback_query(F.data.startswith("selectchat_"))
async def select_active_chat(callback: CallbackQuery):
    if callback.from_user.id not in bot_data.admins: return
    cid = int(callback.data.split("_")[1]); bot_data.default_chat_id = cid; bot_data.save()
    await callback.answer("✅ Рабочий чат переключен."); await callback.message.answer(f"Рабочий чат успешно изменен на ID: {cid}", reply_markup=main_menu_keyboard())

@admin_router.callback_query(F.data.startswith("loto_"))
async def loto_settings_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in bot_data.admins: return
    cmd = callback.data[5:]; await callback.answer()
    if cmd == "chat": await callback.message.answer("Отправьте ID чата (хранилища) куда бот будет отправлять генерируемые карточки Лото:"); await state.set_state(LotoSettingsFlow.waiting_for_target_chat)
    elif cmd == "deadline": await callback.message.answer("Укажите дату и время окончания приема карточек Лото в формате ДД.ММ.ГГГГ ЧЧ:ММ (по Новосибирску):"); await state.set_state(LotoSettingsFlow.waiting_for_deadline)
    elif cmd == "start_msg": await callback.message.answer("Отправьте текст, который бот пришлет пользователю при регистрации в Лото:"); await state.set_state(LotoSettingsFlow.waiting_for_start_message)
    elif cmd == "buttons": await callback.message.answer("Отправьте инфо-кнопки в формате:\nТекст кнопки - Ответ бота\nКаждая кнопка с новой строки."); await state.set_state(LotoSettingsFlow.waiting_for_buttons)
    elif cmd == "bans": await callback.message.answer("Отправьте @username игрока, которого нужно отстранить на одну игру в Лото:"); await state.set_state(LotoSettingsFlow.waiting_for_bans)
    elif cmd == "finalists": await callback.message.answer("Введите необходимое число финалистов Лото для завершения раунда (число):"); await state.set_state(LotoSettingsFlow.waiting_for_finalists)
    elif cmd == "toggle_trigger":
        s = bot_data.chats.get(bot_data.default_chat_id)
        if s: s.loto_trigger_enabled = not s.loto_trigger_enabled; bot_data.save()
        await callback.message.edit_reply_markup(reply_markup=loto_menu_keyboard())
    elif cmd == "triggers": await callback.message.answer("Отправьте ключевые слова-триггеры для проверки через запятую (например: Стоп, Лото, Готово):"); await state.set_state(LotoTriggerInput.waiting_for_triggers)
    elif cmd == "current":
        dl = bot_data.loto_deadline.strftime("%d.%m.%Y %H:%M") if bot_data.loto_deadline else "Не установлен"
        await callback.message.answer(f"ℹ️ Конфигурация Лото:\nЧат карточек: {bot_data.loto_target_chat}\nДедлайн: {dl}\nЛимит финалистов: {bot_data.chats[bot_data.default_chat_id].loto_finalists_count if bot_data.default_chat_id else 3}", reply_markup=loto_menu_keyboard())
    elif cmd == "stats":
        await callback.message.answer(f"📊 Зарегистрировано участников в Лото на текущий момент: {len(bot_data.loto_users)}", reply_markup=loto_menu_keyboard())
    elif cmd == "broadcast": await callback.message.answer("Отправьте медиасообщение или текст для рассылки всем пользователям, когда-либо регистрировавшимся в боте:"); await state.set_state(LotoBroadcast.waiting_for_message)
    elif cmd == "back": await callback.message.answer("⚙️ Меню настроек конфигурации:", reply_markup=settings_menu_keyboard())

@admin_router.callback_query(F.data.startswith("sb_"))
async def sb_settings_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in bot_data.admins: return
    cmd = callback.data[3:]; await callback.answer()
    if cmd == "chat": await callback.message.answer("Отправьте ID чата (хранилища) куда бот будет отправлять генерируемые карточки Морского боя:"); await state.set_state(SeaBattleSettingsFlow.waiting_for_target_chat)
    elif cmd == "deadline": await callback.message.answer("Укажите дату и время окончания приема карточек Морского боя в формате ДД.ММ.ГГГГ ЧЧ:ММ (по Новосибирску):"); await state.set_state(SeaBattleSettingsFlow.waiting_for_deadline)
    elif cmd == "start_msg": await callback.message.answer("Отправьте текст, который бот пришлет пользователю при регистрации в Морской бой:"); await state.set_state(SeaBattleSettingsFlow.waiting_for_start_message)
    elif cmd == "buttons": await callback.message.answer("Отправьте инфо-кнопки в формате:\nТекст кнопки - Ответ бота\nКаждая кнопка с новой строки."); await state.set_state(SeaBattleSettingsFlow.waiting_for_buttons)
    elif cmd == "triggers": await callback.message.answer("Отправьте ключевые слова-триггеры для проверки Морского боя через запятую:"); await state.set_state(SeaBattleTriggerInput.waiting_for_triggers)
    elif cmd == "bans": await callback.message.answer("Отправьте @username игрока, которого нужно отстранить на одну игру в Морской бой:"); await state.set_state(SeaBattleSettingsFlow.waiting_for_bans)
    elif cmd == "finalists": await callback.message.answer("Введите необходимое число финалистов Морского боя для автоматического закрытия чата (число):"); await state.set_state(SeaBattleSettingsFlow.waiting_for_finalists)
    elif cmd == "toggle_trigger":
        s = bot_data.chats.get(bot_data.default_chat_id)
        if s: s.sea_battle_trigger_enabled = not s.sea_battle_trigger_enabled; bot_data.save()
        await callback.message.edit_reply_markup(reply_markup=sea_battle_menu_keyboard())
    elif cmd == "current":
        dl = bot_data.sea_battle_deadline.strftime("%d.%m.%Y %H:%M") if bot_data.sea_battle_deadline else "Не установлен"
        await callback.message.answer(f"ℹ️ Конфигурация Морского Боя:\nЧат карточек: {bot_data.sea_battle_target_chat}\nДедлайн: {dl}\nЛимит финалистов: {bot_data.chats[bot_data.default_chat_id].sea_battle_finalists_count if bot_data.default_chat_id else 3}", reply_markup=sea_battle_menu_keyboard())
    elif cmd == "stats":
        await callback.message.answer(f"📊 Зарегистрировано участников в Морской бой на текущий момент: {len(bot_data.sea_battle_users)}", reply_markup=sea_battle_menu_keyboard())
    elif cmd == "broadcast": await callback.message.answer("Отправьте медиасообщение или текст для рассылки всем пользователям, когда-либо регистрировавшимся в боте:"); await state.set_state(SeaBattleBroadcast.waiting_for_message)
    elif cmd == "back": await callback.message.answer("⚙️ Меню настроек конфигурации:", reply_markup=settings_menu_keyboard())

@admin_router.callback_query(F.data.startswith("admin_"))
async def admin_actions_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in bot_data.admins: return
    cmd = callback.data[6:]; await callback.answer()
    if cmd == "add": await callback.message.answer("Отправьте Telegram ID пользователя для назначения администратором:"); await state.set_state(AdminAdd.waiting_for_id)
    elif cmd == "remove": await callback.message.answer("Отправьте Telegram ID для разжалования администратора:"); await state.set_state(AdminRemove.waiting_for_id)
    elif cmd == "list":
        await callback.message.answer(f"👑 Действующие ID администраторов: {', '.join(map(str, bot_data.admins))}", reply_markup=admin_menu_keyboard())
    elif cmd == "bans":
        now = now_novosibirsk()
        lines = []
        for u, dt in bot_data.banned_users.items():
            if dt > now:
                diff = dt - now
                lines.append(f"❌ @{u} — осталось {diff.days} дн. {diff.seconds // 3600} ч.")
        text = "🏆 Список активных ограничений игроков:\n" + ("\n".join(lines) if lines else "Ограниченных игроков нет.")
        await callback.message.answer(text, reply_markup=admin_menu_keyboard())
    elif cmd == "back": await callback.message.answer("⚙️ Меню настроек конфигурации:", reply_markup=settings_menu_keyboard())

# Хендлеры ввода состояний
@admin_router.message(StateFilter(SetChatIdState.waiting_for_chat_id), F.chat.type == "private")
async def process_set_chat(m: Message, state: FSMContext):
    if m.from_user.id not in bot_data.admins: return
    try: cid = m.forward_from_chat.id if m.forward_from_chat else int(m.text.strip())
    except: return await m.answer("Неверный ID.")
    bot_data.default_chat_id = cid; bot_data.chats.setdefault(cid, bot_data.chats.get(cid)); bot_data.save()
    await m.answer("✅ Активный рабочий чат привязан.", reply_markup=settings_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SetChannelIdState.waiting_for_channel_id), F.chat.type == "private")
async def process_set_channel(m: Message, state: FSMContext):
    if m.from_user.id not in bot_data.admins: return
    try: bot_data.default_channel_id = int(m.text.strip())
    except: return await m.answer("Неверный ID.")
    bot_data.save(); await m.answer("✅ Канал для подписки привязан.", reply_markup=settings_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SetIntervalState.waiting_for_interval), F.chat.type == "private")
async def process_set_interval(m: Message, state: FSMContext):
    if m.from_user.id not in bot_data.admins or not bot_data.default_chat_id: return
    try: val = float(m.text.strip())
    except: return await m.answer("Введите число.")
    bot_data.chats[bot_data.default_chat_id].interval = val; bot_data.save()
    await m.answer(f"✅ Интервал обновлен: {val} сек.", reply_markup=settings_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SetInviteLinkState.waiting_for_link), F.chat.type == "private")
async def process_set_link(m: Message, state: FSMContext):
    if m.from_user.id not in bot_data.admins: return
    bot_data.channel_invite_link = m.text.strip(); bot_data.save()
    await m.answer("✅ Ссылка на канал сохранена.", reply_markup=settings_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(DictationStartMessage.waiting_for_start_message), F.chat.type == "private")
async def process_dictation_start_msg(m: Message, state: FSMContext):
    if m.from_user.id not in bot_data.admins or not bot_data.default_chat_id: return
    bot_data.chats[bot_data.default_chat_id].dictation_start_message = m.text; bot_data.save()
    await m.answer("✅ Текст стартового сообщения диктовки сохранен.", reply_markup=settings_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(AdminAdd.waiting_for_id), F.chat.type == "private")
async def process_admin_add(m: Message, state: FSMContext):
    if m.from_user.id not in bot_data.admins: return
    try: uid = int(m.text.strip())
    except: return await m.answer("Введите валидный ID.")
    bot_data.admins.add(uid); bot_data.save()
    await m.answer(f"✅ Пользователь {uid} добавлен в администраторы.", reply_markup=admin_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(AdminRemove.waiting_for_id), F.chat.type == "private")
async def process_admin_remove(m: Message, state: FSMContext):
    if m.from_user.id not in bot_data.admins: return
    try: uid = int(m.text.strip())
    except: return await m.answer("Введите валидный ID.")
    if uid == MAIN_ADMIN_ID: return await m.answer("Нельзя удалить главного администратора.")
    bot_data.admins.discard(uid); bot_data.save()
    await m.answer(f"✅ Пользователь {uid} удален из администраторов.", reply_markup=admin_menu_keyboard()); await state.clear()

# Хендлеры состояний Лото
@admin_router.message(StateFilter(LotoSettingsFlow.waiting_for_target_chat), F.chat.type == "private")
async def loto_sc1(m: Message, state: FSMContext):
    try: bot_data.loto_target_chat = int(m.text.strip())
    except: return await m.answer("Неверный ID.")
    bot_data.save(); await m.answer("✅ Чат хранилища Лото изменен.", reply_markup=loto_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(LotoSettingsFlow.waiting_for_deadline), F.chat.type == "private")
async def loto_sc2(m: Message, state: FSMContext):
    try: dt = datetime.strptime(m.text.strip(), "%d.%m.%Y %H:%M")
    except: return await m.answer("Неверный формат. Используйте ДД.ММ.ГГГГ ЧЧ:ММ")
    bot_data.loto_deadline = dt; bot_data.save()
    await m.answer(f"✅ Срок приема карточек Лото: {m.text.strip()}", reply_markup=loto_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(LotoSettingsFlow.waiting_for_start_message), F.chat.type == "private")
async def loto_sc3(m: Message, state: FSMContext):
    bot_data.loto_start_message = m.text; bot_data.save()
    await m.answer("✅ Приветствие Лото обновлено.", reply_markup=loto_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(LotoSettingsFlow.waiting_for_buttons), F.chat.type == "private")
async def loto_sc4(m: Message, state: FSMContext):
    lines = m.text.strip().split("\n"); new_btns = {}
    for l in lines:
        if " - " in l: k, v = l.split(" - ", 1); new_btns[k.strip()] = v.strip()
    bot_data.loto_user_buttons = new_btns; bot_data.save()
    await m.answer("✅ Пользовательские инфо-кнопки Лото перезаписаны.", reply_markup=loto_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(LotoSettingsFlow.waiting_for_bans), F.chat.type == "private")
async def loto_sc5(m: Message, state: FSMContext):
    username = m.text.strip().lstrip("@")
    bot_data.banned_users[username] = now_novosibirsk() + timedelta(days=2)
    bot_data.save()
    await m.answer(f"✅ @{username} забанен на одну игру (48 часов).", reply_markup=loto_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(LotoSettingsFlow.waiting_for_finalists), F.chat.type == "private")
async def loto_sc6(m: Message, state: FSMContext):
    if not bot_data.default_chat_id: return
    try: count = int(m.text.strip())
    except: return await m.answer("Введите целое число.")
    bot_data.chats[bot_data.default_chat_id].loto_finalists_count = count; bot_data.save()
    await m.answer(f"✅ Требуемое число финалистов Лото: {count}", reply_markup=loto_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(LotoTriggerInput.waiting_for_triggers), F.chat.type == "private")
async def loto_trig(m: Message, state: FSMContext):
    if not bot_data.default_chat_id: return
    trigs = [t.strip().lower() for t in m.text.split(",") if t.strip()]
    if trigs: bot_data.chats[bot_data.default_chat_id].loto_triggers = trigs; bot_data.save()
    await m.answer("✅ Ключевые слова-триггеры Лото обновлены.", reply_markup=loto_menu_keyboard()); await state.clear()

# Хендлеры состояний Морского Боя
@admin_router.message(StateFilter(SeaBattleSettingsFlow.waiting_for_target_chat), F.chat.type == "private")
async def sb_sc1(m: Message, state: FSMContext):
    try: bot_data.sea_battle_target_chat = int(m.text.strip())
    except: return await m.answer("Неверный ID.")
    bot_data.save(); await m.answer("✅ Чат хранилища Морского боя изменен.", reply_markup=sea_battle_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SeaBattleSettingsFlow.waiting_for_deadline), F.chat.type == "private")
async def sb_sc2(m: Message, state: FSMContext):
    try: dt = datetime.strptime(m.text.strip(), "%d.%m.%Y %H:%M")
    except: return await m.answer("Неверный формат. Используйте ДД.ММ.ГГГГ ЧЧ:ММ")
    bot_data.sea_battle_deadline = dt; bot_data.save()
    await m.answer(f"✅ Срок приема карточек Морского боя: {m.text.strip()}", reply_markup=sea_battle_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SeaBattleSettingsFlow.waiting_for_start_message), F.chat.type == "private")
async def sb_sc3(m: Message, state: FSMContext):
    bot_data.sea_battle_start_message = m.text; bot_data.save()
    await m.answer("✅ Приветствие Морского боя обновлено.", reply_markup=sea_battle_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SeaBattleSettingsFlow.waiting_for_buttons), F.chat.type == "private")
async def sb_sc4(m: Message, state: FSMContext):
    lines = m.text.strip().split("\n"); new_btns = {}
    for l in lines:
        if " - " in l: k, v = l.split(" - ", 1); new_btns[k.strip()] = v.strip()
    bot_data.sea_battle_user_buttons = new_btns; bot_data.save()
    await m.answer("✅ Пользовательские инфо-кнопки Морского боя перезаписаны.", reply_markup=sea_battle_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SeaBattleSettingsFlow.waiting_for_bans), F.chat.type == "private")
async def sb_sc5(m: Message, state: FSMContext):
    username = m.text.strip().lstrip("@")
    bot_data.banned_users[username] = now_novosibirsk() + timedelta(days=2)
    bot_data.save()
    await m.answer(f"✅ @{username} отстранен на одну игру (48 часов).", reply_markup=sea_battle_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SeaBattleSettingsFlow.waiting_for_finalists), F.chat.type == "private")
async def sb_sc6(m: Message, state: FSMContext):
    if not bot_data.default_chat_id: return
    try: count = int(m.text.strip())
    except: return await m.answer("Введите целое число.")
    bot_data.chats[bot_data.default_chat_id].sea_battle_finalists_count = count; bot_data.save()
    await m.answer(f"✅ Требуемое число финалистов Морского боя: {count}", reply_markup=sea_battle_menu_keyboard()); await state.clear()

@admin_router.message(StateFilter(SeaBattleTriggerInput.waiting_for_triggers), F.chat.type == "private")
async def sb_trig(m: Message, state: FSMContext):
    if not bot_data.default_chat_id: return
    trigs = [t.strip().lower() for t in m.text.split(",") if t.strip()]
    if trigs: bot_data.chats[bot_data.default_chat_id].sea_battle_triggers = trigs; bot_data.save()
    await m.answer("✅ Ключевые слова-триггеры Морского боя обновлены.", reply_markup=sea_battle_menu_keyboard()); await state.clear()

# Хендлеры универсальной медиа-рассылки (v4 контент-менеджмент)
@admin_router.message(StateFilter(LotoBroadcast.waiting_for_message))
async def loto_broadcaster(m: Message, state: FSMContext):
    await state.clear(); await m.answer("📢 Рассылка запущена...")
    for uid in list(bot_data.registered_ever):
        try: await bot.copy_message(chat_id=uid, from_chat_id=m.chat.id, message_id=m.message_id)
        except: pass
    await m.answer("✅ Рассылка завершена успешно.", reply_markup=loto_menu_keyboard())

@admin_router.message(StateFilter(SeaBattleBroadcast.waiting_for_message))
async def sb_broadcaster(m: Message, state: FSMContext):
    await state.clear(); await m.answer("📢 Рассылка запущена...")
    for uid in list(bot_data.registered_ever):
        try: await bot.copy_message(chat_id=uid, from_chat_id=m.chat.id, message_id=m.message_id)
        except: pass
    await m.answer("✅ Рассылка завершена успешно.", reply_markup=sea_battle_menu_keyboard())
