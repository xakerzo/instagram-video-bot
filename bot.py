import os
import instaloader
import requests
import tempfile
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Logging ni yoqish
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 🔑 BU YERGA O'Z MA'LUMOTLARINGIZNI QO'YING
BOT_TOKEN = "8294906702:AAHkYE73B6m5NokLedyUBsUTXib4XdLQ2BE"  # ⚠️ @BotFather dan olingan token
INSTAGRAM_USERNAME = "instadanvideoyukla"  # ⚠️ Instagram loginingiz
INSTAGRAM_PASSWORD = "Namangan0700"  # ⚠️ Instagram parolingiz

# Tokenni tekshirish
if BOT_TOKEN == "1234567890:AAFgGfGhIjKlMnOpQrStUvWxYz1234567898294906702:AAHkYE73B6m5NokLedyUBsUTXib4XdLQ2BE":
    print("❌ ILTIMOS: BOT_TOKEN ni @BotFather dan olingan tokenga almashtiring!")
    exit(1)

print(f"✅ Token mavjud: {BOT_TOKEN[:10]}...")

# Instaloader sozlamalari
L = instaloader.Instaloader(
    download_videos=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    request_timeout=60
)

# Instagram login qilish
def login_instagram():
    if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD and INSTAGRAM_USERNAME != "sizning_instagram_login":
        try:
            L.login(instadanvideoyukla, Namangan0700)
            print("✅ Instagramga muvaffaqiyatli login qilindi")
            return True
        except Exception as e:
            print(f"⚠️ Instagram loginda xatolik: {e}")
            print("ℹ️ Login sizsiz ishlaydi (cheklangan)")
            return False
    else:
        print("ℹ️ Instagram login ma'lumotlari kiritilmagan, oddiy rejimda ishlaydi")
        return False

print("🤖 Bot ishga tushmoqda...")

# Start komandasi
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Instagram video yuklab beruvchi botga xush kelibsiz!\n\n"
        "📹 Video yuklash uchun Instagram post linkini yuboring.\n\n"
        "📎 Namuna: https://www.instagram.com/p/ABC12345678/\n"
        "📎 Yoki: https://www.instagram.com/reel/ABC12345678/"
    )

# Instagram shortcode olish
def get_shortcode_from_url(url):
    # Turli Instagram URL formatlarini qo'llab-quvvatlash
    patterns = [
        r'instagram\.com/p/([^/?]+)',
        r'instagram\.com/reel/([^/?]+)',
        r'instagram\.com/stories/[^/]+/([^/?]+)',
        r'instagram\.com/tv/([^/?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Agar hech qaysi pattern mos kelmasa, URL ning oxirgi qismini olish
    parts = url.split('/')
    for part in parts:
        if part and len(part) >= 10 and not part.startswith('http'):
            return part
    
    return None

# Yuklab olish funksiyasi
async def download_instagram_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    
    # Start komandasini tekshirish
    if user_message == '/start':
        return await start_command(update, context)
    
    # URL ni tekshirish
    if "instagram.com" not in user_message:
        await update.message.reply_text("❌ Iltimos, Instagram link yuboring.")
        return
        
    await update.message.reply_text("⏳ Video yuklanyapti, iltimos kuting...")

    try:
        # Shortcode olish
        shortcode = get_shortcode_from_url(user_message)
        
        if not shortcode:
            await update.message.reply_text("❌ Noto'g'ri Instagram link formati. Iltimos, to'g'ri link yuboring.")
            return

        print(f"📥 Yuklanayotgan post: {shortcode}")
        
        # Post ma'lumotlarini olish
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
        except Exception as e:
            await update.message.reply_text(f"❌ Post topilmadi yoki ochiq emas: {e}")
            return

        if not post.is_video:
            await update.message.reply_text("❌ Bu postda video topilmadi. Faqat video postlarni yuklay olaman.")
            return

        # Video URL olish
        video_url = post.video_url
        caption = post.caption or "Instagram video"
        
        if not video_url:
            await update.message.reply_text("❌ Video URL topilmadi.")
            return

        print(f"📹 Video URL topildi, yuklanmoqda...")
        
        # Videoni yuklab olish
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.instagram.com/'
        }
        
        try:
            response = requests.get(video_url, headers=headers, timeout=60, stream=True)
            if response.status_code != 200:
                await update.message.reply_text("❌ Xatolik: videoni yuklab bo'lmadi.")
                return
        except requests.exceptions.Timeout:
            await update.message.reply_text("❌ Vaqt tugadi: video juda katta yoki server sekin.")
            return

        # Vaqtinchalik fayl yaratish
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                video_path = tmp_file.name
        except Exception as e:
            await update.message.reply_text(f"❌ Fayl yaratishda xatolik: {e}")
            return

        print("✅ Video yuklandi, Telegramga yuborilmoqda...")

        # Videoni yuborish
        try:
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"{caption[:500]}\n\n📥 @instadan_video_yuklabot",
                    supports_streaming=True
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Videoni yuborishda xatolik: {e}")
            return
        finally:
            # Faylni o'chirish
            try:
                os.unlink(video_path)
            except:
                pass

        print("✅ Video muvaffaqiyatli yuborildi.")

    except instaloader.exceptions.InstaloaderException as e:
        await update.message.reply_text(f"❌ Instagram xatosi: {e}")
        print(f"Instagram xatosi: {e}")
    except Exception as e:
        error_msg = f"❌ Kutilmagan xatolik: {str(e)}"
        await update.message.reply_text(error_msg)
        print(f"Xatolik: {e}")

# Botni ishga tushirish
def main():
    try:
        # Instagramga login qilish
        login_instagram()
        
        # Botni yaratish
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Handlerlarni qo'shish
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram_video))
        
        print("=" * 50)
        print("🤖 Bot muvaffaqiyatli ishga tushdi!")
        print("📍 Botni tekshirish uchun Telegramda /start bosing")
        print("📍 Instagram link yuboring")
        print("=" * 50)
        
        app.run_polling()
        
    except Exception as e:
        print(f"❌ Botni ishga tushirishda xatolik: {e}")

if __name__ == "__main__":
    main()
