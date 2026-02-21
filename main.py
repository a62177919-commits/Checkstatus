import os
import asyncio
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Считываем секреты
API_ID = int(os.getenv("TG_API_ID").strip())
API_HASH = os.getenv("TG_API_HASH").strip())
SESSION_STR = os.getenv("STRING_SESSION").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY").strip()

# Настройка Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

# Состояние режима разговора
is_talk_mode = False

print("Бот в сети и слушает сообщения...")

@client.on(events.NewMessage(pattern=r'\.Talk$', outgoing=True))
async def talk_on(event):
    global is_talk_mode
    is_talk_mode = True
    await event.edit("🤖 **Режим разговора ВКЛЮЧЕН.**")

@client.on(events.NewMessage(pattern=r'\.TalkOff$', outgoing=True))
async def talk_off(event):
    global is_talk_mode
    is_talk_mode = False
    await event.edit("🔇 **Режим разговора ВЫКЛЮЧЕН.**")

@client.on(events.NewMessage(outgoing=True))
async def chat_handler(event):
    global is_talk_mode
    
    # Игнорируем команды
    if event.message.message.startswith('.'):
        return

    if is_talk_mode:
        try:
            # Отправляем запрос в ИИ
            # Используем простую генерацию без chat_session для теста стабильности
            response = model.generate_content(event.message.message)
            
            # Отвечаем в тот же чат
            await client.send_message(event.chat_id, f"**Gemini:** {response.text}")
        except Exception as e:
            print(f"Ошибка при генерации: {e}")
            # Если что-то пошло не так, бот шепнет об этом в чат
            await client.send_message(event.chat_id, f"⚠️ Ошибка ИИ: {str(e)}")

async def main():
    await client.start()
    print("Авторизация прошла успешно!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
