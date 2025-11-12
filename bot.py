# bot.py
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import instaloader
import os

BOT_TOKEN = 8294906702:AAHkYE73B6m5NokLedyUBsUTXib4XdLQ2BE"
COOKIE_FILE = "insta_session"

# Instaloader obyekti
L = instaloader.Instaloader()

# Instagram login funksiyasi
def insta_login(username, password):
    try:
        if os.path.exists(COOKIE_FILE):
            L.load_session_from_file(username, COOKIE_FILE)
        else:
            L.login(username, password)
            L.save_session_to_file(COOKIE_FILE)
        print("Instagram login successful")
    except Exception as e:
        print("Instagram login error:", e)

# Telegram /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Instagram video yuklash botiga xush kelibsiz.\n\nFoydalanish: /download <username>")

# Telegram /download komandasi
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Iltimos, username kiriting: /download <username>")
        return

    username = context.args[0]
    msg = await update.message.reply_text(f"{username} postlari yuklanmoqda...")

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        posts = list(profile.get_posts())
        count = 0
        for post in posts[:3]:  # oxirgi 3 postni yuklaymiz
            if post.is_video:
                video_url = post.video_url
                await update.message.reply_text(video_url)
                count += 1

        if count == 0:
            await update.message.reply_text("Video topilmadi.")
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"Xatolik yuz berdi: {e}")

# Asosiy ishga tushirish
def main():
    # Instagram login
    insta_username = "instadanvideoyukla1"
    insta_password = "Namangan0700"
    insta_login(insta_username, insta_password)

    # Telegram bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("download", download))

    print("Bot ishga tushmoqda...")
    app.run_polling()

if __name__ == "__main__":
    main()
