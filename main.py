import os
import asyncio
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- ЧИТАЕМ СЕКРЕТЫ ---
# Используем .get() и .strip(), чтобы избежать ошибок из-за пробелов
API_ID_STR = os.getenv("TG_API_ID", "").strip()
API_HASH = os.getenv("TG_API_HASH", "").strip()
SESSION_STR = os.getenv("STRING_SESSION", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not all([API_ID_STR, API_HASH, SESSION_STR, GEMINI_KEY]):
    print("Ошибка: Один из секретов GitHub не заполнен!")
    exit(1)

API_ID = int(API_ID_STR)

# --- НАСТРОЙКА ИИ ---
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Создаем клиент
client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

# Переменная состояния режима разговора
is_talk_mode = False

print("Бот запускается...")

# Команда включения (регистронезависимая)
@client.on(events.NewMessage(pattern=r'(?i)\.talk$', outgoing=True))
async def talk_on(event):
    global is_talk_mode
    is_talk_mode = True
    await event.edit("🤖 **Режим разговора ВКЛЮЧЕН.**\nТеперь я буду отвечать на твои сообщения.")

# Команда выключения
@client.on(events.NewMessage(pattern=r'(?i)\.talkoff$', outgoing=True))
async def talk_off(event):
    global is_talk_mode
    is_talk_mode = False
    await event.edit("🔇 **Режим разговора ВЫКЛЮЧЕН.**")

# Обработка обычных сообщений
@client.on(events.NewMessage(outgoing=True))
async def chat_handler(event):
    global is_talk_mode
    
    # Если это команда (начинается с точки) — ничего не делаем
    if event.text.startswith('.'):
        return

    # Если режим разговора включен
    if is_talk_mode:
        try:
            # Отправляем запрос в Gemini
            response = model.generate_content(event.text)
            # Отвечаем новым сообщением
            await client.send_message(event.chat_id, f"**Gemini:** {response.text}")
        except Exception as e:
            print(f"Ошибка ИИ: {e}")

async def main():
    await client.start()
    print("Бот успешно авторизован и работает!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
