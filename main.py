import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import UserStatusOnline

# Конфигурация из секретов GitHub
API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
SESSION_STRING = os.getenv('TG_SESSION_STRING')
TARGET_USERNAME = 'Здесь_Ник_Цели' # Например, 'durov'

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def check_status():
    print("Мониторинг запущен...")
    # Состояние: False - был оффлайн, True - был онлайн
    last_known_online = False 
    
    async with client:
        while True:
            try:
                user = await client.get_entity(TARGET_USERNAME)
                is_online = isinstance(user.status, UserStatusOnline)

                if is_online and not last_known_online:
                    await client.send_message('me', f"🔔 @{TARGET_USERNAME} зашел в сеть!")
                    last_known_online = True
                elif not is_online and last_known_online:
                    await client.send_message('me', f"💤 @{TARGET_USERNAME} вышел из сети.")
                    last_known_online = False
                
            except Exception as e:
                print(f"Ошибка: {e}")
            
            # Интервал проверки (в секундах)
            await asyncio.sleep(60)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_status())
              
