import os
import asyncio
import requests
import logging
import time
import platform
from datetime import datetime
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# --- ГЛОБАЛЬНАЯ НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ИЗ ОКРУЖЕНИЯ ---
API_ID = int(os.getenv('TG_API_ID', 0))
API_HASH = os.getenv('TG_API_HASH', '')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

# --- РАСШИРЕННАЯ БАЗА ДАННЫХ SHERLOCK ---
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
    "Reddit": "https://www.reddit.com/user/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Behance": "https://www.behance.net/{}",
    "Spotify": "https://open.spotify.com/user/{}"
}

class GhostBot:
    def __init__(self):
        self.client = None
        self.start_time = time.time()
        self.version = "3.5.0-Stable"
        self.is_running = True

    def get_fb_data(self, path):
        try:
            r = requests.get(f"{FB_URL}{path}.json", timeout=10)
            return r.json()
        except Exception as e:
            logger.error(f"Firebase Get Error ({path}): {e}")
            return None

    def put_fb_data(self, path, data):
        try:
            requests.put(f"{FB_URL}{path}.json", json=data, timeout=10)
            return True
        except Exception as e:
            logger.error(f"Firebase Put Error ({path}): {e}")
            return False

    async def get_target_entity(self, username):
        try:
            return await self.client.get_entity(username)
        except:
            return None

    async def initialize(self):
        print(f"📡 Инициализация Ghost Engine v{self.version}...")
        session_data = self.get_fb_data("session")
        
        if not session_data:
            print("❌ Ошибка: Сессия не найдена.")
            return False

        self.client = TelegramClient(StringSession(session_data), API_ID, API_HASH)
        return True

    async def run(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print("❌ Ошибка: Клиент не авторизован.")
            return

        me = await self.client.get_me()
        print(f"💎 Авторизовано: {me.first_name} (@{me.username})")

        # Принудительный статус Offline
        await self.client(functions.account.UpdateStatusRequest(offline=True))

        # Системное уведомление о запуске
        boot_msg = (
            f"💠 **Festka Ghost System v{self.version}**\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"✅ **Статус:** Запущено успешно\n"
            f"🕒 **Время:** {datetime.now().strftime('%H:%M:%S')}\n"
            f"🛡 **Ghost Mode:** Active\n"
            f"💬 Используй `/help` для команд."
        )
        await self.client.send_message('me', boot_msg)

        # Регистрация обработчиков
        self.setup_handlers()
        
        # Запуск фонового мониторинга
        asyncio.create_task(self.monitoring_loop())

        print("🚀 Все модули активированы. Бот готов к работе.")
        await self.client.run_until_disconnected()

    def setup_handlers(self):
        @self.client.on(events.NewMessage(outgoing=True))
        async def main_handler(event):
            raw_text = event.raw_text.strip()
            text = raw_text.lower()

            # --- КОМАНДА ПОМОЩИ ---
            if text == '/help':
                help_text = (
                    "🔳 **Festka Ghost Control Panel**\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
                    "📡 **Мониторинг:**\n"
                    "➕ `+ @nick` — Добавить объект\n"
                    "➖ `- @nick` — Удалить объект\n"
                    "📊 `/status` — Список целей\n\n"
                    "🕵️ **Инструменты Sherlock:**\n"
                    "🔍 `/search nick` — Глубокий OSINT поиск\n\n"
                    "⚙️ **Система:**\n"
                    "📲 `/alt @nick` — Вывод на второй акк\n"
                    "🔄 `/reset_alt` — Вывод в Saved\n"
                    "🤖 `/debug` — Диагностика бота\n"
                    "🧹 `/clear_base` — Очистить цели"
                )
                await event.edit(help_text)

            # --- КОМАНДА SHERLOCK ---
            elif text.startswith('/search'):
                nick = raw_text.split(' ', 1)[1].replace('@', '') if ' ' in raw_text else None
                if not nick:
                    return await event.edit("⚠️ Формат: `/search nick`")

                await event.edit(f"🧬 **OSINT Инициализирован:** `{nick}`\n📡 Сканирование узлов...")
                found = []
                
                for platform, url_template in SOCIAL_NETS.items():
                    try:
                        full_url = url_template.format(nick)
                        res = requests.get(full_url, timeout=4, headers={'User-Agent': 'Mozilla/5.0'})
                        if res.status_code == 200:
                            found.append(f"✅ **{platform}**: {full_url}")
                    except:
                        continue
                
                response = f"🔎 **Результаты поиска для `{nick}`:**\n\n"
                response += "\n".join(found) if found else "❌ Совпадений не обнаружено."
                await event.respond(response)

            # --- ДОБАВЛЕНИЕ ОБЪЕКТА ---
            elif text.startswith('+'):
                target = text.replace('+', '').strip().replace('@', '')
                entity = await self.get_target_entity(target)
                if entity:
                    db = self.get_fb_data("targets") or {}
                    db[target] = False
                    self.put_fb_data("targets", db)
                    await event.respond(f"✅ **Объект @{target} добавлен.**\nID: `{entity.id}`\nСтатус: Мониторинг активен.")
                else:
                    await event.respond(f"❌ Объект @{target} не найден.")

            # --- УДАЛЕНИЕ ОБЪЕКТА ---
            elif text.startswith('-'):
                target = text.replace('-', '').strip().replace('@', '')
                db = self.get_fb_data("targets") or {}
                if target in db:
                    del db[target]
                    self.put_fb_data("targets", db)
                    await event.respond(f"🗑 **Объект @{target} удален.**")
                else:
                    await event.respond(f"⚠️ Объект @{target} не найден в базе.")

            # --- СТАТУС ЦЕЛЕЙ ---
            elif text == '/status':
                db = self.get_fb_data("targets") or {}
                if not db:
                    return await event.respond("📭 Список целей пуст.")
                
                msg = "📋 **Активные цели в мониторинге:**\n\n"
                for idx, t in enumerate(db.keys(), 1):
                    msg += f"{idx}. @{t}\n"
                msg += f"\n💎 **Ghost Mode:** Active"
                await event.respond(msg)

            # --- НАСТРОЙКА АЛЬТЕРНАТИВНОГО АККАУНТА ---
            elif text.startswith('/alt'):
                alt_username = text.replace('/alt', '').strip().replace('@', '')
                alt_ent = await self.get_target_entity(alt_username)
                if alt_ent:
                    self.put_fb_data("alt_account", alt_ent.id)
                    await event.respond(f"📲 **Альт-аккаунт привязан!**\nID: `{alt_ent.id}`\nВсе уведомления теперь будут приходить туда.")
                else:
                    await event.respond("❌ Не удалось найти указанный аккаунт.")

            # --- СБРОС АЛЬТ-АККАУНТА ---
            elif text == '/reset_alt':
                self.put_fb_data("alt_account", None)
                await event.respond("🔄 **Конфигурация сброшена.**\nОтчеты возвращены в Saved Messages.")

            # --- ДИАГНОСТИКА ---
            elif text == '/debug':
                uptime = time.time() - self.start_time
                diag_msg = (
                    f"🤖 **Ghost Debugger**\n"
                    f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                    f"🛰 **Uptime:** {int(uptime // 3600)}h {int((uptime % 3600) // 60)}m\n"
                    f"💻 **OS:** {platform.system()} {platform.release()}\n"
                    f"🐍 **Python:** {platform.python_version()}\n"
                    f"🔥 **Firebase:** Connected\n"
                    f"📡 **API Latency:** {int((time.time() - event.date.timestamp()) * 1000)}ms"
                )
                await event.respond(diag_msg)

    async def monitoring_loop(self):
        """Параллельный процесс цикличной проверки статусов"""
        logger.info("Модуль мониторинга запущен.")
        
        while self.is_running:
            try:
                targets = self.get_fb_data("targets") or {}
                alt_id = self.get_fb_data("alt_account")
                notify_chat = alt_id if alt_id else 'me'

                if isinstance(targets, dict) and targets:
                    for username, last_status in targets.items():
                        try:
                            # Получаем данные пользователя
                            users = await self.client(functions.users.GetUsersRequest(id=[username]))
                            if not users: continue
                            
                            user = users[0]
                            is_online = isinstance(user.status, types.UserStatusOnline)

                            # Если статус изменился
                            if is_online != last_status:
                                icon = "🟢" if is_online else "🔴"
                                status_text = "в сети" if is_online else "вышел(а) из сети"
                                time_now = datetime.now().strftime('%H:%M')
                                
                                alert = f"{icon} **Объект @{username}**\n📍 Сменил статус: **{status_text}**\n🕒 Время: `{time_now}`"
                                
                                try:
                                    await self.client.send_message(notify_chat, alert)
                                except Exception as e:
                                    logger.error(f"Failed to send alert to {notify_chat}: {e}")

                                # Обновляем локально и в базе
                                targets[username] = is_online
                                self.put_fb_data("targets", targets)
                        
                        except FloodWaitError as fe:
                            logger.warning(f"Flood wait: {fe.seconds}s")
                            await asyncio.sleep(fe.seconds)
                        except Exception as inner_e:
                            logger.error(f"Error checking {username}: {inner_e}")
                            continue

                # Поддержание Ghost Mode
                await self.client(functions.account.UpdateStatusRequest(offline=True))
                
                # Интервал проверки (безопасный для API)
                await asyncio.sleep(45)

            except Exception as outer_e:
                logger.error(f"Monitoring Loop Major Error: {outer_e}")
                await asyncio.sleep(60)

# --- ТОЧКА ВХОДА ---
if __name__ == "__main__":
    bot = GhostBot()
    
    loop = asyncio.get_event_loop()
    if loop.run_until_complete(bot.initialize()):
        try:
            loop.run_until_complete(bot.run())
        except KeyboardInterrupt:
            print("\n🛑 Бот остановлен вручную.")
        except Exception as fatal:
            print(f"💀 КРИТИЧЕСКИЙ СБОЙ: {fatal}")
                        
