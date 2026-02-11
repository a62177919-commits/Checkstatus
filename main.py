import os, asyncio, requests
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest

# --- КОНФИГУРАЦИЯ ИЗ SECRETS И FIREBASE ---
API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

# --- БАЗА ДАННЫХ ДЛЯ SHERLOCK (РАСШИРЕННАЯ) ---
SOCIAL_NETS = {
    "Instagram": "https://www.instagram.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Twitter": "https://twitter.com/{}",
    "GitHub": "https://github.com/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Telegram": "https://t.me/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Youtube": "https://www.youtube.com/@{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "Reddit": "https://www.reddit.com/user/{}"
}

async def main():
    print("🚀 Инициализация Ghost Sherlock Engine...")
    
    try:
        # Получение сессии
        session_res = requests.get(f"{FB_URL}session.json")
        session_str = session_res.json()
        
        if not session_str:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Сессия не найдена в Firebase.")
            return

        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)

        async with client:
            # Настройка режима призрака при входе
            me = await client.get_me()
            print(f"✅ Авторизован как: {me.first_name}")
            await client(functions.account.UpdateStatusRequest(offline=True))
            
            # Уведомление о запуске на альт-аккаунт
            alt_id = requests.get(f"{FB_URL}alt_account.json").json()
            start_msg = "🕵️ **Ghost System Online**\n\nВсе системы мониторинга и Sherlock активированы.\nРежим невидимости: ВКЛ"
            await client.send_message(alt_id if alt_id else 'me', start_msg)

            # --- ОБРАБОТЧИК КОМАНД (ЧИТАЕТ ИЗБРАННОЕ И ВЫХОДЯЩИЕ) ---
            @client.on(events.NewMessage)
            async def cmd_handler(event):
                if not event.out:
                    return
                
                cmd = event.raw_text.strip().lower()

                # 1. КОМАНДА ПОИСКА (SHERLOCK)
                if cmd.startswith('/search'):
                    nick = cmd.replace('/search', '').strip().replace('@', '')
                    if not nick:
                        return await event.edit("⚠️ Укажите ник: `/search ник`")
                    
                    await event.edit(f"🔍 **OSINT Поиск:** `{nick}`\nПроверка баз данных...")
                    found_links = []
                    
                    for platform, url_template in SOCIAL_NETS.items():
                        try:
                            target_url = url_template.format(nick)
                            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                            check = requests.get(target_url, timeout=3, headers=headers)
                            if check.status_code == 200:
                                found_links.append(f"🔹 **{platform}**: {target_url}")
                        except:
                            continue
                    
                    result = f"🔎 **Результаты Sherlock для {nick}:**\n\n"
                    result += "\n".join(found_links) if found_links else "Ничего не найдено в открытых источниках."
                    await event.respond(result)

                # 2. ДОБАВЛЕНИЕ ЦЕЛИ (+)
                elif cmd.startswith('+'):
                    user_to_add = cmd.replace('+', '').strip().replace('@', '')
                    try:
                        entity = await client.get_entity(user_to_add)
                        current_targets = requests.get(f"{FB_URL}targets.json").json() or {}
                        current_targets[user_to_add] = False
                        requests.put(f"{FB_URL}targets.json", json=current_targets)
                        await event.respond(f"✅ **Мониторинг активирован**\nЮзер: @{user_to_add}\nID: `{entity.id}`")
                    except Exception as e:
                        await event.respond(f"❌ Ошибка поиска: {str(e)}")

                # 3. УДАЛЕНИЕ ЦЕЛИ (-)
                elif cmd.startswith('-'):
                    user_to_del = cmd.replace('-', '').strip().replace('@', '')
                    current_targets = requests.get(f"{FB_URL}targets.json").json() or {}
                    if user_to_del in current_targets:
                        del current_targets[user_to_del]
                        requests.put(f"{FB_URL}targets.json", json=current_targets)
                        await event.respond(f"🗑 **@{user_to_del}** удален из списков.")

                # 4. УСТАНОВКА АЛЬТ-АККАУНТА (/ALT)
                elif cmd.startswith('/alt'):
                    new_alt = cmd.replace('/alt', '').strip()
                    try:
                        alt_ent = await client.get_entity(new_alt)
                        requests.put(f"{FB_URL}alt_account.json", json=alt_ent.id)
                        await event.respond(f"📲 Альт-аккаунт привязан к ID: `{alt_ent.id}`")
                    except:
                        await event.respond("❌ Не удалось верифицировать аккаунт.")

                # 5. ПРОВЕРКА СТАТУСА (/STATUS)
                elif cmd == '/status':
                    t_list = requests.get(f"{FB_URL}targets.json").json() or {}
                    targets_str = "\n".join([f"• @{k}" for k in t_list.keys()]) if t_list else "Список пуст"
                    await event.respond(f"⚙️ **Текущий конфиг:**\n\n**Цели:**\n{targets_str}\n\nGhost Mode: Active 👻")

            # --- ЦИКЛ МОНИТОРИНГА (GHOST MONITOR) ---
            while True:
                try:
                                # --- МОНИТОРИНГ В ФОНЕ (Заменяет старый while True) ---
            async def monitoring_loop():
                while True:
                    try:
                        targets = requests.get(f"{FB_URL}targets.json").json() or {}
                        alt_id = requests.get(f"{FB_URL}alt_account.json").json()
                        notify_to = alt_id if alt_id else 'me'

                        if isinstance(targets, dict) and targets:
                            for user, last_seen_status in targets.items():
                                try:
                                    user_req = await client(functions.users.GetUsersRequest(id=[user]))
                                    if not user_req: continue
                                    is_online = isinstance(user_req[0].status, types.UserStatusOnline)
                                    
                                    if is_online != last_seen_status:
                                        icon = "🟢" if is_online else "🔴"
                                        action = "в сети" if is_online else "вышел(а)"
                                        await client.send_message(notify_to, f"{icon} Объект @{user} теперь **{action}**.")
                                        
                                        targets[user] = is_online
                                        requests.put(f"{FB_URL}targets.json", json=targets)
                                except: continue

                        await client(functions.account.UpdateStatusRequest(offline=True))
                        await asyncio.sleep(45)
                    except Exception as e:
                        print(f"Ошибка мониторинга: {e}")
                        await asyncio.sleep(30)

            # Запускаем фоновую задачу
            client.loop.create_task(monitoring_loop())

            # --- ОБРАБОТЧИК КОМАНД (Должен быть ТУТ, а не в except) ---
            @client.on(events.NewMessage(outgoing=True))
            async def extra_commands(event):
                text = event.raw_text.strip().lower()
                if text == '/help':
                    await event.respond("🚀 **Ghost Menu**\n`+ @nick` | `- @nick` | `/status` | `/search` | `/alt` | `/debug` | `/reset_alt`")
                elif text == '/debug':
                    await event.respond(f"🤖 **Status:** Online\n👻 **Ghost:** True\n👤 **User:** {me.first_name}")
                elif text == '/reset_alt':
                    requests.put(f"{FB_URL}alt_account.json", json=None)
                    await event.respond("🔄 Отчеты возвращены в Saved Messages.")

            print("✅ Система полностью запущена!")
            await client.run_until_disconnected()

    except Exception as fatal_e:
        print(f"Критический сбой системы: {fatal_e}")

if __name__ == "__main__":
    asyncio.run(main())
                    
