from loader import bot
from models.database import bot_data

async def send_finalists_list(chat_id: int, settings, game: str):
    digits = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    finalists = settings.loto_finalists if game == "loto" else settings.sea_battle_finalists
    if not finalists:
        for admin_id in bot_data.admins:
            try: await bot.send_message(admin_id, "Финалистов пока нет.")
            except: pass
        return
    lines = [f"{digits[i] if i < 10 else f'{i+1}️⃣'} @{uname}" for i, uname in enumerate(finalists)]
    text = f"🏆 Список финалистов ({game.upper()}):\n" + "\n".join(lines)
    for admin_id in bot_data.admins:
        try: await bot.send_message(admin_id, text)
        except: pass

async def check_chat_access(user_id: int, chat_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False
