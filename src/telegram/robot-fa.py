import json
import requests
import os
from urllib.parse import urlparse
import tempfile
import base64
from io import BytesIO
from cryptography.fernet import Fernet
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler
from telegram.ext import filters
from telegram import ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder
import asyncio
import yaml
from datetime import datetime, timedelta
from pytz import timezone
from jdatetime import date as jdate 
from telegram import InputFile
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display
import arabic_reshaper
import re
import requests
from ipaddress import ip_address
import aiohttp
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import aiohttp
TOGGLE_BLOCK = 0  
SELECT_CONFIG = 1
SELECT_PEER = 2
TOGGLE_BLOCK_STATE = 3 
SHOW_BACKUPS = 4
CREATE_BACKUP = 5
DELETE_BACKUP = 6
RESTORE_BACKUP = 7
SELECT_PEER_NAME = 8
SELECT_INTERFACE = 9
STATE_SELECT_INTERFACE = 10
STATE_SELECT_PEER_OR_SEARCH = 11
STATE_SEARCH_PEER = 12
STATE_SELECT_PEER_TO_EDIT = 13
STATE_EDIT_OPTION = 60
STATE_SET_DATA_LIMIT = 61
STATE_SET_DNS = 62
STATE_SET_EXPIRY_TIME = 63
SET_DATA_LIMIT = 14
SET_DNS = 15
SET_EXPIRY_TIME = 16
SELECT_IP_ADDRESS = 17
INPUT_PEER_NAME = 18
SELECT_LIMIT_UNIT = 19
INPUT_LIMIT_VALUE = 20
SELECT_DNS = 21
INPUT_CUSTOM_DNS = 22
INPUT_EXPIRY_TIME = 23
CONFIRM_USAGE = 24
CHOOSE_WG_INTERFACE = 25
ENTER_PEER_NAME = 26
CONFIRM_PEER_DELETION = 27
SELECT_RESET_INTERFACE = 28
ENTER_RESET_PEER_NAME = 29
SHOW_PEER_INFO = 30
CONFIRM_RESET_ACTION = 31
CHOOSE_INTERFACE_STATUS = 32
INPUT_PEER_NAME_STATUS = 33
DISPLAY_PEER_STATUS = 34
USER_UPDATE = 35
PASSWORD_UPDATE = 36
CONFIG_INTERFACE = 37
CONFIG_DETAILS = 38
LOGIN_USERNAME = 39
LOGIN_PASSWORD = 40
CONFIG_PORT = 41
CONFIG_MTU = 42
CONFIG_DNS = 43
CONFIG_CONFIRM = 44
VIEW_TEMPLATE_PEER_NAME = 49
SELECT_TEMPLATE_INTERFACE = 50
CONFIRM_TEMPLATE = 51
SELECT_CONFIG_DYNAMIC = 52
VIEW_PEER_DETAILS = 53
SELECT_TEMPLATE_PEER = 54
INPUT_MTU = 55
INPUT_KEEPALIVE = 56
SELECT_MODE = 57
INPUT_BULK_COUNT = 58
INPUT_EXPIRY_DAYS = 59

def load_telegram_yaml():
    telegram_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(telegram_dir, "telegram.yaml")
    secret_key_path = os.path.join(os.path.dirname(telegram_dir), "secret.key")

    try:
        if not os.path.exists(secret_key_path):
            raise FileNotFoundError(f"Secret key file not found at {secret_key_path}")
        
        with open(secret_key_path, "rb") as key_file:
            key = key_file.read()
        cipher = Fernet(key)

        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Config file not found at {yaml_path}")
        
        with open(yaml_path, "r") as file:
            config = yaml.safe_load(file) or {}  
            encrypted_chat_ids = config.get("admin_chat_ids", [])

            if not encrypted_chat_ids:
                print("No admin chat IDs found in telegram.yaml.")
                return {"admin_chat_ids": []}
            
            chat_ids = [cipher.decrypt(chat_id.encode()).decode() for chat_id in encrypted_chat_ids]
            print(f"Decrypted admin_chat_ids: {chat_ids}")

            return {"admin_chat_ids": chat_ids}

    except FileNotFoundError as e:
        print(f"❌ Config file {yaml_path} or key file {secret_key_path} not found. Error: {e}")
        raise
    except Exception as e:
        print(f"❌ Error loading or decrypting {yaml_path}: {e}")
        raise

def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    
    try:
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
            print(f"Loaded config: {config}")  
            return {
                "bot_token": config.get("bot_token", ""), 
                "base_url": config.get("base_url", ""),    
                "api_key": config.get("api_key", ""),      
            }
    except FileNotFoundError:
        print(f"❌ Config file {config_path} not found.")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {config_path}. {e}")
        raise

config = load_config()
API_BASE_URL = config["base_url"]
TELEGRAM_BOT_TOKEN = config["bot_token"]
if not TELEGRAM_BOT_TOKEN:
    print("bot_token is missing in config.json.")
    exit(1)
API_KEY = config["api_key"]
CONFIG_FILE = "telegram.yaml"


async def api_stuff(endpoint, method="GET", data=None, context=None, retries=3, timeout=30):
    url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    cookies = context.user_data.get("cookies", {}) if context else {}

    for attempt in range(1, retries + 1):
        async with aiohttp.ClientSession(cookies=cookies) as session:
            try:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers, timeout=timeout) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method.upper() == "POST":
                    async with session.post(url, headers=headers, json=data, timeout=timeout) as response:
                        response.raise_for_status()
                        if response.cookies and context:
                            context.user_data["cookies"] = {key: morsel.value for key, morsel in response.cookies.items()}
                        return await response.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers, json=data, timeout=timeout) as response:
                        response.raise_for_status()
                        return await response.json()
                else:
                    return {"error": "HTTP method unsupported"}

            except aiohttp.ClientError as e:
                print(f"Attempt {attempt} failed: {str(e)}")
                if attempt < retries:
                    await asyncio.sleep(2)
                else:
                    return {"error": f"Request failed after {retries} attempts: {str(e)}"}

            except asyncio.TimeoutError:
                print(f"Attempt {attempt} timed out.")
                if attempt < retries:
                    await asyncio.sleep(2)
                else:
                    return {"error": f"Request timed out after {retries} attempts"}



def load_chat_ids():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            data = yaml.safe_load(file)
            return data.get("admin_chat_ids", [])  
    return []

def save_chat_ids(chat_ids):
    config = load_telegram_yaml()  
    config["admin_chat_ids"] = chat_ids  
    with open(CONFIG_FILE, "w") as file:
        yaml.dump(config, file, default_flow_style=False, indent=4)  

def clear_chat_ids():
    config = load_telegram_yaml() 
    if "admin_chat_ids" in config:
        del config["admin_chat_ids"]  
    with open(CONFIG_FILE, "w") as file:
        yaml.dump(config, file, default_flow_style=False, indent=4)  

admin_chat_ids = load_chat_ids()  
current_status = {"status": "inactive"}

async def monitor_health(context: CallbackContext):
    global current_status
    endpoint = "api/health"

    notifications_enabled = context.bot_data.get("notifications_enabled", False)  
    if not notifications_enabled:
        print("Health monitoring is disabled.")
        return

    try:
        response = await api_stuff(endpoint)
        new_status = "running" if response.get("status") == "running" else "inactive"
    except Exception:
        new_status = "inactive"

    if new_status != current_status["status"]:
        current_status["status"] = new_status

        config = load_telegram_yaml()
        admin_chat_ids = config.get("admin_chat_ids", [])

        for chat_id in admin_chat_ids:
            try:
                if new_status == "inactive":
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="⚠️ *هشدار*: برنامه *غیرفعال* شده است. لطفاً وضعیت را بررسی کنید!",
                        parse_mode="Markdown"
                    )
                elif new_status == "running":
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="✅ *اطلاعیه*: برنامه دوباره *فعال* و عملیاتی شد.",
                        parse_mode="Markdown"
                    )
            except Exception as e:
                print(f"خطا در اطلاع‌رسانی به مدیر: {e}")

    try:
        context.job_queue.run_once(monitor_health, 10)
    except Exception as e:
        print(f"خطا در زمان‌بندی مجدد مانیتورینگ : {e}")



async def start_login(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text(
            "👤 *فرآیند ورود:*\n\nلطفاً نام کاربری خود را وارد کنید:",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "👤 *فرآیند ورود:*\n\nلطفاً نام کاربری خود را وارد کنید:",
            parse_mode="Markdown"
        )
    return LOGIN_USERNAME


async def login_username(update: Update, context: CallbackContext):
    context.user_data['login_username'] = update.message.text
    await update.message.reply_text(
        "🔒 *فرآیند ورود:*\n\nلطفاً رمز عبور خود را وارد کنید:",
        parse_mode="Markdown"
    )
    return LOGIN_PASSWORD


async def login_password(update: Update, context: CallbackContext):
    username = context.user_data['login_username']
    password = update.message.text

    payload = {"username": username, "password": password}

    try:
        response = await api_stuff("api/login", method="POST", data=payload, context=context)

        if response.get("message"):
            context.user_data['is_logged_in'] = True
            context.user_data['username'] = username

            await update.message.reply_text(
                f"✅ *ورود موفقیت‌آمیز!*\n\nخوش آمدید، `{username}`!",
                parse_mode="Markdown"
            )

            await settings_menu(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"❌ *ورود ناموفق:*\n\n{response.get('error', 'خطای ناشناخته')}\n\n"
                "لطفاً دوباره با استفاده از دستور /login تلاش کنید.",
                parse_mode="Markdown"
            )
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            f"❌ *خطا:*\n\nمشکلی رخ داد: `{e}`.\n\n"
            "لطفاً بعداً دوباره تلاش کنید.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END


async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    config = load_telegram_yaml()
    admin_chat_ids = config.get("admin_chat_ids", [])

    if not admin_chat_ids:
        print("❌ Admin chat IDs not found in telegram.yaml.")
        return

    for chat_id in admin_chat_ids:
        try:
            await start(context=context, chat_id=chat_id)
        except Exception as e:
            print(f"❌ Failed to send auto message to chat_id {chat_id}: {e}")




def flask_status():
    global current_status
    config = load_config()
    flask_url = config["base_url"] + "/api/health"  

    try:
        response = requests.get(flask_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "running":
                current_status['status'] = 'running'
                print("✅ *اطلاعیه*: برنامه دوباره *فعال* و عملیاتی شد.")
            else:
                current_status['status'] = 'inactive'
                print(f"⚠️ هشدار: وضعیت غیرمعمول از API دریافت شد: {data.get('status')}.")
        else:
            current_status['status'] = 'inactive'
            print(f"⚠️ هشدار: API این کد وضعیت را برگرداند: {response.status_code}.")
    except requests.exceptions.RequestException as e:
        current_status['status'] = 'inactive'
        print(f"❌ امکان اتصال به API وجود ندارد. جزئیات: {e}")


    
async def start(update: Update = None, context: CallbackContext = None, chat_id: int = None):
    global current_status

    if chat_id is None:
        chat_id = update.effective_chat.id if update else None

    config = load_telegram_yaml()
    admin_chat_ids = config.get("admin_chat_ids", [])

    if not str(chat_id) in map(str, admin_chat_ids):  
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ شما مجاز به استفاده از این ربات نیستید.",
            parse_mode="Markdown"
        )
        return

    try:
        flask_status()
    except Exception as e:
        print(f"بررسی سلامت دستی ناموفق بود: {e}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "static/images/telegram.jpg")

    status_icon = "🚦"
    status_message = (
        f"{status_icon} وضعیت برنامه: {'🟢 فعال' if current_status['status'] == 'running' else '🔴 غیرفعال'}"
    )

    notifications_enabled = context.bot_data.get("notifications_enabled", False)  
    notification_status = "✅ فعال" if notifications_enabled else "❌ غیرفعال"

    caption_text = (
        f"<b>به ربات مدیریت وایرگارد خوش آمدید</b>\n\n"
        f"{status_message}\n"
        f"📢 اعلان‌ها: {notification_status}\n\n"
        f"<i>لطفاً یکی از گزینه‌های زیر را انتخاب کنید:</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton("🔕 غیرفعال کردن اعلان‌ها", callback_data="disable_notifications"),
            InlineKeyboardButton("🔔 فعال کردن اعلان‌ها", callback_data="enable_notifications"),
        ],
        [
            InlineKeyboardButton("📊 آمار", callback_data="metrics"),
            InlineKeyboardButton("👥 کاربران", callback_data="peers_menu"),
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings_menu"),
            InlineKeyboardButton("📦 پشتیبان‌ها", callback_data="backups_menu"),
        ],
        [InlineKeyboardButton("📝 گزارشات", callback_data="view_logs")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as photo_file:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=caption_text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
                print("تصویر تلگرام با موفقیت ارسال شد.")
        else:
            print(f"تصویر در مسیر {image_path} یافت نشد.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ بارگذاری تصویر امکان‌پذیر نیست.",
            )
    except Exception as e:
        print(f"ارسال تصویر ناموفق بود: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ ارسال تصویر امکان‌پذیر نیست.",
        )




async def view_logs(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = update.effective_chat.id

    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return

    await query.answer()

    try:
        response = await api_stuff("api/logs?limit=20", method="GET", context=context)
        
        if "logs" in response:
            logs = "\n".join(response["logs"])
            message = f"📝 *گزارشات:*\n\n```\n{logs}\n```"
        else:
            message = "⚠️ هیچ گزارشی موجود نیست یا مشکلی رخ داده است."
    except Exception as e:
        message = f"❌ خطا در دریافت گزارشات: `{e}`"

    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        message, 
        parse_mode="Markdown", 
        reply_markup=reply_markup
    )



async def settings_menu(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message_target = query.message  
    else:
        message_target = update.message 

    is_logged_in = context.user_data.get('is_logged_in', False)
    username = context.user_data.get('username', 'وارد نشده')

    if is_logged_in:
        message = (
            f"⚙️ *منوی تنظیمات:*\n\n"
            f"👤 *وارد شده به سرور:* `{username}`\n\n"
            f"یکی از گزینه‌های زیر را برای بروزرسانی انتخاب کنید:"
        )
        keyboard = [
            [InlineKeyboardButton("👤 بروزرسانی نام کاربری/رمز عبور", callback_data="update_user")],
            [InlineKeyboardButton("🔧 بروزرسانی تنظیمات وایرگارد", callback_data="update_wireguard_config")],
            [InlineKeyboardButton("🚪 خروج از حساب", callback_data="logout")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
        ]
    else:
        message = (
            f"⚙️ *منوی تنظیمات:*\n\n"
            f"❌ *شما وارد سرور نشده‌اید.*\n\n"
            f"لطفاً برای دسترسی به تنظیمات سرور، وارد شوید."
        )
        keyboard = [
            [InlineKeyboardButton("🔑 ورود", callback_data="login")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_target.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def update_user_wire(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if not context.user_data.get('is_logged_in', False):
        await query.message.reply_text(
            "❌ *برای بروزرسانی حساب خود باید وارد شوید.*\n\nاز دستور /login استفاده کنید.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await query.message.reply_text(
        "👤 *بروزرسانی نام کاربری:*\n\nلطفاً نام کاربری جدید خود را وارد کنید:",
        parse_mode="Markdown"
    )
    return USER_UPDATE

async def logout(update: Update, context: CallbackContext):
    response = await api_stuff("api/logout", method="POST", context=context)

    context.user_data.clear()
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message_target = query.message  
    elif update.message:
        message_target = update.message  
    else:
        print("❌ خروج امکان پذیر نیست")
        return

    await message_target.reply_text(
        "🚪 *شما با موفقیت از سرور خارج شدید!*\n\nبرای ورود دوباره از دستور /login استفاده کنید.",
        parse_mode="Markdown"
    )


async def update_username(update: Update, context: CallbackContext):
    new_username = update.message.text
    context.user_data['new_username'] = new_username
    await update.message.reply_text(
        "🔒 *بروزرسانی رمز عبور:*\n\nلطفاً رمز عبور جدید خود را وارد کنید:",
        parse_mode="Markdown"
    )
    return PASSWORD_UPDATE


async def update_password(update: Update, context: CallbackContext):
    new_password = update.message.text
    new_username = context.user_data['new_username']

    payload = {"username": new_username, "password": new_password}
    cookies = context.user_data.get("cookies", {})  

    try:
        response = await api_stuff(
            "api/update-user",
            method="POST",
            data=payload,
            context=context
        )

        if response.get("message"):
            context.user_data['username'] = new_username  
            await update.message.reply_text(
                f"✅ {response['message']}\n\nبازگشت به منوی تنظیمات...",
                parse_mode="Markdown"
            )
            await settings_menu(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"❌ *خطا:*\n\n{response.get('error', 'خطای ناشناخته')}\n\nبازگشت به منوی تنظیمات...",
                parse_mode="Markdown"
            )
            await settings_menu(update, context)
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            f"❌ بروزرسانی کاربر موفقیت امیز نبود: `{e}`\n\nبازگشت به منوی تنظیمات...",
            parse_mode="Markdown"
        )
        await settings_menu(update, context)
        return ConversationHandler.END



async def back_to_settings(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await settings_menu(update, context)
    return ConversationHandler.END


async def update_wireguard_setting(update: Update, context: CallbackContext):
    await update.callback_query.answer()

    interface = context.user_data.get("selected_interface", "wg0.conf")
    context.user_data["interface"] = interface
    message = f"✏️ *بروزرسانی تنظیمات برای {interface}:*\n\nیکی از گزینه‌های زیر را انتخاب کنید:"
    keyboard = [
        [InlineKeyboardButton("🛠️ بروزرسانی پورت", callback_data="update_port")],
        [InlineKeyboardButton("📏 بروزرسانی MTU", callback_data="update_mtu")],
        [InlineKeyboardButton("🌐 بروزرسانی DNS", callback_data="update_dns")],
        [InlineKeyboardButton("✅ اعمال تغییرات", callback_data="apply_changes")],
        [InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data="settings_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return CONFIG_INTERFACE


#not using it
async def select_interface(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    interface = query.data.replace("select_interface_", "")
    context.user_data['interface'] = interface

    await query.message.reply_text(
        f"✏️ *Update Configuration for {interface}:*\n\n"
        f"Please send the configuration in the following format:\n"
        f"`port=<value>, mtu=<value>, dns=<value>`",
        parse_mode="Markdown"
    )
    return CONFIG_DETAILS

async def ask_for_port(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "🔧 *بروزرسانی پورت:*\n\nلطفاً پورت جدید را وارد کنید.\n\nمثال: `51820`",
        parse_mode="Markdown"
    )
    return CONFIG_PORT


async def ask_for_mtu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "📏 *بروزرسانی MTU:*\n\n"
        "لطفاً مقدار جدید MTU را وارد کنید.\n\n"
        "مقدار MTU باید بین `1280` و `1420` باشد.\n\n"
        "مثال: `1420`",
        parse_mode="Markdown"
    )
    return CONFIG_MTU


async def ask_for_dns(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "🌐 *بروزرسانی DNS:*\n\nلطفاً سرور(های) DNS جدید را وارد کنید.\n\nمثال: `8.8.8.8, 8.8.4.4`",
        parse_mode="Markdown"
    )
    return CONFIG_DNS


async def set_port(update: Update, context: CallbackContext):
    port = update.message.text
    context.user_data["port"] = port
    await update.message.reply_text(f"✅ پورت به `{port}` بروزرسانی شد.\n\nگزینه دیگری را انتخاب کنید یا تغییرات را اعمال کنید.",
                                    parse_mode="Markdown")
    await update_wireguard_setting(update, context)
    return CONFIG_INTERFACE


async def set_mtu(update: Update, context: CallbackContext):
    mtu = update.message.text.strip()

    if not mtu.isdigit() or not (1280 <= int(mtu) <= 1420):
        await update.message.reply_text(
            "❌ مقدار MTU نامعتبر است. لطفاً مقداری بین `1280` و `1420` وارد کنید.",
            parse_mode="Markdown"
        )
        return CONFIG_MTU

    context.user_data["mtu"] = int(mtu)

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی تنظیمات", callback_data="settings_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ مقدار MTU به `{mtu}` بروزرسانی شد.\n\n"
        "می‌توانید به منوی تنظیمات بازگردید یا تنظیمات دیگری را بروزرسانی کنید.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return CONFIG_INTERFACE



async def set_dns(update: Update, context: CallbackContext):
    dns = update.message.text
    context.user_data["dns"] = dns
    await update.message.reply_text(f"✅ DNS به `{dns}` بروزرسانی شد.\n\nگزینه دیگری را انتخاب کنید یا تغییرات را اعمال کنید.",
                                    parse_mode="Markdown")
    await update_wireguard_setting(update, context)
    return CONFIG_INTERFACE


async def apply_config(update: Update, context: CallbackContext):
    await update.callback_query.answer()

    interface = context.user_data.get("interface")
    port = context.user_data.get("port", "تنظیم نشده")
    mtu = context.user_data.get("mtu", "تنظیم نشده")
    dns = context.user_data.get("dns", "تنظیم نشده")

    payload = {"config": interface, "port": port, "mtu": mtu, "dns": dns}
    response = await api_stuff("api/update-wireguard-config", method="POST", data=payload, context=context)

    if response.get("message"):
        await update.callback_query.message.reply_text(
            f"✅ *تنظیمات با موفقیت برای {interface} اعمال شد:*\n\n"
            f"پورت: `{port}`\nMTU: `{mtu}`\nDNS: `{dns}`",
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.message.reply_text(
            f"❌ *اعمال تنظیمات برای {interface} شکست خورد:*\n\n"
            f"خطا: {response.get('error', 'خطای ناشناخته')}",
            parse_mode="Markdown"
        )

    await update_wireguard_setting(update, context)
    return CONFIG_INTERFACE


def is_authorized(chat_id):
    config = load_telegram_yaml()
    admin_chat_ids = config["admin_chat_ids"]  

    print(f"Checking authorization for chat_id: {chat_id}, admin_chat_ids: {admin_chat_ids}")
    return str(chat_id) in map(str, admin_chat_ids)  


async def enable_notifications(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ شما مجاز به انجام این عملیات نیستید.",
            parse_mode="Markdown"
        )
        return

    context.bot_data["notifications_enabled"] = True

    context.job_queue.run_once(monitor_health, 10)

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        f"✅ اعلان‌ها برای این چت فعال شدند.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def disable_notifications(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ شما مجاز به انجام این عملیات نیستید.",
            parse_mode="Markdown"
        )
        return

    context.bot_data["notifications_enabled"] = False

    current_jobs = context.job_queue.jobs()
    for job in current_jobs:
        if job.name == "monitor_health":
            job.schedule_removal()

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        f"❌ اعلان‌ها برای این چت غیرفعال شدند.\n\nمی‌توانید از منوی اصلی دوباره آن‌ها را فعال کنید.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )



def register_notification(application):
    application.add_handler(CallbackQueryHandler(enable_notifications, pattern="enable_notifications"))
    application.add_handler(CallbackQueryHandler(disable_notifications, pattern="disable_notifications"))

async def backups_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = update.effective_chat.id

    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return

    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📋 نمایش پشتیبان‌ها", callback_data="show_backups"),
         InlineKeyboardButton("➕ ایجاد پشتیبان", callback_data="create_backup")],
        [InlineKeyboardButton("🗑 حذف پشتیبان", callback_data="delete_backup"),
         InlineKeyboardButton("🔄 بازیابی پشتیبان", callback_data="restore_backup")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "📦 *منوی پشتیبان‌ها:*\n\nچه کاری می‌خواهید انجام دهید؟",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


def fish_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        response.raise_for_status()
        return response.json().get("ip", "localhost")
    except Exception as e:
        print(f"Error retrieving public IP: {e}")
        return "localhost" 
    
def determine_base_url(config):
    base_url = config.get("base_url", "http://localhost").strip()  
    
    parsed_url = urlparse(base_url)
    
    if parsed_url.port:
        return f"{parsed_url.scheme}://{parsed_url.hostname}:{parsed_url.port}"
    
    if base_url.startswith("http://localhost") or base_url == "localhost":
        public_ip = fish_public_ip()
        return f"http://{public_ip}"
    
    if re.match(r"^https?://[a-zA-Z0-9.-]+", base_url):
        return base_url.rstrip("/")
    
    print(f"Warning: Invalid base_url in config: {base_url}. Defaulting to localhost.")
    return "http://localhost"


async def show_backups(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return
    query = update.callback_query
    await query.answer()

    response = await api_stuff("api/backups")
    if "error" in response:
        await query.message.reply_text(f"❌ *خطا در دریافت پشتیبان‌ها:* `{response['error']}`", parse_mode="Markdown")
        return await backups_menu(update, context)

    backups = response.get("backups", [])
    if not backups:
        await query.message.reply_text("⚠️ *هیچ پشتیبان دستی یافت نشد.*", parse_mode="Markdown")
        return await backups_menu(update, context)

    base_url = determine_base_url(config)

    keyboard = [
        [
            InlineKeyboardButton(f"📄 {backup}", callback_data=f"show_backup_details_{backup}"),
            InlineKeyboardButton("⬇️ دانلود", url=f"{base_url}/api/download-backup?name={backup}"),
        ]
        for backup in backups
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی پشتیبان‌ها", callback_data="backups_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "📦 *پشتیبان‌های موجود:*\n\nیک پشتیبان را انتخاب کنید یا مستقیماً دانلود کنید:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )




async def create_backup(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return
    query = update.callback_query
    await query.answer()

    response = await api_stuff("api/create-backup", method="POST")
    if "error" in response:
        await query.message.reply_text(f"❌ *خطا در ایجاد پشتیبان:* `{response['error']}`", parse_mode="Markdown")
    else:
        message = response.get("message", "پشتیبان با موفقیت ایجاد شد.")
        await query.message.reply_text(f"✅ {message}", parse_mode="Markdown")

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی پشتیبان‌ها", callback_data="backups_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("چه کاری می‌خواهید انجام دهید؟", reply_markup=reply_markup)


async def delete_backup_apply(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    response = await api_stuff("api/backups")
    if "error" in response:
        await query.message.reply_text(f"❌ *Fetching backups error:* `{response['error']}`", parse_mode="Markdown")
        return ConversationHandler.END

    backups = response.get("backups", [])
    if not backups:
        await query.message.reply_text("⚠️ *No manual backups found.*", parse_mode="Markdown")
        return await backups_menu(update, context)

    keyboard = [
        [InlineKeyboardButton(f"🗑 {backup}", callback_data=f"delete_{backup}")]
        for backup in backups
    ]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="backups_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "🗑 **Select a backup to delete:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def delete_backup(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    backup_name = query.data.replace("delete_", "")
    print(f"Parsed backup name: {backup_name}")  

    response = await api_stuff(f"api/delete-backup?name={backup_name}&folder=root", method="DELETE")
    if "error" in response:
        await query.message.reply_text(f"❌ *Error deleting backup:* `{response['error']}`", parse_mode="Markdown")
    else:
        message = response.get("message", f"🗑 *Backup `{backup_name}` deleted successfully.*")
        await query.message.reply_text(f"✅ {message}", parse_mode="Markdown")

    return await backups_menu(update, context)



async def restore_backup_apply(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return
    query = update.callback_query
    await query.answer()
    response = await api_stuff("api/backups")
    if "error" in response:
        await query.message.reply_text(f"❌ *خطا در دریافت پشتیبان‌ها:* `{response['error']}`", parse_mode="Markdown")
        return ConversationHandler.END

    backups = response.get("backups", [])
    if not backups:
        await query.message.reply_text("⚠️ *هیچ پشتیبان دستی یافت نشد.*", parse_mode="Markdown")
        await backups_menu(update, context)
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(f"🔄 {backup}", callback_data=f"restore_{backup}")]
        for backup in backups
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="backups_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "🔄 *یک فایل پشتیبان را برای بازیابی انتخاب کنید:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def restore_backup(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    backup_name = query.data.replace("restore_", "")
    response = await api_stuff("api/restore-backup", method="POST", data={"backupName": backup_name})
    if "error" in response:
        await query.message.reply_text(f"❌ *خطا در بازیابی پشتیبان:* `{response['error']}`", parse_mode="Markdown")
    else:
        message = response.get("message", f"🔄 *پشتیبان `{backup_name}` با موفقیت بازیابی شد.*")
        await query.message.reply_text(f"✅ {message}", parse_mode="Markdown")

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی پشتیبان‌ها", callback_data="backups_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("چه کاری می‌خواهید انجام دهید؟", reply_markup=reply_markup)


def register_backup_stuff(application):
    application.add_handler(CallbackQueryHandler(backups_menu, pattern="backups_menu"))
    application.add_handler(CallbackQueryHandler(show_backups, pattern="show_backups"))
    application.add_handler(CallbackQueryHandler(create_backup, pattern="create_backup"))
    application.add_handler(CallbackQueryHandler(delete_backup_apply, pattern="delete_backup"))
    application.add_handler(CallbackQueryHandler(restore_backup_apply, pattern="restore_backup"))
    application.add_handler(CallbackQueryHandler(delete_backup, pattern="delete_.*"))
    application.add_handler(CallbackQueryHandler(restore_backup, pattern="restore_.*"))


async def stat_metrics(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return
    response = await api_stuff("api/metrics")
    if "error" in response:
        await context.bot.send_message(chat_id, text=f"❌ خطا در دریافت آمار سیستم: {response['error']}")
        return

    cpu = response.get("cpu", "Unknown")
    ram = response.get("ram", "Unknown")
    disk = response.get("disk", {"used": "Unknown", "total": "Unknown"})
    uptime = response.get("uptime", "Unknown")

    disk_used = float(disk["used"].replace("GB", "").strip()) if "used" in disk else 0
    disk_total = float(disk["total"].replace("GB", "").strip()) if "total" in disk else 1
    disk_percentage = (disk_used / disk_total) * 100 if disk_total > 0 else 0

    metrics_labels = ["CPU Usage", "RAM Usage", "Disk Usage"]
    metrics_values = [
        float(cpu.replace("%", "")) if "%" in cpu else 0,
        float(ram.replace("%", "")) if "%" in ram else 0,
        disk_percentage,
    ]

    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.family"] = "DejaVu Sans"  

    plt.figure(figsize=(6, 4))
    plt.bar(metrics_labels, metrics_values, color=["blue", "green", "orange"])
    plt.title("System Metrics", fontsize=14)
    plt.ylabel("Percentage / GB", fontsize=12)
    plt.ylim(0, 100)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis="y", linestyle="--", linewidth=0.5)

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", dpi=150)
    buffer.seek(0)

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(
        chat_id,
        photo=buffer,
        caption=f"📊 **آمار سیستم**\n\n"
                f"CPU: {cpu}\n"
                f"RAM: {ram}\n"
                f"DISK: {disk['used']} / {disk['total']}\n"
                f"Uptime: {uptime}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    buffer.close()


async def peers_menu(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return

    message = (
        "🎛 **منوی مدیریت کاربران**\n\n"
        "یکی از گزینه‌ها را برای مدیریت کاربران وایرگارد انتخاب کنید:"
    )

    keyboard = [
        [
            InlineKeyboardButton("✏️ ویرایش کاربر", callback_data="edit_peer"),
            InlineKeyboardButton("🆕 ایجاد کاربر جدید", callback_data="create_peer"),
        ],
        [
            InlineKeyboardButton("🔄 ریست ترافیک/انقضا", callback_data="reset_peer"),
            InlineKeyboardButton("❌ حذف کاربر", callback_data="peer_delete"),
        ],
        [
            InlineKeyboardButton("🔒 مسدود/باز کردن کاربر", callback_data="block_unblock_peer"),
            InlineKeyboardButton("🔍 وضعیت کاربر", callback_data="peer_status"),
        ],
        [
            InlineKeyboardButton("📄 مشاهده قالب", callback_data="view_template"),
            InlineKeyboardButton("⬇️ دانلود / کد QR", callback_data="download_qr_menu"),
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode="Markdown")



async def download_qr_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "✏️ *نام کاربر را وارد نمایید* \n\n"
        "مثال : azumi",
        parse_mode="Markdown"
    )
    return VIEW_PEER_DETAILS

async def view_template_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    response = await api_stuff("api/get-interfaces")
    if "error" in response:
        await query.message.reply_text(
            f"❌ *خطا در دریافت اینترفیس‌ها:* `{response['error']}`",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    interfaces = response.get("interfaces", [])
    if not interfaces:
        await query.message.reply_text(
            "❌ *هیچ اینترفیس Wireguard یافت نشد.*",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(f"🌐 {interface}", callback_data=f"select_template_interface_{interface}")]
        for interface in interfaces
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "🌐 *اینترفیس Wireguard را انتخاب کنید:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECT_TEMPLATE_INTERFACE


async def wire_int_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_interface = query.data.replace("select_template_interface_", "")
    context.user_data["selected_interface"] = selected_interface

    await query.answer()
    await query.message.reply_text(
        f"🌐 اینترفیس انتخاب شده: {selected_interface}.\n\n"
        "✏️ *نام کاربر را وارد کنید تا کاربرهای این اینترفیس را جستجو کنید:*",
        parse_mode="Markdown"
    )
    return VIEW_TEMPLATE_PEER_NAME


async def view_peers_with_name(update: Update, context: CallbackContext):
    peer_name = update.message.text.strip()
    selected_interface = context.user_data.get("selected_interface")
    API_BASE_URL = config.get("base_url")

    if not selected_interface:
        await update.message.reply_text(
            "❌ هیچ اینترفیس Wireguard انتخاب نشده است. لطفاً فرآیند را مجدداً شروع کنید.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    if not API_BASE_URL:
        await update.message.reply_text(
            "❌ خطا در پیکربندی: `base_url` در پیکربندی تنظیم نشده است.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    try:
        response = requests.get(
        f"{API_BASE_URL}/api/get-peers",
        params={"peer_name": peer_name, "config_name": selected_interface},
        timeout=5  
        )
        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ خطا در دریافت اطلاعات کاربرها: {response.text}",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        peers_data = response.json().get("peers", [])
        if not peers_data:
            await update.message.reply_text(
                f"❌ هیچ کاربری با نام `{peer_name}` در اینترفیس `{selected_interface}` یافت نشد.",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        for peer in peers_data:
            peer_details = (
                f"🖧 *نام کاربر:* `{peer['peer_name']}`\n"
                f"🌐 *آی‌پی کاربر:* `{peer.get('peer_ip', 'N/A')}`\n"
                f"📊 *محدودیت داده:* `{peer.get('limit', 'N/A')}`\n"
                f"⏳ *انقضا:* `{peer['expiry_time'].get('months', 0)} ماه, "
                f"{peer['expiry_time'].get('days', 0)} روز`\n"
            )
            keyboard = [
                [InlineKeyboardButton(
                    f"مشاهده قالب {peer['peer_name']} ({peer.get('peer_ip', 'N/A')})",
                    callback_data=(f"view_template_{peer['peer_name']}_{peer['peer_ip']}_"
                                   f"{peer.get('limit', 'N/A')}_"
                                   f"{peer['expiry_time'].get('months', 0)}m_{peer['expiry_time'].get('days', 0)}d")
                )]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(peer_details, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(
            f"❌ خطا در دریافت اطلاعات کاربرها: {str(e)}",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    return SELECT_TEMPLATE_PEER


def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, outline_width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=outline_width)

async def generate_template_with_qr(update, context):
    query = update.callback_query
    await query.answer()

    API_BASE_URL = config.get("base_url")
    if not API_BASE_URL:
        await query.message.reply_text(
            "❌ Config error: `base_url` is not set in the config.",
            parse_mode="Markdown"
        )
        return

    callback_data = query.data.replace("view_template_", "")
    peer_name, peer_ip, data_limit, expiry = callback_data.split("_", 3)
    selected_interface = context.user_data.get("selected_interface")

    expiry = expiry.replace("m_", " months, ").replace("d", " days")

    try:
        details_response = requests.post(
            f"{API_BASE_URL}/api/generate-template",
            json={"peer_name": peer_name, "config_name": selected_interface},
            timeout=5
        )
        if details_response.status_code != 200:
            await query.message.reply_text(
                f"❌ Error fetching peer details: {details_response.text}",
                parse_mode="Markdown"
            )
            return

        qr_response = requests.get(
            f"{API_BASE_URL}/api/qr-code",
            params={"peerName": peer_name, "config": f"{selected_interface}.conf"},
            timeout=5
        )
        if qr_response.status_code != 200:
            await query.message.reply_text(
                f"❌ Error fetching QR code: {qr_response.text}",
                parse_mode="Markdown"
            )
            return

        qr_data = qr_response.json().get("qr_code")
        if not qr_data:
            await query.message.reply_text(
                "❌ QR Code data not found.",
                parse_mode="Markdown"
            )
            return

        qr_image_data = base64.b64decode(qr_data.split(",")[1])
        qr_image = Image.open(BytesIO(qr_image_data))

        template_path = "static/images/template.jpg"
        template_image = Image.open(template_path).convert("RGB")
        template_image = template_image.resize((430, 500))

        draw = ImageDraw.Draw(template_image)

        box_xy = (20, 360, 420, 480)
        draw_rounded_rectangle(draw, box_xy, radius=20, fill="gray", outline="white", outline_width=2)

        qr_image = qr_image.resize((90, 90))
        qr_x, qr_y = 30, 374
        template_image.paste(qr_image, (qr_x, qr_y))

        font_path = "static/fonts/Poppins-Regular.ttf"
        try:
            font = ImageFont.truetype(font_path, 16)
        except IOError:
            font = ImageFont.load_default()

        text_x, text_y = 130, 375 
        line_height = 20
        draw.text((text_x, text_y), f"Peer Name: {peer_name}", font=font, fill="white")
        draw.text((text_x, text_y + line_height), f"Peer IP: {peer_ip}", font=font, fill="white")
        draw.text((text_x, text_y + line_height * 2), f"Data Limit: {data_limit}", font=font, fill="white")
        draw.text((text_x, text_y + line_height * 3), f"Expiry: {expiry}", font=font, fill="white")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            output_path = temp_file.name
            template_image.save(output_path, "JPEG", quality=95)

        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=open(output_path, "rb"),
            caption = f"🎉 قالب برای کاربر: {peer_name} ({peer_ip}) ایجاد شد."
        )

        os.remove(output_path)

    except Exception as e:
        await query.message.reply_text(
            f"❌ Error generating template: {str(e)}",
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی کاربران", callback_data="peers_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "✅ قالب با موفقیت ایجاد شد. چه کار دیگری میخواهید انجام دهید ؟",
        reply_markup=reply_markup
    )


async def peername_search(update: Update, context: CallbackContext):
    peer_name = update.message.text.strip()
    context.user_data["search_peer_name"] = peer_name
    response = await api_stuff("api/get-interfaces")

    if "error" in response:
        await update.message.reply_text(
            f"❌ *خطا در دریافت اینترفیس ها:* `{response['error']}`",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    interfaces = response.get("interfaces", [])
    if not interfaces:
        await update.message.reply_text(
            "❌ *هیچ اینترفیس وایرگارد یافت نشد.*",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(f"🌐 {interface}", callback_data=f"select_interface_{interface}")]
        for interface in interfaces
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🌐 *اینترفیس وایرگارد را انتخاب کنید:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECT_INTERFACE


async def interface_select(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_interface = query.data.replace("select_interface_", "")
    context.user_data["selected_interface"] = selected_interface
    config_file = f"{selected_interface}.conf"
    context.user_data["selected_config"] = config_file

    peer_name = context.user_data.get("search_peer_name", "").strip()

    if not peer_name:
        await query.message.reply_text("❌ *نام کاربر برای جستجو وارد نشده است.*", parse_mode="Markdown")
        return ConversationHandler.END

    response = await api_stuff(f"api/peers-by-interface?interface={selected_interface}")

    if "error" in response:
        await query.message.reply_text(
            f"❌ *خطا در دریافت کاربران:* `{response['error']}`",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    peers = response.get("peers", [])

    matched_peers = [
        peer for peer in peers if peer["peer_name"].lower() == peer_name.lower()
    ]

    if not matched_peers:
        await query.message.reply_text(
            f"❌ *هیچ کاربری با نام:* `{peer_name}` *پیدا نشد.*",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    matched_peer = matched_peers[0] 
    context.user_data["peer_name"] = matched_peer["peer_name"]

    peer_details = (
        f"🔷 **جزئیات کاربر**\n\n"
        f"📛 **نام کاربر:** `{matched_peer['peer_name']}`\n"
        f"🌐 **آی‌پی کاربر:** `{matched_peer['peer_ip']}`\n"
        f"🔑 **کلید عمومی:** `{matched_peer['public_key']}`\n"
        f"⚡ **وضعیت:** {'🟢 فعال' if not matched_peer['expiry_blocked'] else '🔴 مسدود'}\n"
    )
    keyboard = [
        [InlineKeyboardButton("📄 دانلود تنظیمات", callback_data=f"download_create_{matched_peer['peer_name']}")],
        [InlineKeyboardButton("📷 تولید کد QR", callback_data=f"qr_create_{matched_peer['peer_name']}")],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب اینترفیس", callback_data="download_qr_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(peer_details, reply_markup=reply_markup, parse_mode="Markdown")

    return ConversationHandler.END


async def peer_decision(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    action, peer_name = query.data.split("_", 1)
    context.user_data["peer_name"] = peer_name  

    if action == "download":
        await download_peerconfig_create(update, context)
    elif action == "qr":
        await generate_peerqr_create(update, context)



async def download_peerconfig_general(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("_")
    if len(data_parts) < 3:
        await query.message.reply_text("❌ اطلاعات کافی برای دانلود تنظیمات وجود ندارد.", parse_mode="Markdown")
        return

    peer_name = "_".join(data_parts[2:])
    config_file = context.user_data.get("selected_config")

    if not config_file or not config_file.endswith(".conf"):
        await query.message.reply_text("❌ فایل تنظیمات وایرگارد پیدا نشد. لطفاً فرآیند را دوباره آغاز کنید.")
        return

    expiry_days = context.user_data.get("expiry_days", 1)
    data_limit = context.user_data.get("data_limit", "N/A")

    tehran_tz = timezone("Asia/Tehran")
    now_tehran = datetime.now(tehran_tz).date()

    current_jalali_date = jdate.fromgregorian(date=now_tehran)
    expiry_date_jalali = current_jalali_date + timedelta(days=expiry_days)
    expiry_date_jalali_str = f"{expiry_date_jalali.year}/{expiry_date_jalali.month:02}/{expiry_date_jalali.day:02}"

    config_url = f"{API_BASE_URL}/api/download-peer-config?peerName={peer_name}&config={config_file}"
    short_link_url = f"{API_BASE_URL}/api/get-peer-link?peerName={peer_name}&config={config_file}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(short_link_url, headers={"Authorization": f"Bearer {API_KEY}"}) as link_response:
                short_link = "N/A"
                if link_response.status == 200:
                    link_data = await link_response.json()
                    short_link = link_data.get("short_link", "N/A")
                else:
                    print(f"Couldn't retrieve short link. Status: {link_response.status}")

            async with session.get(config_url, headers={"Authorization": f"Bearer {API_KEY}"}) as config_response:
                if config_response.status == 200:
                    peer_config = await config_response.text()

                    keyboard = [
                        [
                            InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu"),
                            InlineKeyboardButton("📋 لیست کاربران", callback_data="peers_menu"),
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    caption = (
                        f"فایل تنظیمات برای {peer_name}\n\n"
                        f"👤 *نام کاربری:* {peer_name}\n"
                        f"⏳ *تاریخ انقضا:* {expiry_days} روز\n"
                        f"📅 *تاریخ انقضا (شمسی):* {expiry_date_jalali_str}\n"
                        f"📏 *میزان حجم:* {data_limit}\n\n"
                        f"🔗 * لینک کوتاه کانفیگ:*\n"
                        f"[{short_link}]({short_link})\n\n"
                        f"📄 *محتوای فایل تنظیمات:*\n"
                        f"```\n{peer_config}\n```"
                    )

                    await context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=BytesIO(peer_config.encode("utf-8")),
                        filename=f"{peer_name}.conf",
                        caption=caption,
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                else:
                    error = await config_response.json()
                    await query.message.reply_text(f"❌ خطا: {error.get('error', 'عدم توانایی در دریافت فایل تنظیمات')}")
        except Exception as e:
            await query.message.reply_text(f"❌ خطا: {str(e)}")

async def generate_peerqr_general(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("_")
    if len(data_parts) < 3:
        await query.message.reply_text("❌ اطلاعات کافی برای دریافت QR Code وجود ندارد.", parse_mode="Markdown")
        return

    peer_name = "_".join(data_parts[2:])
    config_file = context.user_data.get("selected_config")

    if not config_file or not config_file.endswith(".conf"):
        await query.message.reply_text("❌ فایل تنظیمات وایرگارد پیدا نشد. لطفاً فرآیند را دوباره آغاز کنید.")
        return

    expiry_days = context.user_data.get("expiry_days", 1)
    data_limit = context.user_data.get("data_limit", "N/A")

    tehran_tz = timezone("Asia/Tehran")
    now_tehran = datetime.now(tehran_tz).date()

    current_jalali_date = jdate.fromgregorian(date=now_tehran)
    expiry_date_jalali = current_jalali_date + timedelta(days=expiry_days)
    expiry_date_jalali_str = f"{expiry_date_jalali.year}/{expiry_date_jalali.month:02}/{expiry_date_jalali.day:02}"

    qr_url = f"{API_BASE_URL}/api/download-peer-qr?peerName={peer_name}&config={config_file}"
    config_url = f"{API_BASE_URL}/api/download-peer-config?peerName={peer_name}&config={config_file}"
    short_link_url = f"{API_BASE_URL}/api/get-peer-link?peerName={peer_name}&config={config_file}"

    async with aiohttp.ClientSession() as session:
        try:
            short_link = "N/A"
            async with session.get(short_link_url, headers={"Authorization": f"Bearer {API_KEY}"}) as link_response:
                if link_response.status == 200:
                    link_data = await link_response.json()
                    short_link = link_data.get("short_link", "N/A")
                else:
                    print(f"Couldn't retrieve short link. Status: {link_response.status}")

            async with session.get(qr_url, headers={"Authorization": f"Bearer {API_KEY}"}) as qr_response:
                if qr_response.status == 200:
                    qr_image = await qr_response.read()
                else:
                    error = await qr_response.json()
                    await query.message.reply_text(f"❌ خطا در دریافت QR Code: {error.get('error', 'نامشخص')}")
                    return

            peer_config = "N/A"
            async with session.get(config_url, headers={"Authorization": f"Bearer {API_KEY}"}) as config_response:
                if config_response.status == 200:
                    peer_config = await config_response.text()
                else:
                    error = await config_response.json()
                    await query.message.reply_text(f"❌ خطا در دریافت تنظیمات: {error.get('error', 'نامشخص')}")
                    return

            caption = (
                f"فایل تنظیمات برای {peer_name}\n\n"
                f"👤 *نام کاربری:* {peer_name}\n"
                f"⏳ *تاریخ انقضا:* {expiry_days} روز\n"
                f"📅 *تاریخ انقضا (شمسی):* {expiry_date_jalali_str}\n"
                f"📏 *میزان حجم:* {data_limit}\n\n"
                f"🔗 *لینک کوتاه کانفیگ:*\n"
                f"[{short_link}]({short_link})\n\n"
                f"برای کپی کردن تنظیمات، از متن زیر استفاده کنید:\n"
                f"```\n{peer_config}\n```"
            )

            keyboard = [
                [
                    InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu"),
                    InlineKeyboardButton("📋 لیست کاربران", callback_data="peers_menu"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=BytesIO(qr_image),
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception as e:
            await query.message.reply_text(f"❌ خطا: {str(e)}")



async def init_deletepeer(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return
    response = await api_stuff("api/get-interfaces")
    
    if "error" in response:
        await context.bot.send_message(chat_id, f"❌ خطا در دریافت اینترفیس‌ها: `{response['error']}`", parse_mode="Markdown")
        return ConversationHandler.END

    interfaces = response.get("interfaces", [])
    if not interfaces:
        await context.bot.send_message(chat_id, "❌ *هیچ اینترفیسی یافت نشد.*", parse_mode="Markdown")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"📂 {interface}", callback_data=f"peer_interface_{interface}")]
                for interface in interfaces]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id,
        "🌐 *اینترفیس وایرگارد را برای حذف کاربر انتخاب کنید:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CHOOSE_WG_INTERFACE



async def select_interface_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_interface = query.data.replace("peer_interface_", "") + ".conf"
    context.user_data["selected_interface"] = selected_interface

    await query.message.reply_text(
        "✏️ *نام کاربری که می‌خواهید حذف کنید را وارد کنید:* (از حروف فارسی استفاده نکنید)\n\n"
        "مثال: `azumi`",
        parse_mode="Markdown"
    )
    return ENTER_PEER_NAME

async def specify_peername_delete(update: Update, context: CallbackContext):
    peer_name = update.message.text.strip()
    if not re.match(r"^[a-zA-Z0-9_-]+$", peer_name): 
        await update.message.reply_text(
            "❌ فرمت نام کاربر اشتباه است، فقط از حروف و اعداد استفاده کنید."
        )
        return ENTER_PEER_NAME

    context.user_data["peer_name"] = peer_name

    selected_interface = context.user_data["selected_interface"]

    response = await api_stuff(f"api/get-peer-info?peerName={peer_name}&configFile={selected_interface}")
    if "error" in response:
        await update.message.reply_text(
            f"❌ خطا: `{response['error']}`\n\nلطفاً اطمینان حاصل کنید که نام کاربر در `{selected_interface}` وجود دارد.",
            parse_mode="Markdown"
        )
        return ENTER_PEER_NAME

    peer_info = response.get("peerInfo", {})
    context.user_data["peer_info"] = peer_info

    keyboard = [[InlineKeyboardButton("🗑️ حذف کاربر", callback_data="peer_confirm_delete")],
                [InlineKeyboardButton("🔙 بازگشت به انتخاب اینترفیس", callback_data="peer_back_to_interface")]]
    await update.message.reply_text(
        f"👤 *نام کاربر:* `{peer_name}`\n"
        f"🌍 *آدرس IP:* `{peer_info.get('peer_ip', 'Unknown')}`\n"
        f"📄 *فایل تنظیمات:* `{selected_interface}`\n\n"
        "⚠️ *آیا مطمئن هستید که می‌خواهید این کاربر را حذف کنید؟*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CONFIRM_PEER_DELETION



async def apply_peer_deletion(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "peer_confirm_delete":
        peer_name = context.user_data["peer_name"]
        selected_interface = context.user_data["selected_interface"]

        payload = {"peerName": peer_name, "configFile": selected_interface}
        response = await api_stuff("api/delete-peer", method="POST", data=payload)
        if "error" in response:
            await query.message.reply_text(f"❌ خطا: `{response['error']}`", parse_mode="Markdown")
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی کاربرها", callback_data="peers_menu")],
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            f"✅ *کاربر'{peer_name}' با موفقیت حذف شد!*\n\n"
            f"📄 فایل تنظیمات: `{selected_interface}`",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    elif query.data == "peer_back_to_interface":
        return await init_deletepeer(update, context)

    return ConversationHandler.END


async def download_peerconfig_create(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("_")
    if len(data_parts) < 3:
        await query.message.reply_text("❌ اطلاعات کافی برای دانلود تنظیمات وجود ندارد.", parse_mode="Markdown")
        return

    peer_name = "_".join(data_parts[2:])
    config_file = context.user_data.get("selected_config")

    if not config_file or not config_file.endswith(".conf"):
        await query.message.reply_text("❌ فایل تنظیمات وایرگارد پیدا نشد. لطفاً فرآیند را دوباره آغاز کنید.")
        return

    short_link = "N/A" 

    peer_details_url = f"{API_BASE_URL}/api/bot-peer-details-fa?peerName={peer_name}&configName={config_file}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(peer_details_url, headers={"Authorization": f"Bearer {API_KEY}"}) as details_response:
                if details_response.status == 200:
                    details_data = await details_response.json()

                    data_limit = details_data.get("limit", "N/A")
                    used_data = details_data.get("used", 0)
                    remaining_data = details_data.get("remaining", "N/A")
                    expiry_date_human = details_data.get("expiry_human", "N/A") 
                    expiry_date = details_data.get("expiry", "N/A")

                    print(f"Fetched peer details: Limit: {data_limit}, Used: {used_data}, Remaining: {remaining_data}, Expiry: {expiry_date}")

                else:
                    await query.message.reply_text(f"❌ خطا: {details_response.get('error', 'عدم توانایی در دریافت جزئیات کاربر')}")

            short_link_url = f"{API_BASE_URL}/api/get-peer-link?peerName={peer_name}&config={config_file}"
            async with session.get(short_link_url, headers={"Authorization": f"Bearer {API_KEY}"}) as link_response:
                if link_response.status == 200:
                    link_data = await link_response.json()
                    short_link = link_data.get("short_link", "N/A")
                else:
                    print(f"Couldn't retrieve short link. Status: {link_response.status}")

            config_url = f"{API_BASE_URL}/api/download-peer-config?peerName={peer_name}&config={config_file}"
            async with session.get(config_url, headers={"Authorization": f"Bearer {API_KEY}"}) as config_response:
                if config_response.status == 200:
                    peer_config = await config_response.text()

                    keyboard = [
                        [
                            InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu"),
                            InlineKeyboardButton("📋 لیست کاربران", callback_data="peers_menu"),
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    caption = (
                        f"فایل تنظیمات برای {peer_name}\n\n"
                        f"👤 *نام کاربری:* {peer_name}\n"
                        f"⏳ *تاریخ انقضا:* {expiry_date_human}\n"
                        f"📏 *میزان حجم:* {data_limit}\n"
                        f"📉 *حجم استفاده شده:* {used_data} B\n"
                        f"📥 *حجم باقی‌مانده:* {remaining_data} B\n\n"
                        f"🔗 * لینک کوتاه کانفیگ:*\n"
                        f"[{short_link}]({short_link})\n\n"
                        f"📄 *محتوای فایل تنظیمات:*\n"
                        f"```\n{peer_config}\n```"
                    )

                    await context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=BytesIO(peer_config.encode("utf-8")),
                        filename=f"{peer_name}.conf",
                        caption=caption,
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                else:
                    error = await config_response.json()
                    await query.message.reply_text(f"❌ خطا: {error.get('error', 'عدم توانایی در دریافت فایل تنظیمات')}")
        except Exception as e:
            await query.message.reply_text(f"❌ خطا: {str(e)}")

            




async def generate_peerqr_create(update, context):
    query = update.callback_query
    await query.answer()

    peer_name = query.data.replace("qr_create_", "").strip()

    selected_interface = context.user_data.get("selected_interface", "wg0")
    config_file = f"{selected_interface}.conf"

    if not config_file or not config_file.endswith(".conf"):
        await query.message.reply_text("❌ فایل تنظیمات وایرگارد یافت نشد. لطفاً فرآیند را دوباره شروع کنید.")
        return

    qr_url = f"{API_BASE_URL}/api/download-peer-qr?peerName={peer_name}&config={config_file}"
    config_url = f"{API_BASE_URL}/api/download-peer-config?peerName={peer_name}&config={config_file}"
    short_link_url = f"{API_BASE_URL}/api/get-peer-link?peerName={peer_name}&config={config_file}"
    peer_details_url = f"{API_BASE_URL}/api/bot-peer-details-fa?peerName={peer_name}&configName={config_file}"

    async with aiohttp.ClientSession() as session:
        try:
            data_limit, used_data, remaining_data, expiry_date_human, expiry_date = "N/A", 0, "N/A", "N/A", "N/A"

            async with session.get(peer_details_url, headers={"Authorization": f"Bearer {API_KEY}"}) as details_response:
                if details_response.status == 200:
                    details_data = await details_response.json()
                    data_limit = details_data.get("limit", "N/A")
                    used_data = details_data.get("used", 0)
                    remaining_data = details_data.get("remaining", "N/A")
                    expiry_date_human = details_data.get("expiry_human", "N/A") 
                    expiry_date = details_data.get("expiry", "N/A")
                else:
                    print(f"Couldn't retrieve peer details. Status: {details_response.status}")

            short_link = "N/A"
            async with session.get(short_link_url, headers={"Authorization": f"Bearer {API_KEY}"}) as link_response:
                if link_response.status == 200:
                    link_data = await link_response.json()
                    short_link = link_data.get("short_link", "N/A")
                else:
                    print(f"Couldn't retrieve short link. Status: {link_response.status}")

            async with session.get(qr_url, headers={"Authorization": f"Bearer {API_KEY}"}) as qr_response:
                if qr_response.status == 200:
                    qr_image = await qr_response.read()
                else:
                    error = await qr_response.json()
                    await query.message.reply_text(f"❌ خطا در دریافت QR Code: {error.get('error', 'نامشخص')}")
                    return

            async with session.get(config_url, headers={"Authorization": f"Bearer {API_KEY}"}) as config_response:
                if config_response.status == 200:
                    peer_config = await config_response.text()
                else:
                    error = await config_response.json()
                    await query.message.reply_text(f"❌ خطا در دریافت تنظیمات: {error.get('error', 'نامشخص')}")
                    return

            caption = (
                f"📷 کد QR برای کاربر `{peer_name}`\n\n"
                f"🔗 *لینک کوتاه کانفیگ:*\n"
                f"[{short_link}]({short_link})\n\n"
                f"👤 *نام کاربری:* {peer_name}\n"
                f"⏳ *تاریخ انقضا:* {expiry_date_human}\n"
                f"📏 *میزان حجم:* {data_limit}\n"
                f"📉 *حجم استفاده شده:* {used_data} B\n"
                f"📥 *حجم باقی‌مانده:* {remaining_data} B\n\n"
                f"برای کپی کردن تنظیمات، از متن زیر استفاده کنید:\n"
                f"```\n{peer_config}\n```"
            )

            keyboard = [
                [
                    InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu"),
                    InlineKeyboardButton("📋 لیست کاربران", callback_data="peers_menu"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=BytesIO(qr_image),
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception as e:
            await query.message.reply_text(f"❌ خطا: {str(e)}")



async def init_peer_create(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ شما مجاز به انجام این عملیات نیستید.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("➕ ایجاد یک کاربر", callback_data="mode_single")],
        [InlineKeyboardButton("➕➕ ایجاد چند کاربر (Bulk)", callback_data="mode_bulk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id,
        "📋 *انتخاب حالت ایجاد کاربر:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECT_MODE

async def select_mode(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    mode = query.data.replace("mode_", "")
    context.user_data["creation_mode"] = mode  

    response = await api_stuff("api/get-interfaces")
    
    if "error" in response:
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=f"❌ *خطا در دریافت اینترفیس‌ها:* {response['error']}",
                                       parse_mode="Markdown")
        return ConversationHandler.END

    interfaces = response.get("interfaces", [])
    if not interfaces:
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text="❌ *هیچ اینترفیسی یافت نشد.*",
                                       parse_mode="Markdown")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"📂 {interface}", callback_data=f"config_{interface}")]
                for interface in interfaces]
    await query.message.reply_text(
        "🌐 *یک اینترفیس وایرگارد انتخاب کنید:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_CONFIG

async def select_config(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_config = query.data.replace("config_", "") + ".conf"
    context.user_data["selected_config"] = selected_config

    response = await api_stuff(f"api/available-ips?config={selected_config}")
    if "error" in response:
        await query.message.reply_text(f"❌ *خطا در دریافت لیست آی‌پی‌های موجود:* {response['error']}", parse_mode="Markdown")
        return ConversationHandler.END

    available_ips = response.get("availableIps", [])[:5]
    if not available_ips:
        await query.message.reply_text("❌ *هیچ آی‌پی موجودی برای تنظیمات انتخابی پیدا نشد.*", parse_mode="Markdown")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"🌐 {ip}", callback_data=f"ip_{ip}")] for ip in available_ips]
    await query.message.reply_text(
        "🛠 *آدرس آی‌پی مورد نظر برای ایجاد پیر را انتخاب کنید:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_IP_ADDRESS

async def choose_ip(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_ip = query.data.replace("ip_", "")
    context.user_data["selected_ip"] = selected_ip

    mode = context.user_data.get("creation_mode", "single")
    if mode == "bulk":
        await query.message.reply_text(
            "📊 *تعداد کاربران مورد نظر برای ایجاد (حداکثر 50):*\n\n"
            "مثال: `5`",
            parse_mode="Markdown"
        )
        return INPUT_BULK_COUNT
    else:
        await query.message.reply_text(
            "✏️ *نام کاربر را وارد کنید:* (از حروف فارسی استفاده نکنید)\n\n"
            "مثال: `azumi`",
            parse_mode="Markdown"
        )
        return INPUT_PEER_NAME

async def write_bulk_count(update: Update, context: CallbackContext):
    count_text = update.message.text.strip()
    if not count_text.isdigit() or not (1 <= int(count_text) <= 50):
        await update.message.reply_text("❌ مقدار نادرست است. لطفاً یک عدد بین 1 تا 50 وارد کنید.")
        return INPUT_BULK_COUNT

    context.user_data["bulk_count"] = int(count_text)
    await update.message.reply_text(
        "✏️ *نام کاربر را وارد کنید:* (از حروف فارسی استفاده نکنید)\n\n"
        "مثال: `azumi`",
        parse_mode="Markdown"
    )
    return INPUT_PEER_NAME

async def input_peer_name(update: Update, context: CallbackContext):
    peer_name = update.message.text.strip()
    if not re.match(r"^[a-zA-Z0-9_-]+$", peer_name):
        await update.message.reply_text("❌ نام کاربر نادرست است. فقط از حروف و اعداد استفاده کنید.")
        return INPUT_PEER_NAME

    context.user_data["peer_name"] = peer_name

    keyboard = [[InlineKeyboardButton("🧮 MiB", callback_data="unit_MiB")],
                [InlineKeyboardButton("📊 GiB", callback_data="unit_GiB")]]
    await update.message.reply_text(
        "📐 *واحد محدودیت حجم را انتخاب کنید:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_LIMIT_UNIT

async def choose_limit_unit(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    context.user_data["limit_unit"] = query.data.replace("unit_", "")

    await query.message.reply_text(
        "📏 *مقدار محدودیت حجم را وارد کنید:*\n\n"
        "مثال: `500`",
        parse_mode="Markdown"
    )
    return INPUT_LIMIT_VALUE

async def choose_limit_value(update: Update, context: CallbackContext):
    value = update.message.text.strip()
    if not value.isdigit() or not (0 < int(value) <= 1024):
        await update.message.reply_text("❌ مقدار نادرست است. لطفاً عددی بین 1 تا 1024 وارد کنید.")
        return INPUT_LIMIT_VALUE

    context.user_data["data_limit"] = f"{value}{context.user_data['limit_unit']}"

    keyboard = [[InlineKeyboardButton("🌍 1.1.1.1", callback_data="dns_1.1.1.1")],
                [InlineKeyboardButton("🌎 8.8.8.8", callback_data="dns_8.8.8.8")],
                [InlineKeyboardButton("✏️ سفارشی", callback_data="dns_custom")]]
    await update.message.reply_text(
        "🌐 *یک DNS سرور انتخاب کنید یا گزینه سفارشی را انتخاب کنید:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_DNS

async def select_dns(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "dns_custom":
        await query.message.reply_text(
            "✏️ *آدرس‌های DNS کاستوم را وارد کنید (با کاما جدا کنید):*\n\n"
            "مثال: `8.8.8.8,1.1.1.1`",
            parse_mode="Markdown"
        )
        return INPUT_CUSTOM_DNS

    context.user_data["dns"] = query.data.replace("dns_", "")
    await query.message.reply_text(
        "⏳ *تعداد روز‌ها:* (مثال: `10`)",
        parse_mode="Markdown"
    )
    return INPUT_EXPIRY_DAYS

async def write_custom_dns(update: Update, context: CallbackContext):
    dns = update.message.text.strip()
    if not all(
        re.match(r"^\d{1,3}(\.\d{1,3}){3}$", entry) or re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", entry)
        for entry in dns.split(",")
    ):
        await update.message.reply_text("❌ فرمت DNS نادرست است. لطفاً آدرس‌های IP معتبر یا نام دامنه وارد کنید.")
        return INPUT_CUSTOM_DNS

    context.user_data["dns"] = dns
    await update.message.reply_text(
        "⏳ *تعداد روز‌ها:* (مثال: `10`)",
        parse_mode="Markdown"
    )
    return INPUT_EXPIRY_DAYS

async def write_expiry_days(update: Update, context: CallbackContext):
    days_text = update.message.text.strip()
    if not days_text.isdigit() or int(days_text) < 0:
        await update.message.reply_text("❌ مقدار نادرست است. لطفاً یک عدد غیرمنفی وارد کنید.")
        return INPUT_EXPIRY_DAYS

    context.user_data["expiry_days"] = int(days_text)
    
    await update.message.reply_text(
        "⏳ *مقدار MTU را وارد کنید (اختیاری، پیش‌فرض: `1280`):*\n\n"
        "مثال: `1400`",
        parse_mode="Markdown"
    )
    return INPUT_MTU

async def write_mtu(update: Update, context: CallbackContext):
    mtu_value = update.message.text.strip()

    if mtu_value and not mtu_value.isdigit():
        await update.message.reply_text("❌ مقدار MTU نادرست است. لطفاً عددی وارد کنید.")
        return INPUT_MTU

    context.user_data["mtu"] = int(mtu_value) if mtu_value else 1280

    await update.message.reply_text(
        "⏳ *مقدار Persistent Keepalive را وارد کنید (پیش‌فرض: `25`):*\n\n"
        "مثال: `25`",
        parse_mode="Markdown"
    )
    return INPUT_KEEPALIVE

async def write_keepalive(update: Update, context: CallbackContext):
    keepalive_value = update.message.text.strip()
    if keepalive_value and not keepalive_value.isdigit():
        await update.message.reply_text("❌ مقدار Persistent Keepalive نادرست است. لطفاً عددی وارد کنید.")
        return INPUT_KEEPALIVE

    context.user_data["persistent_keepalive"] = int(keepalive_value) if keepalive_value else 25

    keyboard = [
        [InlineKeyboardButton("✅ بله", callback_data="confirm_usage_yes")],
        [InlineKeyboardButton("❌ خیر", callback_data="confirm_usage_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🟢 *فعال کردن 'شروع تاریخ پس از اتصال اول'؟*\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CONFIRM_USAGE

async def confirm_use(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    first_usage = query.data == "confirm_usage_yes"
    context.user_data["first_usage"] = first_usage

    mtu = context.user_data.get("mtu", 1280)
    persistent_keepalive = context.user_data.get("persistent_keepalive", 25)

    expiry_days = context.user_data.get("expiry_days", 0)

    payload = {
        "peerName": context.user_data["peer_name"],
        "peerIp": context.user_data["selected_ip"],
        "dataLimit": context.user_data["data_limit"],
        "configFile": context.user_data["selected_config"],
        "dns": context.user_data["dns"],
        "expiryDays": expiry_days,
        "firstUsage": first_usage,
        "persistentKeepalive": persistent_keepalive,
        "mtu": mtu
    }

    creation_mode = context.user_data.get("creation_mode", "single")
    if creation_mode == "bulk":
        payload["bulkCount"] = context.user_data.get("bulk_count", 1)

    response = await api_stuff("api/create-peer", method="POST", data=payload)
    if "error" in response:
        await query.message.reply_text(f"❌ خطا: {response['error']}", parse_mode="Markdown")
        return ConversationHandler.END

    if creation_mode == "single":
        peer_name = response.get("peer_name", context.user_data["peer_name"])
        short_link = response.get("short_link", "N/A")

        keyboard = [
            [
                InlineKeyboardButton(
                    "📂 دانلود تنظیمات",
                    callback_data=f"download_general_{peer_name}"
                ),
                InlineKeyboardButton(
                    "📷 دریافت کد QR",
                    callback_data=f"qr_general_{peer_name}"
                )
            ],
            [
                InlineKeyboardButton("🔙 بازگشت به منوی کاربران", callback_data="peers_menu"),
                InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            f"✅ *کاربر '{peer_name}' با موفقیت ایجاد شد!* \n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 *Peer Name:* {peer_name}\n"
            f"📂 *Config File Name:* {payload['configFile']}\n"
            f"🌐 *IP Address:* {payload['peerIp']}\n"
            f"📏 *Data Limit:* {payload['dataLimit']}\n"
            f"⏳ *Expiry Time:* {expiry_days} days\n"
            f"📡 *MTU:* {payload['mtu']}\n"
            f"🛜 *DNS:* {payload['dns']}\n"
            f"🟢 *Start Date After First Connection:* {'Enabled 🟢' if first_usage else 'Disabled 🔴'}\n"
            f"🌐 *Persistent Keepalive:* {persistent_keepalive}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"برای دانلود فایل تنظیمات یا دریافت کد QR، از دکمه‌های زیر استفاده کنید:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    elif creation_mode == "bulk":
        peers = response.get("peers", [])
        if not peers:
            await query.message.reply_text("❌ خطا در ایجاد کاربران به صورت گروهی.", parse_mode="Markdown")
            return ConversationHandler.END

        message = f"✅ *{len(peers)} کاربر با موفقیت ایجاد شدند!*"

        await query.message.reply_text(
            message,
            parse_mode="Markdown"
        )

        for peer in peers:
            peer_name = peer.get("peer_name")
            short_link = peer.get("short_link", "N/A")

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📂 دانلود تنظیمات",
                        callback_data=f"download_general_{peer_name}"
                    ),
                    InlineKeyboardButton(
                        "📷 دریافت کد QR",
                        callback_data=f"qr_general_{peer_name}"
                    )
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(
                f"🔹 *نام پیره:* {peer_name}\n"
                f"🔗 *لینک کوتاه کانفیگ:* [{short_link}]({short_link})",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        navigation_keyboard = [
            [
                InlineKeyboardButton("🔙 بازگشت به منوی کاربران", callback_data="peers_menu"),
                InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")
            ]
        ]

        navigation_reply_markup = InlineKeyboardMarkup(navigation_keyboard)

        await query.message.reply_text(
            "🔄 *برای مدیریت بیشتر کاربران، از دکمه‌های زیر استفاده کنید:*",
            parse_mode="Markdown",
            reply_markup=navigation_reply_markup
        )

    return ConversationHandler.END





async def init_resetpeer(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return
    response = await api_stuff("api/get-interfaces")
    
    if "error" in response:
        await context.bot.send_message(chat_id, f"❌ خطا در دریافت اینترفیس‌ها: `{response['error']}`", parse_mode="Markdown")
        return ConversationHandler.END

    interfaces = response.get("interfaces", [])
    if not interfaces:
        await context.bot.send_message(chat_id, "❌ *هیچ اینترفیسی یافت نشد.*", parse_mode="Markdown")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"📂 {interface}", callback_data=f"reset_interface_{interface}")]
                for interface in interfaces]
    await context.bot.send_message(
        chat_id,
        "🌐 *یک اینترفیس وایرگارد را برای ریست ترافیک یا انقضا انتخاب کنید:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_RESET_INTERFACE


async def select_reset_interface(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_interface = query.data.replace("reset_interface_", "") + ".conf"
    context.user_data["selected_reset_interface"] = selected_interface

    await query.message.reply_text(
        "✏️ *نام کاربری که می‌خواهید ترافیک یا انقضای آن را ریست کنید وارد کنید:* (از حروف فارسی استفاده نکنید)\n\n"
        "مثال: `azumi`",
        parse_mode="Markdown"
    )
    return ENTER_RESET_PEER_NAME


async def reset_peername(update: Update, context: CallbackContext):
    peer_name = update.message.text.strip()
    if not re.match(r"^[a-zA-Z0-9_-]+$", peer_name):
        await update.message.reply_text(
            "❌ نام کاربر نادرست است. فقط از حروف و اعداد استفاده کنید."
        )
        return ENTER_RESET_PEER_NAME

    context.user_data["reset_peer_name"] = peer_name
    selected_interface = context.user_data["selected_reset_interface"]
    try:
        response = await api_stuff(f"api/get-peer-info?peerName={peer_name}&configFile={selected_interface}")
    except Exception as e:
        await update.message.reply_text(
            f"❌ *خطا در دریافت اطلاعات کاربر:*\n`{e}`",
            parse_mode="Markdown"
        )
        return ENTER_RESET_PEER_NAME

    if "error" in response:
        await update.message.reply_text(
            f"❌ *خطا:* `{response['error']}`\n\nاطمینان حاصل کنید که نام کاربر در `{selected_interface}` موجود است.",
            parse_mode="Markdown"
        )
        return ENTER_RESET_PEER_NAME

    peer_info = response.get("peerInfo", {})
    context.user_data["reset_peer_info"] = peer_info
    traffic_used = peer_info.get("used", "نامشخص")
    traffic_limit = peer_info.get("limit", "نامشخص")
    expiry = peer_info.get("remaining_time", "نامشخص")

    keyboard = [
        [InlineKeyboardButton("🔄 ریست ترافیک", callback_data="reset_traffic")],
        [InlineKeyboardButton("⏳ ریست انقضا", callback_data="reset_expiry")],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب اینترفیس", callback_data="back_to_reset_interface")]
    ]
    await update.message.reply_text(
        f"👤 *نام کاربر:* `{peer_name}`\n"
        f"📊 *ترافیک مصرف شده:* `{traffic_used}` / `{traffic_limit}`\n"
        f"⏳ *زمان باقی‌مانده:* `{expiry} دقیقه`\n\n"
        "⚙️ *یک عملیات را انتخاب کنید:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SHOW_PEER_INFO


async def reset_action(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    peer_name = context.user_data["reset_peer_name"]
    selected_interface = context.user_data["selected_reset_interface"]

    if query.data == "reset_traffic":
        payload = {"peerName": peer_name, "config": selected_interface}
        response = await api_stuff("api/reset-traffic", method="POST", data=payload)
        if "error" in response:
            await query.message.reply_text(
                f"❌ خطا در ریست ترافیک: `{response['error']}`", parse_mode="Markdown"
            )
            return ConversationHandler.END

        await query.message.reply_text(
            f"✅ *ترافیک برای کاربر '{peer_name}' با موفقیت ریست شد!*", parse_mode="Markdown"
        )

    elif query.data == "reset_expiry":
        payload = {"peerName": peer_name, "config": selected_interface}
        response = await api_stuff("api/reset-expiry", method="POST", data=payload)
        if "error" in response:
            await query.message.reply_text(
                f"❌ خطا در ریست زمان انقضا: `{response['error']}`", parse_mode="Markdown"
            )
            return ConversationHandler.END

        await query.message.reply_text(
            f"✅ *زمان انقضا برای کاربر '{peer_name}' با موفقیت ریست شد!*", parse_mode="Markdown"
        )

    keyboard = [
        [InlineKeyboardButton("🔄 ریست ترافیک", callback_data="reset_traffic")],
        [InlineKeyboardButton("🔄 ریست زمان انقضا", callback_data="reset_expiry")],
        [InlineKeyboardButton("🔙 بازگشت به منوی کاربران", callback_data="peers_menu")],
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"🎉 *عملیات برای کاربر '{peer_name}' انجام شد!*\n\n"
        "لطفاً عملیات دیگری را انتخاب کنید یا به منوی کاربران یا منوی اصلی بازگردید:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

    return SHOW_PEER_INFO  


async def edit_peer_init(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return

    response = await api_stuff("api/get-interfaces")
    if "error" in response:
        await context.bot.send_message(chat_id, text=f"❌ خطا در دریافت اینترفیس‌ها: {response['error']}")
        return ConversationHandler.END

    interfaces = response.get("interfaces", [])
    if not interfaces:
        await context.bot.send_message(chat_id, text="❌ *هیچ اینترفیسی یافت نشد.*")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(interface, callback_data=f"edit_select_interface_{interface}")] for interface in interfaces]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, text="🌐 *اینترفیس وایرگارد را انتخاب کنید:*", reply_markup=reply_markup)
    return STATE_SELECT_INTERFACE


async def edit_select_interface(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_interface = query.data.replace("edit_select_interface_", "")
    context.user_data["selected_interface"] = selected_interface

    response = await api_stuff(f"api/peers-by-interface?interface={selected_interface}")
    if "error" in response:
        await query.message.reply_text(f"❌ خطا در دریافت کاربران: {response['error']}")
        return ConversationHandler.END

    peers = response.get("peers", [])
    if not peers:
        await query.message.reply_text(f"هیچ کاربری برای اینترفیس **{selected_interface}** یافت نشد.")
        return ConversationHandler.END
    displayed_peers = peers[:5]
    keyboard = [[InlineKeyboardButton(peer["peer_name"], callback_data=f"edit_{peer['peer_name']}")] for peer in displayed_peers]
    keyboard.append([InlineKeyboardButton("🔍 جستجوی کاربر بر اساس نام", callback_data="search_peer_name")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "یک کاربر را برای ویرایش انتخاب کنید یا نام کاربر را جستجو کنید:",
        reply_markup=reply_markup
    )
    return STATE_SELECT_PEER_OR_SEARCH


async def search_peername(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "✏️ *نام کاربری که می‌خواهید ترافیک یا انقضای آن را ریست کنید وارد کنید:* (از حروف فارسی استفاده نکنید)\n\n"
        "مثال: `azumi`",
        parse_mode="Markdown"
    )
    return STATE_SEARCH_PEER


async def filter_peersname(update: Update, context: CallbackContext):
    peer_name = update.message.text.strip()
    selected_interface = context.user_data.get("selected_interface")

    response = await api_stuff(f"api/peers-by-interface?interface={selected_interface}")
    if "error" in response:
        await update.message.reply_text(f"❌ خطا در دریافت کاربران: {response['error']}")
        return ConversationHandler.END

    peers = response.get("peers", [])
    matched_peers = [peer for peer in peers if peer_name.lower() in peer["peer_name"].lower()]

    if not matched_peers:
        await update.message.reply_text(f"هیچ کاربری مطابق با **{peer_name}** یافت نشد.")
        return STATE_SEARCH_PEER

    keyboard = [[InlineKeyboardButton(peer["peer_name"], callback_data=f"edit_{peer['peer_name']}")] for peer in matched_peers]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("یک کاربر برای ویرایش انتخاب کنید:", reply_markup=reply_markup)
    return STATE_SELECT_PEER_TO_EDIT


async def select_peer_to_edit(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_peer = query.data.replace("edit_", "")
    context.user_data["selected_peer"] = selected_peer

    selected_interface = context.user_data["selected_interface"]
    response = await api_stuff(f"api/peers-by-interface?interface={selected_interface}")
    peers = response.get("peers", [])
    peer_data = next((peer for peer in peers if peer["peer_name"] == selected_peer), None)

    if not peer_data:
        await query.message.reply_text(f"❌ کاربر یافت نشد: {selected_peer}")
        return ConversationHandler.END

    context.user_data["selected_peer_data"] = peer_data
    current_limit = peer_data.get("limit", "نامشخص")
    expiry_time = peer_data.get("expiry_time", {})
    current_expiry = (
        f"{expiry_time.get('days', 0)} روز, {expiry_time.get('months', 0)} ماه, "
        f"{expiry_time.get('hours', 0)} ساعت, {expiry_time.get('minutes', 0)} دقیقه"
    )

    peer_name = peer_data.get("peer_name", "کاربر بدون نام")
    interface_name = selected_interface

    keyboard = [
        [InlineKeyboardButton("📝 ویرایش محدودیت حجم", callback_data="edit_data_limit")],
        [InlineKeyboardButton("🌐 ویرایش DNS", callback_data="edit_dns")],
        [InlineKeyboardButton("⏳ ویرایش زمان انقضا", callback_data="edit_expiry_time")],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب اینترفیس", callback_data="edit_peer")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"🔷 **جزئیات اکنون کاربر** 🔷\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 **نام کاربر:** `{peer_name}`\n"
        f"🌐 **اینترفیس:** `{interface_name}`\n"
        f"📦 **محدودیت حجم:** `{current_limit}`\n"
        f"⏳ **زمان انقضا:** `{current_expiry}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return STATE_EDIT_OPTION


async def edit_data_limit(update: Update, context: CallbackContext):
    await update.callback_query.answer()

    peer_data = context.user_data.get("selected_peer_data", {})
    current_data_limit = peer_data.get("limit", "نامشخص")

    await update.callback_query.message.reply_text(
        f"محدودیت حجم فعلی: **{current_data_limit}**\n"
        "✏️ محدودیت حجم جدید را برای کاربر وارد کنید (مثال: `500MiB` یا `1GiB`):",
        parse_mode="Markdown"
    )
    return STATE_SET_DATA_LIMIT


async def set_data_limit(update: Update, context: CallbackContext):
    data_limit = update.message.text.strip()
    if not re.match(r"^\d+(MiB|GiB)$", data_limit):
        await update.message.reply_text("❌ فرمت محدودیت حجم نادرست است. از `500MiB` یا `1GiB` استفاده کنید.")
        return STATE_SET_DATA_LIMIT

    context.user_data["new_data_limit"] = data_limit
    await update.message.reply_text("محدودیت حجم به‌روزرسانی شد. در حال ذخیره تغییرات...")
    await save_peer_changes(update, context)
    return ConversationHandler.END


async def edit_dns(update: Update, context: CallbackContext):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "✏️ *لطفاً آدرس های جدید DNS را وارد نمایید:*",
            parse_mode="Markdown"
        )
        return STATE_SET_DNS

    if update.message:
        dns = update.message.text.strip()
        context.user_data["new_dns"] = dns

        await update.message.reply_text("آدرس DNS به روز رسانی شد")
        await save_peer_changes(update, context)
        return ConversationHandler.END



async def edit_expiry_time(update: Update, context: CallbackContext):
    await update.callback_query.answer()

    peer_data = context.user_data.get("selected_peer_data", {})
    expiry_time = peer_data.get("expiry_time", {})
    current_expiry = (
        f"{expiry_time.get('days', 0)} روز, {expiry_time.get('months', 0)} ماه, "
        f"{expiry_time.get('hours', 0)} ساعت, {expiry_time.get('minutes', 0)} دقیقه"
    )

    await update.callback_query.message.reply_text(
        f"زمان انقضای فعلی: **{current_expiry}**\n"
        "✏️ زمان انقضای جدید را به روز وارد کنید (مثال: `10`):",
        parse_mode="Markdown"
    )
    return STATE_SET_EXPIRY_TIME


async def set_expiry_time(update: Update, context: CallbackContext):
    expiry_days = update.message.text.strip()
    if not expiry_days.isdigit() or int(expiry_days) <= 0:
        await update.message.reply_text("❌ مقدار نادرست است. لطفاً یک عدد مثبت برای روزها وارد کنید.")
        return STATE_SET_EXPIRY_TIME

    context.user_data["new_expiry_days"] = int(expiry_days)
    await update.message.reply_text("زمان انقضا به‌روزرسانی شد. در حال ذخیره تغییرات...")
    await save_peer_changes(update, context)
    return ConversationHandler.END


async def save_peer_changes(update: Update, context: CallbackContext):
    peer_name = context.user_data["selected_peer"]
    selected_interface = context.user_data["selected_interface"]
    new_expiry_days = context.user_data.get("new_expiry_days", 0)
    peer_data = context.user_data.get("selected_peer_data", {})
    expiry_time = peer_data.get("expiry_time", {})
    expiry_time["days"] = new_expiry_days

    payload = {
        "peerName": peer_name,
        "dataLimit": context.user_data.get("new_data_limit"),
        "dns": context.user_data.get("new_dns"),
        "expiryDays": new_expiry_days,
        "expiryMonths": expiry_time.get("months", 0),
        "expiryHours": expiry_time.get("hours", 0),
        "expiryMinutes": expiry_time.get("minutes", 0),
        "configFile": f"{selected_interface}.conf",  
    }

    payload = {key: value for key, value in payload.items() if value is not None}
    print(f"Sending API request with payload: {payload}")

    response = await api_stuff("api/edit-peer", method="POST", data=payload)
    if "error" in response:
        await update.message.reply_text(f"❌ خطا در ذخیره تغییرات: {response['error']}")
    else:
        await update.message.reply_text("✅ کاربر با موفقیت به‌روزرسانی شد!")

        keyboard = [[InlineKeyboardButton("🔙 بازگشت به لیست کاربران", callback_data="peers_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("عملیات بعدی خود را انتخاب کنید:", reply_markup=reply_markup)



async def block_unblock_peer(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return
    config_dir = "/etc/wireguard/" 

    try:
        configs = [f for f in os.listdir(config_dir) if f.endswith(".conf")]
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ خطا در دریافت فایل‌های کانفیگ: {e}",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    if not configs:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ فایل کانفیگ یافت نشد.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(config, callback_data=f"select_config:{config}")]
        for config in configs
    ]
    keyboard.append(
        [InlineKeyboardButton("🔙 بازگشت به منوی کاربرها", callback_data="peers_menu")]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "🔒 **مسدود/بازکردن کاربر**\n\n"
        "لطفاً **اینترفیس وایرگارد** که می‌خواهید مدیریت کنید را انتخاب کنید: 🌐"
    )
    await context.bot.send_message(
        chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return SELECT_CONFIG_DYNAMIC

async def select_config_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("select_config:"):
        config_name = data.split("select_config:")[1]
        context.user_data["config_name"] = config_name

        message = (
            "🔒 **مسدود/بازکردن کاربر**\n\n"
            "لطفاً **نام** کاربری را که می‌خواهید مسدود یا باز کنید وارد کنید:"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به اینترفیس ها", callback_data="block_unblock_peer")],
            [InlineKeyboardButton("🔙 بازگشت به منوی کاربرها", callback_data="peers_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )
        return SELECT_PEER
    elif data == "peers_menu":
        return await peers_menu(update, context)
    else:
        await query.message.reply_text("❌ انتخاب نامعتبر.")
        return ConversationHandler.END

async def fetch_config(update: Update, context: CallbackContext):
    peer_name = update.message.text.strip()
    if not re.match(r"^[a-zA-Z0-9_-]+$", peer_name):
        await update.message.reply_text("❌ نام کاربر نامعتبر است. لطفاً دوباره تلاش کنید:")
        return SELECT_PEER

    config_name = context.user_data.get("config_name")
    if not config_name:
        await update.message.reply_text("❌ هیچ تنظیماتی انتخاب نشده است. لطفاً دوباره شروع کنید.")
        return ConversationHandler.END

    response = await api_stuff(f"api/peers?config={config_name}&page=1&limit=50")

    if "error" in response:
        await update.message.reply_text(f"❌ خطا در دریافت کاربرها: {response['error']}")
        return ConversationHandler.END

    peers = response.get("peers", [])
    matched_peer = next(
        (peer for peer in peers if peer.get("peer_name") == peer_name), None
    )

    if not matched_peer:
        await update.message.reply_text(
            "❌ کاربر یافت نشد. لطفاً نام معتبری وارد کنید:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔙 بازگشت به اینترفیس‌ها", callback_data="block_unblock_peer")],
                    [InlineKeyboardButton("🔙 بازگشت به منوی کاربرها", callback_data="peers_menu")],
                ]
            ),
            parse_mode="Markdown",
        )
        return SELECT_PEER

    context.user_data["matched_peer"] = matched_peer

    is_monitor_blocked = matched_peer.get("monitor_blocked", False)
    is_expiry_blocked = matched_peer.get("expiry_blocked", False)
    is_blocked = is_monitor_blocked or is_expiry_blocked  
    status = "مسدود شده" if is_blocked else "غیرمسدود"

    message = (
        f"🔒 **مسدود کردن/رفع مسدودی کاربر**\n\n"
        f"📛 <b>نام کاربر:</b> {peer_name}\n"
        f"⚡ <b>وضعیت فعلی:</b> {status}\n\n"
        f"آیا مایل به تغییر وضعیت هستید؟"
    )
    keyboard = [
        [InlineKeyboardButton("✅ بله", callback_data="toggle_status")],
        [InlineKeyboardButton("❌ خیر", callback_data="peers_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        message, reply_markup=reply_markup, parse_mode="HTML"
    )
    return TOGGLE_BLOCK


async def toggle_block_status(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    matched_peer = context.user_data.get("matched_peer")
    config_name = context.user_data.get("config_name")
    if not matched_peer or not config_name:
        await query.message.reply_text("❌ داده‌ها ناقص هستند. لطفاً دوباره شروع کنید.")
        return ConversationHandler.END

    is_blocked = matched_peer.get("monitor_blocked", False) or matched_peer.get("expiry_blocked", False)

    new_status = not is_blocked

    if matched_peer.get("monitor_blocked", False):
        matched_peer["monitor_blocked"] = new_status
    if matched_peer.get("expiry_blocked", False):
        matched_peer["expiry_blocked"] = new_status

    data = {
        "peerName": matched_peer["peer_name"],
        "blocked": new_status,
        "config": config_name,
    }

    response = await api_stuff("api/toggle-peer", method="POST", data=data)

    if "error" in response:
        await query.message.reply_text(f"❌ خطا در تغییر وضعیت کاربر: {response['error']}")
        return ConversationHandler.END

    context.user_data["matched_peer"] = matched_peer

    status = "مسدود شده" if new_status else "غیرمسدود"
    message = (
        f"🔒 **نام کاربر:** {matched_peer['peer_name']}\n"
        f"⚡ **وضعیت جدید:** {status}\n\n"
        "✅ وضعیت کاربر با موفقیت به‌روزرسانی شد!"
    )
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی کاربرها", callback_data="peers_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        message, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return ConversationHandler.END



async def peer_status_mnu(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ You are not authorized to perform this action.",
            parse_mode="Markdown"
        )
        return
    response = await api_stuff("api/get-interfaces")

    if "error" in response:
        await context.bot.send_message(chat_id, f"❌ خطا در دریافت اینترفیس‌ها: `{response['error']}`", parse_mode="Markdown")
        return ConversationHandler.END

    interfaces = response.get("interfaces", [])
    if not interfaces:
        await context.bot.send_message(chat_id, "❌ *هیچ اینترفیسی برای وایرگارد یافت نشد.*", parse_mode="Markdown")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"📂 {interface}", callback_data=f"status_interface_{interface}")]
                for interface in interfaces]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی کاربران", callback_data="peers_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id,
        "🌐 *یک اینترفیس وایرگارد را برای مشاهده وضعیت کاربران انتخاب کنید:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CHOOSE_INTERFACE_STATUS


async def init_status_interface(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_interface = query.data.replace("status_interface_", "") + ".conf"
    context.user_data["selected_status_interface"] = selected_interface

    await query.message.reply_text(
        "✏️ *نام کاربری که می‌خواهید وضعیت آن را بررسی کنید وارد کنید:* (از حروف فارسی استفاده نکنید)\n\n"
        "مثال: `azumi`",
        parse_mode="Markdown"
    )
    return INPUT_PEER_NAME_STATUS


async def obtain_peer_status(update: Update, context: CallbackContext):
    peer_name = update.message.text.strip()
    selected_interface = context.user_data["selected_status_interface"]

    if not peer_name:
        await update.message.reply_text("❌ نام کاربر نمی‌تواند خالی باشد. لطفاً یک نام معتبر وارد کنید:")
        return INPUT_PEER_NAME_STATUS

    try:
        response = await api_stuff(f"api/peers?config={selected_interface}&fetch_all=true")

        if "error" in response:
            await update.message.reply_text(f"❌ خطا در دریافت کاربران: {response['error']}")
            return INPUT_PEER_NAME_STATUS

        peers = response.get("peers", [])

        matched_peers = [
            peer for peer in peers if peer_name.lower() == peer.get("peer_name", "").lower()
        ]

        if not matched_peers:
            await update.message.reply_text(f"❌ هیچ کاربری با نام **{peer_name}** یافت نشد.")
            return INPUT_PEER_NAME_STATUS

        messages = []
        for peer in matched_peers:
            remaining_minutes = peer.get("remaining_time", 0)
            if remaining_minutes > 0:
                days = remaining_minutes // 1440
                hours = (remaining_minutes % 1440) // 60
                minutes = remaining_minutes % 60
                remaining_human = f"{days} روز, {hours} ساعت, {minutes} دقیقه"
            else:
                remaining_human = "منقضی شده"

            peer_details = (
                f"🎛 **اطلاعات کاربر**\n\n"
                f"📛 **نام کاربر:** `{peer['peer_name']}`\n"
                f"🌐 **آی‌پی کاربر:** `{peer['peer_ip']}`\n"
                f"🔑 **کلید عمومی:** `{peer['public_key']}`\n"
                f"📊 **محدودیت حجم:** `{peer['limit']}`\n"
                f"📡 **حجم باقی مانده:** `{peer['remaining_human']}`\n"
                f"🕒 **زمان انقضا:** {peer['expiry_time']['days']} روز, "
                f"{peer['expiry_time']['hours']} ساعت, {peer['expiry_time']['minutes']} دقیقه\n"
                f"⏳ **زمان باقی مانده:** {remaining_human}\n"
                f"⚡ **وضعیت:** {'🟢 فعال' if not peer['expiry_blocked'] else '🔴 بلاک شده'}\n"
            )
            messages.append(peer_details)

        for msg in messages:
            await update.message.reply_text(msg, parse_mode="Markdown")

        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی کاربران", callback_data="peers_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("بازگشت به منوی کاربران:", reply_markup=reply_markup)

        return ConversationHandler.END

    except Exception as e:
        print(f"خطا در وضعیت کاربر: {e}")
        await update.message.reply_text("❌ خطایی در دریافت وضعیت کاربر رخ داد.")
        return INPUT_PEER_NAME_STATUS



async def mnu_back(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "main_menu":
        return await start(update, context) 
    elif query.data == "backups_menu":
        return await backups_menu(update, context)  
    elif query.data == "peers_menu":
        await peers_menu(update, context)  
        return ConversationHandler.END 
    else:
        return await start(update, context)  

 

def main():

    application = (
    ApplicationBuilder()
    .token(TELEGRAM_BOT_TOKEN)
    .connect_timeout(30.0)  
    .read_timeout(30.0)     
    .build()
)
    application.bot_data = {"notifications_enabled": True} 

    block_unblock_stuff = ConversationHandler(
    entry_points=[CallbackQueryHandler(block_unblock_peer, pattern="block_unblock_peer")],
    states={
        SELECT_CONFIG_DYNAMIC: [
            CallbackQueryHandler(select_config_handler, pattern="^select_config:"),
            CallbackQueryHandler(peers_menu, pattern="peers_menu"),
        ],
        SELECT_PEER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_config),
            CallbackQueryHandler(block_unblock_peer, pattern="block_unblock_peer"),
            CallbackQueryHandler(peers_menu, pattern="peers_menu"),
        ],
        TOGGLE_BLOCK: [
            CallbackQueryHandler(toggle_block_status, pattern="toggle_status"),
            CallbackQueryHandler(peers_menu, pattern="peers_menu"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(peers_menu, pattern="peers_menu")
    ],
    allow_reentry=True,
)
    stuff_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(download_qr_menu, pattern="download_qr_menu")],
    states={
        SELECT_PEER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, peername_search)],
        SELECT_INTERFACE: [CallbackQueryHandler(interface_select, pattern="^select_interface_.*$")],
        VIEW_PEER_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, peername_search)], 
        ConversationHandler.END: [CallbackQueryHandler(peer_decision, pattern="^(download|qr)_.*")]
    },
    fallbacks=[CallbackQueryHandler(peers_menu, pattern="main_menu")],
    allow_reentry=True,
)

    peer_creation_stuff = ConversationHandler(
    entry_points=[CallbackQueryHandler(init_peer_create, pattern="create_peer")],
    states={
        SELECT_MODE: [CallbackQueryHandler(select_mode, pattern="mode_.*")],
        SELECT_CONFIG: [CallbackQueryHandler(select_config, pattern="config_.*")],
        SELECT_IP_ADDRESS: [CallbackQueryHandler(choose_ip, pattern="ip_.*")],
        INPUT_BULK_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_bulk_count)],
        INPUT_PEER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_peer_name)],
        SELECT_LIMIT_UNIT: [CallbackQueryHandler(choose_limit_unit, pattern="unit_.*")],
        INPUT_LIMIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_limit_value)],
        SELECT_DNS: [CallbackQueryHandler(select_dns, pattern="dns_.*")],
        INPUT_CUSTOM_DNS: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_custom_dns)],
        INPUT_EXPIRY_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_expiry_days)],
        INPUT_MTU: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_mtu)],
        INPUT_KEEPALIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_keepalive)],  
        CONFIRM_USAGE: [CallbackQueryHandler(confirm_use, pattern="confirm_usage_.*")],
        ConversationHandler.END: [
            CallbackQueryHandler(download_peerconfig_general, pattern="download_general_.*"),
            CallbackQueryHandler(generate_peerqr_general, pattern="qr_general_.*")
        ]
    },
    fallbacks=[],
    allow_reentry=True,
)

    
    peer_edit_stuff = ConversationHandler(
    entry_points=[CallbackQueryHandler(edit_peer_init, pattern="edit_peer")],
    states={
        STATE_SELECT_INTERFACE: [CallbackQueryHandler(edit_select_interface, pattern="edit_select_interface_.*")],
        STATE_SELECT_PEER_OR_SEARCH: [
            CallbackQueryHandler(select_peer_to_edit, pattern="edit_.*"),
            CallbackQueryHandler(search_peername, pattern="search_peer_name"),
        ],
        STATE_SEARCH_PEER: [MessageHandler(filters.TEXT & ~filters.COMMAND, filter_peersname)],
        STATE_SELECT_PEER_TO_EDIT: [CallbackQueryHandler(select_peer_to_edit, pattern="edit_.*")],
        STATE_EDIT_OPTION: [
            CallbackQueryHandler(edit_data_limit, pattern="edit_data_limit"),
            CallbackQueryHandler(edit_dns, pattern="edit_dns"),
            CallbackQueryHandler(edit_expiry_time, pattern="edit_expiry_time"),
        ],
        STATE_SET_DATA_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_data_limit)],
        STATE_SET_DNS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_dns)],
        STATE_SET_EXPIRY_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_expiry_time)],
    },
    fallbacks=[CallbackQueryHandler(edit_peer_init, pattern="edit_peer")],
    allow_reentry=True,
)
    
    delete_peer_stuff = ConversationHandler(
    entry_points=[CallbackQueryHandler(init_deletepeer, pattern="peer_delete")],
    states={
        CHOOSE_WG_INTERFACE: [CallbackQueryHandler(select_interface_delete, pattern="peer_interface_.*")],
        ENTER_PEER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, specify_peername_delete)],
        CONFIRM_PEER_DELETION: [CallbackQueryHandler(apply_peer_deletion, pattern="peer_confirm_delete|peer_back_to_interface")]
    },
    fallbacks=[],
    allow_reentry=True,
)

    reset_peer_stuff = ConversationHandler(
    entry_points=[CallbackQueryHandler(init_resetpeer, pattern="reset_peer")],
    states={
        SELECT_RESET_INTERFACE: [CallbackQueryHandler(select_reset_interface, pattern="reset_interface_.*")],
        ENTER_RESET_PEER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reset_peername)],
        SHOW_PEER_INFO: [CallbackQueryHandler(reset_action, pattern="reset_traffic|reset_expiry|back_to_reset_interface")]
    },
    fallbacks=[],
    allow_reentry=True,
)
    
    peer_status_stuff = ConversationHandler(
    entry_points=[CallbackQueryHandler(peer_status_mnu, pattern="peer_status")],
    states={
        CHOOSE_INTERFACE_STATUS: [CallbackQueryHandler(init_status_interface, pattern="status_interface_.*")],
        INPUT_PEER_NAME_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtain_peer_status)],
    },
    fallbacks=[CallbackQueryHandler(peer_status_mnu, pattern="peers_menu")],
    allow_reentry=True,
)
    
    user_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(update_user_wire, pattern="update_user")],
    states={
        USER_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_username)],
        PASSWORD_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_password)],
    },
    fallbacks=[CallbackQueryHandler(settings_menu, pattern="settings_menu")]
)
    
    wireguard_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(update_wireguard_setting, pattern="update_wireguard_config")],
    states={
        CONFIG_INTERFACE: [
            CallbackQueryHandler(ask_for_port, pattern="update_port"),
            CallbackQueryHandler(ask_for_mtu, pattern="update_mtu"),
            CallbackQueryHandler(ask_for_dns, pattern="update_dns"),
            CallbackQueryHandler(apply_config, pattern="apply_changes"),
            CallbackQueryHandler(settings_menu, pattern="settings_menu")
        ],
        CONFIG_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_port)],
        CONFIG_MTU: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_mtu)],
        CONFIG_DNS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_dns)],
    },
    fallbacks=[CallbackQueryHandler(settings_menu, pattern="settings_menu")],
)


    login_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("login", start_login), CallbackQueryHandler(start_login, pattern="login")],
    states={
        LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
        LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
    },
    fallbacks=[],
)
    application.add_handler(ConversationHandler(
    entry_points=[
        CallbackQueryHandler(view_template_menu, pattern="view_template")
    ],
    states={
        SELECT_TEMPLATE_INTERFACE: [
            CallbackQueryHandler(wire_int_selection, pattern="select_template_interface_.*")
        ],
        VIEW_TEMPLATE_PEER_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, view_peers_with_name)
        ],
        SELECT_TEMPLATE_PEER: [
            CallbackQueryHandler(generate_template_with_qr, pattern="view_template_.*")
        ],
    },
    fallbacks=[
        CallbackQueryHandler(mnu_back, pattern=".*_menu"),  
        MessageHandler(filters.COMMAND, lambda update, context: ConversationHandler.END)
    ],
))


    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start, pattern="start_action"))
    application.add_handler(CallbackQueryHandler(peers_menu, pattern="peers_menu"))
    application.add_handler(peer_status_stuff)
    application.add_handler(block_unblock_stuff)
    application.add_handler(stuff_handler)
    application.add_handler(CallbackQueryHandler(stat_metrics, pattern="metrics"))
    application.add_handler(CallbackQueryHandler(mnu_back, pattern="main_menu"))
    register_backup_stuff(application)
    application.add_handler(peer_creation_stuff)
    application.add_handler(peer_edit_stuff)
    application.add_handler(delete_peer_stuff)
    application.add_handler(reset_peer_stuff)
    application.add_handler(CallbackQueryHandler(download_peerconfig_create, pattern="^download_create_.*$"))
    application.add_handler(CallbackQueryHandler(download_peerconfig_general, pattern="^download_general_.*$"))
    application.add_handler(CallbackQueryHandler(generate_peerqr_create, pattern="^qr_create_.*$"))
    application.add_handler(CallbackQueryHandler(generate_peerqr_general, pattern="^qr_general_.*$"))

    job_queue = application.job_queue
    job_queue.run_once(monitor_health, 1)
    register_notification(application)
    application.add_handler(CallbackQueryHandler(settings_menu, pattern="settings_menu"))
    application.add_handler(wireguard_conv_handler)
    application.add_handler(user_conv_handler)
    application.add_handler(login_conv_handler)
    application.add_handler(CallbackQueryHandler(start_login, pattern="login"))
    application.add_handler(CallbackQueryHandler(logout, pattern="logout"))
    job_queue = application.job_queue
    job_queue.run_once(auto_message, when=1)
    application.add_handler(CallbackQueryHandler(view_logs, pattern="view_logs"))

    print("Wire Bot is running..")
    application.run_polling()

main()