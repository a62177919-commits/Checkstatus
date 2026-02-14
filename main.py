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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        self.version = "3.6.4-Stable"
        self.is_running = True
        self._init_fb()

    def _init_fb(self):
        if not firebase_admin._apps:
            firebase_admin.initialize_app(options={'databaseURL': FB_URL})
        self.db = db.reference("/")

    async def get_target_entity(self, username):
        try: return await self.client.get_entity(username)
        except: return None

    async def initialize(self):
        print(f"📡 Инициализация Ghost Engine v{self.version}...")
        session_data = self.db.child("session").get()
        if not session_data: return False
        self.client = TelegramClient(StringSession(session_data), API_ID, API_HASH)
        return True

    async def run(self):
        await self.client.connect()
        if not await self.client.is_user_authorized(): return
        me = await self.client.get_me()
        print(f"💎 Авторизовано: {me.first_name}")
        await self.client(functions.account.UpdateStatusRequest(offline=True))
        
        boot_msg = (f"💠 **Festka Ghost System v{self.version}**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                    f"✅ **Статус:** Запущено\n🕒 **Время:** {datetime.now().strftime('%H:%M:%S')}\n"
                    f"🛡 **Ghost Mode:** Active")
        await self.client.send_message('me', boot_msg)
        
        self.setup_handlers()
        asyncio.create_task(self.monitoring_loop())
        await self.client.run_until_disconnected()

    def setup_handlers(self):
        @self.client.on(events.NewMessage(outgoing=True))
        async def main_handler(event):
            raw_text = event.raw_text.strip()
            text = raw_text.lower()

            if text == '/help':
                await event.edit("🔳 **Festka Panel**\n`+ @nick` | `- @nick` | `/status` | `/search` | `/debug`")

            elif text.startswith('/search'):
                nick = raw_text.split(' ', 1)[1].replace('@', '') if ' ' in raw_text else None
                if not nick: return await event.edit("⚠️ `/search nick`")
                await event.edit(f"🧬 **OSINT:** `{nick}`\n📡 Сканирование...")
                import requests
                found = [f"✅ **{p}**" for p, u in SOCIAL_NETS.items() if requests.get(u.format(nick), timeout=3).status_code == 200]
                await event.respond(f"🔎 **Результат `{nick}`:**\n" + ("\n".join(found) if found else "❌ Пусто"))

            elif text.startswith('+'):
                target = text.replace('+', '').strip().replace('@', '')
                if await self.get_target_entity(target):
                    self.db.child(f"targets/{target}").set(False)
                    await event.respond(f"✅ **@{target}** добавлен.")
                else: await event.respond("❌ Не найден.")

            elif text.startswith('-'):
                target = text.replace('-', '').strip().replace('@', '')
                self.db.child(f"targets/{target}").delete()
                await event.respond(f"🗑 **@{target}** удален.")

            elif text == '/status':
                targets = self.db.child("targets").get() or {}
                await event.respond("📋 **Цели:**\n" + "\n".join([f"• @{t}" for t in targets.keys()]))

            elif text.startswith('/alt'):
                alt_user = text.replace('/alt', '').strip().replace('@', '')
                alt_ent = await self.get_target_entity(alt_user)
                if alt_ent:
                    self.db.child("alt_account").set(alt_ent.id)
                    await event.respond(f"📲 Альт привязан: `{alt_ent.id}`")

            elif text == '/debug':
                uptime = time.time() - self.start_time
                await event.respond(f"🤖 **Debug**\nUptime: {int(uptime//60)}m\nFirebase: SDK Connected")

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
                            icon = "🟢" if is_on else "🔴"
                            await self.client.send_message(notify, f"{icon} **@{user}** { 'online' if is_on else 'offline' }")
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
