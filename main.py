import asyncio
import os
import sqlite3
import re
import requests
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from flask import Flask
from threading import Thread

# --- CONFIG ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8513850569:AAHCsKyy1nWTYVKH_MtbW8IhKyOckWLTEDA"
B = "ᴅx" 
APP_URL = os.environ.get("APP_URL") # Render Dashboard এ এটা সেট করবেন

# --- WEB SERVER & KEEP ALIVE ---
web = Flask('')
@web.route('/')
def home(): return f"{B} COIN SYSTEM ONLINE"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web.run(host='0.0.0.0', port=port)

def ping_self():
    """বোটকে অল-টাইম একটিভ রাখার জন্য সেলফ-পিং"""
    while True:
        try:
            if APP_URL:
                requests.get(APP_URL, timeout=10)
        except Exception as e:
            print(f"Ping Error: {e}")
        time.sleep(300)

# --- DATABASE SETUP ---
if not os.path.exists("dx"): 
    os.makedirs("dx")

db = sqlite3.connect("dx/coin_data.db", check_same_thread=False)
db.row_factory = sqlite3.Row
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    username TEXT,
    coins INTEGER DEFAULT 0,
    is_sudo INTEGER DEFAULT 0
)
""")
db.commit()

# --- CLIENT ---
app = Client("DX_COIN_V9", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

INIT_SUDO = [6366113192, 6703335929, 6737589257]

# --- HELPERS ---
async def check_sudo(user_id):
    if user_id in INIT_SUDO: return True
    cursor.execute("SELECT is_sudo FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res["is_sudo"] == 1 if res else False

def get_mention(user_id, name):
    clean_name = re.sub(r'[<>#]', '', name or "User")
    return f"<a href='tg://user?id={user_id}'>{clean_name[:20]}</a>"

def sync_data(user):
    if not user: return
    name = f"{user.first_name} {user.last_name or ''}".strip()
    cursor.execute("""
        INSERT INTO users (user_id, full_name, username, coins, is_sudo)
        VALUES (?, ?, ?, 0, 0)
        ON CONFLICT(user_id) DO UPDATE SET
        full_name = excluded.full_name,
        username = excluded.username
    """, (user.id, name, user.username))
    db.commit()

# --- COMMANDS ---
@app.on_message(filters.command("sudo") & filters.group)
async def sudo_handler(client, message: Message):
    if not await check_sudo(message.from_user.id):
        try: await message.delete()
        except: pass
        return
    
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        sync_data(target)
        cursor.execute("SELECT is_sudo FROM users WHERE user_id = ?", (target.id,))
        current = cursor.fetchone()["is_sudo"]
        new_val = 1 if current == 0 else 0
        cursor.execute("UPDATE users SET is_sudo = ? WHERE user_id = ?", (new_val, target.id))
        db.commit()
        status = "✨ ɴᴏᴡ ᴀ sᴜᴅᴏ ᴜsᴇʀ" if new_val == 1 else "⚡ ʀᴇᴍᴏᴠᴇᴅ sᴜᴅᴏ"
        await message.reply_text(
            f"<b>┏━━━━━━━━━━━━━━━━━━━━━━┓</b>\n"
            f"<b> 👤 ᴜsᴇʀ: {get_mention(target.id, target.first_name)}</b>\n"
            f"<b> 📜 sᴛᴀᴛᴜs: {status}</b>\n"
            f"<b>┗━━━━━━━━━ {B} ━━━━━━━━━┛</b>"
        )
    else:
        cursor.execute("SELECT user_id, full_name FROM users WHERE is_sudo = 1")
        sudos = cursor.fetchall()
        res = f"<b>╭╼━「 ✨ sᴜᴅᴏ ᴜsᴇʀs 」━╾╮</b>\n┃\n"
        for i, s in enumerate(sudos, 1):
            res += f"<b>┃ {i}.</b> {get_mention(s['user_id'], s['full_name'])}\n"
        res += f"┃\n<b>╰╼━━━━━━━ {B} ━━━━━━━╾╯</b>"
        await message.reply_text(res)
    try: await message.delete()
    except: pass

@app.on_message(filters.command("acoin") & filters.group)
async def add_coin(client, message: Message):
    if not await check_sudo(message.from_user.id):
        try: await message.delete()
        except: pass
        return
    if not message.reply_to_message:
        await message.reply(f"<b>❌ {B} » ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ!</b>")
        return
    parts = message.text.split()
    if len(parts) < 2: return
    try:
        amount = int(parts[1])
        target = message.reply_to_message.from_user
        sync_data(target)
        cursor.execute("SELECT coins FROM users WHERE user_id = ?", (target.id,))
        old_val = cursor.fetchone()["coins"]
        new_val = old_val + amount
        cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_val, target.id))
        db.commit()
        await message.reply_text(
            f"<b>┏━━━━━━━ 💰 ᴀᴅᴅᴇᴅ ━━━━━━━┓</b>\n"
            f"<b> ➲ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
            f"<b> ➲ ᴀᴍᴏᴜɴᴛ:</b> <code>{amount}</code>\n"
            f"<b> ➲ ᴛᴏᴛᴀʟ:</b> <code>{new_val}</code>\n"
            f"<b>┗━━━━━━━━━ {B} ━━━━━━━━━┛</b>"
        )
    except: pass
    try: await message.delete()
    except: pass

@app.on_message(filters.command("mcoin") & filters.group)
async def minus_coin(client, message: Message):
    if not await check_sudo(message.from_user.id):
        try: await message.delete()
        except: pass
        return
    if not message.reply_to_message: return
    parts = message.text.split()
    if len(parts) < 2: return
    try:
        amount = int(parts[1])
        target = message.reply_to_message.from_user
        sync_data(target)
        cursor.execute("SELECT coins FROM users WHERE user_id = ?", (target.id,))
        old_val = cursor.fetchone()["coins"]
        new_val = max(0, old_val - amount)
        cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_val, target.id))
        db.commit()
        await message.reply_text(
            f"<b>┏━━━━━━━ 🔻 ᴍɪɴᴜs ━━━━━━━┓</b>\n"
            f"<b> ➲ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
            f"<b> ➲ ᴀᴍᴏᴜɴᴛ:</b> <code>{amount}</code>\n"
            f"<b> ➲ ᴛᴏᴛᴀʟ:</b> <code>{new_val}</code>\n"
            f"<b>┗━━━━━━━━━ {B} ━━━━━━━━━┛</b>"
        )
    except: pass
    try: await message.delete()
    except: pass

@app.on_message(filters.command("reset") & filters.group)
async def reset_coin(client, message: Message):
    if not await check_sudo(message.from_user.id):
        try: await message.delete()
        except: pass
        return
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        cursor.execute("UPDATE users SET coins = 0 WHERE user_id = ?", (target.id,))
        db.commit()
        await message.reply_text(
            f"<b>┏━━━━━━━ 🌀 ʀᴇsᴇᴛ ━━━━━━━┓</b>\n"
            f"<b> ➲ ᴜsᴇʀ:</b> {get_mention(target.id, target.first_name)}\n"
            f"<b> ➲ sᴛᴀᴛᴜs: ʙᴀʟᴀɴᴄᴇ ᴄʟᴇᴀʀᴇᴅ</b>\n"
            f"<b>┗━━━━━━━━━ {B} ━━━━━━━━━┛</b>"
        )
    try: await message.delete()
    except: pass

@app.on_message(filters.command(["coin", "mycoin"]) & filters.group)
async def check_stats(client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    sync_data(target)
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (target.id,))
    coins = cursor.fetchone()["coins"]
    cursor.execute("SELECT COUNT(*) FROM users WHERE coins > ?", (coins,))
    rank = cursor.fetchone()[0] + 1
    await message.reply_text(
        f"<b>╭╼━━━「 📊 sᴛᴀᴛs 」━━━╾╮</b>\n"
        f"<b>┃</b>\n"
        f"<b>┃ 👤 ᴜsᴇʀ :</b> {get_mention(target.id, target.first_name)}\n"
        f"<b>┃ 💰 ᴄᴏɪɴs :</b> <code>{coins}</code>\n"
        f"<b>┃ 🏆 ʀᴀɴᴋ :</b> <code>#{rank}</code>\n"
        f"<b>┃</b>\n"
        f"<b>╰╼━━━━━━━ {B} ━━━━━━━╾╯</b>"
    )
    try: await message.delete()
    except: pass

@app.on_message(filters.command("top") & filters.group)
async def leaderboard(client, message: Message):
    cursor.execute("SELECT user_id, full_name, coins FROM users ORDER BY coins DESC LIMIT 10")
    rows = cursor.fetchall()
    board = f"<b>╭╼━━━━━「 🏆 ᴛᴏᴘ 10 」━━━━━╾╮</b>\n┃\n"
    for i, row in enumerate(rows, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        board += f"<b>┃ {emoji} {i:02d}.</b> {get_mention(row['user_id'], row['full_name'])} ➲ <code>{row['coins']}</code>\n"
    board += f"┃\n<b>╰╼━━━━━━━ {B} ━━━━━━━╾╯</b>"
    await message.reply_text(board)
    try: await message.delete()
    except: pass

@app.on_message(filters.group & ~filters.bot, group=1)
async def auto_sync(client, message: Message):
    if message.from_user: sync_data(message.from_user)

# --- START ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    if APP_URL:
        Thread(target=ping_self, daemon=True).start()
    app.run()
