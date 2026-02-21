import os
import asyncio
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- НАСТРОЙКИ (твои секреты) ---
API_ID = int(os.getenv("TG_API_ID").strip())
API_HASH = os.getenv("TG_API_HASH").strip())
SESSION_STR = os.getenv("STRING_SESSION").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY").strip()

# Настройка Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

# Переменная для хранения состояния режима разговора
is_talk_mode = False

print("Бот-собеседник запущен!")

# --- КОМАНДЫ УПРАВЛЕНИЯ ---

@client.on(events.NewMessage(pattern=r'\.Talk$', outgoing=True))
async def talk_on(event):
    global is_talk_mode
    is_talk_mode = True
    await event.edit("🤖 **Режим разговора ВКЛЮЧЕН.** Теперь я буду отвечать на все твои сообщения.")

@client.on(events.NewMessage(pattern=r'\.TalkOff$', outgoing=True))
async def talk_off(event):
    global is_talk_mode
    is_talk_mode = False
    await event.edit("🔇 **Режим разговора ВЫКЛЮЧЕН.** Я снова работаю только по командам.")

# --- ЛОГИКА ОБЩЕНИЯ ---

@client.on(events.NewMessage(outgoing=True))
async def chat_handler(event):
    global is_talk_mode
    
    # Если сообщение начинается с точки (это команда) — игнорируем здесь
    if event.message.message.startswith('.'):
        return

    # Если режим разговора включен
    if is_talk_mode:
        # Небольшая задержка, чтобы имитировать "печатает..."
        # (Опционально можно добавить event.edit("..."))
        try:
            response = model.generate_content(event.message.message)
            # Отвечаем новым сообщением или редактируем старое? 
            # Для режима беседы лучше отвечать НОВЫМ сообщением:
            await client.send_message(event.chat_id, f"**Gemini:** {response.text}")
        except Exception as e:
            print(f"Ошибка ИИ: {e}")

async def main():
    await client.start()
    print("Сессия активна. Бот в сети.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
