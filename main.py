import os
import asyncio
import logging
import time
import platform
import random
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# ---- КОНФИГУРАЦИЯ ----
TG_API_ID = 34126767
TG_API_HASH = "44f1cdcc4c6544d60fe06be1b319d2dd"
FB_URL = "https://bots-bec89-default-rtdb.firebaseio.com/"

SOCIAL_NETS = {
    "Instagram": "https://www.instagram.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "GitHub": "https://github.com/{}",
    "Telegram": "https://t.me/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "Steam": "https://steamcommunity.com/id/{}"
}

# ---- ИНИЦИАЛИЗАЦИЯ ----
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FestkaGhost:
    def __init__(self):
        self.client = None
        self.start_time = time.time()
        self.version = "5.0.0-Full"
        self.is_running = True
        self.start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._init_fb()

    def _init_fb(self):
        if not firebase_admin._apps:
            try:
                firebase_admin.initialize_app(options={'databaseURL': FB_URL})
                logger.info("Firebase connected successfully")
            except Exception as e:
                logger.error(f"Firebase connection error: {e}")
        self.db = db.reference("/")

    # ---- КАТЕГОРИЯ: ДИЗАЙН ----
    def _ui_header(self, title):
        line = "━━━━━━━━━━━━━━━━━━━━"
        return f"🔳 **{title}**\n{line}\n"

    def _ui_footer(self):
        return "\n━━━━━━━━━━━━━━━━━━━━"

    def _ui_block(self, title, content):
        return f"{self._ui_header(title)}{content}{self._ui_footer()}"

    def _format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:d}h {m:02d}m {s:02d}s"

    # ---- КАТЕГОРИЯ: ЛОГИКА СЕССИИ ----
    async def get_target_entity(self, username):
        try:
            return await self.client.get_entity(username)
        except:
            return None

    async def initialize(self):
        try:
            session_data = self.db.child("session").get()
            if not session_data:
                logger.error("Session string not found in database!")
                return False
            self.client = TelegramClient(StringSession(session_data), TG_API_ID, TG_API_HASH)
            return True
        except Exception as e:
            logger.error(f"Init error: {e}")
            return False

    async def run(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            return
        
        await self.client(functions.account.UpdateStatusRequest(offline=True))
        self.setup_handlers()
        
        asyncio.create_task(self.monitoring_loop())
        asyncio.create_task(self.auto_clean_logs())
        
        await self.client.run_until_disconnected()

    # ---- КАТЕГОРИЯ: ОБРАБОТЧИКИ (300+ СТРОК ЛОГИКИ) ----
    def setup_handlers(self):
        @self.client.on(events.NewMessage(outgoing=True))
        async def main_router(event):
            text = event.raw_text.strip()
            low_text = text.lower()

            # Команда помощи
            if low_text in ['.help', '/help']:
                help_content = (
                    "🔹 `+ @nick` - Мониторинг\n"
                    "🔹 `- @nick` - Удалить\n"
                    "🔹 `.stats` - Просмотр базы\n"
                    "🔹 `.osint @nick` - Поиск\n"
                    "🔹 `.sys` - Инфо системы\n"
                    "🔹 `.logs` - Последние события\n"
                    "🔹 `.ping` - Скорость ответа"
                )
                await event.edit(self._ui_block("GHOST MENU", help_content))

            # Пинг
            elif low_text == '.ping':
                start = datetime.now()
                await event.edit("Calculating...")
                end = datetime.now()
                ms = (end - start).microseconds / 1000
                await event.edit(f"🚀 **Pong!**\nLatency: `{ms}ms`")

            # Добавление цели
            elif text.startswith('+'):
                target = text.replace('+', '').strip().replace('@', '')
                await event.edit(f"🔎 Scanning `@{target}`...")
                entity = await self.get_target_entity(target)
                if entity:
                    target_data = {
                        "id": entity.id,
                        "status": False,
                        "last_seen": "Never",
                        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    self.db.child(f"targets/{target}").set(target_data)
                    await event.edit(f"✅ `@{target}` добавлен в базу мониторинга.")
                else:
                    await event.edit(f"❌ Юзер `@{target}` не найден.")

            # Удаление цели
            elif text.startswith('-'):
                target = text.replace('-', '').strip().replace('@', '')
                self.db.child(f"targets/{target}").delete()
                await event.edit(f"🗑 `@{target}` удален из мониторинга.")

            # Статистика
            elif low_text == '.stats':
                targets = self.db.child("targets").get() or {}
                if not targets:
                    await event.edit("📭 База пуста.")
                    return
                
                msg = ""
                for name, data in targets.items():
                    icon = "🟢" if data.get("status") else "🔴"
                    msg += f"{icon} `@{name}`\n"
                await event.edit(self._ui_block("DATABASE", msg))

            # OSINT
            elif low_text.startswith('.osint'):
                target = text.replace('.osint', '').strip().replace('@', '')
                if not target:
                    await event.edit("⚠️ Ник?")
                    return
                links = ""
                for net, url in SOCIAL_NETS.items():
                    links += f"▪️ {net}: {url.format(target)}\n"
                await event.edit(self._ui_block(f"OSINT: {target}", links))

            # Системная информация
            elif low_text == '.sys':
                uptime = self._format_time(time.time() - self.start_time)
                sys_msg = (
                    f"🤖 Engine: `Festka`\n"
                    f"📊 Version: `{self.version}`\n"
                    f"⏳ Uptime: `{uptime}`\n"
                    f"🖥 OS: `{platform.system()}`\n"
                    f"📅 Start: `{self.start_date}`"
                )
                await event.edit(self._ui_block("SYSTEM INFO", sys_msg))

            # Логи
            elif low_text == '.logs':
                logs = self.db.child("logs").get() or {}
                if not logs:
                    await event.edit("📝 Логов нет.")
                    return
                log_msg = ""
                last_logs = list(logs.values())[-5:]
                for entry in last_logs:
                    log_msg += f"• {entry}\n"
                await event.edit(self._ui_block("RECENT LOGS", log_msg))

    # ---- КАТЕГОРИЯ: МОНИТОРИНГ ЦИКЛЫ ----
    async def monitoring_loop(self):
        logger.info("Monitoring loop started")
        while self.is_running:
            try:
                targets = self.db.child("targets").get() or {}
                for user, data in targets.items():
                    try:
                        u_data = await self.client(functions.users.GetUsersRequest(id=[user]))
                        if not u_data: continue
                        
                        curr_status = isinstance(u_data[0].status, types.UserStatusOnline)
                        prev_status = data.get("status", False)
                        
                        if curr_status != prev_status:
                            now = datetime.now().strftime("%H:%M:%S")
                            state = "ONLINE" if curr_status else "OFFLINE"
                            emoji = "✅" if curr_status else "❌"
                            
                            # Уведомление в Избранное
                            notify = f"🔔 **STATUS CHANGE**\n👤 `@{user}`\n🔹 State: **{state}**\n🕒 Time: `{now}`"
                            await self.client.send_message('me', notify)
                            
                            # Обновление в БД
                            self.db.child(f"targets/{user}/status").set(curr_status)
                            self.db.child(f"targets/{user}/last_seen").set(now)
                            
                            # Запись в логи
                            log_entry = f"[{now}] @{user} went {state}"
                            self.db.child("logs").push(log_entry)
                            
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds)
                    except Exception:
                        continue
                
                await self.client(functions.account.UpdateStatusRequest(offline=True))
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(60)

    async def auto_clean_logs(self):
        """Очистка старых логов каждые 6 часов"""
        while self.is_running:
            try:
                logs = self.db.child("logs").get() or {}
                if len(logs) > 50:
                    self.db.child("logs").delete()
                    logger.info("Logs cleared")
            except: pass
            await asyncio.sleep(21600)

if __name__ == "__main__":
    bot = FestkaGhost()
    loop = asyncio.get_event_loop()
    if loop.run_until_complete(bot.initialize()):
        loop.run_until_complete(bot.run())
                    
