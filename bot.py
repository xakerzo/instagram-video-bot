import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

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

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply(
        "👋 Salom! Menga Instagram video linkini yuboring.\n\n"
        "🟢 Public video yuklab beraman.\n"
        "🔴 Private bo‘lsa, linkni kk.instagram.com ga o‘zgartirib qaytaraman."
    )

@dp.message_handler()
async def handle_message(message: types.Message):
    text = message.text.strip()

    # Instagram linkni tekshirish
    if "instagram.com" not in text:
        await message.reply("⚠️ Iltimos, Instagram post linkini yuboring.")
        return

    # Private akkaunt bo‘lsa — www → kk almashtiramiz
    if "www.instagram.com" in text:
        new_link = text.replace("www.instagram.com", "kk.instagram.com")
        await message.reply(
            f"🔒 Bu xususiy hisobdagi post bo‘lishi mumkin.\n"
            f"📎 Linkni o‘zgartirdim:\n{new_link}"
        )
        return

    # Public video yuklab olish
    await message.reply("⏳ Yuklanmoqda, biroz kuting...")

    video_url = download_instagram_video(text)
    if video_url:
        await message.reply_video(video_url, caption="✅ Yuklab olindi!")
    else:
        await message.reply("❌ Video yuklab bo‘lmadi. Linkni tekshirib qayta yuboring.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
