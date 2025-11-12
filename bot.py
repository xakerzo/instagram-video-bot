#!/usr/bin/env python3
import os
import instaloader
import requests
import tempfile
import shutil
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# ---- Load environment ----
load_dotenv()  # .env faylni o‘qiydi
BOT_TOKEN = os.getenv("8294906702:AAHkYE73B6m5NokLedyUBsUTXib4XdLQ2BE")
ADMIN_CHAT_ID = os.getenv("1373647")  # alertlar uchun (optional)
INSTAGRAM_USERNAME = os.getenv("instadanvideoyukla")
INSTAGRAM_PASSWORD = os.getenv("Namangan0700", "")
SESSION_FILE = os.getenv("SESSION_FILE", "insta_session")
MAX_SEND_BYTES = int(os.getenv("MAX_SEND_BYTES", str(48*1024*1024)))

# ---- Logging ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Instaloader ----
L = instaloader.Instaloader(
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

def insta_login():
    """Login with session fallback."""
    try:
        if Path(SESSION_FILE).exists():
            logger.info(f"Loading Instagram session from {SESSION_FILE}")
            L.load_session_from_file(INSTAGRAM_USERNAME, SESSION_FILE)
            logger.info("Session loaded successfully.")
        elif INSTAGRAM_PASSWORD:
            logger.info(f"Logging in as {INSTAGRAM_USERNAME}")
            L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            L.save_session_to_file(SESSION_FILE)
            logger.info(f"Session saved to {SESSION_FILE}")
        else:
            raise RuntimeError("No session found and no password provided.")
    except Exception as e:
        logger.exception("Instagram login failed.")
        raise

# ---- Telegram handlers ----
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Instagram Video Downloader Bot\n\n"
        "📹 Instagram link yuboring:\n"
        "• https://www.instagram.com/p/ABC123/\n"
        "• https://www.instagram.com/reel/DEF456/\n\n"
        "⚡ @instadan_video_yuklabot"
    )

async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if url == "/start":
        return await start_command(update, context)

    if "instagram.com" not in url:
        await update.message.reply_text("❌ Iltimos, faqat Instagram link yuboring.")
        return

    info_msg = await update.message.reply_text("⏳ Video yuklanyapti, kuting...")

    # Shortcode parsing
    if "/p/" in url:
        shortcode = url.split("/p/")[1].split("/")[0]
    elif "/reel/" in url:
        shortcode = url.split("/reel/")[1].split("/")[0]
    else:
        await update.message.reply_text("❌ Noto'g'ri Instagram link formati.")
        return

    retry_wait = 5
    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        attempt += 1
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            break
        except Exception as e:
            if "429" in str(e) or "too many requests" in str(e).lower():
                await info_msg.edit_text(f"⏳ Instagram rate limit hit. Kutilyapti {retry_wait}s...")
                await asyncio.sleep(retry_wait)
                retry_wait = min(retry_wait*2, 900)
                continue
            else:
                await info_msg.edit_text(f"❌ Instagram xatosi: {e}")
                return
    else:
        await info_msg.edit_text("❌ Ko'p marta urinib bo‘lmadi, keyinroq urinib ko‘ring.")
        return

    if not post.is_video:
        await update.message.reply_text("❌ Bu postda video topilmadi.")
        return

    video_url = post.video_url
    if not video_url:
        await update.message.reply_text("❌ Video URL topilmadi.")
        return

    # Download to temp file
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(video_url, headers=headers, timeout=60)
        if response.status_code != 200:
            await update.message.reply_text("❌ Video yuklab bo‘lmadi.")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(response.content)
            video_path = tmp_file.name

        size = os.path.getsize(video_path)
        if size > MAX_SEND_BYTES:
            await update.message.reply_text(f"⚠️ Video juda katta ({size} bytes). Link: {video_url}")
        else:
            with open(video_path, "rb") as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=post.caption[:500] + f"\n\n📥 @instadan_video_yuklabot",
                    supports_streaming=True
                )
        os.unlink(video_path)
        await info_msg.delete()
        logger.info("Video muvaffaqiyatli yuborildi")
    except Exception as e:
        await update.message.reply_text(f"❌ Kutilmagan xatolik: {e}")
        logger.error(f"Kutilmagan xatolik: {e}")

# ---- Main ----
def main():
    insta_login()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_link))

    logger.info("🚀 Bot ishga tushmoqda...")
    app.run_polling()

if __name__ == "__main__":
    main()
