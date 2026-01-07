import os
import re
import requests
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from flask import Flask
from threading import Thread
from supabase import create_client, Client as SupabaseClient

# --- CONFIGURATION ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8513850569:AAHCsKyy1nWTYVKH_MtbW8IhKyOckWLTEDA"
B = "ᴅx" 
URL = "https://dark-coin.onrender.com"

# --- SUPABASE CONNECTION ---
SUPABASE_URL = "https://iszcjjaewgcfyjhaumgx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlzemNqamFld2djZnlqaGF1bWd4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkzNTMyNTYsImV4cCI6MjA3NDkyOTI1Nn0.o82Y-gBk8tryFmmHWPcgosPGfvWmaguwp6mS7f1tWA4"
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ANTI-SLEEP PING ---
def keep_alive_ping():
    while True:
        try:
            requests.get(URL)
            print(f"📡 ᴀᴄᴛɪᴠᴇ: ᴘɪɴɢ sᴇɴᴛ ᴛᴏ {URL}")
        except: pass
        time.sleep(600)

# --- AUTO DB INIT ---
def initialize_db():
    sql_query = """
    CREATE TABLE IF NOT EXISTS users (
      user_id text PRIMARY KEY,
      full_name text,
      username text,
      coins bigint DEFAULT 0,
      vault bigint DEFAULT 0,
      v_time bigint DEFAULT 0,
      msg_count int DEFAULT 0,
      last_claim bigint DEFAULT 0,
      is_sudo int DEFAULT 0,
      title text DEFAULT 'ɴᴏɴᴇ'
    );
    """
    try: supabase.postgrest.rpc('exec_sql', {'sql_query': sql_query}).execute()
    except: pass

# --- WEB SERVER ---
web = Flask('')
@web.route('/')
def home(): return f"<b>{B} SYSTEM ACTIVE 24/7</b>"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

app = Client("DX_COIN_ULTIMATE", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPERS ---
def sync_data(user):
    if not user: return
    uid = str(user.id)
    name = f"{user.first_name} {user.last_name or ''}".strip()
    res = supabase.table("users").select("*").eq("user_id", uid).execute()
    if not res.data:
        supabase.table("users").insert({
            "user_id": uid, "full_name": name, "username": user.username,
            "coins": 0, "vault": 0, "v_time": int(time.time()), 
            "msg_count": 0, "last_claim": 0, "is_sudo": 0, "title": "ɴᴏɴᴇ"
        }).execute()
    else:
        supabase.table("users").update({"full_name": name, "username": user.username}).eq("user_id", uid).execute()

async def check_sudo(user_id):
    if user_id in INIT_SUDO: return True
    res = supabase.table("users").select("is_sudo").eq("user_id", str(user_id)).execute()
    return res.data[0]['is_sudo'] == 1 if res.data else False

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
    sync_data(target)
    u = supabase.table("users").select("*").eq("user_id", str(target.id)).execute().data[0]
    all_u = supabase.table("users").select("coins").order("coins", desc=True).execute().data
    rank = next((i for i, x in enumerate(all_u, 1) if x['coins'] <= u['coins']), len(all_u))
    await message.reply_text(
        f"<b>┌╼「 📊 sᴛᴀᴛs 」</b>\n"
        f"<b>├ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
        f"<b>├ ᴄᴏɪɴs:</b> <code>{u['coins']}</code>\n"
        f"<b>├ ʀᴀɴᴋ:</b> <code>#{rank}</code>\n"
        f"<b>├ ᴛɪᴛʟᴇ:</b> {u.get('title', 'ɴᴏɴᴇ')}\n"
        f"<b>└╼━━━━ {B} ━━━━╾┘</b>"
    )

@app.on_message(filters.command("top") & filters.group)
async def leaderboard(client, message: Message):
    await del_cmd(message)
    rows = supabase.table("users").select("*").order("coins", desc=True).limit(10).execute().data
    board = f"<b>┌╼「 🏆 ᴛᴏᴘ 10 」</b>\n"
    for i, r in enumerate(rows, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        board += f"<b>├ {emoji} {i:02d}.</b> {get_mention(r['user_id'], r['full_name'])} ➲ <code>{r['coins']}</code>\n"
    board += f"<b>└╼━━━━ {B} ━━━━╾┘</b>"
    await message.reply_text(board)

@app.on_message(filters.command("claim") & filters.group)
async def daily_claim(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = supabase.table("users").select("*").eq("user_id", uid).execute().data[0]
    if time.time() - u['last_claim'] < 86400: 
        return await message.reply("<b>┌╼「 🎁 」\n├ ❌ ᴛʀʏ ᴛᴏᴍᴏʀʀᴏᴡ!\n└╼━━━━╾┘</b>")
    supabase.table("users").update({"coins": u['coins']+100, "last_claim": int(time.time())}).eq("user_id", uid).execute()
    await message.reply("<b>┌╼「 🎁 」\n├ ✅ 100 ᴄᴏɪɴs ᴄʟᴀɪᴍᴇᴅ!\n└╼━━━━╾┘</b>")

# --- 3. VAULT, GIFT, SHOP ---
@app.on_message(filters.command("vault") & filters.group)
async def vault_handler(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    sync_data(message.from_user)
    user = supabase.table("users").select("*").eq("user_id", uid).execute().data[0]
    parts = message.text.split()
    if len(parts) == 1:
        days = int((time.time() - user['v_time']) / 86400)
        interest = int(user['vault'] * (days * 0.0001))
        await message.reply(f"<b>┌╼「 🏦 {B} ᴠᴀᴜʟᴛ 」</b>\n<b>├ 💰 ᴠᴀᴜʟᴛ:</b> <code>{user['vault']}</code>\n<b>├ 📈 ɪɴᴛ:</b> <code>{interest}</code>\n<b>├ ➲ /vault dep [amt]</b>\n<b>└╼━━━━╾┘</b>")
    elif len(parts) >= 3:
        try:
            act, amt = parts[1], int(parts[2])
            if act == "dep" and user['coins'] >= amt:
                supabase.table("users").update({"coins": user['coins']-amt, "vault": user['vault']+amt, "v_time": int(time.time())}).eq("user_id", uid).execute()
                await message.reply("<b>├ ✅ ᴅᴇᴘᴏsɪᴛᴇᴅ!</b>")
            elif act == "wd" and user['vault'] >= amt:
                supabase.table("users").update({"coins": user['coins']+amt, "vault": user['vault']-amt}).eq("user_id", uid).execute()
                await message.reply("<b>├ 🔓 ᴡɪᴛʜᴅʀᴀᴡɴ!</b>")
        except: pass

@app.on_message(filters.command("gift") & filters.group)
async def gift_coin(client, message: Message):
    await del_cmd(message)
    if not message.reply_to_message: return
    try:
        amt = int(message.text.split()[1])
        sid, rid = str(message.from_user.id), str(message.reply_to_message.from_user.id)
        s_u = supabase.table("users").select("coins").eq("user_id", sid).execute().data[0]
        if s_u['coins'] >= amt:
            r_u = supabase.table("users").select("coins").eq("user_id", rid).execute().data[0]
            supabase.table("users").update({"coins": s_u['coins'] - amt}).eq("user_id", sid).execute()
            supabase.table("users").update({"coins": r_u['coins'] + amt}).eq("user_id", rid).execute()
            await message.reply(f"<b>┌╼「 🎁 」\n├ 💸 {amt} ᴄᴏɪɴs sᴇɴᴛ!\n└╼━━━━╾┘</b>")
    except: pass

@app.on_message(filters.command("shop") & filters.group)
async def shop_handler(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    if len(message.text.split()) == 1:
        return await message.reply(f"<b>┌╼「 🛒 sʜᴏᴘ 」</b>\n<b>├ 1. VIP (15) | 2. KING (15)</b>\n<b>└╼━━━━╾┘</b>")
    choice = message.text.split()[1]
    title = "VIP" if choice == "1" else "KING"
    u = supabase.table("users").select("coins").eq("user_id", uid).execute().data[0]
    if u['coins'] >= 15:
        supabase.table("users").update({"coins": u['coins']-15, "title": title}).eq("user_id", uid).execute()
        await message.reply(f"<b>├ 🔥 ɴᴏᴡ ʏᴏᴜ ᴀʀᴇ {title}!</b>")

# --- 4. SUDO ENGINE ---
@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    if not await check_sudo(message.from_user.id): return await del_cmd(message)
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        t_id = str(target.id)
        sync_data(target)
        u = supabase.table("users").select("is_sudo").eq("user_id", t_id).execute().data[0]
        new_val = 1 if u['is_sudo'] == 0 else 0
        supabase.table("users").update({"is_sudo": new_val}).eq("user_id", t_id).execute()
        await message.reply_text(f"<b>├ ⚡ sᴜᴅᴏ ᴜᴘᴅᴀᴛᴇᴅ!</b>")
    else:
        sudos = supabase.table("users").select("*").eq("is_sudo", 1).execute().data
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
        u = supabase.table("users").select("coins").eq("user_id", t_id).execute().data[0]
        supabase.table("users").update({"coins": u['coins'] + amt}).eq("user_id", t_id).execute()
        await message.reply(f"<b>├ 💰 ᴀᴅᴅᴇᴅ {amt} ᴄᴏɪɴs!</b>")
    except: pass
    await del_cmd(message)

@app.on_message(filters.command("mcoin") & filters.group)
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message: return await del_cmd(message)
    try:
        amt = int(message.text.split()[1])
        t_id = str(message.reply_to_message.from_user.id)
        u = supabase.table("users").select("coins").eq("user_id", t_id).execute().data[0]
        supabase.table("users").update({"coins": max(0, u['coins'] - amt)}).eq("user_id", t_id).execute()
        await message.reply(f"<b>├ 🔻 ᴍɪɴᴜs {amt} ᴄᴏɪɴs!</b>")
    except: pass
    await del_cmd(message)

@app.on_message(filters.command("reset") & filters.group)
async def reset_coin(client, message: Message):
    if not await check_sudo(message.from_user.id) or not message.reply_to_message: return await del_cmd(message)
    t_id = str(message.reply_to_message.from_user.id)
    supabase.table("users").update({"coins": 0}).eq("user_id", t_id).execute()
    await message.reply(f"<b>├ 🌀 ʙᴀʟᴀɴᴄᴇ ʀᴇsᴇᴛ!</b>")

# --- 5. ADS & MISSIONS ---
@app.on_message(filters.command("buyad") & filters.group)
async def buy_ad(client, message: Message):
    await del_cmd(message)
    uid = str(message.from_user.id)
    u = supabase.table("users").select("coins").eq("user_id", uid).execute().data[0]
    if u['coins'] < 10: return await message.reply("<b>├ ❌ ɴᴇᴇᴅ 10 ᴄᴏɪɴs!</b>")
    try:
        ad = message.text.split(None, 1)[1]
        supabase.table("users").update({"coins": u['coins']-10}).eq("user_id", uid).execute()
        await message.reply(f"<b>┌╼「 📢 ᴀᴅ 」\n├ ʙʏ: {get_mention(uid, message.from_user.first_name)}\n├ ᴍsɢ: {ad}\n└╼━━━━╾┘</b>")
    except: pass

@app.on_message(filters.group & ~filters.bot, group=1)
async def mission_tracker(client, message: Message):
    if not message.from_user: return
    sync_data(message.from_user)
    uid = str(message.from_user.id)
    u = supabase.table("users").select("*").eq("user_id", uid).execute().data[0]
    if u['msg_count'] + 1 >= 80:
        supabase.table("users").update({"msg_count": 0, "coins": u['coins']+1}).eq("user_id", uid).execute()
        await message.reply(f"<b>🏆 {get_mention(uid, u['full_name'])} ᴇᴀʀɴᴇᴅ 1 ᴄᴏɪɴ!</b>")
    else:
        supabase.table("users").update({"msg_count": u['msg_count']+1}).eq("user_id", uid).execute()

# --- RUN ---
if __name__ == "__main__":
    initialize_db()
    Thread(target=run_web).start()
    Thread(target=keep_alive_ping).start()
    app.run()
