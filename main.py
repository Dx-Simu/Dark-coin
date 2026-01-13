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
from datetime import timedelta

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
web = Flask('')
@web.route('/')
def home(): return f"{B} sʏsᴛᴇᴍ ᴏɴʟɪɴᴇ"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

app = Client("DX_COIN_FINAL", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPERS ---
async def check_sudo(user_id):
    if user_id in INIT_SUDO: return True
    user = users_col.find_one({"user_id": user_id})
    return user.get("is_sudo", 0) == 1 if user else False

def get_mention(user_id, name):
    clean_name = re.sub(r'[<>#]', '', name or "Usᴇʀ")
    return f"<a href='tg://user?id={user_id}'>{clean_name[:15]}</a>"

def get_rank_badge(coins):
    if coins >= 400: return "💎 [ᴄᴏᴅᴇ]"
    elif coins >= 200: return "🌟🌟🌟 (ᴀᴅ/ʀᴜʟᴇʀ)"
    elif coins >= 100: return "🌟🌟 (ʜ-ᴄᴀᴘᴛᴀɪɴ)"
    elif coins >= 50: return "🌟 (ᴅᴇs-ɴᴀᴍᴇ)"
    return "⚪️"

def sync_data(user):
    if not user: return
    users_col.update_one(
        {"user_id": user.id},
        {"$set": {"full_name": f"{user.first_name} {user.last_name or ''}".strip(), "username": user.username}, 
         "$setOnInsert": {"coins": 0, "vault": 0, "v_time": time.time(), "last_claim": 0, "is_sudo": 0}},
        upsert=True
    )

async def del_cmd(message: Message):
    try: await message.delete()
    except: pass

# --- COMMANDS SECTION ---

@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━━━「 ✨ {B} ᴍᴇɴᴜ 」━━━━┓</b>\n"
        f"<b>┃ 👤 ʜɪ: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 📊 /coin  • ᴄʜᴇᴄᴋ ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏆 /ctop  • ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n"
        f"<b>┃ 🎁 /claim • ᴅᴀɪʟʏ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 💸 /gift  • sᴇɴᴅ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🏦 /vault • sᴀᴠᴇ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 📜 /crules• ʙᴏᴛ ʀᴜʟᴇs</b>\n"
        f"<b>┃ 🛠️ /cusage• ʜᴏᴡ ᴛᴏ ᴜsᴇ</b>\n"
        f"<b>┃ ⚡ /sudo  • ᴀᴅᴍɪɴ ʟɪsᴛ</b>\n"
        f"<b>┗━━━━━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.command("acoin") & filters.group)
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    await del_cmd(message)
    if not message.reply_to_message or len(message.text.split()) < 2:
        return await message.reply(f"{get_mention(message.from_user.id, message.from_user.first_name)} ⚠️ ᴜsᴀɢᴇ: ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ `/acoin 10`")
    try:
        amt = int(message.text.split()[1])
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amt}})
        await message.reply(f"<b>┏━━━━「 ✅ ᴀᴅᴅ 」━━━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ 💰: {amt} ᴄᴏɪɴs ᴀᴅᴅᴇᴅ\n┗━━━━━━━━━━━━━━┛</b>")
    except: pass

@app.on_message(filters.command("mcoin") & filters.group)
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    await del_cmd(message)
    if not message.reply_to_message or len(message.text.split()) < 2:
        return await message.reply(f"{get_mention(message.from_user.id, message.from_user.first_name)} ⚠️ ᴜsᴀɢᴇ: ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ `/mcoin 10`")
    try:
        amt = int(message.text.split()[1])
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": -amt}})
        await message.reply(f"<b>┏━━━━「 🔻 ᴍɪɴᴜs 」━━━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ 💰: {amt} ᴄᴏɪɴs ᴍɪɴᴜsᴇᴅ\n┗━━━━━━━━━━━━━━┛</b>")
    except: pass

@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    await del_cmd(message)
    parts = message.text.split()
    if not message.reply_to_message or len(parts) < 2:
        return await message.reply(f"{get_mention(message.from_user.id, message.from_user.first_name)} ⚠️ ᴜsᴀɢᴇ: ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ `/gift 10`")
    try:
        amt = int(parts[1])
        sender_id = message.from_user.id
        receiver = message.reply_to_message.from_user
        if sender_id == receiver.id: return
        sender = users_col.find_one({"user_id": sender_id})
        if sender['coins'] >= amt:
            users_col.update_one({"user_id": sender_id}, {"$inc": {"coins": -amt}})
            users_col.update_one({"user_id": receiver.id}, {"$inc": {"coins": amt}})
            await message.reply(f"<b>┏━━━━「 💸 ɢɪғᴛ 」━━━━┓\n┃ 👤 ғʀᴏᴍ: {get_mention(sender_id, message.from_user.first_name)}\n┃ 👤 ᴛᴏ: {get_mention(receiver.id, receiver.first_name)}\n┃ 💰 ᴀᴍᴛ: {amt} ᴄᴏɪɴs\n┗━━━━━━━━━━━━━━┛</b>")
        else:
            await message.reply("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ᴄᴏɪɴs!")
    except: pass

@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.from_user
    if message.reply_to_message: target = message.reply_to_message.from_user
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    badge = get_rank_badge(user['coins'])
    rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    
    await message.reply_text(
        f"<b>┏━━━━「 📊 ᴄᴏɪɴ sᴛᴀᴛs 」━━━━┓</b>\n"
        f"<b>┃ 👤 ɴᴀᴍᴇ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 🆔 ᴜ-ɪᴅ: <code>{target.id}</code></b>\n"
        f"<b>┣━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 💰 ᴘᴏᴄᴋᴇᴛ: {user['coins']} ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏦 ᴠᴀᴜʟᴛ: {user.get('vault', 0)} ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏆 ʀᴀɴᴋɪɴɢ: #{rank}</b>\n"
        f"<b>┃ 🎖️ ʙᴀᴅɢᴇ: {badge}</b>\n"
        f"<b>┗━━━━━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    last_claim = user.get("last_claim", 0)
    if time.time() - last_claim < 259200:
        rem = 259200 - (time.time() - last_claim)
        return await message.reply(f"<b>┏━━━━「 ⏳ ᴡᴀɪᴛ 」━━━━┓\n┃ 👤: {get_mention(user_id, message.from_user.first_name)}\n┃ ⏳ ɴᴇxᴛ: {str(timedelta(seconds=int(rem)))}\n┗━━━━━━━━━━━━━━┛</b>")
    users_col.update_one({"user_id": user_id}, {"$inc": {"coins": 1}, "$set": {"last_claim": time.time()}})
    await message.reply(f"<b>┏━━━━「 ✅ ᴅᴏɴᴇ 」━━━━┓\n┃ 👤: {get_mention(user_id, message.from_user.first_name)}\n┃ 💰: 1 ᴄᴏɪɴ ᴄʟᴀɪᴍᴇᴅ!\n┗━━━━━━━━━━━━━━┛</b>")

@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    parts = message.text.split()
    
    if len(parts) == 1:
        return await message.reply(
            f"<b>┏━━━━「 🏦 ᴠᴀᴜʟᴛ 」━━━━┓</b>\n"
            f"<b>┃ 👤: {get_mention(user_id, message.from_user.first_name)}</b>\n"
            f"<b>┃ 💰 ʙᴀʟ: {user.get('vault', 0)} ᴄᴏɪɴs</b>\n"
            f"<b>┣━━━━━━━━━━━━━━</b>\n"
            f"<b>┃ 📥 `/vault dep 10` - sᴀᴠᴇ</b>\n"
            f"<b>┃ 📤 `/vault wd 10` - ᴛᴀᴋᴇ</b>\n"
            f"<b>┗━━━━━━━━━━━━━━┛</b>"
        )
    try:
        act, amt = parts[1].lower(), int(parts[2])
        if act == "dep" and user['coins'] >= amt:
            users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -amt, "vault": amt}})
            await message.reply(f"<b>✅ {amt} ᴄᴏɪɴs ᴅᴇᴘᴏsɪᴛᴇᴅ ᴛᴏ ᴠᴀᴜʟᴛ!</b>")
        elif act == "wd" and user.get('vault', 0) >= amt:
            users_col.update_one({"user_id": user_id}, {"$inc": {"coins": amt, "vault": -amt}})
            await message.reply(f"<b>🔓 {amt} ᴄᴏɪɴs ᴡɪᴛʜᴅʀᴀᴡɴ ғʀᴏᴍ ᴠᴀᴜʟᴛ!</b>")
        else:
            await message.reply("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ᴄᴏɪɴs!")
    except:
        await message.reply(f"⚠️ {get_mention(user_id, message.from_user.first_name)} ᴜsᴇ `/vault dep 10` ᴏʀ `/vault wd 10`")

@app.on_message(filters.command("cusage") & filters.group)
async def usage_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━━「 🛠️ ᴄᴏɪɴ ᴜsᴀɢᴇ 」━━━┓</b>\n"
        f"<b>┃ 👤: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 📌 /coin - ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ</b>\n"
        f"<b>┃ 📌 /claim - ᴄʟᴀɪᴍ 1 ᴄᴏɪɴ (3 ᴅᴀʏs)</b>\n"
        f"<b>┃ 📌 /gift [ᴀᴍᴛ] - ʀᴇᴘʟʏ ᴛᴏ sᴇɴᴅ</b>\n"
        f"<b>┃ 📌 /vault dep [ᴀᴍᴛ] - sᴀᴠᴇ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 📌 /vault wd [ᴀᴍᴛ] - ᴛᴀᴋᴇ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 📌 /ctop - sᴇᴇ ʀɪᴄʜᴇsᴛ ᴜsᴇʀs</b>\n"
        f"<b>┃ 📌 /crules - sᴇᴇ ᴇᴀʀɴɪɴɢ ʀᴜʟᴇs</b>\n"
        f"<b>┣━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ ⚠️ ᴀʟᴡᴀʏs ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ</b>\n"
        f"<b>┃ ғᴏʀ /gift, /acoin, /mcoin</b>\n"
        f"<b>┗━━━━━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.group & ~filters.bot)
async def auto_sync(client, message: Message):
    if message.from_user: sync_data(message.from_user)

@app.on_message(filters.command("crules") & filters.group)
async def rules_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━━「 📜 {B} ʀᴜʟᴇs 」━━━┓</b>\n"
        f"<b>┃ 👤: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 🔸 ᴅᴀʀᴋ ɢᴀɴɢ ᴜ-ᴀᴅᴅ: 2 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 ᴀᴅᴅᴀ ɢ-ʜᴀᴄᴋ(500+): 5 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 ᴀᴅᴅᴀ ɢ-ʜᴀᴄᴋ(-500): 3 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔸 ʜᴏᴛʟɪɴᴇ ɢ-ʜᴀᴄᴋ: 10 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 -15 ʏ-ɢʀᴏᴜᴘ ʜᴀᴄᴋ: 12 ᴄᴏɪɴ</b>\n"
        f"<b>┣━━━━━ 🎖️ sᴛᴀʀs ━━━━━</b>\n"
        f"<b>┃ ⭐: ᴅᴇsᴄʀɪʙᴛɪᴏɴ ɴᴀᴍᴇ</b>\n"
        f"<b>┃ ⭐⭐: ʜᴏᴛʟɪɴᴇ ᴄᴀᴘᴛᴀɪɴ</b>\n"
        f"<b>┃ ⭐⭐⭐: ᴀᴅᴍɪɴ / ʀᴜʟᴇʀ</b>\n"
        f"<b>┗━━━━━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.command("ctop") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    rows = list(users_col.find().sort("coins", -1).limit(10))
    board = f"<b>┏━━━━「 🏆 ᴛᴏᴘ ʀɪᴄʜᴇsᴛ 」━━━━┓</b>\n"
    for i, row in enumerate(rows, 1):
        rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}.</b>"
        board += f"<b>┃ {rank_icon} {get_mention(row['user_id'], row.get('full_name'))}</b>\n"
        board += f"<b>┃ ╰╼ 💰 {row.get('coins', 0)} • {get_rank_badge(row.get('coins'))}</b>\n"
    board += f"<b>┗━━━━━━━━━━━━━━┛</b>"
    await message.reply_text(board)

@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    await del_cmd(message)
    parts = message.text.split()
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        if len(parts) > 1 and parts[1].lower() == "r":
            if message.from_user.id != OWNER_ID: return
            users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": 0}})
            return await message.reply(f"<b>┏━━━━「 🔴 sᴜᴅᴏ 」━━━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ ⚡: ʀᴇᴍᴏᴠᴇᴅ\n┗━━━━━━━━━━━━━━┛</b>")
        users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": 1}})
        await message.reply(f"<b>┏━━━━「 🟢 sᴜᴅᴏ 」━━━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ ⚡: ᴀᴅᴅᴇᴅ\n┗━━━━━━━━━━━━━━┛</b>")
    else:
        sudos = list(users_col.find({"is_sudo": 1}))
        res = "<b>┏━━━━「 ✨ sᴜᴅᴏ ʟɪsᴛ 」━━━━┓\n"
        for i, s in enumerate(sudos, 1): res += f"┃ {i}. {get_mention(s['user_id'], s.get('full_name'))}\n"
        res += "┗━━━━━━━━━━━━━━┛</b>"
        await message.reply(res)

async def start_bot():
    await app.start()
    print("Bot Started!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.get_event_loop().run_until_complete(start_bot())
