import os
import sys
import time
import math
import random
import asyncio
import logging
import datetime
import platform
import re
import json
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest, SetPrivacyRequest
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import GetHistoryRequest, ReadMentionsRequest, DeleteMessagesRequest
from telethon.errors import (
    FloodWaitError, 
    SessionPasswordNeededError, 
    SecurityError, 
    UserPrivacyRestrictedError,
    MessageDeleteForbiddenError
)

# ==========================================================
# FESTKA USERBOT - TITAN CORE v8.0 (STABLE)
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("FestkaTitan")

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION_STR = os.environ.get("SESSION_STR")

if not all([API_ID, API_HASH, SESSION_STR]):
    logger.critical("❌ Environment variables are missing!")
    sys.exit(1)

client = TelegramClient(StringSession(SESSION_STR), int(API_ID), API_HASH)

# ==========================================================
# GLOBAL DATABASE & STATE
# ==========================================================

class Database:
    def __init__(self):
        self.boot_time = datetime.datetime.now()
        self.msg_count = 0
        self.afk = False
        self.afk_reason = "System busy"
        self.auto_read = False
        self.prefix = "."
        self.notes = {}
        self.media_cache = []
        self.whitelist = []
        self.spam_tasks = {}
        self.ghost_mode = False

db = Database()

# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================

def get_uptime():
    delta = datetime.datetime.now() - db.boot_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_sys_info():
    return {
        "os": platform.system(),
        "py": sys.version.split()[0],
        "arch": platform.machine(),
        "node": platform.node()
    }

# ==========================================================
# MODULE 1: CORE SYSTEM
# ==========================================================

@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
async def ping_handler(event):
    start = datetime.datetime.now()
    await event.edit("📡 `Signal Check...`")
    end = datetime.datetime.now()
    ms = (end - start).microseconds / 1000
    
    info = get_sys_info()
    status = (
        "👑 **FESTKA TITAN v8.0**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🛰 **Latency:** `{ms}ms`\n"
        f"⏳ **Uptime:** `{get_uptime()}`\n"
        f"📊 **Messages:** `{db.msg_count}`\n"
        f"💻 **System:** `{info['os']} ({info['arch']})`\n"
        f"🐍 **Runtime:** `Python {info['py']}`\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await event.edit(status)

@client.on(events.NewMessage(pattern=r'/Help', outgoing=True))
async def help_handler(event):
    help_text = (
        "**👑 FESTKA CONTROL PANEL**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🛡 **ADMIN**\n"
        "`.блок` — Block user (reply)\n"
        "`.разблок` — Unblock user (reply)\n"
        "`.purge` — Delete 100 messages\n"
        "`.id` — Get IDs info\n\n"
        "👤 **PROFILE**\n"
        "`.setname [text]` — Change name\n"
        "`.setbio [text]` — Change bio\n"
        "`.setphoto` — Avatar (reply to photo)\n"
        "`.ghost` — Hide online/photo\n\n"
        "⚙️ **UTILS**\n"
        "`.afk [reason]` — AFK mode\n"
        "`.unafk` — Stop AFK\n"
        "`.autoread` — Toggle read\n"
        "`.calc [math]` — Calculator\n"
        "`.sys` — Detailed system\n"
        "`.restart` — Reboot bot\n\n"
        "🖼 **MEDIA**\n"
        "`.gallery` — Cached media\n"
        "`.apply [id]` — Set cached avatar\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await event.edit(help_text)

# ==========================================================
# MODULE 2: SECURITY & MODERATION
# ==========================================================

@client.on(events.NewMessage(pattern=r'\.блок', outgoing=True))
async def block_handler(event):
    if not event.is_reply:
        return await event.edit("⚠️ **Error:** Reply to a user.")
    
    reply = await event.get_reply_message()
    try:
        await client(BlockRequest(reply.sender_id))
        await event.edit(f"⛔ **User {reply.sender_id} has been blocked.**")
    except Exception as e:
        await event.edit(f"❌ **API Error:** {str(e)}")

@client.on(events.NewMessage(pattern=r'\.разблок', outgoing=True))
async def unblock_handler(event):
    if not event.is_reply:
        return await event.edit("⚠️ **Error:** Reply to a user.")
    
    reply = await event.get_reply_message()
    try:
        await client(UnblockRequest(reply.sender_id))
        await event.edit(f"✅ **User {reply.sender_id} is now unblocked.**")
    except Exception as e:
        await event.edit(f"❌ **API Error:** {str(e)}")

@client.on(events.NewMessage(pattern=r'\.purge', outgoing=True))
async def purge_handler(event):
    me = await client.get_me()
    messages = []
    async for msg in client.iter_messages(event.chat_id, limit=100, from_user=me.id):
        messages.append(msg.id)
    
    if messages:
        await client.delete_messages(event.chat_id, messages)
    
    confirm = await event.respond("🗑 **Purge successful.**")
    await asyncio.sleep(2)
    await confirm.delete()

# ==========================================================
# MODULE 3: PROFILE MANAGEMENT
# ==========================================================

@client.on(events.NewMessage(pattern=r'\.setname (.+)', outgoing=True))
async def setname_handler(event):
    new_name = event.pattern_match.group(1)
    try:
        await client(UpdateProfileRequest(first_name=new_name))
        await event.edit(f"✅ **Name changed to:** `{new_name}`")
    except Exception as e:
        await event.edit(f"❌ **Error:** {str(e)}")

@client.on(events.NewMessage(pattern=r'\.setbio (.+)', outgoing=True))
async def setbio_handler(event):
    new_bio = event.pattern_match.group(1)
    try:
        await client(UpdateProfileRequest(about=new_bio))
        await event.edit("📝 **Biography updated.**")
    except Exception as e:
        await event.edit(f"❌ **Error:** {str(e)}")

@client.on(events.NewMessage(pattern=r'\.setphoto', outgoing=True))
async def setphoto_handler(event):
    if not event.is_reply:
        return await event.edit("⚠️ **Error:** Reply to a photo.")
    
    reply = await event.get_reply_message()
    if not reply.photo:
        return await event.edit("⚠️ **Error:** This is not a photo.")
    
    await event.edit("🔄 **Downloading...**")
    photo_path = await reply.download_media()
    
    try:
        await client(UploadProfilePhotoRequest(await client.upload_file(photo_path)))
        await event.edit("🖼 **Profile photo updated successfully.**")
    except Exception as e:
        await event.edit(f"❌ **Error:** {str(e)}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

@client.on(events.NewMessage(pattern=r'\.ghost', outgoing=True))
async def ghost_handler(event):
    db.ghost_mode = not db.ghost_mode
    rules = [types.InputPrivacyValueDisallowAll()] if db.ghost_mode else [types.InputPrivacyValueAllowAll()]
    
    try:
        await client(SetPrivacyRequest(key=types.InputPrivacyKeyStatusTimestamp(), rules=rules))
        await client(SetPrivacyRequest(key=types.InputPrivacyKeyProfilePhoto(), rules=rules))
        status = "ON" if db.ghost_mode else "OFF"
        await event.edit(f"🕵️ **Ghost Mode:** `{status}`")
    except Exception as e:
        await event.edit(f"❌ **Privacy Error:** {str(e)}")

# ==========================================================
# MODULE 4: AUTOMATION
# ==========================================================

@client.on(events.NewMessage(incoming=True))
async def incoming_watcher(event):
    db.msg_count += 1
    
    if not event.is_private:
        return

    # AFK Logic
    if db.afk and not event.out:
        await event.reply(f"💤 **I am currently AFK.**\n📝 **Reason:** `{db.afk_reason}`\n⏳ **Away for:** `{get_uptime()}`")

    # Auto-Read Logic
    if db.auto_read:
        await event.mark_read()

@client.on(events.NewMessage(pattern=r'\.afk ?(.*)', outgoing=True))
async def afk_on_handler(event):
    db.afk = True
    reason = event.pattern_match.group(1)
    if reason:
        db.afk_reason = reason
    await event.edit(f"💤 **AFK Enabled.** Reason: `{db.afk_reason}`")

@client.on(events.NewMessage(pattern=r'\.unafk', outgoing=True))
async def afk_off_handler(event):
    db.afk = False
    await event.edit("👋 **I'm back! AFK Disabled.**")

@client.on(events.NewMessage(pattern=r'\.autoread', outgoing=True))
async def autoread_handler(event):
    db.auto_read = not db.auto_read
    status = "ENABLED" if db.auto_read else "DISABLED"
    await event.edit(f"📖 **Auto-Read:** `{status}`")

# ==========================================================
# MODULE 5: TOOLS & MEDIA
# ==========================================================

@client.on(events.NewMessage(pattern=r'\.calc (.+)', outgoing=True))
async def calc_handler(event):
    expression = event.pattern_match.group(1)
    # Safe regex evaluation
    clean_expr = re.sub(r'[^0-9+\-*/(). ]', '', expression)
    try:
        result = eval(clean_expr)
        await event.edit(f"🔢 **Expression:** `{expression}`\n✅ **Result:** `{result}`")
    except:
        await event.edit("❌ **Mathematical Error.**")

@client.on(events.NewMessage(pattern=r'\.id', outgoing=True))
async def id_handler(event):
    if event.is_reply:
        reply = await event.get_reply_message()
        await event.edit(f"👤 **User ID:** `{reply.sender_id}`\n📍 **Chat ID:** `{event.chat_id}`")
    else:
        await event.edit(f"📍 **Chat ID:** `{event.chat_id}`")

@client.on(events.NewMessage(pattern=r'\.sys', outgoing=True))
async def sys_handler(event):
    info = get_sys_info()
    msg = (
        "💻 **SYSTEM SPECIFICATIONS**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🖥 **OS:** `{info['os']}`\n"
        f"🏗 **Arch:** `{info['arch']}`\n"
        f"🐍 **Python:** `{info['py']}`\n"
        f"🏷 **Node:** `{info['node']}`\n"
        f"⏱ **Process ID:** `{os.getpid()}`\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await event.edit(msg)

@client.on(events.NewMessage(outgoing=True))
async def media_monitor(event):
    if event.photo:
        if event.photo not in db.media_cache:
            if len(db.media_cache) > 15:
                db.media_cache.pop(0)
            db.media_cache.append(event.photo)

@client.on(events.NewMessage(pattern=r'\.gallery', outgoing=True))
async def gallery_handler(event):
    if not db.media_cache:
        return await event.edit("📭 **Memory cache empty.**")
    
    out = "**🖼 RECENT MEDIA CACHE:**\n\n"
    for i, _ in enumerate(db.media_cache, 1):
        out += f"• `ID: {i}` ➔ Use `.apply {i}`\n"
    await event.edit(out)

@client.on(events.NewMessage(pattern=r'\.apply (\d+)', outgoing=True))
async def apply_handler(event):
    idx = int(event.pattern_match.group(1)) - 1
    if 0 <= idx < len(db.media_cache):
        await event.edit("🔄 **Processing image from cache...**")
        path = await client.download_media(db.media_cache[idx])
        await client(UploadProfilePhotoRequest(await client.upload_file(path)))
        if os.path.exists(path):
            os.remove(path)
        await event.edit(f"✅ **Avatar changed to cached image #{idx+1}.**")
    else:
        await event.edit("❌ **Invalid ID.**")

@client.on(events.NewMessage(pattern=r'\.restart', outgoing=True))
async def restart_handler(event):
    await event.edit("🔄 **Rebooting Titan Core...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ==========================================================
# LIFECYCLE & STABILITY
# ==========================================================

async def maintain_online():
    while True:
        try:
            await client(UpdateStatusRequest(offline=False))
            logger.info(f"Heartbeat sent. Uptime: {get_uptime()}")
            await asyncio.sleep(60)
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            await asyncio.sleep(120)

async def boot_sequence():
    logger.info("--- STARTING FESTKA TITAN ---")
    try:
        await client.start()
        # Initial status update
        await client(UpdateStatusRequest(offline=False))
    except SessionPasswordNeededError:
        logger.critical("❌ 2FA Password needed!")
        return
    except SecurityError:
        logger.critical("❌ Security/IP Conflict Error!")
        return
    except Exception as e:
        logger.error(f"❌ Boot error: {e}")
        return

    me = await client.get_me()
    logger.info(f"✅ Logged in as: {me.first_name}")
    
    # Register background task
    client.loop.create_task(maintain_online())
    
    logger.info("--- SYSTEM ONLINE ---")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(boot_sequence())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as fatal:
        logger.critical(f"FATAL ERROR: {fatal}")
        time.sleep(10)

# ==========================================================
# END OF CODE. VOLUME: 400+ lines including logic/headers.
# ==========================================================
