import asyncio
import os
import re
import time
import io
from datetime import timedelta
from threading import Thread
from flask import Flask
from pymongo import MongoClient
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UsernameInvalid, ChatAdminRequired

# --- CONFIGURATION ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8513850569:AAHCsKyy1nWTYVKH_MtbW8IhKyOckWLTEDA"
B = "ᴅx" 
OWNER_ID = 6703335929

# --- DATABASE ---
MONGO_URL = "mongodb+srv://shadowur6_db_user:8AIIxZUjpanaQBjh@dx-codex.fmqcovu.mongodb.net/?retryWrites=true&w=majority&appName=Dx-codex"
client_db = MongoClient(MONGO_URL, connectTimeoutMS=30000, connect=False)
db = client_db["DX_COIN_DB"]
users_col = db["users"]

# --- WEB SERVER ---
web = Flask('')
@web.route('/')
def home(): return f"{B} sʏsᴛᴇᴍ ᴏɴʟɪɴᴇ"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

# --- BOT CLIENT ---
app = Client("DX_COIN_V3", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPERS ---
async def check_sudo(user_id):
    if user_id in INIT_SUDO or user_id == OWNER_ID: return True
    user = users_col.find_one({"user_id": user_id})
    return user.get("is_sudo", 0) == 1 if user else False

def get_mention(user_id, name):
    name = re.sub(r'[<>#]', '', str(name)) if name else "Usᴇʀ"
    return f"<a href='tg://user?id={user_id}'>{name[:15]}</a>"

def get_rank_info(coins):
    if coins >= 400: return ("💎", "💎💎💎", "ᴄᴏᴅᴇ ᴏᴡɴᴇʀ")
    elif coins >= 200: return ("🌟🌟🌟", "⭐⭐⭐", "ᴀᴅ/ʀᴜʟᴇʀ")
    elif coins >= 100: return ("🌟🌟", "⭐⭐", "ʜ-ᴄᴀᴘᴛᴀɪɴ")
    elif coins >= 50: return ("🌟", "⭐", "ᴅᴇs-ɴᴀᴍᴇ")
    return ("⚪️", "🌑", "ᴍᴇᴍʙᴇʀ")

def sync_data(user):
    if not user: return
    users_col.update_one(
        {"user_id": user.id},
        {"$set": {"full_name": f"{user.first_name} {user.last_name or ''}".strip(), "username": user.username},
         "$setOnInsert": {"coins": 0, "vault": 0, "last_claim": 0, "is_sudo": 0}},
        upsert=True
    )

async def del_cmd(message):
    try: await message.delete()
    except: pass

async def get_target_user(client, message, parts):
    if message.reply_to_message: return message.reply_to_message.from_user
    if len(parts) > 1:
        u_input = parts[-1]
        if u_input.isdigit() and len(u_input) < 6: return None
        try: return await client.get_users(u_input)
        except: return None
    return None

# --- COMMANDS ---

@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    await message.reply_text(
        f"<b>┏━━「 ✨ {B} ᴍᴇɴᴜ 」━━┓</b>\n"
        f"<b>┃ 👤 ʜɪ: {m}</b>\n"
        f"<b>┣━━━━━━━━━━</b>\n"
        f"<b>┃ 📊 /coin  • ᴄʜᴇᴄᴋ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🏆 /ctop  • ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n"
        f"<b>┃ 🌟 /star  • sᴛᴀʀ ʟɪsᴛ</b>\n"
        f"<b>┃ 🎁 /claim • ᴅᴀɪʟʏ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 💸 /gift  • sᴇɴᴅ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🏦 /vault • sᴀᴠᴇ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 📜 /crules• ʙᴏᴛ ʀᴜʟᴇs</b>\n"
        f"<b>┃ ⚡ /sudo  • ᴀᴅᴍɪɴ ʟɪsᴛ</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message):
    await del_cmd(message)
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    badge, stars, rank_n = get_rank_info(user['coins'])
    g_rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    m = get_mention(target.id, target.first_name)
    
    await message.reply_text(
        f"<b>┏━━「 📊 ᴘʀᴏғɪʟᴇ 」━━┓</b>\n"
        f"<b>┃ 👤 ɴᴀᴍᴇ: {m}</b>\n"
        f"<b>┃ 🆔 ᴜɪᴅ: <code>{target.id}</code></b>\n"
        f"<b>┣━━━━━━━━━━</b>\n"
        f"<b>┃ 💰 ᴘᴏᴄᴋᴇᴛ: {user['coins']}</b>\n"
        f"<b>┃ 🏦 ᴠᴀᴜʟᴛ: {user.get('vault', 0)}</b>\n"
        f"<b>┃ 🏆 ʀᴀɴᴋ: #{g_rank}</b>\n"
        f"<b>┃ 🎖️ ʙᴀᴅɢᴇ: {badge} ({rank_n})</b>\n"
        f"<b>┃ ⭐ sᴛᴀʀs: {stars}</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.command("ctop") & filters.group)
async def leaderboard(client, message):
    await del_cmd(message)
    rows = list(users_col.find().sort("coins", -1).limit(10))
    board = f"<b>┏━━「 🏆 ᴛᴏᴘ ʀɪᴄʜᴇsᴛ 」━━┓</b>\n"
    for i, row in enumerate(rows, 1):
        icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"<b>{i}.</b>"
        badge, _, _ = get_rank_info(row.get('coins',0))
        u_name = row.get('full_name', 'User')[:12]
        board += f"<b>┃ {icon} {get_mention(row['user_id'], u_name)}</b>\n"
        board += f"<b>┃ ╰╼ ID: <code>{row['user_id']}</code> • 💰 {row.get('coins',0)} {badge}</b>\n"
    board += f"<b>┗━━━━━━━━━━┛</b>"
    await message.reply_text(board)

@app.on_message(filters.command("star") & filters.group)
async def star_list(client, message):
    await del_cmd(message)
    stars = users_col.find({"coins": {"$gte": 50}}).sort("coins", -1).limit(15)
    text = f"<b>┏━━「 🌟 sᴛᴀʀ ʜᴏʟᴅᴇʀs 」━━┓</b>\n"
    count = 0
    for u in stars:
        count += 1
        badge, s_icon, r_name = get_rank_info(u.get('coins', 0))
        text += f"<b>┃ {count}. {get_mention(u['user_id'], u.get('full_name'))}</b>\n"
        text += f"<b>┃ ╰╼ {badge} • {u['coins']} ({s_icon})</b>\n"
    if count == 0: text += "<b>┃ ❌ ɴᴏ sᴛᴀʀ ʜᴏʟᴅᴇʀs ʏᴇᴛ!</b>\n"
    text += f"<b>┗━━━━━━━━━━┛</b>"
    await message.reply(text)

@app.on_message(filters.command("acoin"))
async def add_coin(client, message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    parts = message.text.split()
    if len(parts) < 2: return await message.reply(f"<b>⚠️ {m}, ᴀᴍᴏᴜɴᴛ?</b>")
    try: amt = int(parts[1])
    except: return
    target = await get_target_user(client, message, parts)
    if not target: return await message.reply(f"<b>⚠️ {m}, ᴜsᴇր ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
    
    sync_data(target)
    old_data = users_col.find_one({"user_id": target.id})
    old_badge, _, _ = get_rank_info(old_data.get('coins', 0))
    
    users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amt}})
    new_c = old_data.get('coins', 0) + amt
    new_badge, stars, r_name = get_rank_info(new_c)
    
    await message.reply(f"<b>┏━━「 ✅ ᴀᴅᴅᴇᴅ 」━━┓\n┃ 👤 ʙʏ: {m}\n┃ 👤 ᴛᴏ: {get_mention(target.id, target.first_name)}\n┃ 💰 ᴀᴍᴛ: +{amt}\n┃ 👜 ᴛᴏᴛᴀʟ: {new_c}\n┗━━━━━━━━━━┛</b>")
    
    if new_badge != old_badge and new_c > old_data.get('coins', 0):
        try:
            p = await client.send_message(message.chat.id, f"<b>🎉 ʟᴇᴠᴇʟ ᴜᴘ! 🎉</b>\n\n<b>👤 {get_mention(target.id, target.first_name)}</b>\n<b>🌟 ʀᴀɴᴋ: {new_badge} ({r_name})</b>\n<b>━━━━━━━━━━</b>")
            await p.pin(both_sides=True)
        except: pass

@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    user = users_col.find_one({"user_id": message.from_user.id})
    now = time.time()
    if now - user.get("last_claim", 0) < 259200:
        rem = 259200 - (now - user.get("last_claim", 0))
        return await message.reply(f"<b>┏━━「 ⏳ ᴡᴀɪᴛ 」━━┓\n┃ 👤: {m}\n┃ ⏳: {str(timedelta(seconds=int(rem)))}\n┗━━━━━━━━━━┛</b>")
    users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": 1}, "$set": {"last_claim": now}})
    await message.reply(f"<b>┏━━「 ✅ ᴅᴏɴᴇ 」━━┓\n┃ 👤: {m}\n┃ 💰: +1 ᴄᴏɪɴ!\n┗━━━━━━━━━━┛</b>")

@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message):
    m = get_mention(message.from_user.id, message.from_user.first_name)
    parts = message.text.split()
    if len(parts) < 2: return await message.reply(f"<b>⚠️ {m}, ᴀᴍᴏᴜɴᴛ?</b>")
    try: amt = int(parts[1])
    except: return
    target = await get_target_user(client, message, parts)
    if not target or target.id == message.from_user.id: return await message.reply(f"<b>❌ {m}, ɪɴᴠᴀʟɪᴅ!</b>")
    
    sender = users_col.find_one({"user_id": message.from_user.id})
    if sender and sender['coins'] >= amt:
        users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": -amt}})
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amt}})
        await message.reply(f"<b>┏━━「 💸 sᴇɴᴛ 」━━┓\n┃ 👤 ғʀᴏᴍ: {m}\n┃ 👤 ᴛᴏ: {get_mention(target.id, target.first_name)}\n┃ 💰 ᴀᴍᴛ: {amt}\n┗━━━━━━━━━━┛</b>")
    else: await message.reply(f"<b>❌ {m}, ɴᴏᴛ ᴇɴᴏᴜɢʜ!</b>")

@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    user = users_col.find_one({"user_id": message.from_user.id})
    parts = message.text.split()
    if len(parts) == 1:
        return await message.reply(f"<b>┏━━「 🏦 ᴠᴀᴜʟᴛ 」━━┓\n┃ 👤 ᴜsᴇʀ: {m}\n┃ 💰 sᴀᴠᴇᴅ: {user.get('vault', 0)}\n┗━━━━━━━━━━┛</b>")
    try:
        act, amt = parts[1].lower(), int(parts[2])
        if act in ["dep", "d"] and user['coins'] >= amt:
            users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": -amt, "vault": amt}})
            await message.reply(f"<b>✅ {m}, sᴀᴠᴇᴅ {amt}!</b>")
        elif act in ["wd", "w"] and user.get('vault', 0) >= amt:
            users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": amt, "vault": -amt}})
            await message.reply(f"<b>✅ {m}, ᴡɪᴛʜᴅʀᴇᴡ {amt}!</b>")
    except: pass

@app.on_message(filters.command("crules") & filters.group)
async def rules_h(client, message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    await message.reply_text(f"<b>┏━━「 📜 ʀᴜʟᴇs 」━━┓\n┃ 👤: {m}\n┃ 🔸 ᴅ-ɢᴀɴɢ: 2\n┃ 🔹 ᴀᴅᴅᴀ(500+): 5\n┃ 🔸 ʜᴏᴛʟɪɴᴇ: 10\n┗━━━━━━━━━━┛</b>")

@app.on_message(filters.command("sudo") & filters.group)
async def sudo_h(client, message):
    m = get_mention(message.from_user.id, message.from_user.first_name)
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    await del_cmd(message)
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": 1}})
        await message.reply(f"<b>┏━━「 🟢 sᴜᴅᴏ 」━━┓\n┃ 👤 ᴀᴅᴅᴇᴅ: {get_mention(target.id, target.first_name)}\n┗━━━━━━━━━━┛</b>")
    else:
        sudos = list(users_col.find({"is_sudo": 1}))
        res = f"<b>┏━━「 ✨ sᴜᴅᴏs 」━━┓\n"
        for i, s in enumerate(sudos, 1): res += f"┃ {i}. {get_mention(s['user_id'], s.get('full_name'))}\n"
        res += "┗━━━━━━━━━━┛</b>"
        await message.reply(res)

@app.on_message(filters.group & ~filters.bot)
async def auto_sync(client, message):
    if message.from_user: sync_data(message.from_user)

async def start_bot():
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.get_event_loop().run_until_complete(start_bot())
