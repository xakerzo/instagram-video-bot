import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from config import BOT_TOKEN
import asyncio

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Instagram video yuklab olish funksiyasi
def download_instagram_video(url):
    try:
        api_url = f"https://api.sssgram.io/media?url={url}"
        response = requests.get(api_url).json()
        if "url" in response and response["url"]:
            return response["url"]
        return None
    except Exception:
        return None

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Salom! Menga Instagram video linkini yuboring.\n\n"
                         "🟢 Public video yuklab beraman.\n"
                         "🔴 Private bo‘lsa, linkni kk.instagram.com ga o‘zgartirib qaytaraman.")

@dp.message()
async def handle_message(message: Message):
    text = message.text.strip()

    # Instagram linkni tekshirish
    if "instagram.com" not in text:
        await message.answer("⚠️ Iltimos, Instagram post linkini yuboring.")
        return

    # Private akkaunt bo‘lsa — www → kk almashtirish
    if "www.instagram.com" in text:
        new_link = text.replace("www.instagram.com", "kk.instagram.com")
        await message.answer(
            f"🔒 Bu xususiy hisobdagi post bo‘lishi mumkin.\n"
            f"📎 Linkni o‘zgartirdim:\n{new_link}"
        )
        return

    # Public video yuklab olish
    await message.answer("⏳ Yuklanmoqda, biroz kuting...")

    video_url = download_instagram_video(text)
    if video_url:
        await message.answer_video(video_url, caption="✅ Yuklab olindi!")
    else:
        await message.answer("❌ Video yuklab bo‘lmadi. Linkni tekshirib qayta yuboring.")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
