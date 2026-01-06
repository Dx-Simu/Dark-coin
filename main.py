import asyncio
import os
import re
import requests
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- CONFIGURATION ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8513850569:AAHCsKyy1nWTYVKH_MtbW8IhKyOckWLTEDA"
B = "ᴅx" 

# --- MONGODB CONNECTION (SECURED) ---
MONGO_URL = "mongodb+srv://shadowur6_db_user:8AIIxZUjpanaQBjh@dx-codex.fmqcovu.mongodb.net/?appName=Dx-codex"
client_db = MongoClient(MONGO_URL)
db = client_db["DX_COIN_DB"]
users_col = db["users"]

# --- WEB SERVER & KEEP ALIVE ---
APP_URL = os.environ.get("https://dark-coin.onrender.com") # Render Dashboard এ আপনার URL সেট করবেন
web = Flask('')
@web.route('/')
def home(): return f"{B} COIN SYSTEM ONLINE & DATA SECURED ✨"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

def ping_self():
    while True:
        try:
            if APP_URL:
                requests.get(APP_URL, timeout=10)
        except: pass
        time.sleep(300)

app = Client("DX_COIN_V9", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# --- MASTER OWNERS ---
INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPERS ---
async def check_sudo(user_id):
    if user_id in INIT_SUDO: return True
    user = users_col.find_one({"user_id": user_id})
    return user.get("is_sudo", 0) == 1 if user else False

def get_mention(user_id, name):
    clean_name = re.sub(r'[<>#]', '', name or "User")
    return f"<a href='tg://user?id={user_id}'>{clean_name[:20]}</a>"

def sync_data(user):
    if not user: return
    name = f"{user.first_name} {user.last_name or ''}".strip()
    users_col.update_one(
        {"user_id": user.id},
        {"$set": {"full_name": name, "username": user.username}, 
         "$setOnInsert": {"coins": 0, "is_sudo": 0}},
        upsert=True
    )

# --- 1. SUDO SYSTEM ---
@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    if not await check_sudo(message.from_user.id):
        try: await message.delete()
        except: pass
        return
    
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        sync_data(target)
        user = users_col.find_one({"user_id": target.id})
        new_val = 1 if user.get("is_sudo", 0) == 0 else 0
        users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": new_val}})
        
        status = "✨ ɴᴏᴡ ᴀ sᴜᴅᴏ ᴜsᴇʀ" if new_val == 1 else "⚡ ʀᴇᴍᴏᴠᴇᴅ sᴜᴅᴏ"
        await message.reply_text(
            f"<b>┏━━━━━━━━━━━━━━━━━━━━━━┓</b>\n"
            f"<b> 👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
            f"<b> 📜 sᴛᴀᴛᴜs: {status}</b>\n"
            f"<b>┗━━━━━━━━━ {B} ━━━━━━━━━┛</b>"
        )
    else:
        sudos = users_col.find({"is_sudo": 1})
        res = f"<b>╭╼━「 ✨ sᴜᴅᴏ ᴜsᴇʀs 」━╾╮</b>\n┃\n"
        for i, s in enumerate(list(sudos), 1):
            res += f"<b>┃ {i}.</b> {get_mention(s['user_id'], s['full_name'])}\n"
        res += f"┃\n<b>╰╼━━━━━━━ {B} ━━━━━━━╾╯</b>"
        await message.reply_text(res)
    try: await message.delete()
    except: pass

# --- 2. COIN ENGINE ---
@app.on_message(filters.command("acoin") & filters.group)
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id):
        try: await message.delete()
        except: pass
        return
    if not message.reply_to_message:
        await message.reply(f"<b>❌ {B} » ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ!</b>")
        return

    parts = message.text.split()
    if len(parts) < 2: return

    try:
        amount = int(parts[1])
        target = message.reply_to_message.from_user
        sync_data(target)
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amount}})
        user = users_col.find_one({"user_id": target.id})
        
        await message.reply_text(
            f"<b>┏━━━━━━━ 💰 ᴀᴅᴅᴇᴅ ━━━━━━━┓</b>\n"
            f"<b> ➲ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
            f"<b> ➲ ᴀᴍᴏᴜɴᴛ:</b> <code>{amount}</code>\n"
            f"<b> ➲ ᴛᴏᴛᴀʟ:</b> <code>{user['coins']}</code>\n"
            f"<b>┗━━━━━━━━━ {B} ━━━━━━━━━┛</b>"
        )
    except: pass
    try: await message.delete()
    except: pass

@app.on_message(filters.command("mcoin") & filters.group)
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id):
        try: await message.delete()
        except: pass
        return
    if not message.reply_to_message: return

    parts = message.text.split()
    if len(parts) < 2: return

    try:
        amount = int(parts[1])
        target = message.reply_to_message.from_user
        sync_data(target)
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": -amount}})
        user = users_col.find_one({"user_id": target.id})
        if user['coins'] < 0: users_col.update_one({"user_id": target.id}, {"$set": {"coins": 0}})
        
        await message.reply_text(
            f"<b>┏━━━━━━━ 🔻 ᴍɪɴᴜs ━━━━━━━┓</b>\n"
            f"<b> ➲ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
            f"<b> ➲ ᴀᴍᴏᴜɴᴛ:</b> <code>{amount}</code>\n"
            f"<b> ➲ ᴛᴏᴛᴀʟ:</b> <code>{user['coins']}</code>\n"
            f"<b>┗━━━━━━━━━ {B} ━━━━━━━━━┛</b>"
        )
    except: pass
    try: await message.delete()
    except: pass

@app.on_message(filters.command("reset") & filters.group)
async def reset_coin(client, message: Message):
    if not await check_sudo(message.from_user.id):
        try: await message.delete()
        except: pass
        return
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$set": {"coins": 0}})
        await message.reply_text(
            f"<b>┏━━━━━━━ 🌀 ʀᴇsᴇᴛ ━━━━━━━┓</b>\n"
            f"<b> ➲ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
            f"<b> ➲ sᴛᴀᴛᴜs: ʙᴀʟᴀɴᴄᴇ ᴄʟᴇᴀʀᴇᴅ</b>\n"
            f"<b>┗━━━━━━━━━ {B} ━━━━━━━━━┛</b>"
        )
    try: await message.delete()
    except: pass

# --- 3. STATS & LEADERBOARD ---
@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    
    await message.reply_text(
        f"<b>╭╼━━━「 📊 sᴛᴀᴛs 」━━━╾╮</b>\n"
        f"<b>┃</b>\n"
        f"<b>┃ 👤 ᴜsᴇʀ :</b> {get_mention(target.id, target.first_name)}\n"
        f"<b>┃ 💰 ᴄᴏɪɴs :</b> <code>{user['coins']}</code> 🪙\n"
        f"<b>┃ 🏆 ʀᴀɴᴋ :</b> <code>#{rank}</code>\n"
        f"<b>┃</b>\n"
        f"<b>╰╼━━━━━━━ {B} ━━━━━━━╾╯</b>"
    )
    try: await message.delete()
    except: pass

@app.on_message(filters.command("top") & filters.group)
async def leaderboard(client, message: Message):
    rows = users_col.find().sort("coins", -1).limit(10)
    board = f"<b>╭╼━━━━━「 🏆 ᴛᴏᴘ 10 」━━━━━╾╮</b>\n┃\n"
    for i, row in enumerate(list(rows), 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        board += f"<b>┃ {emoji} {i:02d}.</b> {get_mention(row['user_id'], row['full_name'])} ➲ <code>{row['coins']}</code>\n"
    board += f"┃\n<b>╰╼━━━━━━━ {B} ━━━━━━━╾╯</b>"
    await message.reply_text(board)
    try: await message.delete()
    except: pass

# --- AUTO TRACKER ---
@app.on_message(filters.group & ~filters.bot, group=1)
async def auto_sync(client, message: Message):
    if message.from_user: sync_data(message.from_user)

# --- START ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    if APP_URL:
        Thread(target=ping_self, daemon=True).start()
    app.run()
