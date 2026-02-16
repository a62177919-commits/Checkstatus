# API_ID: 34126767
# API_HASH: 44f1cdcc4c6544d60fe06be1b319d2dd

import os
import sys
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.account import UpdateProfileRequest

# Данные
API_ID = 34126767
API_HASH = "44f1cdcc4c6544d60fe06be1b319d2dd"

# Берем из секретов GitHub (через YAML)
SESSION_STR = os.environ.get("SESSION_STR")

if not SESSION_STR:
    print("❌ ОШИБКА: STRING_SESSION не передан в код!")
    sys.exit(1)

client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

# ----КАТЕГОРИЯ: УПРАВЛЕНИЕ ПРОФИЛЕМ----
@client.on(events.NewMessage(pattern=r'\.setphoto', outgoing=True))
async def change_photo(event):
    if not event.is_reply: return
    reply = await event.get_reply_message()
    if reply.photo:
        photo = await client.download_media(reply.photo)
        await client(UploadProfilePhotoRequest(await client.upload_file(photo)))
        await event.delete()

@client.on(events.NewMessage(pattern=r'\.setname (.+)', outgoing=True))
async def change_name(event):
    new_name = event.pattern_match.group(1)
    await client(UpdateProfileRequest(first_name=new_name))
    await event.delete()

# ----КАТЕГОРИЯ: СИСТЕМА----
@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
async def ping(event):
    await event.edit("OK")

if __name__ == "__main__":
    print("🚀 Festka Bot запущен...")
    client.start()
    client.run_until_disconnected()
