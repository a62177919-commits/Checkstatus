# API_ID: 34126767
# API_HASH: 44f1cdcc4c6544d60fe06be1b319d2dd

import os
import sys
import random
import asyncio
import datetime
import time
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, GetHistoryRequest
from telethon.errors import FloodWaitError

# ---- CONFIGURATION ----
API_ID = 34126767
API_HASH = "44f1cdcc4c6544d60fe06be1b319d2dd"
SESSION_STR = os.environ.get("SESSION_STR")

if not SESSION_STR:
    sys.exit(1)

client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

# ---- DATABASE / STATE ----
blocked_ids = []
saved_photos = []
auto_read_enabled = False
afk_enabled = False
afk_reason = "Занят"
start_time = datetime.datetime.now()

# ---- CONSTANTS ----
CRASH_CHARS_SMALL = "".join(chr(random.randint(0x0300, 0x036F)) for _ in range(50))
CRASH_CHARS_BIG = "".join(chr(random.randint(0x0400, 0x08FF)) for _ in range(2000))

# ---- CATEGORY: HELPERS ----
def get_uptime():
    now = datetime.datetime.now()
    delta = now - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}ч {minutes}м {seconds}с"

# ---- CATEGORY: SYSTEM COMMANDS ----
@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
async def ping(event):
    start = datetime.datetime.now()
    await event.edit("🏓 `Pinging...`")
    end = datetime.datetime.now()
    ms = (end - start).microseconds / 1000
    await event.edit(f"🚀 **Festka Online**\n🛰 **Lat:** `{ms}ms`\n⏳ **Uptime:** `{get_uptime()}`")

@client.on(events.NewMessage(pattern=r'\.restart', outgoing=True))
async def restart(event):
    await event.edit("🔄 **Restarting...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.NewMessage(pattern=r'/Help', outgoing=True))
async def help_cmd(event):
    help_text = (
        "**📜 FESTKA USERBOT MENU**\n"
        "ーーー\n"
        "🛡 **БЛОКИРОВКА**\n"
        "• `.блок` — Полная изоляция (reply)\n"
        "• `.разблок` — Снять ограничения (reply)\n"
        "\n"
        "👤 **ПРОФИЛЬ**\n"
        "• `.setname (имя)` — Сменить имя\n"
        "• `.setbio (текст)` — Сменить описание\n"
        "• `.setphoto` — Аватар по реплаю\n"
        "• `/addPhoto` — Список сохраненных фото\n"
        "• `/setnum (номер)` — Поставить из списка\n"
        "\n"
        "🔒 **ПРИВАТНОСТЬ**\n"
        "• `/Privacy` — Скрыть всё (Online, Photo, Invites)\n"
        "• `/Offprivacy` — Вернуть всё на 'Все'\n"
        "\n"
        "⚙️ **УТИЛИТЫ**\n"
        "• `.ping` — Пинг и аптайм\n"
        "• `.autoread` — Переключить авточтение\n"
        "• `.afk (текст)` — Режим AFK\n"
        "• `.unafk` — Выйти из AFK\n"
        "• `.id` — Узнать ID чата/юзера\n"
        "• `.purge` — Удалить свои сообщения\n"
        "ーーー"
    )
    await event.edit(help_text)

# ---- CATEGORY: ADVANCED BLOCK SYSTEM ----
@client.on(events.NewMessage(pattern=r'\.блок', outgoing=True))
async def advanced_block(event):
    if not event.is_reply:
        return await event.edit("❌ Ответь на сообщение цели!")
    
    reply = await event.get_reply_message()
    user = await reply.get_sender()
    
    if not user or isinstance(user, types.Channel):
        return await event.edit("❌ Ошибка: Это не пользователь.")

    u_id = user.id
    if u_id not in blocked_ids:
        blocked_ids.append(u_id)

    try:
        # Переименование в список контактов
        await client(functions.contacts.AddContactRequest(
            id=u_id, first_name="Заблокирован", last_name="", phone="", add_phone_privacy_exception=False
        ))
        # Полный мут
        await client(functions.account.UpdateNotifySettingsRequest(
            peer=types.InputNotifyPeer(peer=await client.get_input_entity(u_id)),
            settings=types.InputPeerNotifySettings(mute_until=2147483647)
        ))
        # В архив
        await client(functions.folders.EditPeerFoldersRequest(
            folder_peers=[types.InputFolderPeer(peer=await client.get_input_entity(u_id), folder_id=1)]
        ))
        await event.edit(f"🔒 **ID {u_id} ИЗОЛИРОВАН**\n• Имя: `Заблокирован`\n• Уведомления: `OFF`\n• Папка: `Архив`")
    except Exception as e:
        await event.edit(f"🛑 Error: {e}")

@client.on(events.NewMessage(pattern=r'\.разблок', outgoing=True))
async def unblock_user(event):
    if not event.is_reply:
        return await event.edit("❌ Ответь на сообщение!")
    
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
            await event.edit(f"🔓 **ID {u_id} РАЗБЛОКИРОВАН**")
        except:
            await event.edit("🔓 Снят локальный бан.")
    else:
        await event.edit("🤔 Этот пользователь не в списке блока.")

@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    if not event.is_private:
        return

    # Логика блока
    if event.sender_id in blocked_ids:
        try:
            await event.reply(f"Нет {CRASH_CHARS_SMALL}")
            await client(functions.folders.EditPeerFoldersRequest(
                folder_peers=[types.InputFolderPeer(peer=event.input_chat, folder_id=1)]
            ))
        except: pass

    # Логика AFK
    if afk_enabled and not event.out:
        await event.reply(f"🛰 **Я сейчас AFK**\n📝 Причина: `{afk_reason}`")

# ---- CATEGORY: PRIVACY CONTROL ----
@client.on(events.NewMessage(pattern=r'/Privacy', outgoing=True))
async def privacy_on(event):
    await event.edit("⚙️ **Применяю настройки приватности...**")
    try:
        rules = [types.InputPrivacyValueDisallowAll()]
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyStatusTimestamp(), rules=rules))
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyProfilePhoto(), rules=rules))
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyChatInvite(), rules=rules))
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyPhoneCall(), rules=rules))
        await event.edit("✅ **Privacy ON**\n• Online: `Hidden`\n• Photo: `Hidden`\n• Invites: `Hidden`")
    except Exception as e:
        await event.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'/Offprivacy', outgoing=True))
async def privacy_off(event):
    await event.edit("⚙️ **Снимаю ограничения...**")
    try:
        rules = [types.InputPrivacyValueAllowAll()]
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyStatusTimestamp(), rules=rules))
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyProfilePhoto(), rules=rules))
        await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyChatInvite(), rules=rules))
        await event.edit("✅ **Privacy OFF**\nВсе настройки возвращены на 'Все'.")
    except Exception as e:
        await event.edit(f"❌ Error: {e}")

# ---- CATEGORY: MEDIA & PHOTOS ----
@client.on(events.NewMessage(outgoing=True))
async def capture_media(event):
    if event.photo:
        if event.photo not in saved_photos:
            saved_photos.append(event.photo)

@client.on(events.NewMessage(pattern=r'/addPhoto', outgoing=True))
async def gallery(event):
    if not saved_photos:
        return await event.edit("📭 Галерея пуста.")
    
    out = "**📂 ВАША МЕДИАТЕКА:**\n"
    for i, _ in enumerate(saved_photos, 1):
        out += f"🖼 Фото #{i} | Установить: `/setnum {i}`\n"
    await event.edit(out)

@client.on(events.NewMessage(pattern=r'/setnum (\d+)', outgoing=True))
async def set_media_num(event):
    idx = int(event.pattern_match.group(1)) - 1
    if 0 <= idx < len(saved_photos):
        await event.edit(f"⏳ Устанавливаю фото #{idx+1}...")
        path = await client.download_media(saved_photos[idx])
        await client(UploadProfilePhotoRequest(await client.upload_file(path)))
        os.remove(path)
        await event.edit(f"✅ Аватар изменен на фото #{idx+1}")
    else:
        await event.edit("❌ Фото с таким номером не существует.")

# ---- CATEGORY: PROFILE EDITING ----
@client.on(events.NewMessage(pattern=r'\.setname (.+)', outgoing=True))
async def name_change(event):
    name = event.pattern_match.group(1)
    await client(UpdateProfileRequest(first_name=name))
    await event.edit(f"✅ Имя изменено на: `{name}`")

@client.on(events.NewMessage(pattern=r'\.setbio (.+)', outgoing=True))
async def bio_change(event):
    bio = event.pattern_match.group(1)
    await client(UpdateProfileRequest(about=bio))
    await event.edit(f"✅ Описание изменено на: `{bio}`")

@client.on(events.NewMessage(pattern=r'\.setphoto', outgoing=True))
async def photo_by_reply(event):
    if not event.is_reply:
        return await event.edit("❌ Ответь на фото.")
    reply = await event.get_reply_message()
    if reply.photo:
        await event.edit("⏳ Загрузка...")
        path = await client.download_media(reply.photo)
        await client(UploadProfilePhotoRequest(await client.upload_file(path)))
        os.remove(path)
        await event.edit("✅ Фото профиля обновлено.")
    else:
        await event.edit("❌ Реплай должен быть на фото.")

# ---- CATEGORY: UTILS ----
@client.on(events.NewMessage(pattern=r'\.id', outgoing=True))
async def get_id(event):
    if event.is_reply:
        reply = await event.get_reply_message()
        await event.edit(f"🆔 **User ID:** `{reply.sender_id}`\n📍 **Chat ID:** `{event.chat_id}`")
    else:
        await event.edit(f"📍 **Chat ID:** `{event.chat_id}`")

@client.on(events.NewMessage(pattern=r'\.purge', outgoing=True))
async def purge_msgs(event):
    chat = await event.get_input_chat()
    msgs = []
    async for msg in client.iter_messages(chat, from_user="me", limit=100):
        msgs.append(msg)
    if msgs:
        await client.delete_messages(chat, msgs)
        status = await event.respond("✅ Чистка завершена.")
        await asyncio.sleep(3)
        await status.delete()

@client.on(events.NewMessage(pattern=r'\.autoread', outgoing=True))
async def toggle_read(event):
    global auto_read_enabled
    auto_read_enabled = not auto_read_enabled
    status = "ВКЛ" if auto_read_enabled else "ВЫКЛ"
    await event.edit(f"📖 **Авточтение:** `{status}`")

@client.on(events.NewMessage(incoming=True))
async def do_autoread(event):
    if auto_read_enabled:
        await event.mark_read()

@client.on(events.NewMessage(pattern=r'\.afk ?(.*)', outgoing=True))
async def set_afk(event):
    global afk_enabled, afk_reason
    reason = event.pattern_match.group(1)
    afk_enabled = True
    if reason:
        afk_reason = reason
    await event.edit(f"💤 **Режим AFK ВКЛ**\nПричина: `{afk_reason}`")

@client.on(events.NewMessage(pattern=r'\.unafk', outgoing=True))
async def unset_afk(event):
    global afk_enabled
    afk_enabled = False
    await event.edit("🌅 **С возвращением! AFK ВЫКЛ**")

# ---- CATEGORY: AUTO-TASKS ----
async def status_cycler():
    """Фоновое обновление статуса (эмуляция онлайна)"""
    while True:
        try:
            await client(UpdateStatusRequest(offline=False))
            await asyncio.sleep(60)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except:
            break

# ---- CATEGORY: SPAM & TOOLS ----
@client.on(events.NewMessage(pattern=r'\.spam (\d+) (.+)', outgoing=True))
async def spammer(event):
    count = int(event.pattern_match.group(1))
    text = event.pattern_match.group(2)
    await event.delete()
    for _ in range(count):
        await client.send_message(event.chat_id, text)
        await asyncio.sleep(0.3)

# ---- CATEGORY: INFO ----
@client.on(events.NewMessage(pattern=r'\.info', outgoing=True))
async def user_info(event):
    if not event.is_reply:
        return await event.edit("❌ Реплайни на юзера.")
    reply = await event.get_reply_message()
    user = await reply.get_sender()
    
    text = f"👤 **ИНФО О ПОЛЬЗОВАТЕЛЕ**\n"
    text += f"ID: `{user.id}`\n"
    text += f"Имя: `{user.first_name}`\n"
    text += f"Фамилия: `{user.last_name or 'Нет'}`\n"
    text += f"Юзернейм: `@{user.username or 'Нет'}`\n"
    text += f"Бот: `{'Да' if user.bot else 'Нет'}`\n"
    await event.edit(text)

# ---- MAIN RUNNER ----
if __name__ == "__main__":
    print("--- FESTKA USERBOT STARTING ---")
    client.start()
    print("--- LOGGED IN SUCCESSFULLY ---")
    
    # Регистрация фоновых задач
    client.loop.create_task(status_cycler())
    
    print("--- BOT IS ACTIVE ---")
    client.run_until_disconnected()

# ---- END OF CODE ----
# Данный код расширен для обеспечения стабильности и функциональности.
# Каждая категория команд изолирована.
# Поддерживается работа через GitHub Actions.
# Строк: ~315.
