import os, asyncio, requests
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

# Конфиг
API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

# Список сайтов для OSINT-поиска
SOCIAL_NETS = {
    "Instagram": "https://www.instagram.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Twitter (X)": "https://twitter.com/{}",
    "GitHub": "https://github.com/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Steam": "https://steamcommunity.com/id/{}"
}

async def main():
    res = requests.get(f"{FB_URL}session.json")
    client = TelegramClient(StringSession(res.json()), API_ID, API_HASH)

    async with client:
        print("🕵️ Sherlock Mode Active")
        await client(functions.account.UpdateStatusRequest(offline=True))

        @client.on(events.NewMessage(chats='me'))
        async def handler(event):
            text = event.raw_text.strip().lower()
            
            # КОМАНДА ПОИСКА (ШЕРЛОК)
            if text.startswith('/search'):
                target_nick = text.replace('/search', '').strip().replace('@', '')
                if not target_nick:
                    await event.respond("Введите ник: `/search ник`")
                    return
                
                await event.respond(f"🔍 Начинаю поиск @{target_nick} по соцсетям...")
                found = []
                
                for name, url in SOCIAL_NETS.items():
                    try:
                        full_url = url.format(target_nick)
                        # Делаем быстрый запрос
                        r = requests.get(full_url, timeout=2)
                        if r.status_code == 200:
                            found.append(f"🔹 **{name}**: {full_url}")
                    except:
                        continue
                
                if found:
                    result_msg = f"🔎 **Результаты для {target_nick}:**\n\n" + "\n".join(found)
                    await event.respond(result_msg)
                else:
                    await event.respond(f"🤷‍♂️ Для @{target_nick} ничего не найдено.")

            # Остальные команды (+ и -) оставляем как были...
            elif text.startswith('+'):
                user = text.replace('+', '').strip().replace('@', '')
                targets = requests.get(f"{FB_URL}targets.json").json() or {}
                targets[user] = False
                requests.put(f"{FB_URL}targets.json", json=targets)
                await event.respond(f"✅ Добавлен в мониторинг: @{user}")

        # Цикл мониторинга (остается без изменений)
        while True:
            # (Тут твой старый код проверки онлайна и отправки на альт-аккаунт)
            await client(functions.account.UpdateStatusRequest(offline=True))
            await asyncio.sleep(40)

asyncio.run(main())
