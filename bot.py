import telebot
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

def convert_link(link):
    link = link.strip()
    return link.replace("www.instagram.com", "kkinstagram.com")

@bot.message_handler(commands=["start"])
def send_welcome(message):
    start_text = """Salom! Menga Instagramdan video linkini yuboring, men sizga yuklab beraman 👇"""
    bot.reply_to(message, start_text)

@bot.message_handler(func=lambda m: True)
def handle_link(message):
    text = message.text
    if "instagram.com" in text:
        new_link = convert_link(text)
        
        # Birinchi xabarda link
        bot.reply_to(message, f"✅ {new_link}")
        
        # Ikkinchi xabarda reklama
        ad_text = """PUBG MOBILE UCHUN ENG ARZON UC SERVICE
💎 @ZakirShaX va @ZakirShaX_Price da"""
        
        bot.send_message(message.chat.id, ad_text)
        
    else:
        error_text = """❌ Iltimos, haqiqiy Instagram link yuboring.

PUBG MOBILE UCHUN ENG ARZON UC SERVICE
💎 @ZakirShaX va @ZakirShaX_Price da"""
        
        bot.reply_to(message, error_text)

print("Bot ishga tushdi ✅")
bot.infinity_polling()
