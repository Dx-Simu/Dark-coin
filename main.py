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
from datetime import datetime, timedelta

# --- CONFIGURATION ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8513850569:AAHCsKyy1nWTYVKH_MtbW8IhKyOckWLTEDA"
B = "ᴅx" 
OWNER_ID = 6703335929

# --- DATABASE ---
MONGO_URL = "mongodb+srv://shadowur6_db_user:8AIIxZUjpanaQBjh@dx-codex.fmqcovu.mongodb.net/?retryWrites=true&w=majority&appName=Dx-codex"
client_db = MongoClient(MONGO_URL, connectTimeoutMS=30000, socketTimeoutMS=None, connect=False)
db = client_db["DX_COIN_DB"]
users_col = db["users"]

# --- WEB SERVER ---
APP_URL = os.environ.get("https://dark-coin.onrender.com") 
web = Flask('')
@web.route('/')
def home(): return f"{B} SYSTEM ONLINE"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

app = Client("DX_COIN_FINAL", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- DAILY BACKUP SYSTEM ---
async def send_daily_backup():
    while True:
        await asyncio.sleep(86400)
        try:
            all_users = list(users_col.find())
            backup_msg = f"📊 **{B} DATABASE BACKUP**\n\n"
            for u in all_users:
                backup_msg += f"ID: `{u['user_id']}` | Coins: {u.get('coins', 0)}\n"
            await app.send_message(OWNER_ID, backup_msg)
        except: pass

# --- HELPERS ---
async def check_sudo(user_id):
    if user_id in INIT_SUDO: return True
    user = users_col.find_one({"user_id": user_id})
    return user.get("is_sudo", 0) == 1 if user else False

def get_mention(user_id, name):
    clean_name = re.sub(r'[<>#]', '', name or "User")
    return f"<a href='tg://user?id={user_id}'>{clean_name[:15]}</a>"

def sync_data(user):
    if not user: return
    users_col.update_one(
        {"user_id": user.id},
        {"$set": {"full_name": f"{user.first_name} {user.last_name or ''}".strip(), "username": user.username}, 
         "$setOnInsert": {"coins": 0, "vault": 0, "v_time": time.time(), "msg_count": 0, "last_claim": 0, "is_sudo": 0}},
        upsert=True
    )

async def del_cmd(message: Message):
    try: await message.delete()
    except: pass

# --- 1. MENU ---
@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━「 ✨ {B} ᴍᴇɴᴜ 」━━┓</b>\n"
        f"<b>┃ 👤 ʜɪ: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 📊 /coin  • /ctop</b>\n"
        f"<b>┃ 🎁 /claim • /gift</b>\n"
        f"<b>┃ 🏦 /vault • /shop</b>\n"
        f"<b>┃ 📢 /buyad • ⚡ /sudo</b>\n"
        f"<b>┗━━━━━━━━━━━━━┛</b>"
    )

# --- 2. COIN STATS ---
@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.from_user
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try: target = await client.get_users(message.command[1])
        except: 
            return await message.reply(f"<b>┏━「 ⚠️ ᴇʀʀᴏʀ 」━┓\n┃ {get_mention(message.from_user.id, message.from_user.first_name)}\n┃ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ!\n┗━━━━━━┛</b>")

    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    await message.reply_text(
        f"<b>┏━━「 📊 sᴛᴀᴛs 」━━┓</b>\n"
        f"<b>┃ 👤: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 💰 ᴄᴏɪɴs: {user['coins']}</b>\n"
        f"<b>┃ 🏆 ʀᴀɴᴋ: #{rank}</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

# --- 3. CLAIM SYSTEM ---
@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    last_claim = user.get("last_claim", 0)
    current_time = time.time()

    if current_time - last_claim < 86400:
        remaining = 86400 - (current_time - last_claim)
        rem_time = str(timedelta(seconds=int(remaining)))
        return await message.reply(
            f"<b>┏━「 🎁 ᴄʟᴀɪᴍ 」━┓</b>\n"
            f"<b>┃ 👤: {get_mention(user_id, message.from_user.first_name)}</b>\n"
            f"<b>┃ ⚠️ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ!</b>\n"
            f"<b>┃ ⏳ ɴᴇxᴛ: {rem_time}</b>\n"
            f"<b>┗━━━━━━━┛</b>"
        )
    
    users_col.update_one({"user_id": user_id}, {"$inc": {"coins": 1}, "$set": {"last_claim": current_time}})
    await message.reply(
        f"<b>┏━「 ✅ ᴅᴏɴᴇ 」━┓</b>\n"
        f"<b>┃ 👤: {get_mention(user_id, message.from_user.first_name)}</b>\n"
        f"<b>┃ 💰 ʏᴏᴜ ɢᴏᴛ 1 ᴄᴏɪɴ!</b>\n"
        f"<b>┃ ✨ ᴄᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏᴍᴏʀʀᴏᴡ.</b>\n"
        f"<b>┗━━━━━━━┛</b>"
    )

# --- 4. VAULT SYSTEM ---
@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    sync_data(message.from_user)
    user = users_col.find_one({"user_id": user_id})
    parts = message.text.split()

    if len(parts) == 1:
        return await message.reply(
            f"<b>┏━「 🏦 ᴠᴀᴜʟᴛ 」━┓</b>\n"
            f"<b>┃ 👤: {get_mention(user_id, message.from_user.first_name)}</b>\n"
            f"<b>┃ 💰 ʙᴀʟ: {user.get('vault', 0)}</b>\n"
            f"<b>┣━━━━ ʀᴜʟᴇs ━━━━</b>\n"
            f"<b>┃ 📥 ᴅᴇᴘᴏsɪᴛ: /vault dep 10</b>\n"
            f"<b>┃ 📤 ᴡɪᴛʜᴅʀᴀᴡ: /vault wd 10</b>\n"
            f"<b>┗━━━━━━━┛</b>"
        )
    try:
        act, amt = parts[1], int(parts[2])
        if act == "dep":
            if user['coins'] < amt: return await message.reply(f"<b>❌ {get_mention(user_id, message.from_user.first_name)}, ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴄᴏɪɴs!</b>")
            users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -amt, "vault": amt}})
            await message.reply(f"<b>✅ {amt} ᴄᴏɪɴs ᴀᴅᴅᴇᴅ ᴛᴏ ᴠᴀᴜʟᴛ!</b>")
        elif act == "wd":
            if user.get('vault', 0) < amt: return await message.reply(f"<b>❌ {get_mention(user_id, message.from_user.first_name)}, ɪɴsᴜғғɪᴄɪᴇɴᴛ ᴠᴀᴜʟᴛ!</b>")
            users_col.update_one({"user_id": user_id}, {"$inc": {"coins": amt, "vault": -amt}})
            await message.reply(f"<b>🔓 {amt} ᴄᴏɪɴs ᴡɪᴛʜᴅʀᴀᴡɴ!</b>")
    except:
        await message.reply(f"<b>⚠️ {get_mention(user_id, message.from_user.first_name)}, ᴜsᴇ ᴄᴏʀʀᴇᴄᴛ ғᴏʀᴍᴀᴛ!</b>")

# --- 5. GIFT SYSTEM ---
@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    await del_cmd(message)
    parts = message.text.split()
    user_id = message.from_user.id
    if not message.reply_to_message or len(parts) < 2:
        return await message.reply(f"<b>┏━「 🎁 ɢɪғᴛ 」━┓\n┃ 👤: {get_mention(user_id, message.from_user.first_name)}\n┃ ⚠️ ʀᴇᴘʟʏ & ᴛʏᴘᴇ: /gift 10\n┗━━━━━━━┛</b>")
    
    amt = int(parts[1])
    target_id = message.reply_to_message.from_user.id
    sender = users_col.find_one({"user_id": user_id})
    if sender['coins'] >= amt:
        users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -amt}})
        users_col.update_one({"user_id": target_id}, {"$inc": {"coins": amt}})
        await message.reply(f"<b>💸 {get_mention(user_id, message.from_user.first_name)} ɢɪғᴛᴇᴅ {amt} ᴛᴏ {get_mention(target_id, message.reply_to_message.from_user.first_name)}!</b>")

# --- 6. LEADERBOARD ---
@app.on_message(filters.command("ctop") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    rows = list(users_col.find().sort("coins", -1).limit(10))
    board = f"<b>┏━━「 🏆 ᴛᴏᴘ 10 」━━┓</b>\n"
    for i, row in enumerate(rows, 1):
        board += f"<b>┃ {i}. {get_mention(row['user_id'], row.get('full_name', 'User'))} • {row.get('coins', 0)}</b>\n"
    board += f"<b>┗━━━━━━━━━━┛</b>"
    await message.reply_text(board)

# --- 7. AUTO SYNC & TRACKER ---
@app.on_message(filters.group & ~filters.bot, group=1)
async def tracker(client, message: Message):
    if not message.from_user: return
    sync_data(message.from_user)
    users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"msg_count": 1}})
    user = users_col.find_one({"user_id": message.from_user.id})
    if user.get('msg_count', 0) >= 100:
        users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": 1}, "$set": {"msg_count": 0}})
        await message.reply(f"<b>🏆 {get_mention(message.from_user.id, message.from_user.first_name)} ᴇᴀʀɴᴇᴅ 1 ᴄᴏɪɴ!</b>")

# --- RUN BOT ---
async def start_bot():
    await app.start()
    asyncio.create_task(send_daily_backup())
    await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.get_event_loop().run_until_complete(start_bot())
