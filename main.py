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

# --- ЛОГИРОВАНИЕ ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ---
API_ID = int(os.getenv('TG_API_ID', 0))
API_HASH = os.getenv('TG_API_HASH', '')
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

SOCIAL_NETS = {
    "Instagram": "https://www.instagram.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "GitHub": "https://github.com/{}",
    "Telegram": "https://t.me/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "Steam": "https://steamcommunity.com/id/{}"
}

class GhostBot:
    def __init__(self):
        self.client = None
        self.start_time = time.time()
        self.version = "3.6.5-Final"
        self.is_running = True
        self._init_fb()

    def _init_fb(self):
        """Фикс: Инициализация без сертификата для публичной БД"""
        if not firebase_admin._apps:
            # Используем пустые креденшалы, чтобы избежать ошибки билда
            cred = credentials.Anonymous()
            firebase_admin.initialize_app(cred, {'databaseURL': FB_URL})
        self.db = db.reference("/")

    async def get_target_entity(self, username):
        try: return await self.client.get_entity(username)
        except: return None

    async def initialize(self):
        print(f"📡 Запуск Ghost Engine v{self.version}...")
        try:
            session_data = self.db.child("session").get()
            if not session_data:
                print("❌ Сессия не найдена в базе!")
                return False
            self.client = TelegramClient(StringSession(session_data), API_ID, API_HASH)
            return True
        except Exception as e:
            print(f"❌ Ошибка Firebase: {e}")
            return False

    async def run(self):
        await self.client.connect()
        if not await self.client.is_user_authorized(): return
        print(f"💎 Бот запущен!")
        await self.client(functions.account.UpdateStatusRequest(offline=True))
        
        self.setup_handlers()
        asyncio.create_task(self.monitoring_loop())
        await self.client.run_until_disconnected()

    def setup_handlers(self):
        @self.client.on(events.NewMessage(outgoing=True))
        async def handler(event):
            text = event.raw_text.strip().lower()
            if text == '/help':
                await event.edit("🔳 **Festka Ghost**\n`+ @nick` | `- @nick` | `/status` | `/debug`")
            elif text.startswith('+'):
                target = text.replace('+', '').strip().replace('@', '')
                if await self.get_target_entity(target):
                    self.db.child(f"targets/{target}").set(False)
                    await event.respond(f"✅ @{target} добавлен")
            elif text.startswith('-'):
                target = text.replace('-', '').strip().replace('@', '')
                self.db.child(f"targets/{target}").delete()
                await event.respond(f"🗑 @{target} удален")
            elif text == '/status':
                t = self.db.child("targets").get() or {}
                await event.respond("📋 Цели:\n" + "\n".join([f"• @{k}" for k in t.keys()]))
            elif text == '/debug':
                await event.respond(f"🤖 Uptime: {int((time.time()-self.start_time)//60)}m")

    async def monitoring_loop(self):
        while self.is_running:
            try:
                targets = self.db.child("targets").get() or {}
                alt_id = self.db.child("alt_account").get()
                notify = alt_id if alt_id else 'me'
                for user, last_st in targets.items():
                    try:
                        u_data = await self.client(functions.users.GetUsersRequest(id=[user]))
                        is_on = isinstance(u_data[0].status, types.UserStatusOnline)
                        if is_on != last_st:
                            await self.client.send_message(notify, f"{'🟢' if is_on else '🔴'} @{user} {'online' if is_on else 'offline'}")
                            self.db.child(f"targets/{user}").set(is_on)
                    except FloodWaitError as e: await asyncio.sleep(e.seconds)
                    except: continue
                await self.client(functions.account.UpdateStatusRequest(offline=True))
                await asyncio.sleep(45)
            except: await asyncio.sleep(60)

if __name__ == "__main__":
    bot = GhostBot()
    loop = asyncio.get_event_loop()
    if loop.run_until_complete(bot.initialize()):
        loop.run_until_complete(bot.run())
