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
from pyrogram import Client, filters, nums
from pyrogram.types import Message, InputFile
from pyrogram.errors import PeerIdInvalid, UsernameInvalid

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
    if user_id in INIT_SUDO or user_id == OWNER_ID: return True
    user = users_col.find_one({"user_id": user_id})
    return user.get("is_sudo", 0) == 1 if user else False

def get_mention(user_id, name):
    clean_name = re.sub(r'[<>#]', '', str(name) or "Usᴇʀ")
    return f"<a href='tg://user?id={user_id}'>{clean_name[:15]}</a>"

def get_rank_info(coins):
    # Returns (Badge, Stars, Rank Name)
    if coins >= 400: return ("💎", "💎💎💎", "ᴄᴏᴅᴇ ᴏᴡɴᴇʀ")
    elif coins >= 200: return ("🌟🌟🌟", "⭐⭐⭐", "ᴀᴅ/ʀᴜʟᴇʀ")
    elif coins >= 100: return ("🌟🌟", "⭐⭐", "ʜ-ᴄᴀᴘᴛᴀɪɴ")
    elif coins >= 50: return ("🌟", "⭐", "ᴅᴇs-ɴᴀᴍᴇ")
    return ("⚪️", "🌑", "ᴍᴇᴍʙᴇʀ")

def sync_data(user):
    if not user: return
    users_col.update_one(
        {"user_id": user.id},
        {
            "$set": {"full_name": f"{user.first_name} {user.last_name or ''}".strip(), "username": user.username}, 
            "$setOnInsert": {"coins": 0, "vault": 0, "v_time": time.time(), "last_claim": 0, "is_sudo": 0}
        },
        upsert=True
    )

async def del_cmd(message: Message):
    try: await message.delete()
    except: pass

async def get_target_user(client, message, command_parts):
    # 1. Check Reply
    if message.reply_to_message:
        return message.reply_to_message.from_user
    
    # 2. Check Arguments (Username or ID)
    if len(command_parts) > 1:
        user_input = command_parts[-1] # Usually the last part is user if amount is first or mixed
        # If input is digit (ID) or starts with @
        if user_input.isdigit() or user_input.startswith("@"):
            try:
                user = await client.get_users(user_input)
                return user
            except (PeerIdInvalid, UsernameInvalid):
                return None
    return None

# --- COMMANDS ---

# 1. OWNER DATA EXPORT (Bot DM Only)
@app.on_message(filters.command("data") & filters.private & filters.user(OWNER_ID))
async def export_data(client, message):
    msg = await message.reply("<b>⏳ ᴇxᴘᴏʀᴛɪɴɢ ᴅᴀᴛᴀ... ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.</b>")
    try:
        all_users = users_col.find({})
        output = "USER_ID | NAME | COINS | VAULT | RANK\n"
        output += "="*50 + "\n"
        
        count = 0
        for u in all_users:
            badge, _, _ = get_rank_info(u.get('coins', 0))
            line = f"{u['user_id']} | {u.get('full_name', 'N/A')} | {u.get('coins', 0)} | {u.get('vault', 0)} | {badge}\n"
            output += line
            count += 1
            
        file_stream = io.BytesIO(output.encode('utf-8'))
        file_stream.name = "dx_users_data.txt"
        
        await message.reply_document(
            document=file_stream,
            caption=f"<b>✅ ᴅᴀᴛᴀ ᴇxᴘᴏʀᴛ sᴜᴄᴄᴇssғᴜʟ!\n👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs: {count}</b>"
        )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ ᴇʀʀᴏʀ: {e}")

# 2. MENU COMMAND
@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━━━「 ✨ {B} ᴍᴇɴᴜ 」━━━━┓</b>\n"
        f"<b>┃ 👤 ʜɪ: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 📊 /coin  • ᴄʜᴇᴄᴋ ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏆 /ctop  • ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n"
        f"<b>┃ 🌟 /star  • sᴛᴀʀ ʜᴏʟᴅᴇʀs</b>\n"
        f"<b>┃ 🎁 /claim • ᴅᴀɪʟʏ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 💸 /gift  • sᴇɴᴅ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🏦 /vault • sᴀᴠᴇ ᴄᴏɪɴ</b>\n"
        f"<b>┃ 📜 /crules• ʙᴏᴛ ʀᴜʟᴇs</b>\n"
        f"<b>┃ 🛠️ /cusage• ʜᴏᴡ ᴛᴏ ᴜsᴇ</b>\n"
        f"<b>┃ ⚡ /sudo  • ᴀᴅᴍɪɴ ʟɪsᴛ</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
    )

# 3. ADD COIN (Advanced with Pin)
@app.on_message(filters.command("acoin"))
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id): 
        return await del_cmd(message)
    
    parts = message.text.split()
    # Logic: /acoin 10 @username OR Reply /acoin 10
    
    if len(parts) < 2:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!\n✅ ᴜsᴀɢᴇ: `/acoin 10` (Reply) ᴏʀ `/acoin 10 @username`</b>")

    try:
        amount = int(parts[1])
    except ValueError:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</b>")

    target = await get_target_user(client, message, parts)
    if not target:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!\n✅ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ ᴍᴇɴᴛɪᴏɴ ᴜsᴇʀɴᴀᴍᴇ.</b>")

    sync_data(target)
    
    # Rank Check Before Update
    user_data_before = users_col.find_one({"user_id": target.id})
    old_coins = user_data_before.get('coins', 0)
    old_badge, _, _ = get_rank_info(old_coins)

    # Update
    users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amount}})
    
    # Rank Check After Update
    new_coins = old_coins + amount
    new_badge, stars, rank_name = get_rank_info(new_coins)

    # Normal Message
    await message.reply(
        f"<b>┏━━━━「 ✅ ᴄᴏɪɴ ᴀᴅᴅᴇᴅ 」━━━━┓</b>\n"
        f"<b>┃ 👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 💰 ᴀᴍᴏᴜɴᴛ: +{amount}</b>\n"
        f"<b>┃ 👜 ᴛᴏᴛᴀʟ: {new_coins}</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
    )

    # PROMOTION PIN MESSAGE (Only if rank changed and improved)
    if new_badge != old_badge and new_coins > old_coins:
        pin_msg = await client.send_message(
            message.chat.id,
            f"<b>🎉 🎊 ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs! ɴᴇᴡ ʀᴀɴᴋ! 🎊 🎉</b>\n\n"
            f"<b>👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
            f"<b>🆔 ɪᴅ: <code>{target.id}</code></b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>🆙 ʟᴇᴠᴇʟ ᴜᴘ!</b>\n"
            f"<b>🥔 ᴏʟᴅ ʀᴀɴᴋ: {old_badge}</b>\n"
            f"<b>🌟 ɴᴇᴡ ʀᴀɴᴋ: {new_badge} ({rank_name})</b>\n"
            f"<b>🌟 sᴛᴀʀs ᴇᴀʀɴᴇᴅ: {stars}</b>\n"
            f"<b>💰 ᴄᴜʀʀᴇɴᴛ ʙᴀʟᴀɴᴄᴇ: {new_coins}</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>👏 ᴇᴠᴇʀʏᴏɴᴇ ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛᴇ ʜɪᴍ!</b>"
        )
        try: await pin_msg.pin(both_sides=True)
        except: pass

# 4. MINUS COIN (Works in Group & Owner DM)
@app.on_message(filters.command("mcoin"))
async def minus_coin(client, message: Message):
    is_owner = message.from_user.id == OWNER_ID
    is_sudo = await check_sudo(message.from_user.id)
    
    if not is_sudo: return await del_cmd(message)

    parts = message.text.split()
    # Format: /mcoin 10 (Reply) OR /mcoin 10 @user OR (Owner Only DM) /mcoin 10 <userid>

    if len(parts) < 2:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!\n✅ ᴜsᴀɢᴇ: `/mcoin 10` (Reply) ᴏʀ `/mcoin 10 @user`</b>")

    try:
        amount = int(parts[1])
    except ValueError:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.</b>")

    target = None
    
    # Special Owner DM Logic for UserID
    if message.chat.type == filters.ChatType.PRIVATE and is_owner and len(parts) == 3:
        try:
            target_id = int(parts[2])
            target = await client.get_users(target_id)
        except:
            target = None
    else:
        target = await get_target_user(client, message, parts)

    if not target:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!\nℹ️ ᴅᴍ-ᴇ ɪᴅ ᴅɪʏᴇ ᴋᴏʀᴛᴇ: `/mcoin 10 12345678`</b>")

    users_col.update_one({"user_id": target.id}, {"$inc": {"coins": -amount}})
    
    # Fetch updated balance
    user_now = users_col.find_one({"user_id": target.id})
    
    await message.reply(
        f"<b>┏━━━━「 🔻 ᴄᴏɪɴ ʀᴇᴍᴏᴠᴇᴅ 」━━━━┓</b>\n"
        f"<b>┃ 👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 💸 ʀᴇᴍᴏᴠᴇᴅ: -{amount}</b>\n"
        f"<b>┃ 👜 ᴄᴜʀʀᴇɴᴛ: {user_now.get('coins', 0)}</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━━━━┛</b>"
    )

# 5. GIFT COIN
@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    parts = message.text.split()
    
    if len(parts) < 2:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!\n✅ ᴜsᴀɢᴇ: `/gift 50` (Reply) ᴏʀ `/gift 50 @username`</b>")

    try:
        amt = int(parts[1])
        if amt <= 0: return await message.reply("<b>❌ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢɪғᴛ 0 ᴏʀ ɴᴇɢᴀᴛɪᴠᴇ ᴄᴏɪɴs.</b>")
    except:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴀᴍᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ.</b>")

    target = await get_target_user(client, message, parts)
    sender_id = message.from_user.id
    
    if not target:
        return await message.reply("<b>⚠️ ᴛᴀʀɢᴇᴛ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
    if target.id == sender_id:
        return await message.reply("<b>❌ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢɪғᴛ ʏᴏᴜʀsᴇʟғ!</b>")
    if target.is_bot:
        return await message.reply("<b>❌ ʙᴏᴛs ᴅᴏɴ'ᴛ ɴᴇᴇᴅ ᴄᴏɪɴs.</b>")

    sender = users_col.find_one({"user_id": sender_id})
    sync_data(target)
    
    if sender and sender['coins'] >= amt:
        users_col.update_one({"user_id": sender_id}, {"$inc": {"coins": -amt}})
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amt}})
        
        await message.reply(
            f"<b>┏━━━━「 💸 sᴜᴄᴄᴇssғᴜʟ 」━━━━┓</b>\n"
            f"<b>┃ 👤 ғʀᴏᴍ: {get_mention(sender_id, message.from_user.first_name)}</b>\n"
            f"<b>┃ 👤 ᴛᴏ: {get_mention(target.id, target.first_name)}</b>\n"
            f"<b>┃ 💰 ᴀᴍᴏᴜɴᴛ: {amt} ᴄᴏɪɴs</b>\n"
            f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
        )
    else:
        await message.reply(f"<b>❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!\n💰 ʏᴏᴜʀ ʙᴀʟ: {sender.get('coins',0)}</b>")

# 6. CHECK COIN
@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.from_user
    if message.reply_to_message: target = message.reply_to_message.from_user
    
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    
    badge, stars, rank_name = get_rank_info(user['coins'])
    global_rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    
    await message.reply_text(
        f"<b>┏━━━━「 📊 ᴜsᴇʀ ᴘʀᴏғɪʟᴇ 」━━━━┓</b>\n"
        f"<b>┃ 👤 ɴᴀᴍᴇ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 🆔 ᴜɪᴅ: <code>{target.id}</code></b>\n"
        f"<b>┣━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 💰 ᴘᴏᴄᴋᴇᴛ: {user['coins']} ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏦 ᴠᴀᴜʟᴛ: {user.get('vault', 0)} ᴄᴏɪɴs</b>\n"
        f"<b>┃ 🏆 ɢʟᴏʙᴀʟ ʀᴀɴᴋ: #{global_rank}</b>\n"
        f"<b>┃ 🎖️ ᴄᴜʀʀᴇɴᴛ ʀᴀɴᴋ: {badge}</b>\n"
        f"<b>┃ ⭐ sᴛᴀʀs: {stars}</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
    )

# 7. VAULT SYSTEM
@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    parts = message.text.split()
    
    if len(parts) == 1:
        return await message.reply(
            f"<b>┏━━━━「 🏦 sᴇᴄᴜʀᴇ ᴠᴀᴜʟᴛ 」━━━━┓</b>\n"
            f"<b>┃ 👤 ᴏᴡɴᴇʀ: {get_mention(user_id, message.from_user.first_name)}</b>\n"
            f"<b>┃ 💰 ᴠᴀᴜʟᴛ ʙᴀʟᴀɴᴄᴇ: {user.get('vault', 0)}</b>\n"
            f"<b>┣━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>┃ 📥 ᴅᴇᴘᴏsɪᴛ: `/vault dep 50`</b>\n"
            f"<b>┃ 📤 ᴡɪᴛʜᴅʀᴀᴡ: `/vault wd 50`</b>\n"
            f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
        )
    
    if len(parts) < 3:
        return await message.reply("<b>⚠️ ᴜsᴀɢᴇ ᴇʀʀᴏʀ!\n✅ ᴛʀʏ: `/vault dep 100` ᴏʀ `/vault wd 100`</b>")

    try:
        action = parts[1].lower()
        amount = int(parts[2])
        if amount <= 0: return await message.reply("❌ ᴀᴍᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴘᴏsɪᴛɪᴠᴇ.")
        
        if action in ["dep", "d"]:
            if user['coins'] >= amount:
                users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -amount, "vault": amount}})
                await message.reply(f"<b>✅ ᴅᴇᴘᴏsɪᴛ sᴜᴄᴄᴇssғᴜʟ!\n📥 ᴀᴅᴅᴇᴅ: {amount} ᴛᴏ ᴠᴀᴜʟᴛ.</b>")
            else:
                await message.reply("<b>❌ ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴄᴏɪɴs ɪɴ ᴘᴏᴄᴋᴇᴛ!</b>")
        
        elif action in ["wd", "w"]:
            if user.get('vault', 0) >= amount:
                users_col.update_one({"user_id": user_id}, {"$inc": {"coins": amount, "vault": -amount}})
                await message.reply(f"<b>✅ ᴡɪᴛʜᴅʀᴀᴡ sᴜᴄᴄᴇssғᴜʟ!\n📤 ᴛᴀᴋᴇɴ: {amount} ғʀᴏᴍ ᴠᴀᴜʟᴛ.</b>")
            else:
                await message.reply("<b>❌ ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴄᴏɪɴs ɪɴ ᴠᴀᴜʟᴛ!</b>")
        else:
            await message.reply("<b>⚠️ ᴜɴᴋɴᴏᴡɴ ᴀᴄᴛɪᴏɴ! ᴜsᴇ `dep` ᴏʀ `wd`.</b>")
            
    except ValueError:
        await message.reply("<b>⚠️ ᴀᴍᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ!</b>")

# 8. STAR LIST (NEW COMMAND)
@app.on_message(filters.command("star") & filters.group)
async def star_list(client, message: Message):
    await del_cmd(message)
    # Find users with coins >= 50 (Minimum for 1 star)
    star_users = users_col.find({"coins": {"$gte": 50}}).sort("coins", -1).limit(20)
    
    text = f"<b>┏━━━━「 🌟 sᴛᴀʀ ʜᴏʟᴅᴇʀs 」━━━━┓</b>\n"
    text += f"<b>┃ 📝 ʟɪsᴛ ᴏғ ᴛᴏᴘ ʀᴀɴᴋᴇᴅ ᴜsᴇʀs</b>\n"
    text += f"<b>┣━━━━━━━━━━━━━━━━━</b>\n"
    
    count = 0
    for u in star_users:
        count += 1
        badge, stars, _ = get_rank_info(u['coins'])
        text += f"<b>┃ {count}. {get_mention(u['user_id'], u.get('full_name'))}</b>\n"
        text += f"<b>┃ ╰╼ {badge} • {u['coins']} ({stars})</b>\n"
        
    if count == 0:
        text += "<b>┃ ❌ ɴᴏ sᴛᴀʀ ʜᴏʟᴅᴇʀs ʏᴇᴛ!</b>\n"
        
    text += f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
    await message.reply(text)

# 9. CLAIM & RULES
@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    last_claim = user.get("last_claim", 0)
    
    # 3 Days cooldown = 259200 seconds
    if time.time() - last_claim < 259200:
        rem = 259200 - (time.time() - last_claim)
        return await message.reply(f"<b>┏━━━━「 ⏳ ᴄᴏᴏʟᴅᴏᴡɴ 」━━━━┓\n┃ 👤: {get_mention(user_id, message.from_user.first_name)}\n┃ 🚫 ʏᴏᴜ ᴄʟᴀɪᴍᴇᴅ ʀᴇᴄᴇɴᴛʟʏ!\n┃ ⏳ ɴᴇxᴛ: {str(timedelta(seconds=int(rem)))}\n┗━━━━━━━━━━━━━━━━━┛</b>")
    
    users_col.update_one({"user_id": user_id}, {"$inc": {"coins": 1}, "$set": {"last_claim": time.time()}})
    await message.reply(f"<b>┏━━━━「 ✅ ᴄʟᴀɪᴍᴇᴅ 」━━━━┓\n┃ 👤: {get_mention(user_id, message.from_user.first_name)}\n┃ 💰: +1 ᴄᴏɪɴ ᴀᴅᴅᴇᴅ!\n┗━━━━━━━━━━━━━━━━━┛</b>")

@app.on_message(filters.command("crules") & filters.group)
async def rules_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━━「 📜 {B} ʀᴜʟᴇs 」━━━┓</b>\n"
        f"<b>┃ 👤: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 🔸 ᴅᴀʀᴋ ɢᴀɴɢ ᴜ-ᴀᴅᴅ: 2 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 ᴀᴅᴅᴀ ɢ-ʜᴀᴄᴋ(500+): 5 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 ᴀᴅᴅᴀ ɢ-ʜᴀᴄᴋ(-500): 3 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔸 ʜᴏᴛʟɪɴᴇ ɢ-ʜᴀᴄᴋ: 10 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 -15 ʏ-ɢʀᴏᴜᴘ ʜᴀᴄᴋ: 12 ᴄᴏɪɴ</b>\n"
        f"<b>┣━━━━━ 🎖️ sᴛᴀʀs ━━━━━</b>\n"
        f"<b>┃ ⭐: 50+ (ᴅᴇs-ɴᴀᴍᴇ)</b>\n"
        f"<b>┃ ⭐⭐: 100+ (ʜ-ᴄᴀᴘᴛᴀɪɴ)</b>\n"
        f"<b>┃ ⭐⭐⭐: 200+ (ʀᴜʟᴇʀ)</b>\n"
        f"<b>┃ 💎: 400+ (ᴄᴏᴅᴇ ᴏᴡɴᴇʀ)</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.command("ctop") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    rows = list(users_col.find().sort("coins", -1).limit(10))
    board = f"<b>┏━━━━「 🏆 ᴛᴏᴘ ʀɪᴄʜᴇsᴛ 」━━━━┓</b>\n"
    for i, row in enumerate(rows, 1):
        rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}.</b>"
        badge, _, _ = get_rank_info(row.get('coins', 0))
        board += f"<b>┃ {rank_icon} {get_mention(row['user_id'], row.get('full_name'))}</b>\n"
        board += f"<b>┃ ╰╼ 💰 {row.get('coins', 0)} • {badge}</b>\n"
    board += f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
    await message.reply_text(board)

@app.on_message(filters.command("cusage") & filters.group)
async def usage_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━━「 🛠️ ᴄᴏɪɴ ᴜsᴀɢᴇ 」━━━┓</b>\n"
        f"<b>┃ 👤: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
        f"<b>┣━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>┃ 📌 /coin - ᴄʜᴇᴄᴋ ʙᴀʟᴀɴᴄᴇ & ʀᴀɴᴋ</b>\n"
        f"<b>┃ 📌 /claim - ᴄʟᴀɪᴍ ᴅᴀɪʟʏ ʀᴇᴡᴀʀᴅ</b>\n"
        f"<b>┃ 📌 /gift 10 - ɢɪғᴛ ᴄᴏɪɴ (ʀᴇᴘʟʏ/ᴛᴀɢ)</b>\n"
        f"<b>┃ 📌 /vault dep 10 - sᴀᴠᴇ ᴛᴏ ᴠᴀᴜʟᴛ</b>\n"
        f"<b>┃ 📌 /vault wd 10 - ᴛᴀᴋᴇ ғʀᴏᴍ ᴠᴀᴜʟᴛ</b>\n"
        f"<b>┃ 📌 /star - sᴇᴇ sᴛᴀʀ ʜᴏʟᴅᴇʀs</b>\n"
        f"<b>┗━━━━━━━━━━━━━━━━━┛</b>"
    )

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
            return await message.reply(f"<b>┏━━━━「 🔴 sᴜᴅᴏ 」━━━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ ⚡: ʀᴇᴍᴏᴠᴇᴅ\n┗━━━━━━━━━━━━━━━━━┛</b>")
        
        users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": 1}})
        await message.reply(f"<b>┏━━━━「 🟢 sᴜᴅᴏ 」━━━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ ⚡: ᴀᴅᴅᴇᴅ\n┗━━━━━━━━━━━━━━━━━┛</b>")
    else:
        sudos = list(users_col.find({"is_sudo": 1}))
        res = "<b>┏━━━━「 ✨ sᴜᴅᴏ ʟɪsᴛ 」━━━━┓\n"
        for i, s in enumerate(sudos, 1): res += f"┃ {i}. {get_mention(s['user_id'], s.get('full_name'))}\n"
        res += "┗━━━━━━━━━━━━━━━━━┛</b>"
        await message.reply(res)

@app.on_message(filters.group & ~filters.bot)
async def auto_sync(client, message: Message):
    if message.from_user: sync_data(message.from_user)

async def start_bot():
    print("Bot Starting...")
    await app.start()
    print("Bot Online! V2.0")
    await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.get_event_loop().run_until_complete(start_bot())
