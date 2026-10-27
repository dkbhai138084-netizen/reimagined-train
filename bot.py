#CREDIT - @CXXWIO
#MAIN CHANNEL - @SHIVAXPORTAL #

import os
import sys
import time
import json
import zipfile
import subprocess
import threading
import html
import psutil
import random
import qrcode
from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import quote

import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# ============================================================
# BOT CONFIG
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", "8675132585"))

STORAGE_DIR = "user_files"
UPLOAD_DIR = os.path.join(STORAGE_DIR, "uplo556ads")
DATA_FILE = os.path.join(STORAGE_DIR, "users.json")
CUSTOM_QR_FILE = os.path.join(STORAGE_DIR, "custom_qr.jpg")

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

UPI_ID = "shiva-singhs@fam"
UPI_NAME = "Shiva Singh"

SUBSCRIPTION_PLANS = {
    'weekly':  {
        'name': 'ᴡᴇᴇᴋʟʏ ᴘʟᴀɴ', 'emoji': '🟢', 'days': 7, 'price': '₹39', 'amt': '39.00', 
        'files': 3, 'upload': '10 MB', 'desc': '7 ᴅᴀʏꜱ ᴏꜰ ᴘʀᴇᴍɪᴜᴍ ʜᴏꜱᴛɪɴɢ'
    },
    'monthly': {
        'name': 'ᴍᴏɴᴛʜʟʏ ᴘʟᴀɴ', 'emoji': '🔵', 'days': 30, 'price': '₹99', 'amt': '99.00', 
        'files': 7, 'upload': '30 MB', 'desc': '30 ᴅᴀʏꜱ ᴏꜰ ᴘʀᴇᴍɪᴜᴍ ʜᴏꜱᴛɪɴɢ'
    },
    'yearly':  {
        'name': 'ʏᴇᴀʀʟʏ ᴘʟᴀɴ', 'emoji': '🟣', 'days': 365, 'price': '₹509', 'amt': '509.00', 
        'files': 13, 'upload': '60 MB', 'desc': '365 ᴅᴀʏꜱ ᴏꜰ ᴘʀᴇᴍɪᴜᴍ ʜᴏꜱᴛɪɴɢ'
    }
}

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"_settings": {"bot_password": "SHIVAGOD", "admins": []}}, f)

# ============================================================
# GLOBALS & PREMIUM EMOJIS
# ============================================================
users = {}
settings = {"bot_password": "SHIVAGOD", "admins": []}
active_scripts = {}
logs_store = {}
payment_sessions = {}
bot_start_time = time.time()
START_TIME = datetime.now()

# Premium IDs
PE_ROCKET    = "6215062030886378130"
PE_CROWN     = "6235252066554484059"
PE_USER      = "5877443460725739250"
PE_FOLDER    = "5210952531676504517"
PE_CHECK     = "6215311461112094002"
PE_CROSS     = "5942877472163892475"
PE_WARNING   = "6147565374289220368"
PE_LOCK      = "5291873529464122510"
PE_DIAMOND   = "6239868537922394674"
PE_MONEY     = "6235459831302460476"
PE_BOT       = "5427168083074628963"
PE_GIFT      = "5287684458881756303"
PE_FIRE      = "6320894534775476960"
PE_STAR      = "6321171873698681876"
PE_SHIELD    = "6215311461112094002" 
PE_PHONE     = "5877443460725739250"
PE_ADMIN     = "6235252066554484059"
PE_UPLOAD    = "6215062030886378130"
PE_SERVER    = "6321171873698681876"

def pe(emoji_id, fallback="💎"):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def safe_html(value):
    return html.escape(str(value), quote=False)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ============================================================
# DATA PERSISTENCE
# ============================================================
def save_data():
    try:
        temp_file = DATA_FILE + ".tmp"
        data_to_save = {str(k): v for k, v in users.items()}
        data_to_save["_settings"] = settings
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        os.replace(temp_file, DATA_FILE)
    except Exception as e:
        print(f"Save Error: {e}")

def load_data():
    global users, settings
    if not os.path.exists(DATA_FILE):
        users = {}
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        users.clear()
        for key, value in raw_data.items():
            if key == "_settings":
                if isinstance(value, dict):
                    settings.update(value)
                continue
            try: uid = int(key)
            except: continue
            if not isinstance(value, dict): value = {}
            value.setdefault("files", [])
            value.setdefault("approved", uid == OWNER_ID)
            value.setdefault("rejected", False)
            value.setdefault("password_verified", uid == OWNER_ID)
            value.setdefault("plan_expiry", "")
            value.setdefault("banned", False)
            users[uid] = value
    except Exception as e:
        print(f"Load Error: {e}")
        users = {}
    settings.setdefault("bot_password", "SHIVAGOD")
    settings.setdefault("admins", [])

load_data()

# ============================================================
# USER / APPROVAL / ADMIN SYSTEM
# ============================================================
def ensure_user(uid):
    if uid not in users:
        users[uid] = {
            "files": [], "approved": uid == OWNER_ID, "rejected": False,
            "password_verified": uid == OWNER_ID, "plan_expiry": "", "banned": False
        }
        save_data()
    else:
        users[uid].setdefault("files", [])
        users[uid].setdefault("approved", uid == OWNER_ID)
        users[uid].setdefault("rejected", False)
        users[uid].setdefault("password_verified", uid == OWNER_ID)
        users[uid].setdefault("plan_expiry", "")
        users[uid].setdefault("banned", False)

def is_owner(uid): return uid == OWNER_ID
def is_admin(uid): return uid == OWNER_ID or uid in settings.get("admins", [])
def is_banned(uid):
    ensure_user(uid)
    return users[uid].get("banned", False)

def is_approved(uid):
    if uid == OWNER_ID: return True
    ensure_user(uid)
    return users[uid].get("approved", False)

def is_premium(uid):
    if uid == OWNER_ID: return True
    exp = users.get(uid, {}).get("plan_expiry", "")
    if exp:
        try: return datetime.fromisoformat(exp) > datetime.now()
        except: return False
    return False

def get_user_file_limit(uid):
    if is_owner(uid): return 999
    if is_premium(uid): return 15
    return 2

def approval_required(message):
    uid = message.from_user.id
    if is_owner(uid): return False
    ensure_user(uid)
    if is_banned(uid):
        bot.reply_to(message, f"{pe(PE_CROSS, '🚫')} <b>ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ</b>\n\n{pe(PE_LOCK, '🔒')} ʏᴏᴜʀ ᴀᴄᴄᴇꜱꜱ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴠᴏᴋᴇᴅ ʙʏ ᴛʜᴇ ᴏᴡɴᴇʀ.", parse_mode="HTML")
        return True
    return False

def verify_password(message):
    uid = message.from_user.id
    text = (message.text or "").strip()
    ensure_user(uid)
    if text == settings.get("bot_password", "SHIVAGOD"):
        users[uid]["password_verified"] = True
        users[uid]["approved"] = True
        save_data()
        send_welcome_message(message)
    else:
        bot.reply_to(message, f"{pe(PE_CROSS, '❌')} ɪɴᴄᴏʀʀᴇᴄᴛ ᴘᴀꜱꜱᴡᴏʀᴅ.\nꜱᴇɴᴅ /start ᴛᴏ ᴛʀʏ ᴀɢᴀɪɴ.", parse_mode="HTML")

# ============================================================
# UTILITIES
# ============================================================
def uptime():
    seconds = int(time.time() - bot_start_time)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{days}ᴅ {hours}ʜ {mins}ᴍ {secs}ꜱ"

def user_folder(uid):
    path = os.path.join(UPLOAD_DIR, str(uid))
    os.makedirs(path, exist_ok=True)
    return path

def get_system_info():
    cpu_freq = psutil.cpu_freq()
    cpu_ghz = cpu_freq.current / 1000 if cpu_freq else 0
    ram = psutil.virtual_memory()
    return cpu_ghz, ram.total / (1024 ** 3), ram.available / (1024 ** 3)

def generate_upi_qr(upi_id, amount, name="Payment"):
    upi_link = f"upi://pay?pa={upi_id}&pn={quote(name)}&am={amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

# ============================================================
# SCRIPT RUNNING
# ============================================================
def run_script_thread(user_id, file_path):
    try:
        proc = subprocess.Popen([sys.executable, os.path.abspath(file_path)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        active_scripts.setdefault(user_id, {})[file_path] = proc
        logs_store.setdefault(user_id, {})[file_path] = []
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None: break
            if line:
                logs_store[user_id][file_path].append(line.strip())
                logs_store[user_id][file_path] = logs_store[user_id][file_path][-50:]
        proc.wait()
    except Exception as e: print(f"Error in script {file_path}: {e}")
    finally:
        if user_id in active_scripts: active_scripts[user_id].pop(file_path, None)

def start_script(user_id, file_path):
    if file_path in active_scripts.get(user_id, {}): return False
    threading.Thread(target=run_script_thread, args=(user_id, file_path), daemon=True).start()
    return True

# ============================================================
# KEYBOARD (WITH COLORS)
# ============================================================
def control_buttons(uid=None):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("🌏 ᴜᴘʟᴏᴀᴅ", style="primary"),
        KeyboardButton("📁 ᴍʏ ꜰɪʟᴇꜱ", style="primary")
    )
    markup.row(
        KeyboardButton("🔄 ʀᴇꜱᴛᴀʀᴛ", style="success"),
        KeyboardButton("⏹ ꜱᴛᴏᴘ", style="danger")
    )
    markup.row(
        KeyboardButton("⚡ ꜱᴘᴇᴇᴅ", style="primary"),
        KeyboardButton("🚀 ꜱᴛᴀᴛᴜꜱ", style="primary")
    )
    markup.row(
        KeyboardButton("💳 ʙᴜʏ ᴘʟᴀɴ", style="success"),
        KeyboardButton("💎 ᴍʏ ᴘʟᴀɴ", style="primary")
    )
    if uid is not None and is_admin(uid):
        markup.row(KeyboardButton("🛡️ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ", style="danger"))
    return markup

def send_welcome_message(message):
    uid = message.from_user.id
    ensure_user(uid)
    welcome = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ {pe(PE_ROCKET, '🚀')} <b>ꜱʜɪᴠᴀ ʜᴏꜱᴛɪɴɢ</b> ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"{pe(PE_GIFT, '🎁')} <b>ᴡᴇʟᴄᴏᴍᴇ</b> {safe_html(message.from_user.first_name or 'User')}!\n\n"
        f"{pe(PE_PHONE, '🆔')} <b>ᴜꜱᴇʀ ɪᴅ:</b> <code>{uid}</code>\n"
        f"{pe(PE_FOLDER, '📁')} <b>ꜰɪʟᴇꜱ:</b> {len(users[uid]['files'])}/{get_user_file_limit(uid)}\n\n"
        f"{pe(PE_CHECK, '✅')} ᴀᴜᴛᴏ-ʀᴇᴄᴏᴠᴇʀʏ ꜱʏꜱᴛᴇᴍ\n"
        f"{pe(PE_BOT, '🤖')} ᴘʏᴛʜᴏɴ / ᴢɪᴘ ꜱᴜᴘᴘᴏʀᴛ"
    )
    bot.send_message(uid, welcome, reply_markup=control_buttons(uid), parse_mode="HTML")

# ============================================================
# HANDLERS
# ============================================================
@bot.message_handler(commands=["start"])
def start_command(message):
    uid = message.from_user.id
    ensure_user(uid)
    if uid == OWNER_ID:
        users[uid].update({"approved": True, "rejected": False, "password_verified": True, "banned": False})
        save_data()
        send_welcome_message(message)
        return
    if not users[uid].get("password_verified", False):
        msg = bot.reply_to(message, f"{pe(PE_LOCK, '🔐')} <b>ꜱᴇɴᴅ ᴛʜᴇ ʙᴏᴛ ᴘᴀꜱꜱᴡᴏʀᴅ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ.</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, verify_password)
        return
    send_welcome_message(message)

@bot.message_handler(commands=["setqr"])
def set_qr_command(message):
    if message.from_user.id != OWNER_ID: return
    msg = bot.reply_to(message, f"{pe(PE_UPLOAD, '📸')} <b>ꜱᴇɴᴅ ᴛʜᴇ ǫʀ ɪᴍᴀɢᴇ ɴᴏᴡ (ᴀꜱ ᴀ ᴘʜᴏᴛᴏ):</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_custom_qr)

def process_custom_qr(message):
    if not message.photo and not message.document:
        return bot.reply_to(message, "❌ ꜱᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ.")
    try:
        if message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
        else:
            file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(CUSTOM_QR_FILE, "wb") as new_file:
            new_file.write(downloaded_file)
        bot.reply_to(message, f"{pe(PE_CHECK, '✅')} <b>ᴄᴜꜱᴛᴏᴍ ǫʀ ꜱᴀᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ! ɴᴏᴡ ɪᴛ ᴡɪʟʟ ꜱʜᴏᴡ ɪɴ ǫʀ 2.</b>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ ᴇʀʀᴏʀ: {e}")

@bot.message_handler(func=lambda message: True, content_types=["text"])
def control_handler(message):
    uid = message.from_user.id
    text = (message.text or "").strip()
    ensure_user(uid)
    if approval_required(message): return

    if text.startswith("🌏"):
        bot.reply_to(message, f"{pe(PE_UPLOAD, '📤')} <b>ꜱᴇɴᴅ ʏᴏᴜʀ .ᴘʏ, .ᴢɪᴘ ᴏʀ .ᴛxᴛ ꜰɪʟᴇ ᴀꜱ ᴀ ᴅᴏᴄᴜᴍᴇɴᴛ.</b>", parse_mode="HTML")
    
    elif text.startswith("🛡️"):
        if not is_admin(uid): return
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(InlineKeyboardButton("🔐 ᴄʜᴀɴɢᴇ ᴘᴀꜱꜱᴡᴏʀᴅ", callback_data="admin_changepass"), InlineKeyboardButton("🚫 ʙᴀɴ ᴜꜱᴇʀ", callback_data="admin_ban"))
        markup.row(InlineKeyboardButton("✅ ᴜɴʙᴀɴ ᴜꜱᴇʀ", callback_data="admin_unban"), InlineKeyboardButton("👑 ᴀᴅᴅ ᴀᴅᴍɪɴ", callback_data="admin_addadmin"))
        markup.row(InlineKeyboardButton("🗑 ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ", callback_data="admin_removeadmin"), InlineKeyboardButton("📋 ᴀᴅᴍɪɴ ʟɪꜱᴛ", callback_data="admin_list"))
        bot.reply_to(message, f"{pe(PE_ADMIN, '🛡️')} <b>ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ</b>", reply_markup=markup, parse_mode="HTML")

    elif text.startswith("📁"):
        files = users[uid]["files"]
        if not files: return bot.reply_to(message, f"{pe(PE_CROSS, '❌')} <b>ɴᴏ ꜰɪʟᴇꜱ.</b>", parse_mode="HTML")
        buttons = [[InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{f}")] for f in files]
        bot.reply_to(message, f"{pe(PE_FOLDER, '📁')} <b>ʏᴏᴜʀ ꜰɪʟᴇꜱ:</b>\n<i>Select a file to manage:</i>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

    elif text.startswith("⚡"):
        cpu_ghz, total_ram_gb, free_ram_gb = get_system_info()
        bot.reply_to(message, f"{pe(PE_FIRE, '⚡')} <b>ꜱᴘᴇᴇᴅ</b>\nᴄᴘᴜ: {round(cpu_ghz, 2)} ɢʜᴢ\nʀᴀᴍ: {round(total_ram_gb, 2)} ɢʙ", parse_mode="HTML")

    elif text.startswith("🔄"):
        if uid in active_scripts:
            for p in list(active_scripts[uid].values()):
                try: p.kill()
                except: pass
            active_scripts[uid] = {}
        folder = user_folder(uid)
        for fname in users[uid]["files"]:
            if fname.endswith(".py"):
                path = os.path.join(folder, fname)
                if os.path.exists(path): start_script(uid, path)
        bot.reply_to(message, f"{pe(PE_ROCKET, '🔄')} <b>ᴀʟʟ ꜱᴄʀɪᴘᴛꜱ ʀᴇꜱᴛᴀʀᴛᴇᴅ.</b>", parse_mode="HTML")

    elif text.startswith("⏹"):
        if uid in active_scripts:
            for p in list(active_scripts[uid].values()):
                try: p.kill()
                except: pass
            active_scripts[uid] = {}
        bot.reply_to(message, f"{pe(PE_SHIELD, '⏹')} <b>ꜱᴛᴏᴘᴘᴇᴅ.</b>", parse_mode="HTML")

    elif text.startswith("🚀"):
        total_users = len(users)
        total_files = sum(len(u.get("files", [])) for u in users.values())
        running_scripts = sum(len(scripts) for scripts in active_scripts.values())
        is_locked = "TRUE" if settings.get("bot_password") else "FALSE"
        
        # ⬇⬇ PREMIUM EMOJIS ADDED HERE ⬇⬇
        status_text = (
            f"{pe(PE_STAR, '📊')} <b>ꜱᴛᴀᴛᴜꜱ</b>\n"
            f"{pe(PE_USER, '👥')} ᴜꜱᴇʀꜱ: {total_users}\n"
            f"{pe(PE_FOLDER, '📁')} ꜰɪʟᴇꜱ: {total_files}\n"
            f"{pe(PE_CHECK, '🟢')} ʀᴜɴɴɪɴɢ: {running_scripts}\n"
            f"{pe(PE_FIRE, '⏱️')} ᴜᴘᴛɪᴍᴇ: {uptime()}\n"
            f"{pe(PE_LOCK, '🔒')} ʙᴏᴛ ʟᴏᴄᴋᴇᴅ: {is_locked}"
        )
        bot.reply_to(message, status_text, parse_mode="HTML")

    elif text.startswith("💳"):
        markup = InlineKeyboardMarkup(row_width=1)
        for k, v in SUBSCRIPTION_PLANS.items():
            markup.add(InlineKeyboardButton(f"{v['emoji']} {v['name']} - {v['price']}", callback_data=f"pickplan_{k}"))
        markup.add(InlineKeyboardButton("↩️ ʙᴀᴄᴋ", callback_data="main_menu"))
        bot.reply_to(message, f"{pe(PE_DIAMOND, '💎')} <b>ꜱᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʟᴀɴ</b>", reply_markup=markup, parse_mode="HTML")

    elif text.startswith("💎"):
        exp = users[uid].get("plan_expiry", "")
        status = "🆓 ꜰʀᴇᴇ"
        if exp:
            try: status = "⭐ ᴘʀᴇᴍɪᴜᴍ" if datetime.fromisoformat(exp) > datetime.now() else "⌛ ᴇxᴘɪʀᴇᴅ"
            except: pass
        bot.reply_to(message, f"{pe(PE_DIAMOND, '💎')} <b>ᴍʏ ᴘʟᴀɴ:</b> {status}", parse_mode="HTML")

# ============================================================
# FILE UPLOAD & OWNER APPROVAL
# ============================================================
@bot.message_handler(content_types=["document"])
def document_handler(message):
    uid = message.from_user.id
    ensure_user(uid)
    if approval_required(message): return
    
    doc = message.document
    filename = os.path.basename(doc.file_name or "")
    if not filename.lower().endswith((".py", ".zip", ".txt")):
        return bot.reply_to(message, f"{pe(PE_CROSS, '❌')} <b>ᴏɴʟʏ .ᴘʏ, .ᴢɪᴘ, .ᴛxᴛ.</b>", parse_mode="HTML")

    msg = bot.reply_to(message, f"{pe(PE_UPLOAD, '⬇️')} <b>ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...</b>", parse_mode="HTML")
    try:
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        save_path = os.path.join(user_folder(uid), filename)
        with open(save_path, "wb") as f: f.write(downloaded_file)
        
        if filename not in users[uid]["files"]:
            users[uid]["files"].append(filename)
            save_data()

        if uid == OWNER_ID:
            if filename.endswith(".py"): start_script(uid, save_path)
            bot.edit_message_text(f"{pe(PE_CHECK, '✅')} <b>ꜰɪʟᴇ ᴜᴘʟᴏᴀᴅᴇᴅ & ꜱᴛᴀʀᴛᴇᴅ!</b>", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("📁 ᴍʏ ꜰɪʟᴇꜱ", callback_data="myfiles")))
        else:
            bot.edit_message_text(f"{pe(PE_WARNING, '⏳')} <b>ꜰɪʟᴇ ᴜᴘʟᴏᴀᴅᴇᴅ! ᴡᴀɪᴛɪɴɢ ꜰᴏʀ ᴀᴅᴍɪɴ ᴀᴘᴘʀᴏᴠᴀʟ...</b>", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="HTML")
            owner_text = (
                f"{pe(PE_FOLDER, '📁')} <b>ɴᴇᴡ ꜰɪʟᴇ ᴜᴘʟᴏᴀᴅᴇᴅ</b>\n\n"
                f"{pe(PE_USER, '👤')} <b>ᴜꜱᴇʀ ɪᴅ:</b> <code>{uid}</code>\n"
                f"{pe(PE_USER, '👤')} <b>ɴᴀᴍᴇ:</b> {safe_html(message.from_user.first_name)}\n"
                f"{pe(PE_FOLDER, '📄')} <b>ꜰɪʟᴇ:</b> <code>{safe_html(filename)}</code>"
            )
            owner_markup = InlineKeyboardMarkup()
            owner_markup.row(
                InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ & ʀᴜɴ", callback_data=f"f_approve_{uid}_{filename}"),
                InlineKeyboardButton("❌ ʀᴇᴊᴇᴄᴛ", callback_data=f"f_reject_{uid}_{filename}")
            )
            bot.send_document(OWNER_ID, doc.file_id, caption=owner_text, reply_markup=owner_markup, parse_mode="HTML")

    except Exception as e:
        bot.edit_message_text(f"{pe(PE_CROSS, '❌')} <b>ꜰᴀɪʟᴇᴅ.</b>\n<code>{safe_html(e)}</code>", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="HTML")

# ============================================================
# CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    uid = call.from_user.id
    ensure_user(uid)
    data = call.data or ""

    if data.startswith("pickplan_"):
        plan_key = data.replace('pickplan_', '')
        plan = SUBSCRIPTION_PLANS.get(plan_key)
        if not plan: return bot.answer_callback_query(call.id, "❌ ɪɴᴠᴀʟɪᴅ ᴘʟᴀɴ.")
        
        # ⬇⬇ PREMIUM EMOJIS ADDED HERE (CONFIRM PLAN) ⬇⬇
        caption = (
            f"{pe(PE_FOLDER, '📋')} <b>ᴄᴏɴꜰɪʀᴍ ʏᴏᴜʀ ᴘʟᴀɴ</b>\n\n"
            f"{pe(PE_GIFT, '📦')} <b>{plan['name']}</b>\n"
            f"• {pe(PE_MONEY, '💳')} <b>ᴘʀɪᴄᴇ:</b> ₹{plan['amt']}\n"
            f"• {pe(PE_DIAMOND, '💰')} <b>ᴠᴀʟɪᴅɪᴛʏ:</b> {plan['days']} ᴅᴀʏꜱ\n"
            f"• {pe(PE_FOLDER, '📁')} <b>ꜰɪʟᴇꜱ:</b> {plan['files']} • <b>ᴜᴘʟᴏᴀᴅ:</b> {plan['upload']}\n\n"
            f"<i>{plan['desc']}</i>\n\n"
            f"{pe(PE_ROCKET, '🚀')} ᴘʀᴏᴄᴇᴇᴅ ᴛᴏ ᴜᴘɪ ǫʀ ᴘᴀʏᴍᴇɴᴛ?"
        )
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("✅ ʏᴇꜱ, ᴄᴏɴᴛɪɴᴜᴇ", callback_data=f"confirm_plan_{plan_key}"),
            InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="cancel_qr")
        )
        markup.row(
            InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="back_to_plans"),
            InlineKeyboardButton("🏠 ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")
        )
        
        bot.edit_message_text(caption, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)
        return

    if data.startswith("confirm_plan_"):
        plan_key = data.replace('confirm_plan_', '')
        plan = SUBSCRIPTION_PLANS.get(plan_key)
        if not plan: return bot.answer_callback_query(call.id, "❌ ɪɴᴠᴀʟɪᴅ ᴘʟᴀɴ.")
        order_id = hex(random.getrandbits(48))[2:].upper()
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("📸 Qʀ 1", callback_data=f"show_qr1_{plan_key}_{order_id}"),
            InlineKeyboardButton("📸 Qʀ 2", callback_data=f"show_qr2_{plan_key}_{order_id}")
        )
        markup.row(InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="cancel_qr"))
        bot.edit_message_text(f"{pe(PE_MONEY, '📪')} <b>ꜱᴇʟᴇᴄᴛ ᴘᴀʏᴍᴇɴᴛ ᴏᴘᴛɪᴏɴ:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)
        return
        
    if data == "back_to_plans":
        markup = InlineKeyboardMarkup(row_width=1)
        for k, v in SUBSCRIPTION_PLANS.items():
            markup.add(InlineKeyboardButton(f"{v['emoji']} {v['name']} - {v['price']}", callback_data=f"pickplan_{k}"))
        markup.add(InlineKeyboardButton("↩️ ʙᴀᴄᴋ", callback_data="main_menu"))
        bot.edit_message_text(f"{pe(PE_DIAMOND, '💎')} <b>ꜱᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʟᴀɴ</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)
        return
        
    if data == "main_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.answer_callback_query(call.id, "🏠 ʀᴇᴛᴜʀɴᴇᴅ ᴛᴏ ᴍᴀɪɴ ᴍᴇɴᴜ")
        return

    if data.startswith("show_qr1_"):
        parts = data.split('_')
        plan_key = parts[2]
        order_id = parts[3]
        plan = SUBSCRIPTION_PLANS.get(plan_key)
        qr_img = generate_upi_qr(UPI_ID, plan['amt'], UPI_NAME)
        
        # ⬇⬇ PREMIUM EMOJIS ADDED HERE (QR CAPTION) ⬇⬇
        caption = (
            f"{pe(PE_MONEY, '📪')} <b>ᴜᴘɪ ᴘᴀʏᴍᴇɴᴛ</b>\n\n"
            f"{pe(PE_STAR, '💸')} <b>ᴘʟᴀɴ:</b> {plan['name']}\n"
            f"{pe(PE_MONEY, '💰')} <b>ᴀᴍᴏᴜɴᴛ:</b> ₹{plan['amt']}\n"
            f"{pe(PE_FOLDER, '🏦')} <b>ᴜᴘɪ ɪᴅ:</b> <code>{UPI_ID}</code>\n\n"
            f"<b>ꜱᴛᴇᴘꜱ:</b> ꜱᴄᴀɴ Qʀ & ᴘᴀʏ, ᴛʜᴇɴ ᴛᴀᴘ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ."
        )
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("📥 ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ", callback_data=f"paid_{plan_key}_{order_id}"),
            InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="cancel_qr")
        )
        bot.send_photo(call.message.chat.id, qr_img, caption=caption, reply_markup=markup, parse_mode="HTML")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("show_qr2_"):
        parts = data.split('_')
        plan_key = parts[2]
        order_id = parts[3]
        plan = SUBSCRIPTION_PLANS.get(plan_key)
        
        # ⬇⬇ PREMIUM EMOJIS ADDED HERE (CUSTOM QR CAPTION) ⬇⬇
        caption = (
            f"{pe(PE_MONEY, '📪')} <b>ᴄᴜꜱᴛᴏᴍ ᴘᴀʏᴍᴇɴᴛ Qʀ</b>\n\n"
            f"{pe(PE_STAR, '💸')} <b>ᴘʟᴀɴ:</b> {plan['name']}\n"
            f"{pe(PE_MONEY, '💰')} <b>ᴀᴍᴏᴜɴᴛ:</b> ₹{plan['amt']}\n\n"
            f"<b>ꜱᴛᴇᴘꜱ:</b> ꜱᴄᴀɴ Qʀ & ᴘᴀʏ, ᴛʜᴇɴ ᴛᴀᴘ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ."
        )
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("📥 ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ", callback_data=f"paid_{plan_key}_{order_id}"),
            InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="cancel_qr")
        )
        if os.path.exists(CUSTOM_QR_FILE):
            with open(CUSTOM_QR_FILE, "rb") as f:
                bot.send_photo(call.message.chat.id, f, caption=caption, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(call.message.chat.id, "⚠️ ᴏᴡɴᴇʀ ɴᴇ ᴄᴜꜱᴛᴏᴍ ǫʀ ꜱᴇᴛ ɴᴀʜɪ ᴋɪʏᴀ ʜᴀɪ. ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ ǫʀ 1.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("paid_"):
        parts = data.split('_')
        plan_key = parts[1]
        order_id = parts[2] if len(parts) > 2 else "N/A"
        payment_sessions[uid] = {'plan_key': plan_key, 'order_id': order_id}
        msg = bot.send_message(call.message.chat.id, f"{pe(PE_FIRE, '📈')} <b>ꜱᴇɴᴅ ʏᴏᴜʀ ᴜᴛʀ / ᴛʀᴀɴꜱᴀᴄᴛɪᴏɴ ɪᴅ:</b>\n\nᴇxᴀᴍᴘʟᴇ: <code>412345678901</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_utr_step)
        bot.answer_callback_query(call.id)
        return

    if data in ["cancel_qr", "cancel_payment"]:
        if uid in payment_sessions: del payment_sessions[uid]
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.answer_callback_query(call.id, "ᴄᴀɴᴄᴇʟʟᴇᴅ.")
        return

    if data.startswith("approve_pay_"):
        if uid != OWNER_ID: return bot.answer_callback_query(call.id, "❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
        parts = data.split("_")
        target_uid = int(parts[2])
        plan_key = parts[3]
        if plan_key not in SUBSCRIPTION_PLANS: return bot.answer_callback_query(call.id, "❌ ɪɴᴠᴀʟɪᴅ ᴘʟᴀɴ.")
        days = SUBSCRIPTION_PLANS[plan_key]['days']
        current = users[target_uid].get("plan_expiry", "")
        try: base = datetime.fromisoformat(current) if current and datetime.fromisoformat(current) > datetime.now() else datetime.now()
        except: base = datetime.now()
        new_exp = base + timedelta(days=days)
        users[target_uid]["plan_expiry"] = new_exp.isoformat()
        save_data()
        try: bot.send_message(target_uid, f"{pe(PE_GIFT, '🎉')} <b>ᴘᴀʏᴍᴇɴᴛ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\n{pe(PE_DIAMOND, '💎')} ᴘʟᴀɴ: <b>{SUBSCRIPTION_PLANS[plan_key]['name']}</b>", parse_mode="HTML")
        except: pass
        try: bot.edit_message_text(f"{pe(PE_CHECK, '✅')} <b>ᴘᴀʏᴍᴇɴᴛ ᴀᴘᴘʀᴏᴠᴇᴅ ꜰᴏʀ {target_uid}</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        except: pass
        bot.answer_callback_query(call.id, "✅ ᴀᴘᴘʀᴏᴠᴇᴅ")
        return

    if data.startswith("reject_pay_"):
        if uid != OWNER_ID: return bot.answer_callback_query(call.id, "❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
        parts = data.split("_")
        target_uid = int(parts[2])
        try: bot.send_message(target_uid, f"{pe(PE_CROSS, '❌')} <b>ᴘᴀʏᴍᴇɴᴛ ʀᴇᴊᴇᴄᴛᴇᴅ!</b>\n\nᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ.", parse_mode="HTML")
        except: pass
        try: bot.edit_message_text(f"{pe(PE_CROSS, '❌')} <b>ᴘᴀʏᴍᴇɴᴛ ʀᴇᴊᴇᴄᴛᴇᴅ ꜰᴏʀ {target_uid}</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        except: pass
        bot.answer_callback_query(call.id, "❌ ʀᴇᴊᴇᴄᴛᴇᴅ")
        return

    if data.startswith("f_approve_"):
        if uid != OWNER_ID: return
        parts = data.split("_")
        target_uid = int(parts[2])
        fname = "_".join(parts[3:])
        path = os.path.join(user_folder(target_uid), fname)
        if os.path.exists(path) and fname.endswith(".py"):
            start_script(target_uid, path)
            bot.answer_callback_query(call.id, "✅ ꜰɪʟᴇ ᴀᴘᴘʀᴏᴠᴇᴅ & ꜱᴛᴀʀᴛᴇᴅ!")
            try: bot.send_message(target_uid, f"{pe(PE_CHECK, '✅')} <b>ꜰɪʟᴇ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>", parse_mode="HTML")
            except: pass
        else:
            bot.answer_callback_query(call.id, "✅ ꜰɪʟᴇ ᴀᴘᴘʀᴏᴠᴇᴅ!")
            try: bot.send_message(target_uid, f"{pe(PE_CHECK, '✅')} <b>ꜰɪʟᴇ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>", parse_mode="HTML")
            except: pass
        bot.edit_message_caption(f"{pe(PE_CHECK, '✅')} <b>ᴀᴘᴘʀᴏᴠᴇᴅ & ᴘʀᴏᴄᴇꜱꜱᴇᴅ</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        return

    if data.startswith("f_reject_"):
        if uid != OWNER_ID: return
        parts = data.split("_")
        target_uid = int(parts[2])
        fname = "_".join(parts[3:])
        path = os.path.join(user_folder(target_uid), fname)
        if os.path.exists(path): os.remove(path)
        if fname in users[target_uid]["files"]: users[target_uid]["files"].remove(fname)
        save_data()
        bot.answer_callback_query(call.id, "❌ ꜰɪʟᴇ ʀᴇᴊᴇᴄᴛᴇᴅ!")
        try: bot.send_message(target_uid, f"{pe(PE_CROSS, '❌')} <b>ꜰɪʟᴇ ʀᴇᴊᴇᴄᴛᴇᴅ!</b>", parse_mode="HTML")
        except: pass
        bot.edit_message_caption(f"{pe(PE_CROSS, '❌')} <b>ʀᴇᴊᴇᴄᴛᴇᴅ</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        return

    if data == "myfiles":
        files = users[uid]["files"]
        if not files: return bot.edit_message_text(f"{pe(PE_CROSS, '❌')} <b>ɴᴏ ꜰɪʟᴇꜱ.</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        buttons = [[InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{f}")] for f in files]
        bot.edit_message_text(f"{pe(PE_FOLDER, '📁')} <b>ʏᴏᴜʀ ꜰɪʟᴇꜱ:</b>\n<i>Select a file to manage:</i>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

    elif data.startswith("file_"):
        fname = data[5:]
        path = os.path.join(user_folder(uid), fname)
        running = path in active_scripts.get(uid, {})
        msg = f"{pe(PE_STAR, '⚡')} <b>ꜰɪʟᴇ ᴍᴀɴᴀɢᴇʀ</b>\n\n{pe(PE_FOLDER, '📁')} <b>ꜰɪʟᴇ:</b> <code>{safe_html(fname)}</code>\n{pe(PE_CHECK, '🟢')} <b>ꜱᴛᴀᴛᴜꜱ:</b> <code>{'Running' if running else 'Stopped'}</code>\n\n<i>Choose an action:</i>"
        buttons = [
            [InlineKeyboardButton("▶ ʀᴜɴ", callback_data=f"run_{fname}"), InlineKeyboardButton("⏹ ꜱᴛᴏᴘ", callback_data=f"stop_{fname}")],
            [InlineKeyboardButton("🗑 ᴅᴇʟᴇᴛᴇ", callback_data=f"del_{fname}")],
            [InlineKeyboardButton("⬅ ʙᴀᴄᴋ", callback_data="myfiles")]
        ]
        bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

    elif data.startswith("run_"):
        fname = data[4:]
        path = os.path.join(user_folder(uid), fname)
        if start_script(uid, path): bot.answer_callback_query(call.id, f"▶ {fname} ꜱᴛᴀʀᴛᴇᴅ")
        else: bot.answer_callback_query(call.id, "⚠️ ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ.")
        return

    elif data.startswith("stop_"):
        fname = data[5:]
        path = os.path.join(user_folder(uid), fname)
        proc = active_scripts.get(uid, {}).get(path)
        if proc:
            proc.kill()
            active_scripts[uid].pop(path, None)
            bot.answer_callback_query(call.id, f"⏹ {fname} ꜱᴛᴏᴘᴘᴇᴅ")
        else: bot.answer_callback_query(call.id, "❌ ɴᴏᴛ ʀᴜɴɴɪɴɢ")
        return
        
    elif data.startswith("del_"):
        fname = data[4:]
        path = os.path.join(user_folder(uid), fname)
        proc = active_scripts.get(uid, {}).get(path)
        if proc: proc.kill()
        if os.path.exists(path): os.remove(path)
        if fname in users[uid]["files"]: users[uid]["files"].remove(fname)
        save_data()
        bot.answer_callback_query(call.id, "🗑 ꜰɪʟᴇ ᴅᴇʟᴇᴛᴇᴅ!")
        files = users[uid]["files"]
        if not files: return bot.edit_message_text(f"{pe(PE_CROSS, '❌')} <b>ɴᴏ ꜰɪʟᴇꜱ.</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        buttons = [[InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{f}")] for f in files]
        bot.edit_message_text(f"{pe(PE_FOLDER, '📁')} <b>ʏᴏᴜʀ ꜰɪʟᴇꜱ:</b>\n<i>Select a file to manage:</i>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
        return

    elif data == "admin_changepass":
        if not is_owner(uid): return bot.answer_callback_query(call.id, "❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
        msg = bot.send_message(call.message.chat.id, f"{pe(PE_LOCK, '🔐')} <b>ꜱᴇɴᴅ ɴᴇᴡ ʙᴏᴛ ᴘᴀꜱꜱᴡᴏʀᴅ:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_change_password)
        bot.answer_callback_query(call.id)

    elif data == "admin_ban":
        if not is_admin(uid): return bot.answer_callback_query(call.id, "❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
        msg = bot.send_message(call.message.chat.id, f"{pe(PE_CROSS, '🚫')} <b>ꜱᴇɴᴅ ᴜꜱᴇʀ ɪᴅ ᴛᴏ ʙᴀɴ:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_ban_user)
        bot.answer_callback_query(call.id)

    elif data == "admin_unban":
        if not is_admin(uid): return bot.answer_callback_query(call.id, "❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
        msg = bot.send_message(call.message.chat.id, f"{pe(PE_CHECK, '✅')} <b>ꜱᴇɴᴅ ᴜꜱᴇʀ ɪᴅ ᴛᴏ ᴜɴʙᴀɴ:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_unban_user)
        bot.answer_callback_query(call.id)

    elif data == "admin_addadmin":
        if not is_owner(uid): return bot.answer_callback_query(call.id, "❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
        msg = bot.send_message(call.message.chat.id, f"{pe(PE_ADMIN, '👑')} <b>ꜱᴇɴᴅ ᴜꜱᴇʀ ɪᴅ ᴛᴏ ᴍᴀᴋᴇ ᴀᴅᴍɪɴ:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_add_admin)
        bot.answer_callback_query(call.id)

    elif data == "admin_removeadmin":
        if not is_owner(uid): return bot.answer_callback_query(call.id, "❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
        msg = bot.send_message(call.message.chat.id, f"{pe(PE_CROSS, '🗑')} <b>ꜱᴇɴᴅ ᴀᴅᴍɪɴ ᴜꜱᴇʀ ɪᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_remove_admin)
        bot.answer_callback_query(call.id)
        
    elif data == "admin_list":
        if not is_admin(uid): return bot.answer_callback_query(call.id, "❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
        admins = settings.get("admins", [])
        admin_text = f"{pe(PE_ADMIN, '👑')} <b>ᴀᴅᴍɪɴ ʟɪꜱᴛ</b>\n\n"
        admin_text += f"👑 <b>ᴏᴡɴᴇʀ:</b> <code>{OWNER_ID}</code>\n\n"
        if admins:
            admin_text += "🛡️ <b>ᴀᴅᴍɪɴꜱ:</b>\n" + "\n".join([f"• <code>{a}</code>" for a in admins])
        else:
            admin_text += "🛡️ <b>ᴀᴅᴍɪɴꜱ:</b> ɴᴏ ᴀᴅᴍɪɴꜱ."
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, admin_text, parse_mode="HTML")

# ============================================================
# PAYMENT & ADMIN STEP HANDLERS
# ============================================================
def process_utr_step(message):
    uid = message.from_user.id
    if uid not in payment_sessions: return bot.send_message(message.chat.id, "ꜱᴇꜱꜱɪᴏɴ ᴇxᴘɪʀᴇᴅ.")
    utr = (message.text or "").strip()
    if not utr or len(utr) < 6: return bot.send_message(message.chat.id, "❌ ɪɴᴠᴀʟɪᴅ ᴜᴛʀ.")
    payment_sessions[uid]['utr'] = utr
    msg = bot.send_message(message.chat.id, f"{pe(PE_STAR, '🌐')} <b>ᴜᴛʀ ꜱᴀᴠᴇᴅ</b>\n\n⏳ ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ᴀꜱ ᴀ ᴘʜᴏᴛᴏ.", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_screenshot_step)

def process_screenshot_step(message):
    uid = message.from_user.id
    if uid not in payment_sessions: return bot.send_message(message.chat.id, "ꜱᴇꜱꜱɪᴏɴ ᴇxᴘɪʀᴇᴅ.")
    if not message.photo and not message.document: return bot.send_message(message.chat.id, "❌ ꜱᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ.")
    session = payment_sessions[uid]
    plan_key = session['plan_key']
    utr = session.get('utr', 'N/A')
    plan = SUBSCRIPTION_PLANS.get(plan_key)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
        InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ", callback_data=f"approve_pay_{uid}_{plan_key}"),
        InlineKeyboardButton("❌ ʀᴇᴊᴇᴄᴛ", callback_data=f"reject_pay_{uid}")
    )
    owner_msg = f"{pe(PE_SERVER, '🔔')} <b>ɴᴇᴡ ᴘᴀʏᴍᴇɴᴛ</b>\n{pe(PE_USER, '👤')} <code>{uid}</code>\n{pe(PE_FOLDER, '📦')} {plan['name']}\n{pe(PE_FIRE, '🔢')} ᴜᴛʀ: <code>{safe_html(utr)}</code>"
    bot.send_message(OWNER_ID, owner_msg, reply_markup=markup, parse_mode="HTML")
    bot.forward_message(OWNER_ID, message.chat.id, message.message_id)
    bot.reply_to(message, f"{pe(PE_CHECK, '✅')} ᴘʀᴏᴏꜰ ꜱᴇɴᴛ! ᴡᴀɪᴛ ꜰᴏʀ ᴀᴘᴘʀᴏᴠᴀʟ.", parse_mode="HTML")
    del payment_sessions[uid]

def process_change_password(message):
    if not is_owner(message.from_user.id): return
    settings["bot_password"] = (message.text or "").strip()
    save_data()
    bot.reply_to(message, f"{pe(PE_CHECK, '✅')} <b>ᴘᴀꜱꜱᴡᴏʀᴅ ᴜᴘᴅᴀᴛᴇᴅ!</b>", parse_mode="HTML")

def process_ban_user(message):
    if not is_admin(message.from_user.id): return
    try: target = int(message.text.strip())
    except: return bot.reply_to(message, "❌ ɪɴᴠᴀʟɪᴅ ɪᴅ")
    ensure_user(target)
    users[target]["banned"] = True
    save_data()
    bot.reply_to(message, f"{pe(PE_CROSS, '🚫')} <b>ᴜꜱᴇʀ ʙᴀɴɴᴇᴅ!</b>", parse_mode="HTML")

def process_unban_user(message):
    if not is_admin(message.from_user.id): return
    try: target = int(message.text.strip())
    except: return bot.reply_to(message, "❌ ɪɴᴠᴀʟɪᴅ ɪᴅ")
    ensure_user(target)
    users[target]["banned"] = False
    save_data()
    bot.reply_to(message, f"{pe(PE_CHECK, '✅')} <b>ᴜꜱᴇʀ ᴜɴʙᴀɴɴᴇᴅ!</b>", parse_mode="HTML")

def process_add_admin(message):
    if not is_owner(message.from_user.id): return
    try: target = int(message.text.strip())
    except: return bot.reply_to(message, "❌ ɪɴᴠᴀʟɪᴅ ɪᴅ")
    if target not in settings["admins"]:
        settings["admins"].append(target)
        save_data()
    bot.reply_to(message, f"{pe(PE_ADMIN, '👑')} <b>ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ!</b>", parse_mode="HTML")

def process_remove_admin(message):
    if not is_owner(message.from_user.id): return
    try: target = int(message.text.strip())
    except: return bot.reply_to(message, "❌ ɪɴᴠᴀʟɪᴅ ɪᴅ")
    if target in settings["admins"]:
        settings["admins"].remove(target)
        save_data()
    bot.reply_to(message, f"{pe(PE_CROSS, '🗑')} <b>ᴀᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ!</b>", parse_mode="HTML")

# ============================================================
# START BOT
# ============================================================
if __name__ == "__main__":
    print("SHIVA HOSTING BOT IS RUNNING 🏃")
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
