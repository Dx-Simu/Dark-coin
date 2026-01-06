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

# --- MONGODB CONNECTION ---
MONGO_URL = "mongodb+srv://shadowur6_db_user:8AIIxZUjpanaQBjh@dx-codex.fmqcovu.mongodb.net/?retryWrites=true&w=majority&appName=Dx-codex"
client_db = MongoClient(MONGO_URL, connectTimeoutMS=30000, socketTimeoutMS=None, connect=False)
db = client_db["DX_COIN_DB"]
users_col = db["users"]

# --- WEB SERVER & KEEP ALIVE ---
APP_URL = os.environ.get("APP_URL") 
web = Flask('')
@web.route('/')
def home(): return f"{B} COIN SYSTEM ONLINE"

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
INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPERS ---
async def check_sudo(user_id):
    if user_id in INIT_SUDO: return True
    try:
        user = users_col.find_one({"user_id": user_id})
        return user.get("is_sudo", 0) == 1 if user else False
    except: return False

def get_mention(user_id, name):
    clean_name = re.sub(r'[<>#]', '', name or "User")
    return f"<a href='tg://user?id={user_id}'>{clean_name[:15]}</a>"

def sync_data(user):
    if not user: return
    try:
        name = f"{user.first_name} {user.last_name or ''}".strip()
        users_col.update_one(
            {"user_id": user.id},
            {"$set": {"full_name": name, "username": user.username}, 
             "$setOnInsert": {"coins": 0, "is_sudo": 0, "last_claim": 0}},
            upsert=True
        )
    except: pass

# --- 1. MENU COMMAND ---
@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    menu_text = (
        f"<b>┌╼「 ✨ {B} ᴄᴏɪɴ ᴍᴇɴᴜ 」</b>\n"
        f"<b>│</b>\n"
        f"<b>├ 📊 ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        f"<b>│ ➲ /coin - ᴄʜᴇᴄᴋ ʙᴀʟᴀɴᴄᴇ</b>\n"
        f"<b>│ ➲ /top - ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n"
        f"<b>│ ➲ /claim - ᴅᴀɪʟʏ ʙᴏɴᴜs</b>\n"
        f"<b>│ ➲ /gift [ᴀᴍᴛ] - ɢɪғᴛ ᴄᴏɪɴs</b>\n"
        f"<b>│</b>\n"
        f"<b>├ ⚡ sᴜᴅᴏ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        f"<b>│ ➲ /acoin [ᴀᴍᴛ] - ᴀᴅᴅ ᴄᴏɪɴ</b>\n"
        f"<b>│ ➲ /mcoin [ᴀᴍᴛ] - ᴍɪɴᴜs ᴄᴏɪɴ</b>\n"
        f"<b>│ ➲ /reset - ʀᴇsᴇᴛ ᴄᴏɪɴs</b>\n"
        f"<b>│ ➲ /sudo - ᴍᴀɴᴀɢᴇ sᴜᴅᴏ</b>\n"
        f"<b>│</b>\n"
        f"<b>└╼━━━━ {B} ━━━━╾┘</b>"
    )
    await message.reply_text(menu_text)

# --- 2. DAILY CLAIM ---
@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    user_id = message.from_user.id
    sync_data(message.from_user)
    
    user = users_col.find_one({"user_id": user_id})
    last_claim = user.get("last_claim", 0)
    current_time = time.time()
    
    if current_time - last_claim < 86400:
        remaining = int((86400 - (current_time - last_claim)) / 3600)
        await message.reply_text(f"<b>❌ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ!\n🕒 ᴛʀʏ ᴀɢᴀɪɴ ɪɴ {remaining} ʜᴏᴜʀs.</b>")
        return

    bonus = 100
    users_col.update_one({"user_id": user_id}, {"$inc": {"coins": bonus}, "$set": {"last_claim": current_time}})
    await message.reply_text(f"<b>┌╼「 🎁 ᴅᴀɪʟʏ ʙᴏɴᴜs 」</b>\n<b>│ ᴜsᴇʀ: {get_mention(user_id, message.from_user.first_name)}</b>\n<b>│ ᴀᴍᴏᴜɴᴛ: +{bonus} ᴄᴏɪɴs</b>\n<b>└╼━━━━ {B} ━━━━╾┘</b>")

# --- 3. COIN GIFT ---
@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    if not message.reply_to_message:
        await message.reply("<b>❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ɢɪғᴛ!</b>")
        return
    parts = message.text.split()
    if len(parts) < 2: return
    try:
        amount = int(parts[1])
        if amount <= 0: return
        sender_id = message.from_user.id
        receiver = message.reply_to_message.from_user
        sync_data(message.from_user)
        sync_data(receiver)
        sender = users_col.find_one({"user_id": sender_id})
        if sender['coins'] < amount:
            await message.reply("<b>❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ᴄᴏɪɴs!</b>")
            return
        users_col.update_one({"user_id": sender_id}, {"$inc": {"coins": -amount}})
        users_col.update_one({"user_id": receiver.id}, {"$inc": {"coins": amount}})
        await message.reply_text(f"<b>┌╼「 💸 ᴄᴏɪɴ ɢɪғᴛ 」</b>\n<b>│ ғʀᴏᴍ: {get_mention(sender_id, message.from_user.first_name)}</b>\n<b>│ ᴛᴏ: {get_mention(receiver.id, receiver.first_name)}</b>\n<b>│ ᴀᴍᴏᴜɴᴛ: {amount}</b>\n<b>└╼━━━━ {B} ━━━━╾┘</b>")
    except: pass

# --- SUDO, ACOIN, MCOIN, RESET, STATS, TOP (Same as before) ---
@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    if not await check_sudo(message.from_user.id): return
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        sync_data(target)
        user = users_col.find_one({"user_id": target.id})
        new_val = 1 if user.get("is_sudo", 0) == 0 else 0
        users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": new_val}})
        status = "✨ sᴜᴅᴏ ᴀᴅᴅᴇᴅ" if new_val == 1 else "⚡ sᴜᴅᴏ ʀᴇᴍᴏᴠᴇᴅ"
        await message.reply_text(f"<b>┌╼「 sᴜᴅᴏ sᴛᴀᴛᴜs 」</b>\n<b>│ ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n<b>│ sᴛᴀᴛᴜs: {status}</b>\n<b>└╼━━━━ {B} ━━━━╾┘</b>")
    else:
        sudos = list(users_col.find({"is_sudo": 1}))
        res = f"<b>┌╼「 ✨ sᴜᴅᴏ ᴜsᴇʀs 」</b>\n"
        for i, s in enumerate(sudos, 1):
            res += f"<b>│ {i}.</b> {get_mention(s['user_id'], s.get('full_name', 'User'))}\n"
        res += f"<b>└╼━━━━ {B} ━━━━╾┘</b>"
        await message.reply_text(res)

@app.on_message(filters.command("acoin") & filters.group)
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): return
    if not message.reply_to_message: return
    parts = message.text.split()
    if len(parts) < 2: return
    try:
        amount = int(parts[1])
        target = message.reply_to_message.from_user
        sync_data(target)
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amount}})
        user = users_col.find_one({"user_id": target.id})
        await message.reply_text(f"<b>┌╼「 💰 ᴄᴏɪɴ ᴀᴅᴅᴇᴅ 」</b>\n<b>│ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n<b>│ ᴀᴍᴏᴜɴᴛ:</b> <code>{amount}</code>\n<b>│ ᴛᴏᴛᴀʟ:</b> <code>{user['coins']}</code>\n<b>└╼━━━━ {B} ━━━━╾┘</b>")
    except: pass

@app.on_message(filters.command("mcoin") & filters.group)
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): return
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
        await message.reply_text(f"<b>┌╼「 🔻 ᴄᴏɪɴ ᴍɪɴᴜs 」</b>\n<b>│ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n<b>│ ᴀᴍᴏᴜɴᴛ:</b> <code>{amount}</code>\n<b>│ ᴛᴏᴛᴀʟ:</b> <code>{user['coins']}</code>\n<b>└╼━━━━ {B} ━━━━╾┘</b>")
    except: pass

@app.on_message(filters.command("reset") & filters.group)
async def reset_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): return
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$set": {"coins": 0}})
        await message.reply_text(f"<b>┌╼「 🌀 ᴄᴏɪɴ ʀᴇsᴇᴛ 」</b>\n<b>│ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n<b>│ sᴛᴀᴛᴜs: ʙᴀʟᴀɴᴄᴇ ᴄʟᴇᴀʀᴇᴅ</b>\n<b>└╼━━━━ {B} ━━━━╾┘</b>")

@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    await message.reply_text(f"<b>┌╼「 📊 ᴜsᴇʀ sᴛᴀᴛs 」</b>\n<b>│ ᴜsᴇʀ :</b> {get_mention(target.id, target.first_name)}\n<b>│ ᴄᴏɪɴs :</b> <code>{user['coins']}</code>\n<b>│ ʀᴀɴᴋ :</b> <code>#{rank}</code>\n<b>└╼━━━━ {B} ━━━━╾┘</b>")

@app.on_message(filters.command("top") & filters.group)
async def leaderboard(client, message: Message):
    rows = list(users_col.find().sort("coins", -1).limit(10))
    board = f"<b>┌╼「 🏆 ᴛᴏᴘ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ 」</b>\n"
    for i, row in enumerate(rows, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        board += f"<b>│ {emoji} {i:02d}.</b> {get_mention(row['user_id'], row.get('full_name', 'User'))} ➲ <code>{row.get('coins', 0)}</code>\n"
    board += f"<b>└╼━━━━ {B} ━━━━╾┘</b>"
    await message.reply_text(board)

@app.on_message(filters.group & ~filters.bot, group=1)
async def auto_sync(client, message: Message):
    if message.from_user: sync_data(message.from_user)

if __name__ == "__main__":
    Thread(target=run_web).start()
    if APP_URL: Thread(target=ping_self, daemon=True).start()
    app.run()
