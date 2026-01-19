import asyncio
import os
import re
import time
import io
import traceback
from datetime import timedelta
from threading import Thread
from flask import Flask
from pymongo import MongoClient
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UsernameInvalid, UserNotParticipant, ChatAdminRequired

# --- CONFIGURATION ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8513850569:AAHCsKyy1nWTYVKH_MtbW8IhKyOckWLTEDA"
B = "ᴅx" 
OWNER_ID = 6703335929

# --- DATABASE CONNECTION ---
MONGO_URL = "mongodb+srv://shadowur6_db_user:8AIIxZUjpanaQBjh@dx-codex.fmqcovu.mongodb.net/?retryWrites=true&w=majority&appName=Dx-codex"
client_db = MongoClient(MONGO_URL, connectTimeoutMS=30000, socketTimeoutMS=None, connect=False)
db = client_db["DX_COIN_DB"]
users_col = db["users"]

# --- WEB SERVER ---
web = Flask('')
@web.route('/')
def home(): return f"{B} sʏsᴛᴇᴍ ᴏɴʟɪɴᴇ & ʀᴜɴɴɪɴɢ..."

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

# --- BOT CLIENT ---
app = Client(
    "DX_COIN_FINAL_FIXED", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN, 
    in_memory=True
)

INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPER FUNCTIONS ---

async def check_sudo(user_id):
    if user_id in INIT_SUDO or user_id == OWNER_ID: return True
    user = users_col.find_one({"user_id": user_id})
    return user.get("is_sudo", 0) == 1 if user else False

def get_mention(user_id, name):
    valid_name = str(name) if name else "Usᴇʀ"
    clean_name = re.sub(r'[<>#]', '', valid_name)
    return f"<a href='tg://user?id={user_id}'>{clean_name[:15]}</a>"

def get_rank_info(coins):
    if coins >= 400: return ("💎", "💎💎💎", "ᴄᴏᴅᴇ ᴏᴡɴᴇʀ")
    elif coins >= 200: return ("🌟🌟🌟", "⭐⭐⭐", "ᴀᴅ/ʀᴜʟᴇʀ")
    elif coins >= 100: return ("🌟🌟", "⭐⭐", "ʜ-ᴄᴀᴘᴛᴀɪɴ")
    elif coins >= 50: return ("🌟", "⭐", "ᴅᴇs-ɴᴀᴍᴇ")
    return ("⚪️", "🌑", "ᴍᴇᴍʙᴇʀ")

def sync_data(user):
    if not user: return
    try:
        users_col.update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "full_name": f"{user.first_name} {user.last_name or ''}".strip(), 
                    "username": user.username
                }, 
                "$setOnInsert": {
                    "coins": 0, 
                    "vault": 0, 
                    "v_time": time.time(), 
                    "last_claim": 0, 
                    "is_sudo": 0
                }
            },
            upsert=True
        )
    except Exception as e:
        print(f"Sync Error: {e}")

async def del_cmd(message: Message):
    try: await message.delete()
    except: pass

async def get_target_user(client, message, command_parts):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    
    if len(command_parts) > 1:
        user_input = command_parts[-1]
        if user_input.isdigit() and len(user_input) < 5: 
            return None 

        try:
            user = await client.get_users(user_input)
            return user
        except (PeerIdInvalid, UsernameInvalid, IndexError):
            return None
    return None

# --- COMMANDS SECTION ---

# 1. DATA EXPORT
@app.on_message(filters.command("data") & filters.private)
async def export_data(client, message):
    if message.from_user.id != OWNER_ID: return
    m = get_mention(message.from_user.id, message.from_user.first_name)
    msg = await message.reply(f"<b>⏳ {m}, ᴇxᴘᴏʀᴛɪɴɢ ᴅᴀᴛᴀ...</b>")
    try:
        all_users = list(users_col.find({}))
        output = f"TOTAL USERS: {len(all_users)}\nUSER_ID | NAME | COINS | VAULT\n" + "="*40 + "\n"
        for u in all_users:
            output += f"{u['user_id']} | {u.get('full_name', 'N/A')} | {u.get('coins', 0)} | {u.get('vault', 0)}\n"
        file_stream = io.BytesIO(output.encode('utf-8'))
        file_stream.name = "dx_users.txt"
        await message.reply_document(document=file_stream, caption=f"<b>✅ {m}, ᴅᴀᴛᴀ ᴇxᴘᴏʀᴛᴇᴅ!</b>")
        await msg.delete()
    except Exception as e: await msg.edit(f"❌ ᴇʀʀᴏʀ: {e}")

# 2. MENU
@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    await message.reply_text(
        f"<b>┏━━「 ✨ {B} ᴍᴇɴᴜ 」━━┓</b>\n"
        f"<b>┃ 👤 ʜɪ: {m}</b>\n"
        f"<b>┣━━━━━━━━━━</b>\n"
        f"<b>┃ 📊 /coin  • ᴄʜᴇᴄᴋ ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏆 /ctop  • ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n"
        f"<b>┃ 🌟 /star  • sᴛᴀʀ ʜᴏʟᴅᴇʀs</b>\n"
        f"<b>┃ 🎁 /claim • ᴅᴀɪʟʏ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 💸 /gift  • sᴇɴᴅ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🏦 /vault • sᴀᴠᴇ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 📜 /crules• ʙᴏᴛ ʀᴜʟᴇs</b>\n"
        f"<b>┃ 🛠️ /cusage• ʜᴏᴡ ᴛᴏ ᴜsᴇ</b>\n"
        f"<b>┃ ⚡ /sudo  • ᴀᴅᴍɪɴ ʟɪsᴛ</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

# 3. ADD COIN
@app.on_message(filters.command("acoin"))
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    parts = message.text.split()
    if len(parts) < 2: return await message.reply(f"<b>⚠️ {m}, ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!</b>")
    try: amount = int(parts[1])
    except: return await message.reply(f"<b>⚠️ {m}, ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</b>")
    target = await get_target_user(client, message, parts)
    if not target: return await message.reply(f"<b>⚠️ {m}, ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
    sync_data(target)
    user_data = users_col.find_one({"user_id": target.id})
    old_coins = user_data.get('coins', 0)
    old_badge, _, _ = get_rank_info(old_coins)
    users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amount}})
    new_coins = old_coins + amount
    new_badge, stars, rank_name = get_rank_info(new_coins)
    await message.reply(
        f"<b>┏━━「 ✅ ᴄᴏɪɴ ᴀᴅᴅᴇᴅ 」━━┓</b>\n"
        f"<b>┃ 👤 ʙʏ: {m}</b>\n"
        f"<b>┃ 👤 ᴛᴏ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 💰 ᴀᴅᴅᴇᴅ: +{amount}</b>\n"
        f"<b>┃ 👜 ᴛᴏᴛᴀʟ: {new_coins}</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )
    if new_badge != old_badge and new_coins > old_coins:
        try:
            pin_msg = await client.send_message(message.chat.id, f"<b>🎉 🎊 ʟᴇᴠᴇʟ ᴜᴘ! 🎊 🎉</b>\n\n<b>👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n<b>🌟 ɴᴇᴡ ʀᴀɴᴋ: {new_badge} ({rank_name})</b>\n<b>━━━━━━━━━━</b>")
            await pin_msg.pin(both_sides=True)
        except: pass

# 4. MINUS COIN
@app.on_message(filters.command("mcoin"))
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    parts = message.text.split()
    if len(parts) < 2: return await message.reply(f"<b>⚠️ {m}, ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!</b>")
    try: amount = int(parts[1])
    except: return await message.reply(f"<b>⚠️ {m}, ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.</b>")
    target = await get_target_user(client, message, parts)
    if not target: return await message.reply(f"<b>⚠️ {m}, ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
    users_col.update_one({"user_id": target.id}, {"$inc": {"coins": -amount}})
    await message.reply(f"<b>┏━━「 🔻 ʀᴇᴍᴏᴠᴇᴅ 」━━┓\n┃ 👤 ʙʏ: {m}\n┃ 👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}\n┃ 💸 ʟᴏss: -{amount}\n┗━━━━━━━━━━┛</b>")

# 5. GIFT COIN
@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    m = get_mention(message.from_user.id, message.from_user.first_name)
    parts = message.text.split()
    if len(parts) < 2: return await message.reply(f"<b>⚠️ {m}, ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!</b>")
    try: amt = int(parts[1])
    except: return await message.reply(f"<b>⚠️ {m}, ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</b>")
    target = await get_target_user(client, message, parts)
    if not target or target.id == message.from_user.id: return await message.reply(f"<b>❌ {m}, ɪɴᴠᴀʟɪᴅ ᴛᴀʀɢᴇᴛ!</b>")
    sender = users_col.find_one({"user_id": message.from_user.id})
    if sender and sender['coins'] >= amt:
        users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": -amt}})
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amt}})
        await message.reply(f"<b>┏━━「 💸 sᴜᴄᴄᴇss 」━━┓\n┃ 👤 ғʀᴏᴍ: {m}\n┃ 👤 ᴛᴏ: {get_mention(target.id, target.first_name)}\n┃ 💰 sᴇɴᴛ: {amt}\n┗━━━━━━━━━━┛</b>")
    else: await message.reply(f"<b>❌ {m}, ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!</b>")

# 6. STATS
@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    badge, stars, _ = get_rank_info(user['coins'])
    await message.reply_text(
        f"<b>┏━━「 📊 ᴘʀᴏғɪʟᴇ 」━━┓</b>\n"
        f"<b>┃ 👤 ɴᴀᴍᴇ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 💰 ᴄᴏɪɴs: {user['coins']}</b>\n"
        f"<b>┃ 🏦 ᴠᴀᴜʟᴛ: {user.get('vault', 0)}</b>\n"
        f"<b>┃ 🎖️ ʙᴀᴅɢᴇ: {badge}</b>\n"
        f"<b>┃ ⭐ sᴛᴀʀs: {stars}</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

# 7. VAULT
@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message: Message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    user = users_col.find_one({"user_id": message.from_user.id})
    parts = message.text.split()
    if len(parts) == 1:
        return await message.reply(f"<b>┏━━「 🏦 ᴠᴀᴜʟᴛ 」━━┓\n┃ 👤 ᴜsᴇʀ: {m}\n┃ 💰 sᴀᴠᴇᴅ: {user.get('vault', 0)}\n┗━━━━━━━━━━┛</b>")
    try:
        action, amount = parts[1].lower(), int(parts[2])
        if action in ["dep", "d"] and user['coins'] >= amount:
            users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": -amount, "vault": amount}})
            await message.reply(f"<b>✅ {m}, ᴅᴇᴘᴏsɪᴛᴇᴅ {amount} ᴄᴏɪɴs!</b>")
        elif action in ["wd", "w"] and user.get('vault', 0) >= amount:
            users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": amount, "vault": -amount}})
            await message.reply(f"<b>✅ {m}, ᴡɪᴛʜᴅʀᴇᴡ {amount} ᴄᴏɪɴs!</b>")
        else: await message.reply(f"<b>❌ {m}, ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!</b>")
    except: await message.reply(f"<b>⚠️ {m}, ᴜsᴀɢᴇ: `/vault dep 10`</b>")

# 8. STAR LIST (No mention needed as per request)
@app.on_message(filters.command("star") & filters.group)
async def star_list(client, message: Message):
    await del_cmd(message)
    stars = users_col.find({"coins": {"$gte": 50}}).sort("coins", -1).limit(20)
    text = f"<b>┏━━「 🌟 sᴛᴀʀs 」━━┓</b>\n"
    for i, u in enumerate(stars, 1):
        badge, s_icon, _ = get_rank_info(u.get('coins', 0))
        text += f"<b>┃ {i}. {u.get('full_name')[:10]} ({u['coins']}) {badge}</b>\n"
    text += f"<b>┗━━━━━━━━━━┛</b>"
    await message.reply(text)

# 9. CLAIM & RULES
@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    user = users_col.find_one({"user_id": message.from_user.id})
    if time.time() - user.get("last_claim", 0) < 259200:
        rem = 259200 - (time.time() - user.get("last_claim", 0))
        return await message.reply(f"<b>┏━━「 ⏳ ᴡᴀɪᴛ 」━━┓\n┃ 👤: {m}\n┃ ⏳: {str(timedelta(seconds=int(rem)))}\n┗━━━━━━━━━━┛</b>")
    users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"coins": 1}, "$set": {"last_claim": time.time()}})
    await message.reply(f"<b>┏━━「 ✅ ᴅᴏɴᴇ 」━━┓\n┃ 👤: {m}\n┃ 💰: +1 ᴄᴏɪɴ ᴀᴅᴅᴇᴅ!\n┗━━━━━━━━━━┛</b>")

@app.on_message(filters.command("crules") & filters.group)
async def rules_handler(client, message: Message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    await message.reply_text(f"<b>┏━━「 📜 {B} ʀᴜʟᴇs 」━━┓\n┃ 👤: {m}\n┃ 🔸 ᴅᴀʀᴋ ɢᴀɴɢ: 2\n┃ 🔹 ᴀᴅᴅᴀ(500+): 5\n┃ 🔹 ᴀᴅᴅᴀ(-500): 3\n┃ 🔸 ʜᴏᴛʟɪɴᴇ: 10\n┃ 🔹 -15 ʏ-ɢ: 12\n┗━━━━━━━━━━┛</b>")

@app.on_message(filters.command("ctop") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    rows = list(users_col.find().sort("coins", -1).limit(10))
    board = f"<b>┏━━「 🏆 ᴛᴏᴘ 10 」━━┓</b>\n"
    for i, row in enumerate(rows, 1):
        board += f"<b>┃ {i}. {row.get('full_name','User')[:10]} - {row.get('coins', 0)}</b>\n"
    board += f"<b>┗━━━━━━━━━━┛</b>"
    await message.reply_text(board)

@app.on_message(filters.command("cusage") & filters.group)
async def usage_handler(client, message: Message):
    await del_cmd(message)
    m = get_mention(message.from_user.id, message.from_user.first_name)
    await message.reply_text(f"<b>┏━━「 🛠️ ᴜsᴀɢᴇ 」━━┓\n┃ 👤: {m}\n┃ 📌 /coin - sᴛᴀᴛs\n┃ 📌 /claim - ᴅᴀɪʟʏ\n┃ 📌 /gift 10 - sᴇɴᴅ\n┃ 📌 /vault dep 10\n┗━━━━━━━━━━┛</b>")

@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    m = get_mention(message.from_user.id, message.from_user.first_name)
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    await del_cmd(message)
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": 1}})
        await message.reply(f"<b>┏━━「 🟢 sᴜᴅᴏ 」━━┓\n┃ 👤 ʙʏ: {m}\n┃ 👤 ᴀᴅᴅᴇᴅ: {get_mention(target.id, target.first_name)}\n┗━━━━━━━━━━┛</b>")
    else:
        sudos = list(users_col.find({"is_sudo": 1}))
        res = f"<b>┏━━「 ✨ sᴜᴅᴏs 」━━┓\n┃ 👤 ʀᴇǫ: {m}\n"
        for i, s in enumerate(sudos, 1): res += f"┃ {i}. {s.get('full_name','Sudo')[:10]}\n"
        res += "┗━━━━━━━━━━┛</b>"
        await message.reply(res)

@app.on_message(filters.group & ~filters.bot)
async def auto_sync(client, message: Message):
    if message.from_user: sync_data(message.from_user)

async def start_bot():
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.get_event_loop().run_until_complete(start_bot())
