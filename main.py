import os, asyncio, requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import UserStatusOnline

# Данные берутся из Secrets
API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

async def main():
    # 1. Тянем сессию из Firebase
    response = requests.get(f"{FB_URL}session.json")
    session_str = response.json()
    
    if not session_str:
        print("❌ Ошибка: Сессия не найдена в Firebase!")
        return

    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)

    async with client:
        print("✅ Festka запущена!")
        await client.send_message('me', "🚀 **Festka Online**\n\nБот готов. Команды:\n`+ ник` — следить\n`- ник` — удалить")

        # ОБРАБОТЧИК КОМАНД (в Избранном)
        @client.on(events.NewMessage(chats='me'))
        async def handler(event):
            text = event.raw_text.strip().lower()
            targets = requests.get(f"{FB_URL}targets.json").json() or {}
            if not isinstance(targets, dict): targets = {}
            
            if text.startswith('+'):
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

        # МОНИТОРИНГ ОНЛАЙНА
        while True:
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
