import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from google import genai

# Загрузка секретов с очисткой пробелов
def get_env(name):
    val = os.getenv(name)
    return val.strip() if val else None

try:
    API_ID = int(get_env("TG_API_ID"))
    API_HASH = get_env("TG_API_HASH")
    SESSION_STR = get_env("STRING_SESSION")
    GEMINI_KEY = get_env("GEMINI_API_KEY")
except Exception as e:
    print(f"Критическая ошибка в секретах: {e}")
    exit(1)

# Инициализация клиентов
gen_client = genai.Client(api_key=GEMINI_KEY)
tg_client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

is_talk_mode = False

print("--- СИСТЕМА ЗАПУЩЕНА ---")

@tg_client.on(events.NewMessage(outgoing=True))
async def handler(event):
    global is_talk_mode
    text = event.raw_text.lower()

    if text == ".talk":
        is_talk_mode = True
        await event.edit("🤖 **ИИ активен.**")
        return

    if text == ".talkoff":
        is_talk_mode = False
        await event.edit("🔇 **ИИ выключен.**")
        return

    if is_talk_mode and not text.startswith("."):
        try:
            response = gen_client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=event.raw_text
            )
            await tg_client.send_message(event.chat_id, f"**Gemini:** {response.text}")
        except Exception as e:
            print(f"Ошибка Gemini: {e}")

async def start():
    await tg_client.start()
    print("--- БОТ В СЕТИ ---")
    await tg_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(start())
    
