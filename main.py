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

# --- DATABASE ---
MONGO_URL = "mongodb+srv://shadowur6_db_user:8AIIxZUjpanaQBjh@dx-codex.fmqcovu.mongodb.net/?retryWrites=true&w=majority&appName=Dx-codex"
client_db = MongoClient(MONGO_URL, connectTimeoutMS=30000, socketTimeoutMS=None, connect=False)
db = client_db["DX_COIN_DB"]
users_col = db["users"]

# --- WEB SERVER & KEEP ALIVE ---
APP_URL = os.environ.get("https://dark-coin.onrender.com") 
web = Flask('')
@web.route('/')
def home(): return f"{B} ADVANCED SYSTEM ONLINE"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

def ping_self():
    while True:
        try:
            if APP_URL: requests.get(APP_URL, timeout=10)
        except: pass
        time.sleep(300)

app = Client("DX_COIN_FINAL", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
INIT_SUDO = [6366113192, 6703335929, 6737589257]

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
    try:
        name = f"{user.first_name} {user.last_name or ''}".strip()
        users_col.update_one(
            {"user_id": user.id},
            {"$set": {"full_name": name, "username": user.username}, 
             "$setOnInsert": {"coins": 0, "vault": 0, "v_time": time.time(), "msg_count": 0, "last_claim": 0, "is_sudo": 0}},
            upsert=True
        )
    except: pass

async def del_cmd(message: Message):
    try: await message.delete()
    except: pass

# --- 1. MENU ---
@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>╭╼「 ✨ {B} ᴍᴇɴᴜ 」</b>\n"
        f"<b>│ 👤 {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>├ 📊 /coin • /top • /claim</b>\n"
        f"<b>├ 🏦 /vault • /gift • /shop</b>\n"
        f"<b>├ 📢 /buyad | ⚡ /sudo</b>\n"
        f"<b>╰╼━━━━ {B} ━━━━╾╯</b>"
    )

# --- 2. COIN & RANKING ---
@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    await message.reply_text(
        f"<b>╭╼「 📊 sᴛᴀᴛs 」</b>\n"
        f"<b>├ ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>├ ᴄᴏɪɴ: {user['coins']} • ʀᴀɴᴋ: #{rank}</b>\n"
        f"<b>╰╼━━━━ {B} ━━━━╾╯</b>"
    )

@app.on_message(filters.command("top") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    rows = list(users_col.find().sort("coins", -1).limit(10))
    board = f"<b>╭╼「 🏆 ᴛᴏᴘ 10 」</b>\n"
    for i, row in enumerate(rows, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        board += f"<b>├ {emoji} {get_mention(row['user_id'], row.get('full_name', 'User'))} • <code>{row.get('coins', 0)}</code></b>\n"
    board += f"<b>╰╼━━━━ {B} ━━━━╾╯</b>"
    await message.reply_text(board)

# --- 3. VAULT ---
@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    sync_data(message.from_user)
    user = users_col.find_one({"user_id": user_id})
    parts = message.text.split()
    if len(parts) == 1:
        days = int((time.time() - user.get("v_time", time.time())) / 86400)
        interest = int(user.get('vault', 0) * (days * 0.0001))
        await message.reply(
            f"<b>╭╼「 🏦 ᴠᴀᴜʟᴛ 」</b>\n"
            f"<b>├ ᴜsᴇʀ: {get_mention(user_id, message.from_user.first_name)}</b>\n"
            f"<b>├ ʙᴀʟ: {user.get('vault', 0)} | ɪɴᴛ: {interest}</b>\n"
            f"<b>╰╼━━━━ {B} ━━━━╾╯</b>"
        )
    elif len(parts) >= 3:
        act, amt = parts[1], int(parts[2])
        if act == "dep" and user['coins'] >= amt:
            users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -amt, "vault": amt}, "$set": {"v_time": time.time()}})
            await message.reply(f"<b>✅ {get_mention(user_id, message.from_user.first_name)} ᴅᴇᴘᴏsɪᴛᴇᴅ!</b>")
        elif act == "wd" and user.get('vault', 0) >= amt:
            users_col.update_one({"user_id": user_id}, {"$inc": {"coins": amt, "vault": -amt}})
            await message.reply(f"<b>🔓 {get_mention(user_id, message.from_user.first_name)} ᴡɪᴛʜᴅʀᴀᴡɴ!</b>")

# --- 4. SUDO ENGINE ---
@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    if not await check_sudo(message.from_user.id):
        return await del_cmd(message)
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        sync_data(target)
        user = users_col.find_one({"user_id": target.id})
        new_val = 1 if user.get("is_sudo", 0) == 0 else 0
        users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": new_val}})
        status = "✨ ᴀᴅᴅᴇᴅ" if new_val == 1 else "⚡ ʀᴇᴍᴏᴠᴇᴅ"
        await message.reply_text(f"<b>╭╼「 sᴜᴅᴏ 」</b>\n<b>├ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n<b>├ sᴛᴀᴛᴜs:</b> {status}\n<b>╰╼━━━━╾╯</b>")
    else:
        sudos = list(users_col.find({"is_sudo": 1}))
        res = f"<b>╭╼「 ✨ sᴜᴅᴏ ʟɪsᴛ 」</b>\n"
        for i, s in enumerate(sudos, 1):
            res += f"<b>├ {i}. {get_mention(s['user_id'], s.get('full_name', 'User'))}</b>\n"
        res += f"<b>╰╼━━━━╾╯</b>"
        await message.reply_text(res)
    await del_cmd(message)

# --- 5. COIN CONTROL ---
@app.on_message(filters.command("acoin") & filters.group)
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message:
        return await del_cmd(message)
    try:
        amt = int(message.text.split()[1])
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amt}})
        await message.reply(f"<b>💰 ᴀᴅᴅᴇᴅ {amt} ᴄᴏɪɴs ᴛᴏ {get_mention(target.id, target.first_name)}</b>")
    except: pass
    await del_cmd(message)

@app.on_message(filters.command("mcoin") & filters.group)
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message:
        return await del_cmd(message)
    try:
        amt = int(message.text.split()[1])
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": -amt}})
        await message.reply(f"<b>🔻 ᴍɪɴᴜs {amt} ᴄᴏɪɴs ғʀᴏᴍ {get_mention(target.id, target.first_name)}</b>")
    except: pass
    await del_cmd(message)

@app.on_message(filters.command("reset") & filters.group)
async def reset_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message:
        return await del_cmd(message)
    target = message.reply_to_message.from_user
    users_col.update_one({"user_id": target.id}, {"$set": {"coins": 0}})
    await message.reply(f"<b>🌀 ʙᴀʟᴀɴᴄᴇ ʀᴇsᴇᴛ ғᴏʀ {get_mention(target.id, target.first_name)}</b>")
    await del_cmd(message)

@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    if time.time() - user.get("last_claim", 0) < 86400: 
        return await message.reply(f"<b>❌ {get_mention(user_id, message.from_user.first_name)}, ᴛʀʏ ᴛᴏᴍᴏʀʀᴏᴡ!</b>")
    users_col.update_one({"user_id": user_id}, {"$inc": {"coins": 1}, "$set": {"last_claim": time.time()}})
    await message.reply(f"<b>🎁 {get_mention(user_id, message.from_user.first_name)}, 1 ᴄᴏɪɴs ᴄʟᴀɪᴍᴇᴅ!</b>")

@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    await del_cmd(message)
    if not message.reply_to_message: return
    try:
        amt = int(message.text.split()[1])
        sender_id = message.from_user.id
        target_id = message.reply_to_message.from_user.id
        sender = users_col.find_one({"user_id": sender_id})
        if sender['coins'] >= amt:
            users_col.update_one({"user_id": sender_id}, {"$inc": {"coins": -amt}})
            users_col.update_one({"user_id": target_id}, {"$inc": {"coins": amt}})
            await message.reply(f"<b>💸 {get_mention(sender_id, message.from_user.first_name)} ɢɪғᴛᴇᴅ {amt} ᴛᴏ {get_mention(target_id, message.reply_to_message.from_user.first_name)}!</b>")
    except: pass

# --- 6. SHOP & ADS ---
@app.on_message(filters.command("buyad") & filters.group)
async def buy_ad(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    if user['coins'] < 10: return await message.reply(f"<b>❌ {get_mention(user_id, message.from_user.first_name)}, ɴᴇᴇᴅ 10 ᴄᴏɪɴs!</b>")
    ad = message.text.split(None, 1)[1]
    users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -10}})
    await message.reply(f"<b>╭╼「 📢 {B} ᴀᴅ 」</b>\n<b>├ ʙʏ: {get_mention(user_id, message.from_user.first_name)}</b>\n<b>├ ᴍsɢ: {ad}</b>\n<b>╰╼━━━━╾╯</b>")

@app.on_message(filters.command("shop") & filters.group)
async def shop_handler(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    if len(message.text.split()) == 1:
        return await message.reply(f"<b>╭╼「 🛒 sʜᴏᴘ 」</b>\n<b>├ 1. VIP (15) • 2. KING (15)</b>\n<b>╰╼━━━━╾╯</b>")
    title = "VIP" if message.text.split()[1] == "1" else "KING"
    user = users_col.find_one({"user_id": user_id})
    if user['coins'] >= 15:
        users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -15}, "$set": {"title": title}})
        await message.reply(f"<b>🔥 {get_mention(user_id, message.from_user.first_name)} ɪs ɴᴏᴡ {title}!</b>")

# --- 7. MISSION & AUTO SYNC ---
@app.on_message(filters.group & ~filters.bot, group=1)
async def mission_tracker(client, message: Message):
    if not message.from_user: return
    sync_data(message.from_user)
    users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"msg_count": 1}})
    user = users_col.find_one({"user_id": message.from_user.id})
    if user.get('msg_count', 0) >= 100:
        users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": 1}, "$set": {"msg_count": 0}})
        await message.reply(f"<b>🏆 {get_mention(user['user_id'], user['full_name'])} ᴇᴀʀɴᴇᴅ 1 ᴄᴏɪɴ!</b>")

if __name__ == "__main__":
    Thread(target=run_web).start()
    if APP_URL: Thread(target=ping_self, daemon=True).start()
    app.run()
