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

# ---- КОНФИГУРАЦИЯ ----
# Вставленные данные по твоему запросу
TG_API_ID = 34126767
TG_API_HASH = "44f1cdcc4c6544d60fe06be1b319d2dd"
FB_URL = "https://monitoring-5f98a-default-rtdb.firebaseio.com/"

SOCIAL_NETS = {
    "Instagram": "https://www.instagram.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "GitHub": "https://github.com/{}",
    "Telegram": "https://t.me/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "Steam": "https://steamcommunity.com/id/{}"
}

# ---- ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ ----
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GhostBot:
    def __init__(self):
        self.client = None
        self.start_time = time.time()
        self.version = "3.7.0-Premium"
        self.is_running = True
        self.session_str = os.getenv('STRING_SESSION', '')
        self._init_fb()

    def _init_fb(self):
        """Категория: База данных"""
        if not firebase_admin._apps:
            # Инициализация для работы с RTDB
            cred = credentials.Anonymous() 
            firebase_admin.initialize_app(cred, {'databaseURL': FB_URL})
        self.db = db.reference("/")

    # ---- ДИЗАЙН И ВИЗУАЛ ----
    def _get_header(self, title):
        """Генерация стильных заголовков"""
        line = "----------------------------"
        return f"🔳 **{title}**\n{line}\n"

    def _format_target_list(self, targets):
        """Категория: Визуал списка целей"""
        if not targets:
            return "❌ Список целей пуст."
        res = self._get_header("СПИСОК МОНИТОРИНГА")
        for k, v in targets.items():
            status = "🟢 ON" if v else "🔴 OFF"
            res += f"👤 `@{k}` | {status}\n"
        return res

    # ---- ЛОГИКА СЕССИИ ----
    async def get_target_entity(self, username):
        try: 
            return await self.client.get_entity(username)
        except Exception as e: 
            logger.error(f"Entity error: {e}")
            return None

    async def initialize(self):
        print(f"📡 Запуск Festka Ghost Engine v{self.version}...")
        try:
            # Пытаемся взять сессию из переменной окружения или из базы
            if not self.session_str:
                session_data = self.db.child("session").get()
                if not session_data:
                    print("❌ Сессия не найдена!")
                    return False
                self.session_str = session_data
            
            self.client = TelegramClient(StringSession(self.session_str), TG_API_ID, TG_API_HASH)
            return True
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False

    async def run(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print("❌ Клиент не авторизован!")
            return
            
        print(f"💎 Festka Ghost запущен!")
        # Ставим статус 'невидимый'
        await self.client(functions.account.UpdateStatusRequest(offline=True))

        self.setup_handlers()
        asyncio.create_task(self.monitoring_loop())
        await self.client.run_until_disconnected()

    # ---- ОБРАБОТЧИКИ КОМАНД ----
    def setup_handlers(self):
        @self.client.on(events.NewMessage(outgoing=True))
        async def handler(event):
            text = event.raw_text.strip().lower()
            
            # Команда помощи
            if text == '/help' or text == '.help':
                help_text = self._get_header("FESTKA HELPER")
                help_text += (
                    "`+ @nick` - Добавить цель\n"
                    "`- @nick` - Удалить цель\n"
                    "`/status` - Список целей\n"
                    "`/osint @nick` - Поиск по соцсетям\n"
                    "`/debug` - Инфо о системе\n"
                    "`/reboot` - Перезапуск (GitHub)"
                )
                await event.edit(help_text)

            # Добавление цели
            elif text.startswith('+'):
                target = text.replace('+', '').strip().replace('@', '')
                entity = await self.get_target_entity(target)
                if entity:
                    self.db.child(f"targets/{target}").set(False)
                    await event.edit(f"✅ **Успешно:** `@{target}` добавлен в мониторинг.")
                else:
                    await event.edit(f"⚠️ **Ошибка:** Пользователь `@{target}` не найден.")

            # Удаление цели
            elif text.startswith('-'):
                target = text.replace('-', '').strip().replace('@', '')
                self.db.child(f"targets/{target}").delete()
                await event.edit(f"🗑 **Удалено:** `@{target}` больше не отслеживается.")

            # Статус мониторинга
            elif text == '/status':
                targets = self.db.child("targets").get() or {}
                await event.edit(self._format_target_list(targets))

            # OSINT поиск
            elif text.startswith('/osint'):
                target = text.replace('/osint', '').strip().replace('@', '')
                if not target:
                    await event.edit("❌ Укажите ник: `/osint nick`")
                    return
                
                osint_res = self._get_header(f"OSINT: {target}")
                for net, url in SOCIAL_NETS.items():
                    osint_res += f"🔹 {net}: {url.format(target)}\n"
                await event.edit(osint_res)

            # Отладка
            elif text == '/debug':
                uptime = int((time.time() - self.start_time) // 60)
                sys_info = (
                    f"🤖 **Festka Engine**\n"
                    f"🔹 Версия: `{self.version}`\n"
                    f"🔹 Uptime: `{uptime} min`\n"
                    f"🔹 Platform: `{platform.system()}`\n"
                    f"🔹 API ID: `{TG_API_ID}`"
                )
                await event.edit(sys_info)

    # ---- КАТЕГОРИЯ: МОНИТОРИНГ ----
    async def monitoring_loop(self):
        print("🔍 Цикл мониторинга запущен...")
        while self.is_running:
            try:
                targets = self.db.child("targets").get() or {}
                alt_id = self.db.child("alt_account").get()
                notify_to = alt_id if alt_id else 'me'
                
                for user, last_status in targets.items():
                    try:
                        # Получаем актуальные данные пользователя
                        u_data = await self.client(functions.users.GetUsersRequest(id=[user]))
                        if not u_data: continue
                        
                        current_status = isinstance(u_data[0].status, types.UserStatusOnline)
                        
                        # Если статус изменился
                        if current_status != last_status:
                            emoji = "🟢" if current_status else "🔴"
                            state = "ONLINE" if current_status else "OFFLINE"
                            now = datetime.now().strftime("%H:%M:%S")
                            
                            msg = f"🔔 **Уведомление**\n`@{user}` -> **{state}**\n🕒 Время: `{now}`"
                            await self.client.send_message(notify_to, msg)
                            
                            # Обновляем статус в базе
                            self.db.child(f"targets/{user}").set(current_status)
                            
                    except FloodWaitError as e:
                        logger.warning(f"Flood wait: {e.seconds}s")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        logger.error(f"Error checking {user}: {e}")
                        continue
                
                # Поддержание статуса 'Offline' для юзербота
                await self.client(functions.account.UpdateStatusRequest(offline=True))
                await asyncio.sleep(30) # Частота проверки
                
            except Exception as e:
                logger.error(f"Loop error: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    bot = GhostBot()
    loop = asyncio.get_event_loop()
    if loop.run_until_complete(bot.initialize()):
        loop.run_until_complete(bot.run())
