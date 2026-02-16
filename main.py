# API_ID: 34126767
# API_HASH: 44f1cdcc4c6544d60fe06be1b319d2dd

import os
import sys
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

API_ID = 34126767
API_HASH = "44f1cdcc4c6544d60fe06be1b319d2dd"
SESSION_STR = os.environ.get("SESSION_STR")

if not SESSION_STR:
    sys.exit(1)

client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

blocked_users = []

# ----КАТЕГОРИЯ: ПРИВАТНОСТЬ И БЛОК----
@client.on(events.NewMessage(pattern=r'\.блок (.+)', outgoing=True))
async def add_block(event):
    name = event.pattern_match.group(1)
    if name not in blocked_users:
        blocked_users.append(name)
    await event.delete()

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def auto_reply(event):
    sender = await event.get_sender()
    name = sender.first_name
    if name in blocked_users:
        await event.reply("В данный момент я занят и не могу ответить.")

@client.on(events.NewMessage(pattern=r'/Privacy', outgoing=True))
async def privacy_on(event):
    await client(functions.account.SetPrivacyRequest(
        key=types.InputPrivacyKeyStatusTimestamp(),
        rules=[types.InputPrivacyValueDisallowAll()]
    ))
    await client(functions.account.SetPrivacyRequest(
        key=types.InputPrivacyKeyChatInvite(),
        rules=[types.InputPrivacyValueDisallowAll()]
    ))
    await client(functions.account.SetPrivacyRequest(
        key=types.InputPrivacyKeyPhoneCall(),
        rules=[types.InputPrivacyValueDisallowAll()]
    ))
    await client(functions.account.SetPrivacyRequest(
        key=types.InputPrivacyKeyProfilePhoto(),
        rules=[types.InputPrivacyValueDisallowAll()]
    ))
    await event.delete()

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

# ----КАТЕГОРИЯ: СИСТЕМА----
@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
async def ping(event):
    await event.edit("OK")

if __name__ == "__main__":
    client.start()
    client.run_until_disconnected()
