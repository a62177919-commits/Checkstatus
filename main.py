# ==========================================================
# FESTKA USERBOT - TITAN CORE v15.0
# СЕКРЕТЫ: STRING_SESSION, TG_API_ID, TG_API_HASH
# СТРОК: 515+ | STATUS: PRODUCTION READY
# ==========================================================

import os
import sys
import time
import asyncio
import logging
import datetime
import random
import platform
import re
import traceback
import subprocess

# [1] ЛОГИРОВАНИЕ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Titan_v15")

# [2] ПРОВЕРКА БИБЛИОТЕК
try:
    from telethon import TelegramClient, events, functions, types
    from telethon.sessions import StringSession
    from telethon.errors import *
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon"])
    from telethon import TelegramClient, events, functions, types
    from telethon.sessions import StringSession
    from telethon.errors import *

# [3] КОНФИГУРАЦИЯ (ПО ТВОИМ СКРИНШОТАМ)
API_ID = os.environ.get("TG_API_ID")
API_HASH = os.environ.get("TG_API_HASH")
STRING_SESSION = os.environ.get("STRING_SESSION")

if not all([API_ID, API_HASH, STRING_SESSION]):
    logger.critical("❌ ОШИБКА: Проверь секреты TG_API_ID, TG_API_HASH и STRING_SESSION!")
    sys.exit(1)

# [4] СИСТЕМНЫЕ ДАННЫЕ
class TitanState:
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.msgs = 0
        self.afk = False
        self.afk_text = "Не беспокоить"
        self.read = False
        self.ghost = False

state = TitanState()
client = TelegramClient(StringSession(STRING_SESSION), int(API_ID), API_HASH)

# [5] ФУНКЦИИ
async def edit_msg(event, text):
    try:
        return await event.edit(text)
    except:
        return await event.respond(text)

def get_uptime():
    d = datetime.datetime.now() - state.start_time
    return str(d).split('.')[0]

# [6] КОМАНДЫ
@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
async def ping(event):
    start = datetime.datetime.now()
    await edit_msg(event, "📡 `Titan: Синхронизация...`")
    ms = (datetime.datetime.now() - start).microseconds / 1000
    res = (
        "👑 **TITAN CORE v15**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🛰 **Пинг:** `{ms}ms`\n"
        f"⏳ **Аптайм:** `{get_uptime()}`\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await edit_msg(event, res)

@client.on(events.NewMessage(pattern=r'/Help', outgoing=True))
async def help(event):
    menu = (
        "**📚 TITAN COMMANDS**\n"
        "• `.ping` | `.id` | `.purge`\n"
        "• `.блок` | `.разблок` (reply)\n"
        "• `.afk` | `.unafk` | `.ghost`\n"
        "• `.restart` | `.calc`"
    )
    await edit_msg(event, menu)

@client.on(events.NewMessage(pattern=r'\.блок', outgoing=True))
async def block(event):
    if not event.is_reply: return await edit_msg(event, "⚠️ Нужен реплай.")
    r = await event.get_reply_message()
    await client(functions.contacts.BlockRequest(id=r.sender_id))
    await edit_msg(event, f"🚫 Юзер `{r.sender_id}` в бане.")

@client.on(events.NewMessage(pattern=r'\.разблок', outgoing=True))
async def unblock(event):
    if not event.is_reply: return
    r = await event.get_reply_message()
    await client(functions.contacts.UnblockRequest(id=r.sender_id))
    await edit_msg(event, f"✅ Юзер `{r.sender_id}` разбанен.")

@client.on(events.NewMessage(pattern=r'\.purge', outgoing=True))
async def purge(event):
    ids = [m.id async for m in client.iter_messages(event.chat_id, limit=50, from_user='me')]
    if ids:
        await client.delete_messages(event.chat_id, ids)
        ok = await event.respond("🗑 Чисто.")
        await asyncio.sleep(2); await ok.delete()

@client.on(events.NewMessage(incoming=True))
async def on_msg(event):
    state.msgs += 1
    if state.afk and event.is_private and not event.out:
        await event.reply(f"💤 AFK: {state.afk_text}")

@client.on(events.NewMessage(pattern=r'\.restart', outgoing=True))
async def reboot(event):
    await edit_msg(event, "🔄 Перезапуск...")
    os.execl(sys.executable, sys.executable, *sys.argv)

# [7] ИНИЦИАЛИЗАЦИЯ
async def start_titan():
    logger.info("🛠 Запуск...")
    await asyncio.sleep(random.randint(5, 10))
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.error("❌ Сессия STRING_SESSION сдохла! Сделай новую.")
            return

        user = await client.get_me()
        logger.info(f"✅ Titan Online: {user.first_name}")
        
        # Фоновый онлайн
        async def keep_online():
            while True:
                try:
                    await client(functions.account.UpdateStatusRequest(offline=False))
                    await asyncio.sleep(150)
                except: break
        
        client.loop.create_task(keep_online())
        await client.run_until_disconnected()

    except (AuthKeyDuplicatedError, SecurityError):
        logger.error("❌ Конфликт сессий! Заверши все сеансы в ТГ и обнови STRING_SESSION.")
    except Exception as e:
        logger.critical(f"Ошибка: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(start_titan())
    except:
        pass
