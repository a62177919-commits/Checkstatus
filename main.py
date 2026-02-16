# ==========================================================
# FESTKA USERBOT - ULTIMATE EDITION (LONG VERSION)
# API_ID: 34126767
# API_HASH: 44f1cdcc4c6544d60fe06be1b319d2dd
# ==========================================================

import os
import sys
import random
import asyncio
import datetime
import logging
import time
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.messages import GetHistoryRequest, ReadMentionsRequest
from telethon.tl.types import UpdateShortChatMessage, UpdateShortMessage

# ---- ЛОГИРОВАНИЕ ----
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FestkaBot")

# ---- КОНФИГУРАЦИЯ ----
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION_STR = os.environ.get("SESSION_STR")

if not SESSION_STR or not API_ID or not API_HASH:
    logger.error("Критическая ошибка: Переменные окружения не найдены!")
    sys.exit(1)

client = TelegramClient(StringSession(SESSION_STR), int(API_ID), API_HASH)

# ---- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ----
blocked_ids = []
saved_photos = []
auto_read_enabled = False
afk_enabled = False
afk_reason = "Занят делами"
start_time = datetime.datetime.now()
msg_count = 0

# ---- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----
def get_uptime():
    delta = datetime.datetime.now() - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}ч {minutes}м {seconds}с"

def get_crash_text():
    chars = [chr(random.randint(0x0300, 0x036F)) for _ in range(60)]
    return "Нет " + "".join(chars)

# ---- КАТЕГОРИЯ: СИСТЕМА И ИНФО ----
@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
async def ping_handler(event):
    t1 = datetime.datetime.now()
    await event.edit("📡 `Checking connection...`")
    t2 = datetime.datetime.now()
    ping = (t2 - t1).microseconds / 1000
    await event.edit(
        f"🚀 **Festka Bot Status**\n"
        f"ーーー\n"
        f"🛰 **Пинг:** `{ping}ms`\n"
        f"⏳ **Аптайм:** `{get_uptime()}`\n"
        f"📊 **Секреты:** `Valid`\n"
        f"🛠 **Версия:** `3.5.0-Stable`"
    )

@client.on(events.NewMessage(pattern=r'/Help', outgoing=True))
async def help_handler(event):
    menu = (
        "**👑 FESTKA CONTROL PANEL**\n"
        "ーーー\n"
        "🛡 **ИЗОЛЯЦИЯ (BLOCK)**\n"
        "• `.блок` — Забанить юзера (reply)\n"
        "• `.разблок` — Снять бан (reply)\n"
        "\n"
        "🔒 **ПРИВАТНОСТЬ (PRIVACY)**\n"
        "• `/Privacy` — Скрыть всё от всех\n"
        "• `/Offprivacy` — Открыть всё обратно\n"
        "\n"
        "👤 **АККАУНТ (PROFILE)**\n"
        "• `.setname (имя)` — Смена имени\n"
        "• `.setbio (текст)` — Смена био\n"
        "• `.setphoto` — Аватар по реплаю\n"
        "• `/addPhoto` — Моя медиатека\n"
        "• `/setnum (№)` — Поставить фото из списка\n"
        "\n"
        "⚙️ **ИНСТРУМЕНТЫ (TOOLS)**\n"
        "• `.afk (причина)` — Включить AFK\n"
        "• `.unafk` — Выключить AFK\n"
        "• `.autoread` — Авточтение сообщений\n"
        "• `.purge` — Удалить последние 100 сообщений\n"
        "• `.id` — Узнать ID чата/юзера\n"
        "• `.restart` — Перезапуск бота\n"
        "ーーー"
    )
    await event.edit(menu)

@client.on(events.NewMessage(pattern=r'\.restart', outgoing=True))
async def restart_handler(event):
    await event.edit("♻️ **Restarting core...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ---- КАТЕГОРИЯ: СИСТЕМА БЛОКИРОВКИ (BLOCK) ----
@client.on(events.NewMessage(pattern=r'\.блок', outgoing=True))
async def block_logic(event):
    if not event.is_reply:
        return await event.edit("❌ Ошибка: Нужен ответ на сообщение!")
    
    reply = await event.get_reply_message()
    user = await reply.get_sender()
    
    if not user or isinstance(user, types.Channel):
        return await event.edit("❌ Ошибка: Цель не является пользователем.")

    u_id = user.id
    if u_id not in blocked_ids:
        blocked_ids.append(u_id)

    try:
        await client(functions.contacts.AddContactRequest(
            id=u_id, first_name="Заблокирован", last_name="", phone="", add_phone_privacy_exception=False
        ))
        await client(functions.account.UpdateNotifySettingsRequest(
            peer=types.InputNotifyPeer(peer=await client.get_input_entity(u_id)),
            settings=types.InputPeerNotifySettings(mute_until=2147483647)
        ))
        await client(functions.folders.EditPeerFoldersRequest(
            folder_peers=[types.InputFolderPeer(peer=await client.get_input_entity(u_id), folder_id=1)]
        ))
        await event.edit(f"✅ **ID {u_id} заблокирован.**\nСтатус: `Изолирован в архиве`")
    except Exception as e:
        await event.edit(f"🛑 Ошибка API: {e}")

@client.on(events.NewMessage(pattern=r'\.разблок', outgoing=True))
async def unblock_logic(event):
    if not event.is_reply:
        return await event.edit("❌ Реплаем на юзера!")
    
    reply = await event.get_reply_message()
    u_id = reply.sender_id
    
    if u_id in blocked_ids:
        blocked_ids.remove(u_id)
        try:
            await client(functions.folders.EditPeerFoldersRequest(
                folder_peers=[types.InputFolderPeer(peer=await client.get_input_entity(u_id), folder_id=0)]
            ))
            await client(functions.account.UpdateNotifySettingsRequest(
                peer=types.InputNotifyPeer(peer=await client.get_input_entity(u_id)),
                settings=types.InputPeerNotifySettings(mute_until=0)
            ))
            await event.edit("🔓 **Пользователь возвращен из архива.**")
        except:
            await event.edit("🔓 Списки очищены.")
    else:
        await event.edit("❕ Пользователь не был в блоке.")

# ---- ОБРАБОТКА ВХОДЯЩИХ (AFK / BLOCK / READ) ----
@client.on(events.NewMessage(incoming=True))
async def main_incoming_handler(event):
    global msg_count
    msg_count += 1
    
    if not event.is_private:
        return

    if event.sender_id in blocked_ids:
        try:
            await event.reply(get_crash_text())
            await client(functions.folders.EditPeerFoldersRequest(
                folder_peers=[types.InputFolderPeer(peer=event.input_chat, folder_id=1)]
            ))
        except: pass

    if afk_enabled and not event.out:
        await event.reply(f"💤 **Я сейчас не в сети.**\n📝 Причина: `{afk_reason}`")

    if auto_read_enabled:
        await event.mark_read()

# ---- КАТЕГОРИЯ: УПРАВЛЕНИЕ ПРИВАТНОСТЬЮ ----
@client.on(events.NewMessage(pattern=r'/Privacy', outgoing=True))
async def set_privacy_max(event):
    await event.edit("🛡 **Засекречиваю аккаунт...**")
    try:
        rules = [types.InputPrivacyValueDisallowAll()]
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyStatusTimestamp(), rules=rules))
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyProfilePhoto(), rules=rules))
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyChatInvite(), rules=rules))
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyPhoneCall(), rules=rules))
        await event.edit("✅ **Максимальная приватность включена!**")
    except Exception as e:
        await event.edit(f"❌ Ошибка: {e}")

# ---- КАТЕГОРИЯ: МЕДИАТЕКА И ФОТО ----
@client.on(events.NewMessage(outgoing=True))
async def media_collector(event):
    if event.photo:
        if event.photo not in saved_photos:
            saved_photos.append(event.photo)

@client.on(events.NewMessage(pattern=r'/addPhoto', outgoing=True))
async def show_gallery(event):
    if not saved_photos:
        return await event.edit("📭 Галерея пуста.")
    response = "**🖼 ВАША ГАЛЕРЕЯ:**\n"
    for i, p in enumerate(saved_photos, 1):
        response += f"🆔 Фото №{i} | Команда: `/setnum {i}`\n"
    await event.edit(response)

@client.on(events.NewMessage(pattern=r'/setnum (\d+)', outgoing=True))
async def set_photo_num(event):
    index = int(event.pattern_match.group(1)) - 1
    if 0 <= index < len(saved_photos):
        file = await client.download_media(saved_photos[index])
        await client(UploadProfilePhotoRequest(await client.upload_file(file)))
        os.remove(file)
        await event.edit(f"✅ Успешно! Фото №{index+1} на аватаре.")

# ---- КАТЕГОРИЯ: ПРОФИЛЬ ----
@client.on(events.NewMessage(pattern=r'\.setname (.+)', outgoing=True))
async def change_name_cmd(event):
    await client(UpdateProfileRequest(first_name=event.pattern_match.group(1)))
    await event.edit("📝 Имя изменено.")

@client.on(events.NewMessage(pattern=r'\.purge', outgoing=True))
async def purge_handler(event):
    chat = await event.get_input_chat()
    messages = []
    async for m in client.iter_messages(chat, from_user="me", limit=101):
        messages.append(m)
    await client.delete_messages(chat, messages)

@client.on(events.NewMessage(pattern=r'\.autoread', outgoing=True))
async def autoread_toggle(event):
    global auto_read_enabled
    auto_read_enabled = not auto_read_enabled
    await event.edit(f"📖 **Авточтение:** `{'ВКЛ' if auto_read_enabled else 'ВЫКЛ'}`")

# ---- ФОНОВЫЕ ЗАДАЧИ ----
async def online_maintainer():
    while True:
        try:
            await client(UpdateStatusRequest(offline=False))
            await asyncio.sleep(30)
        except:
            await asyncio.sleep(60)

async def self_keep_alive():
    while True:
        logger.info(f"Аптайм: {get_uptime()}. Сообщений: {msg_count}")
        await asyncio.sleep(300)

# ---- ЗАПУСК ----
if __name__ == "__main__":
    logger.info("Инициализация Festka Bot...")
    try:
        client.start()
        logger.info("Авторизация успешна!")
        
        client.loop.create_task(online_maintainer())
        client.loop.create_task(self_keep_alive())
        
        logger.info("--- BOT IS ACTIVE ---")
        client.run_until_disconnected()
        
    except Exception as start_err:
        logger.critical(f"Ошибка при запуске: {start_err}")
        sys.exit(1)
