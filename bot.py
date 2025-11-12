import os
import instaloader
import requests
import tempfile
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

print("Bot ishga tushmoqda")

BOT_TOKEN = os.environ['8294906702:AAHkYE73B6m5NokLedyUBsUTXib4XdLQ2BE']
INSTAGRAM_USERNAME = os.environ.get('instadanvideoyukla1, '')
INSTAGRAM_PASSWORD = os.environ.get('Namangan0700, '')

L = instaloader.Instaloader(download_videos=False)

if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
    try:
        L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print("Instagram login OK")
        time.sleep(2)
    except Exception as e:
        print(f"Login error: {e}")

async def start(update, context):
    await update.message.reply_text("Salom! Instagram link yuboring")

async def handle_video(update, context):
    url = update.message.text.strip()
    
    if url == '/start':
        return await start(update, context)
    
    if "instagram.com" not in url:
        await update.message.reply_text("Instagram link kerak")
        return
        
    await update.message.reply_text("Yuklanmoqda...")
    
    try:
        if "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        elif "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        else:
            await update.message.reply_text("Notogri link")
            return
        
        print(f"Yuklanayotgan: {shortcode}")
        time.sleep(1)
        
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        if not post.is_video:
            await update.message.reply_text("Video topilmadi")
            return
        
        response = requests.get(post.video_url, timeout=60)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(response.content)
            video_path = f.name
        
        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption="Instagram video")
        
        os.unlink(video_path)
        await update.message.reply_text("Muvaffaqiyatli!")
        
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {str(e)}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    print("Bot ishga tushdi")
    app.run_polling()

if __name__ == "__main__":
    main()
