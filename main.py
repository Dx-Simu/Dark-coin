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
def home(): return f"{B} ꜱʏꜱᴛᴇᴍ ᴏɴʟɪɴᴇ"

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
    clean_name = re.sub(r'[<>#]', '', name or "User")
    return f"<a href='tg://user?id={user_id}'>{clean_name[:15]}</a>"

def get_rank_badge(coins):
    if coins >= 400: return "💎 [ᴄᴏᴅᴇ]"
    elif coins >= 200: return "🌟🌟🌟 (ᴀᴅ/ʀᴜʟᴇʀ)"
    elif coins >= 100: return "🌟🌟 (ʜ-ᴄᴀᴘᴛᴀɪɴ)"
    elif coins >= 50: return "🌟 (ᴅᴇs-ɴᴀᴍᴇ)"
    return "🌑"

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

# --- COMMANDS SECTION ---

@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━━━「 ✨ {B} ᴍᴇɴᴜ 」━━━━┓</b>\n"
        f"<b>┃ 👤 ʜɪ: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 📊 /coin  • /ctop</b>\n"
        f"<b>┃ 🎁 /claim • /gift</b>\n"
        f"<b>┃ 🏦 /vault • /shop</b>\n"
        f"<b>┃ 📜 /crules • 🛠️ /cusage</b>\n"
        f"<b>┃ ⚡ /sudo • 📢 /buyad</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.command("acoin") & filters.group)
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    await del_cmd(message)
    if not message.reply_to_message:
        return await message.reply(f"❌ {get_mention(message.from_user.id, message.from_user.first_name)}, ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ!\nᴜsᴀɢᴇ: <code>/acoin [ᴀᴍᴏᴜɴᴛ]</code>")
    try:
        amt = int(message.text.split()[1])
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amt}})
        await message.reply(f"<b>┏━━━━「 ✅ ᴀᴅᴅ 」━━━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ 💰: {amt} ᴄᴏɪɴs ᴀᴅᴅᴇᴅ\n┗━━━━━━━━━━━━━━━┛</b>")
    except:
        await message.reply(f"❌ {get_mention(message.from_user.id, message.from_user.first_name)}, ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ!\nᴜsᴀɢᴇ: <code>/acoin 10</code>")

@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    await del_cmd(message)
    parts = message.text.split()
    if not message.reply_to_message or len(parts) < 2:
        return await message.reply(f"❌ {get_mention(message.from_user.id, message.from_user.first_name)}, ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ!\nᴜsᴀɢᴇ: <code>/gift [ᴀᴍᴏᴜɴᴛ]</code>")
    try:
        amt = int(parts[1])
        sender_id = message.from_user.id
        receiver = message.reply_to_message.from_user
        sender = users_col.find_one({"user_id": sender_id})
        if sender['coins'] >= amt:
            users_col.update_one({"user_id": sender_id}, {"$inc": {"coins": -amt}})
            users_col.update_one({"user_id": receiver.id}, {"$inc": {"coins": amt}})
            await message.reply(f"<b>┏━━━━「 💸 ɢɪғᴛ 」━━━━┓\n┃ 👤 ғʀᴏᴍ: {get_mention(sender_id, message.from_user.first_name)}\n┃ 👤 ᴛᴏ: {get_mention(receiver.id, receiver.first_name)}\n┃ 💰 ᴀᴍᴛ: {amt} ᴄᴏɪɴs\n┗━━━━━━━━━━━━━━━┛</b>")
        else:
            await message.reply(f"❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ᴄᴏɪɴs!")
    except: pass

@app.on_message(filters.command("shop") & filters.group)
async def shop_handler(client, message: Message):
    await del_cmd(message)
    shop_text = (
        f"<b>┏━━━━「 🛒 {B} sʜᴏᴘ 」━━━━┓</b>\n"
        f"<b>┃ 👤: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 𝟷. ᴀᴅ-ᴘᴏsᴛ (𝟷ʜ): 𝟻𝟶 ᴄᴏɪɴs</b>\n"
        f"<b>┃ 𝟸. ᴠɪᴘ ʀᴀɴᴋ (𝟽ᴅ): 𝟸𝟶𝟶 ᴄᴏɪɴs</b>\n"
        f"<b>┃ 𝟹. ᴘʀᴇᴍɪᴜᴍ ᴛᴀɢ: 𝟷𝟶𝟶 ᴄᴏɪɴs</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 💡 ᴛᴏ ʙᴜʏ ᴜsᴇ: /buyad [ɪᴛᴇᴍ ɴᴏ]</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━┛</b>"
    )
    await message.reply_text(shop_text)

@app.on_message(filters.command("buyad") & filters.group)
async def buy_handler(client, message: Message):
    await del_cmd(message)
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply(f"❌ {get_mention(message.from_user.id, message.from_user.first_name)}, ᴘʟᴇᴀsᴇ sᴇʟᴇᴄᴛ ᴀɴ ɪᴛᴇᴍ!\nᴜsᴀɢᴇ: <code>/buyad [𝟷/𝟸/𝟹]</code>")
    
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    item = parts[1]
    
    costs = {"1": 50, "2": 200, "3": 100}
    names = {"1": "ᴀᴅ-ᴘᴏsᴛ (𝟷ʜ)", "2": "ᴠɪᴘ ʀᴀɴᴋ (𝟽ᴅ)", "3": "ᴘʀᴇᴍɪᴜᴍ ᴛᴀɢ"}

    if item in costs:
        if user['coins'] >= costs[item]:
            users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -costs[item]}})
            await message.reply(f"<b>┏━━━━「 🛍️ ᴘᴜʀᴄʜᴀsᴇ 」━━━━┓\n┃ 👤: {get_mention(user_id, message.from_user.first_name)}\n┃ 📦 ɪᴛᴇᴍ: {names[item]}\n┃ ✅ sᴛᴀᴛᴜs: sᴜᴄᴄᴇssғᴜʟ\n┗━━━━━━━━━━━━━━━┛</b>")
            await app.send_message(OWNER_ID, f"📢 ɴᴇᴡ ᴘᴜʀᴄʜᴀsᴇ!\nᴜsᴇʀ: {user_id}\nɪᴛᴇᴍ: {names[item]}")
        else:
            await message.reply("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ᴄᴏɪɴs ᴛᴏ ʙᴜʏ ᴛʜɪs!")
    else:
        await message.reply("❌ ɪɴᴠᴀʟɪᴅ ɪᴛᴇᴍ ɴᴜᴍʙᴇʀ!")

@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.from_user
    if message.reply_to_message: target = message.reply_to_message.from_user
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    badge = get_rank_badge(user['coins'])
    rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    
    stats_msg = (
        f"<b>┏━━━━━「 📊 ᴄᴏɪɴ sᴛᴀᴛs 」━━━━━┓</b>\n"
        f"<b>┃ 👤 ɴᴀᴍᴇ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 🆔 ᴜ-ɪᴅ: <code>{target.id}</code></b>\n"
        f"<b>┣━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 💰 ᴄᴏɪɴs: {user['coins']} ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏦 ᴠᴀᴜʟᴛ: {user.get('vault', 0)} ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏆 ʀᴀɴᴋ: #{rank} ɪɴ ɢʟᴏʙᴀʟ</b>\n"
        f"<b>┃ 🎖️ ʟᴇᴠᴇʟ: {badge}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 📅 ᴘᴏᴡᴇʀᴇᴅ: ᴅx ᴄʜᴀɪɴ—ᴛᴇᴄʜɴᴏʟᴏɢʏ</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━━━━━━┛</b>"
    )
    await message.reply_text(stats_msg)

@app.on_message(filters.command("cusage") & filters.group)
async def usage_handler(client, message: Message):
    await del_cmd(message)
    usage_text = (
        f"<b>┏━━━「 🛠️ {B} ʜᴇʟᴘ ɢᴜɪᴅᴇ 」━━┓</b>\n"
        f"<b>┃ 👤: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 📊 /coin - ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ</b>\n"
        f"<b>┃ 🏆 /ctop - sʜᴏᴡ ᴛᴏᴘ ʀɪᴄʜ ᴜsᴇʀs</b>\n"
        f"<b>┃ 🎁 /claim - ɢᴇᴛ ғʀᴇᴇ ᴅᴀɪʟʏ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 💸 /gift [ᴀᴍᴛ] - sᴇɴᴅ ᴄᴏɪɴ ᴛᴏ ᴜsᴇʀ</b>\n"
        f"<b>┃ 🏦 /vault dep [ᴀᴍᴛ] - sᴀᴠᴇ ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🔓 /vault wd [ᴀᴍᴛ] - ᴛᴀᴋᴇ ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🛒 /shop - ᴠɪᴇᴡ ɪᴛᴇᴍs ᴛᴏ ʙᴜʏ</b>\n"
        f"<b>┃ 📢 /buyad [ɴᴏ] - ʙᴜʏ sʜᴏᴘ ɪᴛᴇᴍs</b>\n"
        f"<b>┃ 📜 /crules - sᴇᴇ ᴇᴀʀɴɪɴɢ ʀᴜʟᴇs</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ ⚡ sᴜᴅᴏ ᴄᴏᴍᴍᴀɴᴅs: /acoin, /mcoin</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━━┛</b>"
    )
    await message.reply_text(usage_text)

# --- (Other existing commands with updated fonts & auto-delete) ---

@app.on_message(filters.command("crules") & filters.group)
async def rules_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━━━「 📜 {B} ʀᴜʟᴇs 」━━━━┓</b>\n"
        f"<b>┃ 👤: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 🔸 ᴅᴀʀᴋ ɢᴀɴɢ ᴜ-ᴀᴅᴅ: <code>2 ᴄᴏɪɴ</code></b>\n"
        f"<b>┃ 🔹 ᴀᴅᴅᴀ ɢ-ʜᴀᴄᴋ(500+): <code>5 ᴄᴏɪɴ</code></b>\n"
        f"<b>┃ 🔹 ᴀᴅᴅᴀ ɢ-ʜᴀᴄᴋ(-500): <code>3 ᴄᴏɪɴ</code></b>\n"
        f"<b>┃ 🔸 ʜᴏᴛʟɪɴᴇ ɢ-ʜᴀᴄᴋ: <code>10 ᴄᴏɪɴ</code></b>\n"
        f"<b>┃ 🔹 -15 ʏ-ɢʀᴏᴜᴘ ʜᴀᴄᴋ: <code>12 ᴄᴏɪɴ</code></b>\n"
        f"<b>┣━━━━ 🎖️ sᴛᴀʀs ━━━━</b>\n"
        f"<b>┃ ⭐: ᴅᴇsᴄʀɪʙᴛɪᴏɴ ɴᴀᴍᴇ</b>\n"
        f"<b>┃ ⭐⭐: ʜᴏᴛʟɪɴᴇ ᴄᴀᴘᴛᴀɪɴ</b>\n"
        f"<b>┃ ⭐⭐⭐: ᴀᴅᴍɪɴ / ʀᴜʟᴇʀ</b>\n"
        f"<b>┗━━━━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.group & ~filters.bot)
async def auto_sync(client, message: Message):
    if message.from_user: sync_data(message.from_user)

async def start_bot():
    await app.start()
    print("Bot Started!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.get_event_loop().run_until_complete(start_bot())
