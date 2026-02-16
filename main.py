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

# ----КАТЕГОРИЯ: УЛЬТРА-ХАЙД (БЕСКОНЕЧНЫЙ ЦИКЛ)----
async def flood_archiver():
    """Максимально быстрый переброс чатов в архив"""
    global hide_mode
    while True:
        if hide_mode:
            try:
                # Берем все диалоги из папки 0 (основная) и кидаем в 1 (архив)
                async for dialog in client.iter_dialogs(folder=0):
                    if dialog.id == 777000: continue # Пропускаем системный ТГ
                    await client(functions.folders.EditPeerFoldersRequest(
                        folder_peers=[types.InputFolderPeer(peer=dialog.input_entity, folder_id=1)]
                    ))
                # Минимальная задержка, чтобы не получить FloodWait, но было быстро
                await asyncio.sleep(0.1) 
            except Exception:
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(1)

@client.on(events.NewMessage(pattern=r'/Hide', outgoing=True))
async def toggle_hide(event):
    global hide_mode
    hide_mode = not hide_mode
    status = "🔥 УЛЬТРА-СКОРОСТЬ" if hide_mode else "ВЫКЛЮЧЕН"
    await event.edit(f"🔒 **Hide Mode**: {status}")

# Мгновенная реакция на входящие (чтобы не ждал цикла)
@client.on(events.NewMessage(incoming=True))
async def on_new_msg(event):
    if hide_mode:
        try:
            await client(functions.folders.EditPeerFoldersRequest(
                folder_peers=[types.InputFolderPeer(peer=event.input_chat, folder_id=1)]
            ))
        except: pass

# ----КАТЕГОРИЯ: БЛОК И КРАШ----
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
        crash_chars = "".join(chr(random.randint(0x0400, 0x08FF)) for _ in range(3000))
        await event.reply(f"SYSTEM_ERROR: BUSY.\n{crash_chars}")

# ----КАТЕГОРИЯ: ПРИВАТНОСТЬ----
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

# ----ОСНОВНОЕ----
@client.on(events.NewMessage(pattern=r'/Help', outgoing=True))
async def help_cmd(event):
    await event.edit("**CMD:**\n`.ping` | `.блок` | `/Hide` | `/Privacy` | `/Offprivacy`")

@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
async def ping(event):
    await event.edit("STABLE")

if __name__ == "__main__":
    client.start()
    # Запускаем фоновый цикл переброса в архив
    client.loop.create_task(flood_archiver())
    client.run_until_disconnected()
