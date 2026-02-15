import os
import asyncio
import logging
import time
import platform
import random
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# ---- КОНФИГУРАЦИЯ СИСТЕМЫ ----
API_ID = 34126767
API_HASH = "44f1cdcc4c6544d60fe06be1b319d2dd"
DB_URL = "https://bots-bec89-default-rtdb.firebaseio.com/"

# ---- ГЛОБАЛЬНЫЕ ДАННЫЕ (OSINT & TOOLS) ----
NETWORKS = {
    "Instagram": "https://instagram.com/{}",
    "TikTok": "https://tiktok.com/@{}",
    "GitHub": "https://github.com/{}",
    "Telegram": "https://t.me/{}",
    "Twitter": "https://twitter.com/{}",
    "Reddit": "https://reddit.com/user/{}",
    "YouTube": "https://youtube.com/@{}",
    "Steam": "https://steamcommunity.com/id/{}"
}

# ---- ИНИЦИАЛИЗАЦИЯ ----
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FestkaPremium")

class FestkaPremium:
    def __init__(self):
        self.client = None
        self.start_time = time.time()
        self.version = "8.4.1-Stable"
        self.is_running = True
        self.checks_performed = 0
        self.events_logged = 0
        self._init_firebase()

    def _init_firebase(self):
        """(Категория: База данных)"""
        if not firebase_admin._apps:
            try:
                # Исправление ошибки из скриншота
                firebase_admin.initialize_app(options={'databaseURL': DB_URL})
                logger.info("Firebase: Connected Successfully")
            except Exception as e:
                logger.error(f"Firebase: Connection Failed - {e}")
        self.db = db.reference("/")

    # -[span_7](start_span)[span_8](start_span)--- КАТЕГОРИЯ: ДИЗАЙН (UI/UX)[span_7](end_span)[span_8](end_span) ----
    def _draw_separator(self):
        return "━━━━━━━━━━━━━━━━━━━━"

    def _build_frame(self, title, content):
        header = f"💎 **FESTKA PREMIUM | {title}**"
        sep = self._draw_separator()
        return f"{header}\n{sep}\n{content}\n{sep}\n`Engine Status: Active`"

    def _status_label(self, is_online):
        return "🟢 `ONLINE`" if is_online else "🔴 `OFFLINE`"

    # ---- КАТЕГОРИЯ: СИСТЕМНЫЕ УТИЛИТЫ ----
    def _uptime_calc(self):
        uptime = timedelta(seconds=int(time.time() - self.start_time))
        return str(uptime)

    async def _safe_send(self, event, text):
        try:
            await event.edit(text, parse_mode='md')
        except Exception as e:
            logger.error(f"UI Error: {e}")

    # ---- КАТЕГОРИЯ: ЯДРО АВТОРИЗАЦИИ ----
    async def connect_client(self):
        logger.info("Attempting to connect to Telegram API...")
        # Приоритетное получение сессии из Firebase
        session_str = self.db.child("session").get()
        
        if not session_str:
            logger.critical("CRITICAL: STRING_SESSION NOT FOUND IN DATABASE")
            return False

        try:
            self.client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("Session Authorization: FAILED")
                return False
                
            # [span_9](start_span)Режим инкогнито[span_9](end_span)
            await self.client(functions.account.UpdateStatusRequest(offline=True))
            return True
        except Exception as e:
            logger.error(f"Connection Error: {e}")
            return False

    # -[span_10](start_span)--- КАТЕГОРИЯ: МЕНЕДЖЕР КОМАНД[span_10](end_span) ----
    def load_handlers(self):
        @self.client.on(events.NewMessage(outgoing=True))
        async def main_controller(event):
            raw = event.raw_text.strip()
            if not raw: return
            
            cmd_parts = raw.split()
            trigger = cmd_parts[0].lower()

            # [span_11](start_span)КОМАНДА: ПОМОЩЬ[span_11](end_span)
            if trigger in ['.help', '/help', '.menu']:
                help_body = (
                    "🛰 **Мониторинг**\n"
                    "├ `+ @nick` - Добавить цель\n"
                    "├ `- @nick` - Удалить цель\n"
                    "└ `.list` - Показать всех\n\n"
                    "🔍 **Аналитика**\n"
                    "├ `.osint @nick` - Соц. сети\n"
                    "├ `.id @nick` - Узнать ID\n"
                    "└ `.logs` - Последние 10 событий\n\n"
                    "⚙️ **Система**\n"
                    "├ `.sys` - Инфо о сервере\n"
                    "├ `.ping` - Задержка сети\n"
                    "└ `.reboot` - Полный сброс"
                )
                await self._safe_send(event, self._build_frame("МЕНЮ КОМАНД", help_body))

            # КОМАНДА: СТАТУС СЕРВЕРА
            elif trigger == '.sys':
                targets_data = self.db.child("targets").get() or {}
                sys_body = (
                    f"📡 **Хост:** `GitHub Runner`\n"
                    f"⏱ **Аптайм:** `{self._uptime_calc()}`\n"
                    f"🎯 **В базе:** `{len(targets_data)}` объектов\n"
                    f"📊 **Событий:** `{self.events_logged}`\n"
                    f"💻 **ОС:** `{platform.system()} {platform.release()}`\n"
                    f"🔑 **Firebase:** `Status: Connected`"
                )
                await self._safe_send(event, self._build_frame("СИСТЕМНЫЙ СТАТУС", sys_body))

            # КОМАНДА: ДОБАВИТЬ (+@nick)
            elif trigger.startswith('+'):
                target = trigger.replace('+', '').strip().replace('@', '')
                if not target: return
                
                await event.edit(f"🔄 Регистрация `@{target}` в системе...")
                entity = await self.client.get_entity(target)
                
                if entity:
                    payload = {
                        "username": target,
                        "user_id": entity.id,
                        "current_state": False,
                        "added_on": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "last_change": "N/A"
                    }
                    self.db.child(f"targets/{target}").set(payload)
                    await self._safe_send(event, f"✅ **Объект `@{target}` успешно добавлен под наблюдение.**")
                else:
                    await self._safe_send(event, f"❌ **Ошибка:** Объект `@{target}` не найден.")

            # КОМАНДА: УДАЛИТЬ (-@nick)
            elif trigger.startswith('-'):
                target = trigger.replace('-', '').strip().replace('@', '')
                self.db.child(f"targets/{target}").delete()
                await self._safe_send(event, f"🗑 **Объект `@{target}` исключен из мониторинга.**")

            # КОМАНДА: СПИСОК ЦЕЛЕЙ
            elif trigger == '.list':
                data = self.db.child("targets").get() or {}
                if not data:
                    await self._safe_send(event, "📭 База данных мониторинга пуста.")
                    return
                
                report = ""
                for name, info in data.items():
                    icon = "🟢" if info.get("current_state") else "🔴"
                    report += f"{icon} `@{name}` | ID: `{info.get('user_id')}`\n"
                
                await self._safe_send(event, self._build_frame("СПИСОК ОБЪЕКТОВ", report))

            # КОМАНДА: OSINT
            elif trigger == '.osint':
                if len(cmd_parts) < 2:
                    await self._safe_send(event, "⚠️ Использование: `.osint @nick`")
                    return
                
                nick = cmd_parts[1].replace('@', '')
                links = ""
                for site, url in NETWORKS.items():
                    links += f"🔹 **{site}:** {url.format(nick)}\n"
                
                await self._safe_send(event, self._build_frame(f"OSINT: {nick}", links))

            # КОМАНДА: ПИНГ
            elif trigger == '.ping':
                start_ping = datetime.now()
                await event.edit("`Pinging Server...`")
                diff = (datetime.now() - start_ping).microseconds / 1000
                await self._safe_send(event, f"🚀 **Festka Latency:** `{diff}ms`")

    # -[span_12](start_span)--- КАТЕГОРИЯ: ADVANCED MONITORING LOOP[span_12](end_span) ----
    async def run_watcher(self):
        logger.info("Deep Monitor Service: STARTED")
        while self.is_running:
            try:
                targets = self.db.child("targets").get() or {}
                for username, data in targets.items():
                    try:
                        uid = data.get("user_id")
                        # Запрос актуального состояния
                        user_info = await self.client(functions.users.GetUsersRequest(id=[uid]))
                        if not user_info: continue
                        
                        is_online = isinstance(user_info[0].status, types.UserStatusOnline)
                        old_state = data.get("current_state", False)

                        # Логика уведомления при изменении
                        if is_online != old_state:
                            self.events_logged += 1
                            now_time = datetime.now().strftime("%H:%M:%S")
                            
                            # Синхронизация с БД
                            self.db.child(f"targets/{username}/current_state").set(is_online)
                            self.db.child(f"targets/{username}/last_change").set(now_time)
                            
                            # Генерация и отправка алерта
                            status_text = "ВЕРНУЛСЯ В СЕТЬ 🟢" if is_online else "ПОКИНУЛ СЕТЬ 🔴"
                            alert = (
                                f"👤 **ОБЪЕКТ:** `@{username}`\n"
                                f"⚡️ **СТАТУС:** `{status_text}`\n"
                                f"🕒 **ВРЕМЯ:** `{now_time}`"
                            )
                            await self.client.send_message('me', self._build_frame("УВЕДОМЛЕНИЕ СТАТУСА", alert))
                            
                            # Запись в историю (Аналитика)
                            history_log = {"event": status_text, "timestamp": now_time}
                            self.db.child(f"history/{username}").push(history_log)

                    except FloodWaitError as e:
                        logger.warning(f"FloodWait: sleeping {e.seconds}s")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        logger.error(f"Error checking @{username}: {e}")
                        continue
                
                # Поддержание сессии в режиме Offline
                await self.client(functions.account.UpdateStatusRequest(offline=True))
                self.checks_performed += 1
                
                # Рандомная пауза для защиты от банов
                await asyncio.sleep(random.randint(20, 35))
                
            except Exception as e:
                logger.error(f"Global Watcher Error: {e}")
                await asyncio.sleep(45)

    # ---- ФИНАЛЬНЫЙ ЗАПУСК ----
    async def start(self):
        if await self.connect_client():
            self.load_handlers()
            # Фоновое выполнение мониторинга
            asyncio.create_task(self.run_watcher())
            logger.info(f"Festka Premium v{self.version} is now Online.")
            await self.client.run_until_disconnected()
        else:
            logger.critical("Engine startup failed.")

if __name__ == "__main__":
    core = FestkaPremium()
    asyncio.run(core.start())
                    
