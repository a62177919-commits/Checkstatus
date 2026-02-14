import os
import asyncio
import logging
import time
import platform
import firebase_admin
from firebase_admin import credentials, db
from google.oauth2 import service_account # Нужно для фикса
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

class GhostBot:
    def __init__(self):
        self.client = None
        self.start_time = time.time()
        self.version = "3.6.3-Final-Fix"
        self.is_running = True
        self._init_firebase()

    def _init_firebase(self):
        """Полный обход DefaultCredentialsError"""
        if not firebase_admin._apps:
            try:
                # Создаем пустой объект учетных данных
                # Это заставляет Firebase думать, что авторизация пройдена
                firebase_admin.initialize_app(options={'databaseURL': FB_URL})
            except Exception as e:
                # Если падает — пробуем альтернативный метод без кред
                firebase_admin.initialize_app(
                    credentials.Certificate({
                        "type": "service_account",
                        "project_id": "monitoring-5f98a",
                        "client_email": "fake@fake.com",
                        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC7\n-----END PRIVATE KEY-----\n",
                    }), 
                    {'databaseURL': FB_URL}
                )
        self.db_ref = db.reference("/")

    async def get_target_entity(self, username):
        try:
            return await self.client.get_entity(username)
        except:
            return None

    async def initialize(self):
        print(f"📡 Инициализация Ghost Engine v{self.version}...")
        try:
            # Читаем сессию
            session_data = self.db_ref.child("session").get()
        except Exception as e:
            print(f"❌ Ошибка доступа к Firebase: {e}")
            return False
        
        if not session_data:
            print("❌ Ошибка: Сессия не найдена в Firebase.")
            return False

        self.client = TelegramClient(StringSession(session_data), API_ID, API_HASH)
        return True

    async def run(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print("❌ Ошибка: Сессия невалидна.")
            return

        me = await self.client.get_me()
        print(f"💎 Авторизовано: {me.first_name} (@{me.username})")

        # Offline статус
        await self.client(functions.account.UpdateStatusRequest(offline=True))

        boot_msg = f"💠 **Ghost System v{self.version}**\n✅ Запущено успешно."
        await self.client.send_message('me', boot_msg)

        self.setup_handlers()
        asyncio.create_task(self.monitoring_loop())
        await self.client.run_until_disconnected()

    def setup_handlers(self):
        @self.client.on(events.NewMessage(outgoing=True))
        async def main_handler(event):
            text = event.raw_text.strip().lower()

            if text == '/help':
                await event.edit("🔳 **Panel**\n`+ @nick` | `- @nick` | `/status` | `/debug`")

            elif text.startswith('+'):
                target = text.replace('+', '').strip().replace('@', '')
                entity = await self.get_target_entity(target)
                if entity:
                    self.db_ref.child(f"targets/{target}").set(False)
                    await event.respond(f"✅ **@{target}** добавлен.")
                else:
                    await event.respond("❌ Не найден.")

            elif text.startswith('-'):
                target = text.replace('-', '').strip().replace('@', '')
                self.db_ref.child(f"targets/{target}").delete()
                await event.respond(f"🗑 **@{target}** удален.")

            elif text == '/status':
                db_data = self.db_ref.child("targets").get() or {}
                msg = "📋 **Цели:**\n" + "\n".join([f"• @{t}" for t in db_data.keys()])
                await event.respond(msg)

            elif text == '/debug':
                uptime = time.time() - self.start_time
                await event.respond(f"🤖 **Ghost Debug**\nUptime: {int(uptime//60)}m")

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
