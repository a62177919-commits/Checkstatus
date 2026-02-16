# API_ID: 34126767
# API_HASH: 44f1cdcc4c6544d60fe06be1b319d2dd

import os
import sys
import random
import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

API_ID = 34126767
API_HASH = "44f1cdcc4c6544d60fe06be1b319d2dd"
SESSION_STR = os.environ.get("SESSION_STR")

if not SESSION_STR:
    sys.exit(1)

client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

blocked_users = []
saved_photos = []
hide_mode = False

# ----КАТЕГОРИЯ: СПРАВКА----
@client.on(events.NewMessage(pattern=r'/Help', outgoing=True))
async def help_cmd(event):
    help_text = (
        "**📜 СПИСОК КОМАНД**\n"
        "ーーー\n"
        "🔹 `.ping` — Проверка связи\n"
        "🔹 `.блок (имя)` — Краш-автоответчик\n"
        "🔹 `.разблок (имя)` — Снять блок\n"
        "🔹 `/Privacy` — Режим инкогнито\n"
        "🔹 `/Offprivacy` — Вернуть настройки\n"
        "🔹 `/Hide` — Авто-архив (On/Off)\n"
        "🔹 `/addPhoto` — Список сохраненных фото\n"
        "🔹 `.setphoto` — Смена фото (реплай)\n"
        "🔹 `.setname (имя)` — Смена имени\n"
        "🔹 `.setbio (текст)` — Смена описания\n"
        "ーーー"
    )
    await event.edit(help_text)

# ----КАТЕГОРИЯ: УМНЫЙ АРХИВ----
@client.on(events.NewMessage(pattern=r'/Hide', outgoing=True))
async def toggle_hide(event):
    global hide_mode
    hide_mode = not hide_mode
    status = "ВКЛЮЧЕН" if hide_mode else "ВЫКЛЮЧЕН"
    await event.edit(f"🔒 Режим авто-архива: **{status}**")
    
    if hide_mode:
        await archive_all()

async def archive_all():
    async for dialog in client.iter_dialogs():
        if dialog.folder_id is None or dialog.folder_id == 0:
            await client(functions.folders.EditPeerFoldersRequest(
                folder_peers=[types.InputFolderPeer(peer=dialog.input_entity, folder_id=1)]
            ))

async def unarchive_all():
    async for dialog in client.iter_dialogs():
        if dialog.folder_id == 1:
            await client(functions.folders.EditPeerFoldersRequest(
                folder_peers=[types.InputFolderPeer(peer=dialog.input_entity, folder_id=0)]
            ))

@client.on(events.UserUpdate)
async def monitor_archive(event):
    global hide_mode
    if not hide_mode:
        return

    # Отслеживаем "прочтение" или заход в папку архива через статус присутствия/активности
    # Telegram API не дает прямого ивента "открыл архив", поэтому имитируем логику
    # Если зафиксировано действие в скрытом чате — временно достаем всё
    if event.typing or event.recording:
        await unarchive_all()
        await asyncio.sleep(30) # Даем 30 секунд на действия
        if hide_mode:
            await archive_all()

# ----КАТЕГОРИЯ: ПРИВАТНОСТЬ И БЛОК----
@client.on(events.NewMessage(pattern=r'\.блок (.+)', outgoing=True))
async def add_block(event):
    name = event.pattern_match.group(1)
    if name not in blocked_users:
        blocked_users.append(name)
    await event.delete()

@client.on(events.NewMessage(pattern=r'\.разблок (.+)', outgoing=True))
async def remove_block(event):
    name = event.pattern_match.group(1)
    if name in blocked_users:
        blocked_users.remove(name)
    await event.delete()

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def crash_auto_reply(event):
    sender = await event.get_sender()
    if sender and sender.first_name in blocked_users:
        crash_chars = "".join(chr(random.randint(0x0400, 0x04FF)) for _ in range(1000))
        await event.reply(f"В данный момент я занят и не могу ответить.\n{crash_chars}")

@client.on(events.NewMessage(pattern=r'/Privacy', outgoing=True))
async def privacy_on(event):
    await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyStatusTimestamp(), rules=[types.InputPrivacyValueDisallowAll()]))
    await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyProfilePhoto(), rules=[types.InputPrivacyValueDisallowAll()]))
    await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyChatInvite(), rules=[types.InputPrivacyValueDisallowAll()]))
    await event.delete()

@client.on(events.NewMessage(pattern=r'/Offprivacy', outgoing=True))
async def privacy_off(event):
    await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyStatusTimestamp(), rules=[types.InputPrivacyValueAllowAll()]))
    await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyProfilePhoto(), rules=[types.InputPrivacyValueAllowAll()]))
    await client(functions.account.SetPrivacyRequest(key=types.InputPrivacyKeyChatInvite(), rules=[types.InputPrivacyValueAllowAll()]))
    await event.delete()

# ----КАТЕГОРИЯ: МЕДИАТЕКА----
@client.on(events.NewMessage(outgoing=True))
async def save_photo_to_db(event):
    if event.photo:
        saved_photos.append(event.photo)

@client.on(events.NewMessage(pattern=r'/addPhoto', outgoing=True))
async def list_photos(event):
    if not saved_photos:
        return await event.edit("Список фото пуст.")
    msg = "**🖼 Сохраненные фото:**\n"
    for i, _ in enumerate(saved_photos, 1):
        msg += f"Номер {i}: `/setnum {i}`\n"
    await event.edit(msg)

@client.on(events.NewMessage(pattern=r'/setnum (\d+)', outgoing=True))
async def set_photo_by_number(event):
    num = int(event.pattern_match.group(1)) - 1
    if 0 <= num < len(saved_photos):
        photo = await client.download_media(saved_photos[num])
        await client(functions.photos.UploadProfilePhotoRequest(await client.upload_file(photo)))
        await event.edit(f"✅ Фото №{num+1} установлено.")
    else:
        await event.edit("Неверный номер.")

# ----КАТЕГОРИЯ: УПРАВЛЕНИЕ ПРОФИЛЕМ----
@client.on(events.NewMessage(pattern=r'\.setphoto', outgoing=True))
async def change_photo(event):
    if not event.is_reply: return
    reply = await event.get_reply_message()
    if reply.photo:
        photo = await client.download_media(reply.photo)
        await client(functions.photos.UploadProfilePhotoRequest(await client.upload_file(photo)))
        await event.delete()

@client.on(events.NewMessage(pattern=r'\.setname (.+)', outgoing=True))
async def change_name(event):
    new_name = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(first_name=new_name))
    await event.delete()

@client.on(events.NewMessage(pattern=r'\.setbio (.+)', outgoing=True))
async def change_bio(event):
    new_bio = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(about=new_bio))
    await event.delete()

# ----КАТЕГОРИЯ: СИСТЕМА----
@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
async def ping(event):
    await event.edit("OK")

if __name__ == "__main__":
    client.start()
    client.run_until_disconnected()
