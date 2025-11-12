#!/usr/bin/env python3
"""
Prod-ready Telegram bot + Instaloader.
Features:
 - cookie/session login with Instaloader (load/save)
 - handles 429 responses with exponential backoff and telegram alerting
 - /download <username> downloads recent video posts and sends to telegram
 - uses environment variables for secrets
"""
import asyncio
import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional

import instaloader
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load env
load_dotenv()

# Required env vars
BOT_TOKEN = os.getenv("8294906702:AAHkYE73B6m5NokLedyUBsUTXib4XdLQ2BE")
ADMIN_CHAT_ID = os.getenv("1373647")  # for alerts, e.g. your telegram id
INSTA_USERNAME = os.getenv("instadanvideoyukla1")
INSTA_PASSWORD = os.getenv("Namangan0700")  # only needed first run to create session
SESSION_FILE = os.getenv("SESSION_FILE", "insta_session")
MAX_SEND_BYTES = int(os.getenv("MAX_SEND_BYTES", str(48 * 1024 * 1024)))  # default 48 MB

if not BOT_TOKEN or not ADMIN_CHAT_ID or not INSTA_USERNAME:
    raise SystemExit("Please set BOT_TOKEN, ADMIN_CHAT_ID and INSTA_USERNAME in .env")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Instaloader instance
L = instaloader.Instaloader(dirname_pattern=tempfile.gettempdir() + "/instaloader/{profile}")

# Utility: send admin alert
async def alert_admin(app, text: str):
    try:
        await app.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=text)
    except Exception as e:
        logger.exception("Failed to send admin alert: %s", e)

# Login / load session (try load -> otherwise login and save)
def insta_login():
    try:
        if Path(SESSION_FILE).exists():
            logger.info("Loading Instagram session from %s", SESSION_FILE)
            L.load_session_from_file(INSTA_USERNAME, SESSION_FILE)
            logger.info("Loaded session.")
        else:
            if not INSTA_PASSWORD:
                raise RuntimeError("No session file and INSTA_PASSWORD not set for initial login.")
            logger.info("Logging in to Instagram as %s", INSTA_USERNAME)
            L.login(INSTA_USERNAME, INSTA_PASSWORD)
            L.save_session_to_file(SESSION_FILE)
            logger.info("Saved session to %s", SESSION_FILE)
    except Exception:
        logger.exception("Instagram login/load session failed.")
        raise

# Helper: download post video to a temp file (returns filepath or None)
def download_post_video(post, tmpdir: Path) -> Optional[Path]:
    """
    Uses Instaloader to download post. Instaloader saves files into its dirname_pattern.
    We'll call download_post and then find the saved video file.
    """
    try:
        profile_dir = Path(tmpdir) / "instaloader" / post.owner_username
        # ensure clean folder
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)

        # instaloader will download into dirname_pattern configured above
        L.dirname_pattern = str(profile_dir)
        L.download_post(post, target=post.owner_username)

        # find the first mp4 in profile_dir (post filename starts with shortcode)
        for p in profile_dir.rglob("*.mp4"):
            return p
        # if not mp4, maybe saved as .jpg (not a video)
        return None
    except Exception:
        logger.exception("Failed to download post %s", getattr(post, "shortcode", None))
        return None

# Detect "429" in exception message
def is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "too many requests" in msg or "rate limit" in msg

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! /download <username> orqali Instagram videolarini olish mumkin.")

# Command: /download <username> (downloads last N posts' videos)
async def download_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    if len(context.args) != 1:
        await update.message.reply_text("Iltimos, username kiriting: /download <username>")
        return

    target_username = context.args[0].lstrip("@")
    info_msg = await update.message.reply_text(f"{target_username} postlari tekshirilmoqda...")
    N = 5  # default latest posts to check
    try:
        retry_wait = 10  # initial wait seconds on 429
        max_retries = 6
        attempt = 0
        while True:
            attempt += 1
            try:
                profile = instaloader.Profile.from_username(L.context, target_username)
                break
            except Exception as e:
                logger.exception("Error fetching profile %s (attempt %d)", target_username, attempt)
                if is_rate_limit_error(e):
                    # notify admin and wait with backoff
                    await alert_admin(app, f"Instagram rate limit (429) while fetching profile {target_username}. Waiting {retry_wait}s (attempt {attempt}).")
                    await info_msg.edit_text(f"Instagram rate limit hit. Kutilyapti {retry_wait}s... (attempt {attempt})")
                    await asyncio.sleep(retry_wait)
                    retry_wait = min(retry_wait * 2, 900)  # exponential backoff up to 15 min
                    if attempt >= max_retries:
                        await info_msg.edit_text("Ko‘p marta urinib bo‘lmadi — adminga xabar yuborildi.")
                        return
                    continue
                else:
                    await info_msg.edit_text(f"Profilni olishda xatolik: {e}")
                    return

        posts = profile.get_posts()
        sent_any = False
        checked = 0
        tempdir = Path(tempfile.mkdtemp(prefix="igbot_"))
        try:
            async for post in _aiter_posts(posts, N):
                checked += 1
                if getattr(post, "is_video", False):
                    await info_msg.edit_text(f"Video topildi — yuklanmoqda ({checked}/{N})...")
                    video_path = await asyncio.get_event_loop().run_in_executor(None, download_post_video, post, tempdir)
                    if video_path and video_path.exists():
                        size = video_path.stat().st_size
                        if size <= MAX_SEND_BYTES:
                            # send as file
                            await context.bot.send_video(chat_id=update.effective_chat.id, video=open(video_path, "rb"), caption=f"@{post.owner_username} — {post.shortcode}")
                            sent_any = True
                        else:
                            # too big -> send url
                            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Video juda katta ({size} bytes). Link: {post.url}")
                            sent_any = True
                        # cleanup this profile dir (instaloader may have created files)
                        shutil.rmtree(video_path.parent, ignore_errors=True)
                    else:
                        # fallback to sending url
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Video yuklab bo‘lmadi. Link: {post.url}")
                        sent_any = True
                # small pause between posts to avoid rapid queries
                await asyncio.sleep(2)
            if not sent_any:
                await update.message.reply_text("Oxirgi tekshirgan postlarda video topilmadi.")
            else:
                await info_msg.delete()
        finally:
            # cleanup tempdir
            try:
                shutil.rmtree(tempdir)
            except Exception:
                pass

    except Exception as e:
        logger.exception("Unhandled error in /download")
        await info_msg.edit_text(f"Xatolik yuz berdi: {e}")
        await alert_admin(app, f"Botda xatolik: {e}")

# Utility to iterate first N posts asynchronously (since instaloader yields sync generator)
async def _aiter_posts(posts_iter, n):
    """Yield up to n posts from a synchronous iterator using run_in_executor"""
    loop = asyncio.get_event_loop()
    count = 0
    iterator = posts_iter
    # posts.get_posts() returns a generator; we'll pull items in executor to avoid blocking
    while count < n:
        try:
            post = await loop.run_in_executor(None, lambda: next(iterator))
        except StopIteration:
            break
        except Exception:
            # sometimes instaloader generator raises network exceptions with 429 etc.
            raise
        yield post
        count += 1

# Main
def main():
    insta_login()  # will raise on failure

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("download", download_cmd))

    logger.info("Bot ishga tushmoqda...")
    # start polling
    app.run_polling()

if __name__ == "__main__":
    main()
