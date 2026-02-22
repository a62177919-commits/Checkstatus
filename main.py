import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from google import genai

# Читаем секреты
API_ID = int(os.getenv("TG_API_ID").strip())
API_HASH = os.getenv("TG_API_HASH").strip()
SESSION_STR = os.getenv("STRING_SESSION").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY").strip()

# Настройка нового клиента Gemini
gen_client = genai.Client(api_key=GEMINI_KEY)
tg_client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

is_talk_mode = False

print("--- СИСТЕМА ЗАПУЩЕНА ---")

@tg_client.on(events.NewMessage(outgoing=True))
async def handler(event):
    global is_talk_mode
    text = event.raw_text.lower()

    # Проверка команд
    if text == ".talk":
        is_talk_mode = True
        await event.edit("🤖 **ИИ активен. Я тебя слушаю.**")
        print("Режим разговора включен")
        return

    if text == ".talkoff":
        is_talk_mode = False
        await event.edit("🔇 **ИИ выключен.**")
        print("Режим разговора выключен")
        return

    # Если режим включен и это не команда
    if is_talk_mode and not text.startswith("."):
        print(f"Запрос к ИИ: {event.raw_text}")
        try:
            # Новый метод генерации контента
            response = gen_client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=event.raw_text
            )
            await tg_client.send_message(event.chat_id, f"**Gemini:** {response.text}")
        except Exception as e:
            print(f"Ошибка: {e}")
            await tg_client.send_message(event.chat_id, f"⚠️ Ошибка: {str(e)}")

async def start():
    await tg_client.start()
    print("--- АВТОРИЗАЦИЯ УСПЕШНА ---")
    await tg_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(start())
    
