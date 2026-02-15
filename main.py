import os
import asyncio
import logging
import time
import platform
import random
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, SessionPasswordNeededError

# ---- КОНФИГУРАЦИЯ СИСТЕМЫ ----
API_ID = 34126767
API_HASH = "44f1cdcc4c6544d60fe06be1b319d2dd"
DATABASE_URL = "https://bots-bec89-default-rtdb.firebaseio.com/"

# Словари для OSINT и расширенных функций
NETWORKS = {
    "Instagram": "https://instagram.com/{}",
    "TikTok": "https://tiktok.com/@{}",
    "GitHub": "https://github.com/{}",
    "Telegram": "https://t.me/{}",
    "Twitter": "https://twitter.com/{}",
    "Reddit": "https://reddit.com/user/{}",
    "YouTube": "https://youtube.com/@{}",
    "Pinterest": "https://pinterest.com/{}"
}

# ---- ИНИЦИАЛИЗАЦИЯ ----
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FestkaPremium")

class FestkaPremium:
    def __init__(self):
        self.client = None
        self.uptime_start = time.time()
        self.version = "7.2.0-Ultimate"
        self.is_active = True
        self.total_checks = 0
        self.notifications_sent = 0
        self._init_firebase()

    def _init_firebase(self):
        """Категория: База данных"""
        if not firebase_admin._apps:
            try:
                firebase_admin.initialize_app(options={'databaseURL': DATABASE_URL})
                logger.info("Firebase Integration: SUCCESS")
            except Exception as e:
                logger.error(f"Firebase Integration: FAILED - {e}")
        self.db_root = db.reference("/")

    # ---- ДИЗАЙН (UI/UX) ----
    def _generate_border(self, char="━", length=30):
        return char * length

    def _create_window(self, title, body):
        border = self._generate_border()
        header = f"💎 **FESTKA PREMIUM | {title}**"
        return f"{header}\n{border}\n{body}\n{border}\n`v{self.version}`"

    def _get_status_icon(self, state):
        return "🟢 `ONLINE`" if state else "🔴 `OFFLINE`"

    # ---- СЛУЖЕБНЫЕ МЕТОДЫ ----
    def _calculate_uptime(self):
        diff = int(time.time() - self.uptime_start)
        return str(timedelta(seconds=diff))

    async def _safe_edit(self, event, text, parse_mode='md'):
        try:
            return await event.edit(text, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Edit Error: {e}")

    # ---- ЯДРО СИСТЕМЫ ----
    async def boot(self):
        logger.info("Booting Festka Premium Engine...")
        session_str = self.db_root.child("session").get()
        
        if not session_str:
            logger.critical("NO SESSION FOUND IN FIREBASE")
            return False

        try:
            self.client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("Session is invalid or expired")
                return False
                
            # Скрытый режим
            await self.client(functions.account.UpdateStatusRequest(offline=True))
            return True
        except Exception as e:
            logger.error(f"Boot Error: {e}")
            return False

    # ---- ОБРАБОТЧИКИ КОМАНД (МЕНЕДЖЕР) ----
    def register_handlers(self):
        @self.client.on(events.NewMessage(outgoing=True))
        async def global_router(event):
            raw = event.raw_text.strip()
            args = raw.split()
            if not args: return
            cmd = args[0].lower()

            # МЕНЮ ПОМОЩИ
            if cmd in ['.help', '/start', '.menu']:
                menu = (
                    "🛰 **Мониторинг:**\n"
                    "└ `+ @nick` - Добавить в трекер\n"
                    "└ `- @nick` - Удалить из трекера\n"
                    "└ `.list` - Текущие цели\n\n"
                    "🔍 **Инструменты:**\n"
                    "└ `.osint @nick` - Соц. сети\n"
                    "└ `.id @nick` - Получить ID\n\n"
                    "⚙️ **Система:**\n"
                    "└ `.sys` - Состояние сервера\n"
                    "└ `.ping` - Задержка\n"
                    "└ `.clean` - Сброс логов"
                )
                await self._safe_edit(event, self._create_window("ГЛАВНОЕ МЕНЮ", menu))

            # СИСТЕМНЫЙ СТАТУС
            elif cmd == '.sys':
                mem_data = self.db_root.child("targets").get() or {}
                targets_count = len(mem_data)
                sys_body = (
                    f"📡 **Узел:** `GitHub Actions`\n"
                    f"⏳ **Аптайм:** `{self._calculate_uptime()}`\n"
                    f"🎯 **Цели:** `{targets_count}`\n"
                    f"🔔 **Уведомления:** `{self.notifications_sent}`\n"
                    f"🐍 **Python:** `{platform.python_version()}`\n"
                    f"📍 **Firebase:** `Connected`"
                )
                await self._safe_edit(event, self._create_window("SYSTEM STATUS", sys_body))

            # ДОБАВЛЕНИЕ ОБЪЕКТА
            elif cmd.startswith('+'):
                target = cmd.replace('+', '').strip().replace('@', '')
                if not target: return
                
                await self._safe_edit(event, f"🔄 Поиск `@{target}` в базе Telegram...")
                entity = await self.client.get_entity(target) if target.isalpha() else None
                
                if entity:
                    user_payload = {
                        "username": target,
                        "uid": entity.id,
                        "status": False,
                        "added_at": datetime.now().strftime("%d.%m %H:%M"),
                        "checks": 0
                    }
                    self.db_root.child(f"targets/{target}").set(user_payload)
                    await self._safe_edit(event, f"✅ **Объект `@{target}` взят на сопровождение.**")
                else:
                    await self._safe_edit(event, f"❌ **Объект `@{target}` не найден.**")

            # УДАЛЕНИЕ ОБЪЕКТА
            elif cmd.startswith('-'):
                target = cmd.replace('-', '').strip().replace('@', '')
                self.db_root.child(f"targets/{target}").delete()
                await self._safe_edit(event, f"🗑 **Объект `@{target}` удален из системы.**")

            # ТЕКУЩИЕ ЦЕЛИ
            elif cmd == '.list':
                data = self.db_root.child("targets").get() or {}
                if not data:
                    await self._safe_edit(event, "📭 Система мониторинга пуста.")
                    return
                
                list_str = ""
                for name, info in data.items():
                    icon = "🟢" if info.get("status") else "🔴"
                    list_str += f"{icon} `@{name}` (ID: `{info.get('uid')}`)\n"
                
                await self._safe_edit(event, self._create_window("ACTIVE TARGETS", list_str))

            # OSINT ПОИСК
            elif cmd == '.osint':
                if len(args) < 2:
                    await self._safe_edit(event, "⚠️ Введите ник: `.osint nick`")
                    return
                
                nick = args[1].replace('@', '')
                osint_body = ""
                for site, url in NETWORKS.items():
                    osint_body += f"🔹 **{site}:** {url.format(nick)}\n"
                
                await self._safe_edit(event, self._create_window(f"OSINT: {nick}", osint_body))

            # ПИНГ
            elif cmd == '.ping':
                s = datetime.now()
                await event.edit("`Pinging...`")
                ms = (datetime.now() - s).microseconds / 1000
                await self._safe_edit(event, f"🚀 **Festka Response:** `{ms}ms`")

    # ---- МОНИТОРИНГ ЦИКЛ (ADVANCED) ----
    async def watcher_loop(self):
        logger.info("Watcher thread: STARTED")
        while self.is_active:
            try:
                targets = self.db_root.child("targets").get() or {}
                for username, data in targets.items():
                    try:
                        # Запрос статуса
                        user_id = data.get("uid")
                        result = await self.client(functions.users.GetUsersRequest(id=[user_id]))
                        if not result: continue
                        
                        current_online = isinstance(result[0].status, types.UserStatusOnline)
                        previous_online = data.get("status", False)

                        # Если статус изменился
                        if current_online != previous_online:
                            self.notifications_sent += 1
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            
                            # Обновление в Firebase
                            self.db_root.child(f"targets/{username}/status").set(current_online)
                            
                            # Отправка уведомления
                            msg_type = "ЗАШЕЛ В СЕТЬ 🟢" if current_online else "ВЫШЕЛ ИЗ СЕТИ 🔴"
                            log_msg = f"👤 **@{username}**\n⚡️ Статус: `{msg_type}`\n🕒 Время: `{timestamp}`"
                            
                            await self.client.send_message('me', self._create_window("EVENT LOG", log_msg))
                            
                            # Аналитика: сохраняем историю событий
                            event_entry = {"time": timestamp, "type": msg_type}
                            self.db_root.child(f"history/{username}").push(event_entry)

                    except FloodWaitError as e:
                        logger.warning(f"Flood Wait: {e.seconds}s")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        logger.error(f"Watcher error on {username}: {e}")
                        continue
                
                # Поддержание невидимости
                await self.client(functions.account.UpdateStatusRequest(offline=True))
                self.total_checks += 1
                
                # Рандомная задержка для имитации поведения человека
                await asyncio.sleep(random.randint(25, 40))
                
            except Exception as e:
                logger.error(f"Global Watcher Error: {e}")
                await asyncio.sleep(60)

    # ---- ПУСК ----
    async def start_engine(self):
        if await self.boot():
            self.register_handlers()
            # Запуск циклов
            asyncio.create_task(self.watcher_loop())
            logger.info("Festka Premium is fully operational.")
            await self.client.run_until_disconnected()
        else:
            logger.critical("Engine failure during boot.")

if __name__ == "__main__":
    bot_system = FestkaPremium()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot_system.start_engine())
                
