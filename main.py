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
    
    msg = await message.reply("<b>⏳ ᴇxᴘᴏʀᴛɪɴɢ ᴅᴀᴛᴀ...</b>")
    try:
        all_users = list(users_col.find({}))
        output = f"TOTAL USERS: {len(all_users)}\n"
        output += "USER_ID | NAME | COINS | VAULT | RANK\n"
        output += "="*40 + "\n"
        
        for u in all_users:
            badge, _, rank_name = get_rank_info(u.get('coins', 0))
            line = f"{u['user_id']} | {u.get('full_name', 'N/A')} | {u.get('coins', 0)} | {u.get('vault', 0)} | {rank_name}\n"
            output += line
            
        file_stream = io.BytesIO(output.encode('utf-8'))
        file_stream.name = "dx_users_data.txt"
        
        await message.reply_document(
            document=file_stream,
            caption=f"<b>✅ ᴅᴀᴛᴀ ᴇxᴘᴏʀᴛᴇᴅ!\n📂 ғɪʟᴇ: dx_users_data.txt</b>"
        )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ ᴇʀʀᴏʀ: {e}")

# 2. MENU
@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━「 ✨ {B} ᴍᴇɴᴜ 」━━┓</b>\n"
        f"<b>┃ 👤 ʜɪ: {get_mention(message.from_user.id, message.from_user.first_name)}</b>\n"
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
    if not await check_sudo(message.from_user.id): 
        return await del_cmd(message)
    
    parts = message.text.split()
    
    if len(parts) < 2:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!</b>")

    try:
        amount = int(parts[1])
    except ValueError:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</b>")

    target = await get_target_user(client, message, parts)
    
    if not target:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")

    sync_data(target)
    
    user_data_before = users_col.find_one({"user_id": target.id})
    old_coins = user_data_before.get('coins', 0)
    old_badge, _, _ = get_rank_info(old_coins)

    users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amount}})
    
    new_coins = old_coins + amount
    new_badge, stars, rank_name = get_rank_info(new_coins)

    await message.reply(
        f"<b>┏━━「 ✅ ᴄᴏɪɴ ᴀᴅᴅᴇᴅ 」━━┓</b>\n"
        f"<b>┃ 👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 💰 ᴀᴅᴅᴇᴅ: +{amount}</b>\n"
        f"<b>┃ 👜 ᴛᴏᴛᴀʟ: {new_coins}</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

    # RANK UP PIN
    if new_badge != old_badge and new_coins > old_coins:
        try:
            pin_msg = await client.send_message(
                message.chat.id,
                f"<b>🎉 🎊 ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs! 🎊 🎉</b>\n\n"
                f"<b>👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
                f"<b>🆔 ɪᴅ: <code>{target.id}</code></b>\n"
                f"<b>━━━━━━━━━━</b>\n"
                f"<b>🆙 ʟᴇᴠᴇʟ ᴜᴘ!</b>\n"
                f"<b>🥔 ᴏʟᴅ: {old_badge}</b>\n"
                f"<b>🌟 ɴᴇᴡ: {new_badge} ({rank_name})</b>\n"
                f"<b>🌟 sᴛᴀʀs: {stars}</b>\n"
                f"<b>💰 ʙᴀʟᴀɴᴄᴇ: {new_coins}</b>\n"
                f"<b>━━━━━━━━━━</b>\n"
                f"<b>👏 ᴇᴠᴇʀʏᴏɴᴇ ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛᴇ ʜɪᴍ!</b>"
            )
            await pin_msg.pin(both_sides=True)
        except ChatAdminRequired:
            await message.reply("<b>⚠️ ᴡᴀʀɴɪɴɢ: ɪ ᴄᴀɴ'ᴛ ᴘɪɴ!</b>")
        except Exception:
            pass

# 4. MINUS COIN
@app.on_message(filters.command("mcoin"))
async def minus_coin(client, message: Message):
    user_id = message.from_user.id
    is_owner = (user_id == OWNER_ID)
    is_sudo = await check_sudo(user_id)
    
    if not is_sudo: 
        return await del_cmd(message)

    parts = message.text.split()

    if len(parts) < 2:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!</b>")

    try:
        amount = int(parts[1])
    except ValueError:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.</b>")

    target = None
    if message.chat.type == enums.ChatType.PRIVATE and is_owner and len(parts) == 3:
        try:
            users_col.update_one({"user_id": int(parts[2])}, {"$inc": {"coins": -amount}})
            return await message.reply(f"<b>✅ ғᴏʀᴄᴇᴅ ᴍɪɴᴜs {amount} ғʀᴏᴍ ɪᴅ: `{parts[2]}`</b>")
        except: return
    else:
        target = await get_target_user(client, message, parts)

    if not target:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")

    users_col.update_one({"user_id": target.id}, {"$inc": {"coins": -amount}})
    user_now = users_col.find_one({"user_id": target.id})
    current_coins = user_now.get('coins', 0) if user_now else "N/A"
    
    await message.reply(
        f"<b>┏━━「 🔻 ʀᴇᴍᴏᴠᴇᴅ 」━━┓</b>\n"
        f"<b>┃ 👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 💸 ʟᴏss: -{amount}</b>\n"
        f"<b>┃ 👜 ɴᴏᴡ: {current_coins}</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

# 5. GIFT COIN
@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    parts = message.text.split()
    
    if len(parts) < 2:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴀᴍᴏᴜɴᴛ ᴍɪssɪɴɢ!</b>")

    try:
        amt = int(parts[1])
        if amt <= 0: return await message.reply("<b>❌ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.</b>")
    except:
        return await message.reply("<b>⚠️ ᴇʀʀᴏʀ: ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.</b>")

    target = await get_target_user(client, message, parts)
    sender_id = message.from_user.id
    
    if not target: return await message.reply("<b>⚠️ ᴛᴀʀɢᴇᴛ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
    if target.id == sender_id: return await message.reply("<b>❌ ᴄᴀɴ'ᴛ ɢɪғᴛ sᴇʟғ!</b>")
    if target.is_bot: return await message.reply("<b>❌ ɴᴏ ʙᴏᴛs.</b>")

    sender = users_col.find_one({"user_id": sender_id})
    sync_data(target)
    
    if sender and sender['coins'] >= amt:
        users_col.update_one({"user_id": sender_id}, {"$inc": {"coins": -amt}})
        users_col.update_one({"user_id": target.id}, {"$inc": {"coins": amt}})
        
        await message.reply(
            f"<b>┏━━「 💸 sᴜᴄᴄᴇss 」━━┓</b>\n"
            f"<b>┃ 👤 ғʀᴏᴍ: {get_mention(sender_id, message.from_user.first_name)}</b>\n"
            f"<b>┃ 👤 ᴛᴏ: {get_mention(target.id, target.first_name)}</b>\n"
            f"<b>┃ 💰 sᴇɴᴛ: {amt} ᴄᴏɪɴs</b>\n"
            f"<b>┗━━━━━━━━━━┛</b>"
        )
    else:
        await message.reply(f"<b>❌ ʟᴏᴡ ʙᴀʟᴀɴᴄᴇ! ʏᴏᴜ ʜᴀᴠᴇ: {sender.get('coins',0)}</b>")

# 6. STATS
@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.from_user
    if message.reply_to_message: target = message.reply_to_message.from_user
    
    sync_data(target)
    user = users_col.find_one({"user_id": target.id})
    
    badge, stars, _ = get_rank_info(user['coins'])
    global_rank = users_col.count_documents({"coins": {"$gt": user['coins']}}) + 1
    
    await message.reply_text(
        f"<b>┏━━「 📊 ᴘʀᴏғɪʟᴇ 」━━┓</b>\n"
        f"<b>┃ 👤 ɴᴀᴍᴇ: {get_mention(target.id, target.first_name)}</b>\n"
        f"<b>┃ 🆔 ᴜɪᴅ: <code>{target.id}</code></b>\n"
        f"<b>┣━━━━━━━━━━</b>\n"
        f"<b>┃ 💰 ᴄᴏɪɴs: {user['coins']}</b>\n"
        f"<b>┃ 🏦 ᴠᴀᴜʟᴛ: {user.get('vault', 0)}</b>\n"
        f"<b>┃ 🏆 ʀᴀɴᴋ: #{global_rank}</b>\n"
        f"<b>┃ 🎖️ ʙᴀᴅɢᴇ: {badge}</b>\n"
        f"<b>┃ ⭐ sᴛᴀʀs: {stars}</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

# 7. VAULT
@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    parts = message.text.split()
    
    if len(parts) == 1:
        return await message.reply(
            f"<b>┏━━「 🏦 ᴠᴀᴜʟᴛ 」━━┓</b>\n"
            f"<b>┃ 👤 ᴜsᴇʀ: {get_mention(user_id, message.from_user.first_name)}</b>\n"
            f"<b>┃ 💰 sᴀᴠᴇᴅ: {user.get('vault', 0)}</b>\n"
            f"<b>┣━━━━━━━━━━</b>\n"
            f"<b>┃ 📥 ᴀᴅᴅ: `/vault dep 50`</b>\n"
            f"<b>┃ 📤 ɢᴇᴛ: `/vault wd 50`</b>\n"
            f"<b>┗━━━━━━━━━━┛</b>"
        )
    
    try:
        action = parts[1].lower()
        amount = int(parts[2])
        if amount <= 0: return await message.reply("❌ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.")
        
        if action in ["dep", "d"]:
            if user['coins'] >= amount:
                users_col.update_one({"user_id": user_id}, {"$inc": {"coins": -amount, "vault": amount}})
                await message.reply(f"<b>✅ ᴅᴇᴘᴏsɪᴛᴇᴅ {amount} ᴄᴏɪɴs!</b>")
            else:
                await message.reply("<b>❌ ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴄᴏɪɴs!</b>")
        elif action in ["wd", "w"]:
            if user.get('vault', 0) >= amount:
                users_col.update_one({"user_id": user_id}, {"$inc": {"coins": amount, "vault": -amount}})
                await message.reply(f"<b>✅ ᴡɪᴛʜᴅʀᴇᴡ {amount} ᴄᴏɪɴs!</b>")
            else:
                await message.reply("<b>❌ ɴᴏᴛ ᴇɴᴏᴜɢʜ ɪɴ ᴠᴀᴜʟᴛ!</b>")
    except:
        await message.reply("<b>⚠️ ᴇʀʀᴏʀ: `/vault dep 10`</b>")

# 8. STAR LIST
@app.on_message(filters.command("star") & filters.group)
async def star_list(client, message: Message):
    await del_cmd(message)
    star_users = users_col.find({"coins": {"$gte": 50}}).sort("coins", -1).limit(20)
    
    text = f"<b>┏━━「 🌟 sᴛᴀʀs 」━━┓</b>\n"
    text += f"<b>┃ 📝 ᴛᴏᴘ ᴜsᴇʀs ʟɪsᴛ</b>\n"
    text += f"<b>┣━━━━━━━━━━</b>\n"
    
    count = 0
    for u in star_users:
        count += 1
        badge, stars, _ = get_rank_info(u.get('coins', 0))
        name = u.get('full_name', 'Unknown')
        text += f"<b>┃ {count}. <a href='tg://user?id={u['user_id']}'>{name[:12]}</a></b>\n"
        text += f"<b>┃ ╰╼ {badge} • {u['coins']} ({stars})</b>\n"
        
    if count == 0: text += "<b>┃ ❌ ɴᴏ ᴅᴀᴛᴀ!</b>\n"
    text += f"<b>┗━━━━━━━━━━┛</b>"
    await message.reply(text)

# 9. CLAIM & RULES
@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    last_claim = user.get("last_claim", 0)
    
    if time.time() - last_claim < 259200:
        rem = 259200 - (time.time() - last_claim)
        return await message.reply(f"<b>┏━━「 ⏳ ᴡᴀɪᴛ 」━━┓\n┃ ⏳: {str(timedelta(seconds=int(rem)))}\n┗━━━━━━━━━━┛</b>")
    
    users_col.update_one({"user_id": user_id}, {"$inc": {"coins": 1}, "$set": {"last_claim": time.time()}})
    await message.reply(f"<b>┏━━「 ✅ ᴅᴏɴᴇ 」━━┓\n┃ 💰: +1 ᴄᴏɪɴ ᴀᴅᴅᴇᴅ!\n┗━━━━━━━━━━┛</b>")

@app.on_message(filters.command("crules") & filters.group)
async def rules_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━「 📜 {B} ʀᴜʟᴇs 」━━┓</b>\n"
        f"<b>┃ 🔸 ᴅᴀʀᴋ ɢᴀɴɢ: 2 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 ᴀᴅᴅᴀ(500+): 5 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 ᴀᴅᴅᴀ(-500): 3 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔸 ʜᴏᴛʟɪɴᴇ: 10 ᴄᴏɪɴ</b>\n"
        f"<b>┃ 🔹 -15 ʏ-ɢʀᴏᴜᴘ: 12 ᴄᴏɪɴ</b>\n"
        f"<b>┣━━━ 🎖️ sᴛᴀʀs ━━━</b>\n"
        f"<b>┃ ⭐: 50+ (ᴅᴇs-ɴᴀᴍᴇ)</b>\n"
        f"<b>┃ ⭐⭐: 100+ (ʜ-ᴄᴀᴘᴛᴀɪɴ)</b>\n"
        f"<b>┃ ⭐⭐⭐: 200+ (ʀᴜʟᴇʀ)</b>\n"
        f"<b>┃ 💎: 400+ (ᴄᴏᴅᴇ ᴏᴡɴᴇʀ)</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
    )

@app.on_message(filters.command("ctop") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    rows = list(users_col.find().sort("coins", -1).limit(10))
    board = f"<b>┏━━「 🏆 ᴛᴏᴘ 10 」━━┓</b>\n"
    for i, row in enumerate(rows, 1):
        rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}.</b>"
        badge, _, _ = get_rank_info(row.get('coins', 0))
        board += f"<b>┃ {rank_icon} {get_mention(row['user_id'], row.get('full_name'))}</b>\n"
        board += f"<b>┃ ╰╼ 💰 {row.get('coins', 0)} • {badge}</b>\n"
    board += f"<b>┗━━━━━━━━━━┛</b>"
    await message.reply_text(board)

@app.on_message(filters.command("cusage") & filters.group)
async def usage_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┏━━「 🛠️ ᴜsᴀɢᴇ 」━━┓</b>\n"
        f"<b>┃ 📌 /coin - sᴛᴀᴛs</b>\n"
        f"<b>┃ 📌 /claim - ᴅᴀɪʟʏ</b>\n"
        f"<b>┃ 📌 /gift 10 - sᴇɴᴅ</b>\n"
        f"<b>┃ 📌 /vault dep 10</b>\n"
        f"<b>┃ 📌 /vault wd 10</b>\n"
        f"<b>┃ 📌 /star - ʟɪsᴛ</b>\n"
        f"<b>┗━━━━━━━━━━┛</b>"
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
            return await message.reply(f"<b>┏━━「 🔴 sᴜᴅᴏ 」━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ ⚡: ʀᴇᴍᴏᴠᴇᴅ\n┗━━━━━━━━━━┛</b>")
        
        users_col.update_one({"user_id": target.id}, {"$set": {"is_sudo": 1}})
        await message.reply(f"<b>┏━━「 🟢 sᴜᴅᴏ 」━━┓\n┃ 👤: {get_mention(target.id, target.first_name)}\n┃ ⚡: ᴀᴅᴅᴇᴅ\n┗━━━━━━━━━━┛</b>")
    else:
        sudos = list(users_col.find({"is_sudo": 1}))
        res = "<b>┏━━「 ✨ sᴜᴅᴏs 」━━┓\n"
        for i, s in enumerate(sudos, 1): res += f"┃ {i}. {get_mention(s['user_id'], s.get('full_name'))}\n"
        res += "┗━━━━━━━━━━┛</b>"
        await message.reply(res)

@app.on_message(filters.group & ~filters.bot)
async def auto_sync(client, message: Message):
    if message.from_user: sync_data(message.from_user)

async def start_bot():
    print("Bot Starting...")
    await app.start()
    print("Bot Online! V2.2 (Short Lines)")
    await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.get_event_loop().run_until_complete(start_bot())
