import os
import re
import requests
import time
import firebase_admin
from firebase_admin import credentials, db
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8513850569:AAHCsKyy1nWTYVKH_MtbW8IhKyOckWLTEDA"
B = "ᴅx" 
URL = "https://dark-coin.onrender.com"

# --- FIREBASE CONNECTION (FIXED) ---
FIREBASE_DB_URL = "https://dxsimu-c0f49-default-rtdb.firebaseio.com"

if not firebase_admin._apps:
    # credentials.Anonymous() এর বদলে সরাসরি নিচের মত ডিক্লেয়ার করুন
    firebase_admin.initialize_app(options={
        'databaseURL': FIREBASE_DB_URL
    })

# Main Database Reference
db_ref = db.reference("users")

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
def home(): return f"<b>{B} SYSTEM ACTIVE (FIREBASE)</b>"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

app = Client("DX_COIN_FIREBASE", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPERS (FIREBASE SYNC) ---
def sync_data(user):
    if not user: return None
    uid = str(user.id)
    name = f"{user.first_name} {user.last_name or ''}".strip()
    user_ref = db_ref.child(uid)
    data = user_ref.get()
    
    if not data:
        data = {
            "user_id": uid, "full_name": name, "username": user.username or "None",
            "coins": 0, "vault": 0, "v_time": int(time.time()), 
            "msg_count": 0, "last_claim": 0, "is_sudo": 0, "title": "ɴᴏɴᴇ"
        }
        user_ref.set(data)
    else:
        user_ref.update({"full_name": name, "username": user.username or "None"})
    return data

async def check_sudo(user_id):
    if user_id in INIT_SUDO: return True
    data = db_ref.child(str(user_id)).get()
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
        f"<b>┌╼「 ✨ {B} ᴍᴇɴᴜ 」</b>\n"
        f"<b>├ 📊 ᴜsᴇʀ:</b> /coin, /top, /claim\n"
        f"<b>├ 🏦 ᴠᴀᴜʟᴛ:</b> /vault, /gift, /shop\n"
        f"<b>├ 📢 ᴀᴅs:</b> /buyad (10 ᴄᴏɪɴs)\n"
        f"<b>├ ⚡ sᴜᴅᴏ:</b> /acoin, /mcoin, /sudo, /reset\n"
        f"<b>└╼━━━━ {B} ━━━━╾┘</b>"
    )

# --- 2. USER SYSTEMS ---
@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    await del_cmd(message)
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    u = sync_data(target)
    
    all_data = db_ref.get() or {}
    sorted_users = sorted(all_data.values(), key=lambda x: x.get('coins', 0), reverse=True)
    rank = next((i for i, x in enumerate(sorted_users, 1) if str(x['user_id']) == str(target.id)), len(sorted_users))
    
    await message.reply_text(
        f"<b>┌╼「 📊 sᴛᴀᴛs 」</b>\n"
        f"<b>├ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
        f"<b>├ ᴄᴏɪɴs:</b> <code>{u.get('coins', 0)}</code>\n"
        f"<b>├ ʀᴀɴᴋ:</b> <code>#{rank}</code>\n"
        f"<b>├ ᴛɪᴛʟᴇ:</b> {u.get('title', 'ɴᴏɴᴇ')}\n"
        f"<b>└╼━━━━ {B} ━━━━╾┘</b>"
    )

@app.on_message(filters.command("top") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    all_data = db_ref.get() or {}
    sorted_users = sorted(all_data.values(), key=lambda x: x.get('coins', 0), reverse=True)[:10]
    
    board = f"<b>┌╼「 🏆 ᴛᴏᴘ 10 」</b>\n"
    for i, r in enumerate(sorted_users, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        board += f"<b>├ {emoji} {i:02d}.</b> {get_mention(r['user_id'], r['full_name'])} ➲ <code>{r.get('coins', 0)}</code>\n"
    board += f"<b>└╼━━━━ {B} ━━━━╾┘</b>"
    await message.reply_text(board)

@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    if time.time() - u.get('last_claim', 0) < 86400: 
        return await message.reply("<b>┌╼「 🎁 」\n├ ❌ ᴛʀʏ ᴛᴏᴍᴏʀʀᴏᴡ!\n└╼━━━━╾┘</b>")
    
    db_ref.child(uid).update({"coins": u.get('coins', 0) + 100, "last_claim": int(time.time())})
    await message.reply("<b>┌╼「 🎁 」\n├ ✅ 100 ᴄᴏɪɴs ᴄʟᴀɪᴍᴇᴅ!\n└╼━━━━╾┘</b>")

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
        await message.reply(f"<b>┌╼「 🏦 {B} ᴠᴀᴜʟᴛ 」</b>\n<b>├ 💰 ᴠᴀᴜʟᴛ:</b> <code>{u.get('vault', 0)}</code>\n<b>├ 📈 ɪɴᴛ:</b> <code>{interest}</code>\n<b>├ ➲ /vault dep [amt]</b>\n<b>└╼━━━━╾┘</b>")
    elif len(parts) >= 3:
        try:
            act, amt = parts[1], int(parts[2])
            if amt <= 0: return
            if act == "dep" and u.get('coins', 0) >= amt:
                db_ref.child(uid).update({"coins": u['coins']-amt, "vault": u['vault']+amt, "v_time": int(time.time())})
                await message.reply("<b>├ ✅ ᴅᴇᴘᴏsɪᴛᴇᴅ!</b>")
            elif act == "wd" and u.get('vault', 0) >= amt:
                db_ref.child(uid).update({"coins": u['coins']+amt, "vault": u['vault']-amt})
                await message.reply("<b>├ 🔓 ᴡɪᴛʜᴅʀᴀᴡɴ!</b>")
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
        r_u = sync_data(message.reply_to_message.from_user)
        if s_u['coins'] >= amt:
            db_ref.child(sid).update({"coins": s_u['coins'] - amt})
            db_ref.child(rid).update({"coins": r_u['coins'] + amt})
            await message.reply(f"<b>┌╼「 🎁 」\n├ 💸 {amt} ᴄᴏɪɴs sᴇɴᴛ!\n└╼━━━━╾┘</b>")
    except: pass

@app.on_message(filters.command("shop") & filters.group)
async def shop_handler(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    if len(message.text.split()) == 1:
        return await message.reply(f"<b>┌╼「 🛒 sʜᴏᴘ 」</b>\n<b>├ 1. VIP (15) | 2. KING (15)</b>\n<b>└╼━━━━╾┘</b>")
    
    choice = message.text.split()[1]
    title = "VIP" if choice == "1" else "KING"
    if u.get('coins', 0) >= 15:
        db_ref.child(uid).update({"coins": u['coins']-15, "title": title})
        await message.reply(f"<b>├ 🔥 ɴᴏᴡ ʏᴏᴜ ᴀʀᴇ {title}!</b>")

# --- 4. SUDO ENGINE ---
@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        t_id = str(target.id)
        u = sync_data(target)
        new_val = 1 if u.get('is_sudo', 0) == 0 else 0
        db_ref.child(t_id).update({"is_sudo": new_val})
        await message.reply_text(f"<b>├ ⚡ sᴜᴅᴏ ᴜᴘᴅᴀᴛᴇᴅ!</b>")
    else:
        all_data = db_ref.get() or {}
        sudos = [v for v in all_data.values() if v.get('is_sudo') == 1]
        res = f"<b>┌╼「 ✨ sᴜᴅᴏ ᴜsᴇʀs 」</b>\n"
        for i, s in enumerate(sudos, 1): res += f"<b>├ {i}.</b> {get_mention(s['user_id'], s['full_name'])}\n"
        res += f"<b>└╼━━━━╾┘</b>"
        await message.reply_text(res)
    await del_cmd(message)

@app.on_message(filters.command("acoin") & filters.group)
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message: return await del_cmd(message)
    try:
        amt = int(message.text.split()[1])
        t_id = str(message.reply_to_message.from_user.id)
        u = sync_data(message.reply_to_message.from_user)
        db_ref.child(t_id).update({"coins": u.get('coins', 0) + amt})
        await message.reply(f"<b>├ 💰 ᴀᴅᴅᴇᴅ {amt} ᴄᴏɪɴs!</b>")
    except: pass
    await del_cmd(message)

@app.on_message(filters.command("mcoin") & filters.group)
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message: return await del_cmd(message)
    try:
        amt = int(message.text.split()[1])
        t_id = str(message.reply_to_message.from_user.id)
        u = sync_data(message.reply_to_message.from_user)
        db_ref.child(t_id).update({"coins": max(0, u.get('coins', 0) - amt)})
        await message.reply(f"<b>├ 🔻 ᴍɪɴᴜs {amt} ᴄᴏɪɴs!</b>")
    except: pass
    await del_cmd(message)

@app.on_message(filters.command("reset") & filters.group)
async def reset_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message: return await del_cmd(message)
    t_id = str(message.reply_to_message.from_user.id)
    db_ref.child(t_id).update({"coins": 0})
    await message.reply(f"<b>├ 🌀 ʙᴀʟᴀɴᴄᴇ ʀᴇsᴇᴛ!</b>")

@app.on_message(filters.command("buyad") & filters.group)
async def buy_ad(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    if u.get('coins', 0) < 10: return await message.reply("<b>├ ❌ ɴᴇᴇᴅ 10 ᴄᴏɪɴs!</b>")
    try:
        ad = message.text.split(None, 1)[1]
        db_ref.child(uid).update({"coins": u['coins']-10})
        await message.reply(f"<b>┌╼「 📢 ᴀᴅ 」\n├ ʙʏ: {get_mention(uid, message.from_user.first_name)}\n├ ᴍsɢ: {ad}\n└╼━━━━╾┘</b>")
    except: pass

# --- 5. MISSIONS ---
@app.on_message(filters.group & ~filters.bot, group=1)
async def mission_tracker(client, message: Message):
    if not message.from_user: return
    uid = str(message.from_user.id)
    u = sync_data(message.from_user)
    
    if u.get('msg_count', 0) + 1 >= 80:
        db_ref.child(uid).update({"msg_count": 0, "coins": u.get('coins', 0) + 1})
        await message.reply(f"<b>🏆 {get_mention(uid, u['full_name'])} ᴇᴀʀɴᴇᴅ 1 ᴄᴏɪɴ!</b>")
    else:
        db_ref.child(uid).update({"msg_count": u.get('msg_count', 0) + 1})

# --- RUN ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    Thread(target=keep_alive_ping).start()
    print("🚀 Bot started with Fixed Firebase!")
    app.run()
