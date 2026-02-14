import os
import asyncio
import logging
import time
import platform
import firebase_admin
from firebase_admin import credentials, db
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

# --- КОНФИГУРАЦИЯ ---
API_ID = int(os.getenv('TG_API_ID', 0))
API_HASH = os.getenv('TG_API_HASH', '')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

# --- БАЗА ДАННЫХ SHERLOCK ---
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
        self.version = "3.6.2-Fixed-SDK"
        self.is_running = True
        self._init_firebase()

    def _init_firebase(self):
        """Инициализация Firebase без локального файла ключа"""
        if not firebase_admin._apps:
            # Для публичных БД инициализируем без явных креденшалов
            firebase_admin.initialize_app(options={'databaseURL': FB_URL})
        self.db_ref = db.reference("/")

    async def get_target_entity(self, username):
        try:
            return await self.client.get_entity(username)
        except:
            return None

    async def initialize(self):
        print(f"📡 Инициализация Ghost Engine v{self.version}...")
        try:
            # Прямое чтение строки сессии из Firebase
            session_data = self.db_ref.child("session").get()
        except Exception as e:
            print(f"❌ Ошибка доступа к Firebase: {e}")
            return False
        
        if not session_data:
            print("❌ Ошибка: Сессия не найдена в Firebase по пути /session.")
            return False

        self.client = TelegramClient(StringSession(session_data), API_ID, API_HASH)
        return True

    async def run(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print("❌ Ошибка: Сессия невалидна. Перегенерируй StringSession.")
            return

        me = await self.client.get_me()
        print(f"💎 Авторизовано: {me.first_name} (@{me.username})")

        # Ghost Mode: Принудительный Offline
        await self.client(functions.account.UpdateStatusRequest(offline=True))

        boot_msg = (
            f"💠 **Festka Ghost System v{self.version}**\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"✅ **Статус:** Запущено успешно\n"
            f"🕒 **Время:** {datetime.now().strftime('%H:%M:%S')}\n"
            f"🛡 **Ghost Mode:** Active"
        )
        await self.client.send_message('me', boot_msg)

        self.setup_handlers()
        asyncio.create_task(self.monitoring_loop())
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
                    "🔍 `/search nick` — OSINT поиск\n\n"
                    "⚙️ **Система:**\n"
                    "📲 `/alt @nick` — Вывод на второй акк\n"
                    "🔄 `/reset_alt` — Вывод в Saved\n"
                    "🤖 `/debug` — Диагностика бота"
                )
                await event.edit(help_text)

            # --- КОМАНДА SHERLOCK ---
            elif text.startswith('/search'):
                nick = raw_text.split(' ', 1)[1].replace('@', '') if ' ' in raw_text else None
                if not nick: return await event.edit("⚠️ Формат: `/search nick`")
                await event.edit(f"🧬 **OSINT:** `{nick}`\n📡 Сканирование...")
                found = []
                import requests
                for platform, url_template in SOCIAL_NETS.items():
                    try:
                        res = requests.get(url_template.format(nick), timeout=3)
                        if res.status_code == 200: found.append(f"✅ **{platform}**")
                    except: continue
                await event.respond(f"🔎 **Результаты `{nick}`:**\n" + ("\n".join(found) if found else "❌ Пусто"))

            # --- ДОБАВЛЕНИЕ ОБЪЕКТА ---
            elif text.startswith('+'):
                target = text.replace('+', '').strip().replace('@', '')
                entity = await self.get_target_entity(target)
                if entity:
                    self.db_ref.child(f"targets/{target}").set(False)
                    await event.respond(f"✅ **@{target}** добавлен в мониторинг.")
                else:
                    await event.respond(f"❌ @{target} не найден.")

            # --- УДАЛЕНИЕ ОБЪЕКТА ---
            elif text.startswith('-'):
                target = text.replace('-', '').strip().replace('@', '')
                self.db_ref.child(f"targets/{target}").delete()
                await event.respond(f"🗑 **@{target}** удален.")

            # --- СТАТУС ЦЕЛЕЙ ---
            elif text == '/status':
                db_data = self.db_ref.child("targets").get() or {}
                msg = "📋 **Цели:**\n" + "\n".join([f"• @{t}" for t in db_data.keys()])
                await event.respond(msg)

            # --- АЛЬТЕРНАТИВНЫЙ АККАУНТ ---
            elif text.startswith('/alt'):
                alt_username = text.replace('/alt', '').strip().replace('@', '')
                alt_ent = await self.get_target_entity(alt_username)
                if alt_ent:
                    self.db_ref.child("alt_account").set(alt_ent.id)
                    await event.respond(f"📲 Альт привязан: `{alt_ent.id}`")

            # --- СБРОС АЛЬТА ---
            elif text == '/reset_alt':
                self.db_ref.child("alt_account").delete()
                await event.respond("🔄 Сброшено в Saved Messages.")

            # --- ДИАГНОСТИКА ---
            elif text == '/debug':
                uptime = time.time() - self.start_time
                await event.respond(f"🤖 **Ghost Debug**\nUptime: {int(uptime//60)}m\nFirebase: Connected")

    async def monitoring_loop(self):
        while self.is_running:
            try:
                targets = self.db_ref.child("targets").get() or {}
                alt_id = self.db_ref.child("alt_account").get()
                notify_chat = alt_id if alt_id else 'me'

                if targets:
                    for username, last_status in targets.items():
                        try:
                            users = await self.client(functions.users.GetUsersRequest(id=[username]))
                            if not users: continue
                            is_online = isinstance(users[0].status, types.UserStatusOnline)

                            if is_online != last_status:
                                icon = "🟢" if is_online else "🔴"
                                status_text = "в сети" if is_online else "вышел(а)"
                                alert = f"{icon} **@{username}** {status_text} | {datetime.now().strftime('%H:%M')}"
                                await self.client.send_message(notify_chat, alert)
                                self.db_ref.child(f"targets/{username}").set(is_online)
                        except FloodWaitError as fe:
                            await asyncio.sleep(fe.seconds)
                        except: continue

                await self.client(functions.account.UpdateStatusRequest(offline=True))
                await asyncio.sleep(45)
            except:
                await asyncio.sleep(60)

if __name__ == "__main__":
    bot = GhostBot()
    loop = asyncio.get_event_loop()
    if loop.run_until_complete(bot.initialize()):
        loop.run_until_complete(bot.run())
