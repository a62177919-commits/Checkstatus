import os, asyncio, requests
from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telethon.tl.types import UserStatusOnline

# Данные из Secrets
API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

# Флаг вечного онлайна (в памяти скрипта)
always_online = False

async def main():
    global always_online
    response = requests.get(f"{FB_URL}session.json")
    session_str = response.json()
    
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)

    async with client:
        print("✅ Festka запущена с функцией Online!")
        await client.send_message('me', "🚀 **Festka Online**\n\nНовые команды:\n`/online_on` — включить вечный онлайн\n`/online_off` — выключить")

        # ОБРАБОТЧИК КОМАНД
        @client.on(events.NewMessage(chats='me'))
        async def handler(event):
            global always_online
            text = event.raw_text.strip().lower()
            targets = requests.get(f"{FB_URL}targets.json").json() or {}
            if not isinstance(targets, dict): targets = {}
            
            # Управление вечным онлайном
            if text == '/online_on':
                always_online = True
                await event.respond("🟢 Режим «Вечно в сети» ВКЛЮЧЕН.")
            elif text == '/online_off':
                always_online = False
                await event.respond("⚪ Режим «Вечно в сети» ВЫКЛЮЧЕН.")

            # Управление списком слежки
            elif text.startswith('+'):
                user = text.replace('+', '').strip().replace('@', '')
                targets[user] = False
                requests.put(f"{FB_URL}targets.json", json=targets)
                await event.respond(f"✅ Теперь слежу за @{user}")
            elif text.startswith('-'):
                user = text.replace('-', '').strip().replace('@', '')
                if user in targets:
                    del targets[user]
                    requests.put(f"{FB_URL}targets.json", json=targets)
                    await event.respond(f"❌ Удалено: @{user}")

        # ГЛАВНЫЙ ЦИКЛ (Мониторинг + Пинг онлайна)
        counter = 0
        while True:
            # 1. Держим онлайн (каждые 40 секунд, если включено)
            if always_online:
                await client(functions.account.UpdateStatusRequest(offline=False))
            
            # 2. Проверяем цели (каждые 40 секунд)
            targets = requests.get(f"{FB_URL}targets.json").json() or {}
            if isinstance(targets, dict):
                for user, last_status in targets.items():
                    try:
                        u = await client.get_entity(user)
                        is_online = isinstance(u.status, UserStatusOnline)
                        if is_online != last_status:
                            icon = "🟢" if is_online else "🔴"
                            status_txt = "в сети" if is_online else "вышел(а)"
                            await client.send_message('me', f"{icon} @{user} теперь {status_txt}")
                            targets[user] = is_online
                            requests.put(f"{FB_URL}targets.json", json=targets)
                    except: continue
            
            await asyncio.sleep(40)

asyncio.run(main())
