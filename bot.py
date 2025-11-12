import os
import instaloader
import requests
import tempfile
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

print('Bot ishga tushmoqda')

BOT_TOKEN = os.environ['BOT_TOKEN']
INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME', '')
INSTAGRAM_PASSWORD = os.environ.get('INSTAGRAM_PASSWORD', '')

L = instaloader.Instaloader(download_videos=False)

if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
    try:
        L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print('Instagram login OK')
        time.sleep(2)
    except Exception as e:
        print(f'Login error: {e}')

