import os, asyncio, requests
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

# Конфигурация
API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

# База для Шерлока
SOCIAL_NETS = {
    "Instagram": "https://www.instagram.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Twitter": "https://twitter.com/{}",
    "GitHub": "https://github.com/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Telegram": "https://t.me/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "Steam": "https://steamcommunity.com/id/{}"
}

async def main():
    try:
        res = requests.get(f"{FB_URL}session.json")
        session_data = res.json()
        if not session_data:
            print("❌ Ошибка: Сессия в Firebase пуста!")
            return
            
        client = TelegramClient(StringSession(session_data), API_ID, API_HASH)
        
        async with client:
            print("🕵️ Бот запущен в режиме призрака")
            # Ставим оффлайн сразу
            await client(functions.account.UpdateStatusRequest(offline=True))
            
            # Уведомление в альт-аккаунт о перезагрузке
            alt_id = requests.get(f"{FB_URL}alt_account.json").json()
            target_chat = alt_id if alt_id else 'me'
            await client.send_message(target_chat, "🔄 **Бот перезапущен и готов к работе!**")

            @client.on(events.NewMessage(chats='me'))
            async def handler(event):
                text = event.raw_text.strip().lower()
                
                # КОМАНДА ПОИСКА (ШЕРЛОК)
                if text.startswith('/search'):
                    nick = text.replace('/search', '').strip().replace('@', '')
                    if not nick: return await event.respond("Пиши: `/search ник`")
                    
                    await event.respond(f"🔍 Ищу следы `{nick}`...")
                    found = []
                    for name, url in SOCIAL_NETS.items():
                        try:
                            r = requests.get(url.format(nick), timeout=3)
                            if r.status_code == 200:
                                found.append(f"✅ {name}: {url.format(nick)}")
                        except: continue
                    
                    response = f"🔎 **Результаты для {nick}:**\n\n" + ("\n".join(found) if found else "Ничего не найдено")
                    await event.respond(response)

                # УПРАВЛЕНИЕ ЦЕЛЯМИ
                elif text.startswith('+'):
                    user = text.replace('+', '').strip().replace('@', '')
                    data = requests.get(f"{FB_URL}targets.json").json() or {}
                    data[user] = False
                    requests.put(f"{FB_URL}targets.json", json=data)
                    await event.respond(f"✅ Добавлен в мониторинг: @{user}")

            # ЦИКЛ МОНИТОРИНГА
            while True:
                try:
                    targets = requests.get(f"{FB_URL}targets.json").json() or {}
                    alt_id = requests.get(f"{FB_URL}alt_account.json").json()
                    notify_chat = alt_id if alt_id else 'me'

                    if isinstance(targets, dict):
                        for user, last_status in targets.items():
                            u_data = await client(functions.users.GetUsersRequest(id=[user]))
                            if not u_data: continue
                            
                            is_online = isinstance(u_data[0].status, types.UserStatusOnline)
                            if is_online != last_status:
                                icon = "🟢" if is_online else "🔴"
                                await client.send_message(notify_chat, f"{icon} @{user} {'в сети' if is_online else 'вышел'}")
                                targets[user] = is_online
                                requests.put(f"{FB_URL}targets.json", json=targets)
                    
                    # Поддерживаем Ghost Mode
                    await client(functions.account.UpdateStatusRequest(offline=True))
                    await asyncio.sleep(40) # Пауза чтобы не забанили
                except Exception as e:
                    print(f"Ошибка в цикле: {e}")
                    await asyncio.sleep(60)

    except Exception as e:
        print(f"Критическая ошибка: {e}")

asyncio.run(main())
