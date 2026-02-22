import os
import asyncio
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Считываем переменные
API_ID_STR = os.getenv("TG_API_ID", "").strip()
API_HASH = os.getenv("TG_API_HASH", "").strip()
SESSION_STR = os.getenv("STRING_SESSION", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Настройка ИИ
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

client = TelegramClient(StringSession(SESSION_STR), int(API_ID_STR), API_HASH)

is_talk_mode = False

print("--- БОТ ЗАПУСКАЕТСЯ ---")

@client.on(events.NewMessage(outgoing=True))
async def handler(event):
    global is_talk_mode
    text = event.raw_text
    print(f"Вижу сообщение: {text}") # Это появится в логах GitHub

    # Команда включения
    if text.lower() == ".talk":
        is_talk_mode = True
        await event.edit("🤖 **ИИ включен**")
        return

    # Команда выключения
    if text.lower() == ".talkoff":
        is_talk_mode = False
        await event.edit("🔇 **ИИ выключен**")
        return

    # Если режим включен и это не команда
    if is_talk_mode and not text.startswith("."):
        try:
            response = model.generate_content(text)
            await client.send_message(event.chat_id, f"**Gemini:** {response.text}")
        except Exception as e:
            print(f"Ошибка Gemini: {e}")

async def main():
    await client.start()
    print("--- БОТ В СЕТИ ---")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
