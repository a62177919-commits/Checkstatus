import os
import asyncio
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest

# --- ЧИТАЕМ ТВОИ СЕКРЕТЫ С ГИТХАБА ---
API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION_STR = os.getenv("STRING_SESSION")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Настраиваем Gemini (твой ИИ-мозг)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Запускаем селф-бота
client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

print("Твой живой ИИ-помощник запущен!")

# Команда .ai [текст] — спросить меня о чем угодно
@client.on(events.NewMessage(pattern=r'\.ai (.*)', outgoing=True))
async def ai_handler(event):
    user_prompt = event.pattern_match.group(1)
    await event.edit("⚡️ *Нейросеть генерирует ответ...*")
    try:
        response = model.generate_content(user_prompt)
        # Если ответ слишком длинный, Telegram может выдать ошибку, 
        # но для обычных чатов flash-модель подходит идеально.
        await event.edit(response.text)
    except Exception as e:
        await event.edit(f"❌ Ошибка: {str(e)}")

# Команда .bio [текст] — сменить описание профиля
@client.on(events.NewMessage(pattern=r'\.bio (.*)', outgoing=True))
async def bio_handler(event):
    new_bio = event.pattern_match.group(1)
    await client(UpdateProfileRequest(about=new_bio))
    await event.edit(f"✅ Био обновлено на: `{new_bio}`")

# Запуск
client.start()
client.run_until_disconnected()
