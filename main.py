import os
import asyncio
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- ЧТЕНИЕ СЕКРЕТОВ ---
try:
    API_ID = int(os.getenv("TG_API_ID").strip())
    API_HASH = os.getenv("TG_API_HASH").strip()
    SESSION_STR = os.getenv("STRING_SESSION").strip()
    GEMINI_KEY = os.getenv("GEMINI_API_KEY").strip()
except Exception as e:
    print(f"Ошибка в секретах: {e}")
    exit(1)

# --- НАСТРОЙКА ИИ ---
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
# Создаем чат-сессию для памяти контекста
chat_session = model.start_chat(history=[])

client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

# Состояние режима разговора
is_talk_mode = False

print("Бот запущен и ждет команд...")

# --- КОМАНДЫ ---

@client.on(events.NewMessage(pattern=r'\.Talk$', outgoing=True))
async def talk_on(event):
    global is_talk_mode
    is_talk_mode = True
    await event.edit("🤖 **Режим разговора ВКЛЮЧЕН.**\nЯ буду отвечать на все твои сообщения.")

@client.on(events.NewMessage(pattern=r'\.TalkOff$', outgoing=True))
async def talk_off(event):
    global is_talk_mode
    is_talk_mode = False
    await event.edit("🔇 **Режим разговора ВЫКЛЮЧЕН.**")

# --- ЛОГИКА ОБЩЕНИЯ ---

@client.on(events.NewMessage(outgoing=True))
async def chat_handler(event):
    global is_talk_mode
    
    # Не реагируем, если это команда (начинается с точки)
    if event.message.message.startswith('.'):
        return

    # Если режим разговора включен
    if is_talk_mode:
        try:
            # Отправляем сообщение в чат-сессию Gemini
            response = chat_session.send_message(event.message.message)
            
            # Отвечаем новым сообщением
            await client.send_message(event.chat_id, f"**Gemini:** {response.text}")
        except Exception as e:
            print(f"Ошибка ИИ: {e}")

# --- ЗАПУСК ---
async def start_bot():
    await client.start()
    print("Авторизация успешна!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
    
