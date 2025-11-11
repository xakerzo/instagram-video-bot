import os
import instaloader
import requests
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ['8294906702:AAHkYE73B6m5NokLedyUBsUTXib4XdLQ2BE']
INSTAGRAM_USERNAME = os.environ.get('instadanvideoyukla, '')
INSTAGRAM_PASSWORD = os.environ.get('Namangan0700', '')

print('🚀 Bot ishga tushmoqda...')

L = instaloader.Instaloader(download_videos=False)

if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
    try:
        L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print('✅ Instagramga login qilindi')
    except Exception as e:
        print(f'⚠️ Login xatosi: {e}')
else:
    print('ℹ️ Loginsiz ishlaydi')

