import re
from datetime import timedelta
from aiogram import Router, F, types
from aiogram.types import ChatPermissions, Message

from loader import bot, queue_manager
from models.database import bot_data
from services.game_logic import process_dice_sequence, calc_slot_sum, is_recent_card
from handlers.shared import send_finalists_list

group_router = Router()

async def mute_user(chat_id: int, user_id: int, chat_settings):
    try:
        from datetime import datetime
        await bot.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False), until_date=datetime.now() + timedelta(hours=1))
        chat_settings.muted_users.append(user_id); bot_data.save()
    except: pass

async def check_trigger(chat_id, user, settings, game):
    if not user.username: return
    db_users = bot_data.loto_users if game == "loto" else bot_data.sea_battle_users
    if user.id not in db_users: return
    user_data = db_users[user.id]
    if not is_recent_card(user_data.registered_at): return
    if (game == "loto" and settings.loto_finalists_disabled) or (game == "sb" and settings.sea_battle_finalists_disabled): return

    if user_data.photo_file_id: queue_manager.enqueue_message(chat_id, photo=user_data.photo_file_id, caption=f"@{user.username} карточка")
    queue_manager.enqueue_message(chat_id, "⚠ ПОЛНАЯ ТИШИНА ⚠\nКарточка проверяется...")
    
    dictated = [item.upper() for item in settings.items[:settings.index]]
    user_items = user_data.numbers if game == "loto" else user_data.cells
    missing = [n for n in user_items if str(n).upper() not in dictated]
    
    sub_ok = True
    if bot_data.default_channel_id:
        try: mem = await bot.get_chat_member(bot_data.default_channel_id, user.id); sub_ok = mem.status in ("member", "administrator", "creator", "restricted")
        except: sub_ok = False

    if missing or not sub_ok: await mute_user(chat_id, user.id, settings)
    
    res = "✅ Карточка верна" if not missing else f"❌ Не было: {', '.join(map(str, missing))}"
    res += " | 🟢 Подписан" if sub_ok else " | 🚫 Не подписан | Вылет ⛔"
    queue_manager.enqueue_message(chat_id, res)

    if not missing and sub_ok:
        fin_list = settings.loto_finalists if game == "loto" else settings.sea_battle_finalists
        if user.username not in fin_list:
            fin_list.append(user.username); bot_data.save()
            queue_manager.enqueue_message(chat_id, f"✅ @{user.username} финалист №{len(fin_list)}!")
            count = settings.loto_finalists_count if game == "loto" else settings.sea_battle_finalists_count
            if len(fin_list) >= count:
                if game == "loto": settings.loto_finalists_disabled = True
                else: settings.sea_battle_finalists_disabled = True
                bot_data.save()
                await send_finalists_list(chat_id, settings, "loto" if game == "loto" else "sea_battle")
                try: await bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
                except: pass
                queue_manager.enqueue_message(chat_id, "🏁 Набрано нужное количество. Чат закрывается.")

@group_router.message(F.chat.type.in_({"group", "supergroup"}), ~F.from_user.is_bot)
async def group_handler(message: Message):
    chat_id = message.chat.id; settings = bot_data.chats.get(chat_id)
    if not settings: return
    
    is_admin = False
    try: mem = await bot.get_chat_member(chat_id, message.from_user.id); is_admin = mem.status in ("creator", "administrator")
    except: pass

    text = message.text.lower().strip() if message.text else ""
    
    if is_admin and text in ("вот кубик", "вот слот"):
        bot_data.check_subscription = False; bot_data.save()
        try: await bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        except: pass
        return queue_manager.enqueue_message(chat_id, "🔓 Чат открыт! Ожидаем бросков!")

    if is_admin and text == "стоп игра":
        for uid in settings.muted_users[:]:
            try: await bot.restrict_chat_member(chat_id, uid, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)); settings.muted_users.remove(uid)
            except: pass
        bot_data.save()
        return queue_manager.enqueue_message(chat_id, "✅ Ограничения сняты.")

    if not is_admin and text:
        if settings.loto_enabled and settings.loto_trigger_enabled and not settings.loto_finalists_disabled:
            if any(t.lower() in text for t in settings.loto_triggers):
                if settings.status in ("playing", "paused"):
                    if settings.status == "playing": settings.status = "paused"; bot_data.save()
                    queue_manager.enqueue_check(chat_id, check_trigger(chat_id, message.from_user, settings, "loto"))
                    return
        if settings.sea_battle_enabled and settings.sea_battle_trigger_enabled and not settings.sea_battle_finalists_disabled:
            if any(t.lower() in text for t in settings.sea_battle_triggers):
                if settings.status in ("playing", "paused"):
                    if settings.status == "playing": settings.status = "paused"; bot_data.save()
                    queue_manager.enqueue_check(chat_id, check_trigger(chat_id, message.from_user, settings, "sb"))
                    return

    if not is_admin and message.dice:
        if message.dice.emoji == "🎲" and settings.dice_enabled:
            total = await process_dice_sequence(chat_id, message.from_user.id, message.dice.value)
            if total: queue_manager.bot.loop.create_task(asyncio.sleep(3)).add_done_callback(lambda _: queue_manager.bot.loop.create_task(message.reply(f"@{message.from_user.username} {total}")))
        elif message.dice.emoji == "🎰" and settings.slot_enabled:
            total = calc_slot_sum(message.dice.value)
            queue_manager.bot.loop.create_task(asyncio.sleep(3)).add_done_callback(lambda _: queue_manager.bot.loop.create_task(message.reply(f"@{message.from_user.username} {total}")))
