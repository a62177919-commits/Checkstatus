import os, asyncio, requests
from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telethon.tl.types import UserStatusOnline

# Данные из Secrets
API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

always_online = False

async def main():
    global always_online
    response = requests.get(f"{FB_URL}session.json")
    session_str = response.json()
    
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)

    async with client:
        print("✅ Festka запущена!")
        # При запуске проверяем, есть ли альт-аккаунт в базе
        alt_id = requests.get(f"{FB_URL}alt_account.json").json()
        
        # Определяем, куда слать сервисные сообщения (в избранное или на альт)
        report_to = alt_id if alt_id else 'me'
        await client.send_message(report_to, "🚀 **Festka Online Up**\n\nИспользуй `/alt @username` чтобы перенести уведомления сюда.")

        @client.on(events.NewMessage(chats='me'))
        async def handler(event):
            global always_online
            text = event.raw_text.strip().lower()
            
            # Настройка второго аккаунта
            if text.startswith('/alt'):
                target = text.replace('/alt', '').strip()
                try:
                    alt_entity = await client.get_entity(target)
                    new_alt_id = alt_entity.id
                    requests.put(f"{FB_URL}alt_account.json", json=new_alt_id)
                    await event.respond(f"📲 Теперь уведомления будут приходить на ID: `{new_alt_id}`")
                    await client.send_message(new_alt_id, "🔔 Теперь я буду присылать отчеты сюда!")
                except Exception as e:
                    await event.respond(f"❌ Не удалось найти юзера: {e}")

            elif text == '/online_on':
                always_online = True
                await event.respond("🟢 Вечный онлайн включен")
            elif text == '/online_off':
                always_online = False
                await event.respond("⚪ Вечный онлайн выключен")

            # Управление списком целей
            elif text.startswith('+'):
                user = text.replace('+', '').strip().replace('@', '')
                targets = requests.get(f"{FB_URL}targets.json").json() or {}
                targets[user] = False
                requests.put(f"{FB_URL}targets.json", json=targets)
                await event.respond(f"✅ Слежу за @{user}")

        # Цикл мониторинга
        while True:
            if always_online:
                await client(functions.account.UpdateStatusRequest(offline=False))
            
            # Проверяем цели и шлем уведомления
            targets = requests.get(f"{FB_URL}targets.json").json() or {}
            current_alt = requests.get(f"{FB_URL}alt_account.json").json()
            notify_chat = current_alt if current_alt else 'me'

            if isinstance(targets, dict):
                for user, last_status in targets.items():
                    try:
                        u = await client.get_entity(user)
                        is_online = isinstance(u.status, UserStatusOnline)
                        if is_online != last_status:
                            icon = "🟢" if is_online else "🔴"
                            msg = f"{icon} @{user} {'в сети' if is_online else 'вышел(а)'}"
                            await client.send_message(notify_chat, msg)
                            targets[user] = is_online
                            requests.put(f"{FB_URL}targets.json", json=targets)
                    except: continue
            await asyncio.sleep(40)

asyncio.run(main())
