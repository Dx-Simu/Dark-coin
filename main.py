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

# আপনার দেওয়া নতুন মঙ্গো ইউআরএল (Password: 8AIIxZUjpanaQBjh)
MONGO_URL = "mongodb+srv://shadowur6_db_user:8AIIxZUjpanaQBjh@dx-codex.fmqcovu.mongodb.net/?retryWrites=true&w=majority&appName=Dx-codex"

B = "ᴅx" 
URL = "https://dark-coin.onrender.com"

# --- MONGODB SETUP ---
try:
    mongo_client = MongoClient(MONGO_URL)
    db = mongo_client["dx_coin_db"]
    users_col = db["users"]
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

# --- ANTI-SLEEP PING ---
def keep_alive_ping():
    while True:
        try:
            requests.get(URL, timeout=10)
            print(f"📡 ᴀᴄᴛɪᴠᴇ: ᴘɪɴɢ sᴇɴᴛ ᴛᴏ {URL}")
        except: pass
        time.sleep(600)

# --- WEB SERVER ---
web = Flask('')
@web.route('/')
def home(): return f"<b>{B} SYSTEM ONLINE (MONGODB)</b>"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

app = Client("DX_COIN_MONGO", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPERS (MONGODB SYNC) ---
def sync_data(user):
    if not user: return None
    uid = str(user.id)
    name = f"{user.first_name} {user.last_name or ''}".strip()
    data = users_col.find_one({"user_id": uid})
    
    if not data:
        data = {
            "user_id": uid, "full_name": name, "username": user.username or "None",
            "coins": 0, "vault": 0, "v_time": int(time.time()), 
            "msg_count": 0, "last_claim": 0, "is_sudo": 0, "title": "ɴᴏɴᴇ"
        }
        users_col.insert_one(data)
    else:
        users_col.update_one({"user_id": uid}, {"$set": {"full_name": name, "username": user.username or "None"}})
    return data

async def check_sudo(user_id):
    if user_id in INIT_SUDO: return True
    data = users_col.find_one({"user_id": str(user_id)})
    return (data.get('is_sudo', 0) == 1) if data else False

def get_mention(user_id, name):
    clean_name = re.sub(r'[<>#]', '', name or "User")
    return f"<a href='tg://user?id={user_id}'>{clean_name[:15]}</a>"

async def del_cmd(message: Message):
    try: await message.delete()
    except: pass

# --- 1. MENU ---
@app.on_message(filters.command("menu") & filters.group)
async def menu_handler(client, message: Message):
    await del_cmd(message)
    await message.reply_text(
        f"<b>┌──╼「 ✨ ᴅx sʏsᴛᴇᴍ ᴍᴇɴᴜ 」</b>\n"
        f"<b>│</b>\n"
        f"<b>├─📊 ᴜsᴇʀ ➲</b> /coin, /top, /claim\n"
        f"<b>├─🏦 ᴠᴀᴜʟᴛ ➲</b> /vault, /gift, /shop\n"
        f"<b>├─📢 ᴀᴅs ➲</b> /buyad <code>(10 ᴄᴏɪɴs)</code>\n"
        f"<b>├─⚡ sᴜᴅᴏ ➲</b> /acoin, /mcoin, /sudo, /reset\n"
        f"<b>│</b>\n"
        f"<b>└╼━━━━━「 {B} sɪᴍᴜ 」━━━━━╾┘</b>"
    )

# --- 2. USER SYSTEMS ---
@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    u = sync_data(target)
    
    all_users = list(users_col.find().sort("coins", -1))
    rank = next((i for i, x in enumerate(all_users, 1) if x['user_id'] == str(target.id)), len(all_users))
    
    await message.reply_text(
        f"<b>┌──╼「 📊 ᴜsᴇʀ sᴛᴀᴛɪsᴛɪᴄs 」</b>\n"
        f"<b>│</b>\n"
        f"<b>├─👤 ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
        f"<b>├─💰 ᴄᴏɪɴs:</b> <code>{u.get('coins', 0)}</code>\n"
        f"<b>├─🏆 ʀᴀɴᴋ:</b> <code>#{rank}</code>\n"
        f"<b>├─🎖️ ᴛɪᴛʟᴇ:</b> <code>{u.get('title', 'ɴᴏɴᴇ')}</code>\n"
        f"<b>│</b>\n"
        f"<b>└╼━━━━━「 {B} 」━━━━━╾┘</b>"
    )

@app.on_message(filters.command("top") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    top_users = users_col.find().sort("coins", -1).limit(10)
    
    board = f"<b>┌──╼「 🏆 ʀɪᴄʜᴇsᴛ ᴘʟᴀʏᴇʀs 」</b>\n<b>│</b>\n"
    for i, r in enumerate(top_users, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        board += f"<b>├─{emoji} {i:02d}.</b> {get_mention(r['user_id'], r['full_name'])} ➲ <code>{r.get('coins', 0)}</code>\n"
    board += f"<b>│</b>\n<b>└╼━━━━━「 {B} 」━━━━━╾┘</b>"
    await message.reply_text(board)

@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    if time.time() - u.get('last_claim', 0) < 86400: 
        return await message.reply("<b>┌╼「 🎁 」\n├─❌ ᴛʀʏ ᴀɢᴀɪɴ ᴛᴏᴍᴏʀʀᴏᴡ!\n└╼━━━━╾┘</b>")
    
    users_col.update_one({"user_id": uid}, {"$inc": {"coins": 100}, "$set": {"last_claim": int(time.time())}})
    await message.reply("<b>┌╼「 🎁 」\n├─✅ 100 ᴄᴏɪɴs ᴀᴅᴅᴇᴅ!\n└╼━━━━╾┘</b>")

# --- 3. VAULT, GIFT, SHOP ---
@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    parts = message.text.split()
    
    if len(parts) == 1:
        days = int((time.time() - u.get('v_time', 0)) / 86400)
        interest = int(u.get('vault', 0) * (days * 0.0001))
        await message.reply(
            f"<b>┌──╼「 🏦 sᴇᴄᴜʀᴇ ᴠᴀᴜʟᴛ 」</b>\n"
            f"<b>│</b>\n"
            f"<b>├─💰 ʙᴀʟᴀɴᴄᴇ:</b> <code>{u.get('vault', 0)}</code>\n"
            f"<b>├─📈 ᴘʀᴏғɪᴛ:</b> <code>{interest}</code>\n"
            f"<b>├─💡 ᴜsᴀɢᴇ:</b> <code>/vault dep [amt]</code>\n"
            f"<b>│</b>\n"
            f"<b>└╼━━━━━「 {B} 」━━━━━╾┘</b>"
        )
    elif len(parts) >= 3:
        try:
            act, amt = parts[1], int(parts[2])
            if amt <= 0: return
            if act == "dep" and u.get('coins', 0) >= amt:
                users_col.update_one({"user_id": uid}, {"$inc": {"coins": -amt, "vault": amt}, "$set": {"v_time": int(time.time())}})
                await message.reply("<b>┌╼「 🏦 」\n├─✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇᴘᴏsɪᴛᴇᴅ!\n└╼━━━━╾┘</b>")
            elif act == "wd" and u.get('vault', 0) >= amt:
                users_col.update_one({"user_id": uid}, {"$inc": {"coins": amt, "vault": -amt}})
                await message.reply("<b>┌╼「 🏦 」\n├─🔓 ᴡɪᴛʜᴅʀᴀᴡ sᴜᴄᴄᴇss!\n└╼━━━━╾┘</b>")
        except: pass

@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    await del_cmd(message)
    if not message.reply_to_message: return
    try:
        amt = int(message.text.split()[1])
        if amt <= 0: return
        sid, rid = str(message.from_user.id), str(message.reply_to_message.from_user.id)
        s_u = sync_data(message.from_user)
        if s_u['coins'] >= amt:
            sync_data(message.reply_to_message.from_user) 
            users_col.update_one({"user_id": sid}, {"$inc": {"coins": -amt}})
            users_col.update_one({"user_id": rid}, {"$inc": {"coins": amt}})
            await message.reply(f"<b>┌╼「 🎁 」\n├─💸 ᴛʀᴀɴsғᴇʀʀᴇᴅ: {amt}\n└╼━━━━╾┘</b>")
    except: pass

@app.on_message(filters.command("shop") & filters.group)
async def shop_handler(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    if len(message.text.split()) == 1:
        return await message.reply(f"<b>┌╼「 🛒 sʜᴏᴘ 」\n├─1. VIP (15)\n├─2. KING (15)\n└╼━━━━╾┘</b>")
    
    choice = message.text.split()[1]
    title = "VIP" if choice == "1" else "KING"
    if u.get('coins', 0) >= 15:
        users_col.update_one({"user_id": uid}, {"$inc": {"coins": -15}, "$set": {"title": title}})
        await message.reply(f"<b>┌╼「 🛒 」\n├─🔥 ᴛɪᴛʟᴇ ᴜᴘɢʀᴀᴅᴇᴅ ᴛᴏ {title}!\n└╼━━━━╾┘</b>")

# --- 4. SUDO ENGINE ---
@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        t_id = str(target.id)
        u = sync_data(target)
        new_val = 1 if u.get('is_sudo', 0) == 0 else 0
        users_col.update_one({"user_id": t_id}, {"$set": {"is_sudo": new_val}})
        await message.reply_text(f"<b>┌╼「 ⚡ 」\n├─sᴜᴅᴏ ᴘᴇʀᴍɪssɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ!\n└╼━━━━╾┘</b>")
    else:
        sudos = list(users_col.find({"is_sudo": 1}))
        res = f"<b>┌╼「 ✨ sᴜᴅᴏ ʟɪsᴛ 」</b>\n"
        for i, s in enumerate(sudos, 1): res += f"<b>├─{i}.</b> {get_mention(s['user_id'], s['full_name'])}\n"
        res += f"<b>└╼━━━━╾┘</b>"
        await message.reply_text(res)
    await del_cmd(message)

@app.on_message(filters.command("acoin") & filters.group)
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message: return await del_cmd(message)
    try:
        amt = int(message.text.split()[1])
        t_id = str(message.reply_to_message.from_user.id)
        users_col.update_one({"user_id": t_id}, {"$inc": {"coins": amt}})
        await message.reply(f"<b>┌╼「 💰 」\n├─ᴀᴅᴅᴇᴅ {amt} ᴄᴏɪɴs!\n└╼━━━━╾┘</b>")
    except: pass
    await del_cmd(message)

@app.on_message(filters.command("mcoin") & filters.group)
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message: return await del_cmd(message)
    try:
        amt = int(message.text.split()[1])
        t_id = str(message.reply_to_message.from_user.id)
        users_col.update_one({"user_id": t_id}, {"$inc": {"coins": -amt}})
        await message.reply(f"<b>┌╼「 🔻 」\n├─ᴅᴇᴅᴜᴄᴛᴇᴅ {amt} ᴄᴏɪɴs!\n└╼━━━━╾┘</b>")
    except: pass
    await del_cmd(message)

@app.on_message(filters.command("reset") & filters.group)
async def reset_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message: return await del_cmd(message)
    t_id = str(message.reply_to_message.from_user.id)
    users_col.update_one({"user_id": t_id}, {"$set": {"coins": 0}})
    await message.reply(f"<b>┌╼「 🌀 」\n├─ʙᴀʟᴀɴᴄᴇ ʜᴀs ʙᴇᴇɴ ʀᴇsᴇᴛ!\n└╼━━━━╾┘</b>")

@app.on_message(filters.command("buyad") & filters.group)
async def buy_ad(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    if u.get('coins', 0) < 10: return await message.reply("<b>┌╼「 📢 」\n├─❌ ɴᴇᴇᴅ 10 ᴄᴏɪɴs!\n└╼━━━━╾┘</b>")
    try:
        ad = message.text.split(None, 1)[1]
        users_col.update_one({"user_id": uid}, {"$inc": {"coins": -10}})
        await message.reply(f"<b>┌──╼「 📢 ᴘʀᴏᴍᴏᴛɪᴏɴ 」</b>\n<b>│</b>\n<b>├─👤 ʙʏ:</b> {get_mention(uid, message.from_user.first_name)}\n<b>├─💬 ᴍsɢ:</b> <code>{ad}</code>\n<b>│</b>\n<b>└╼━━━━━「 {B} 」━━━━━╾┘</b>")
    except: pass

# --- 5. MISSIONS ---
@app.on_message(filters.group & ~filters.bot, group=1)
async def mission_tracker(client, message: Message):
    if not message.from_user: return
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    
    if u.get('msg_count', 0) + 1 >= 80:
        users_col.update_one({"user_id": uid}, {"$set": {"msg_count": 0}, "$inc": {"coins": 1}})
        await message.reply(f"<b>┌──╼「 🏆 ᴍɪssɪᴏɴ ᴄᴏᴍᴘʟᴇᴛᴇ 」</b>\n<b>│</b>\n<b>├─👤 ᴘʟᴀʏᴇʀ:</b> {get_mention(uid, u['full_name'])}\n<b>├─💰 ʀᴇᴡᴀʀᴅ:</b> <code>1 ᴄᴏɪɴ</code>\n<b>│</b>\n<b>└╼━━━━━「 {B} 」━━━━━╾┘</b>")
    else:
        users_col.update_one({"user_id": uid}, {"$inc": {"msg_count": 1}})

# --- RUN ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    Thread(target=keep_alive_ping).start()
    print("┌╼━━━━━━━━━━━━━━━╾┐")
    print("│ ✨ DX SYSTEM ACTIVE │")
    print("│ 📂 DB: MONGODB      │")
    print("└╼━━━━━━━━━━━━━━━╾┘")
    app.run()
