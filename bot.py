import os
import re
import random
import string
import discord
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "?"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)

_MOD_RE = re.compile(r"^\?(warn|weekban|permban|unban)\s+(.+)$", re.IGNORECASE)
_RULE_RE = re.compile(r"^\?rule\s+(\d+)$", re.IGNORECASE)
_MEOW_RE = re.compile(r"^\?meow(?:\s+(.+))?$", re.IGNORECASE)
_EMOJI_RE = re.compile(r"^\?emoji\s+(.+)$", re.IGNORECASE)
_DICE_RE = re.compile(r"^\?dice(\d*)?$", re.IGNORECASE)
_NONSENSE_RE = re.compile(r"^\?nonsense(\d*)?$", re.IGNORECASE)
_UWU_RE = re.compile(r"^\?uwu(?:\_\((.+)\))?$", re.IGNORECASE)

async def handle_banlist(message):
    if not message.author.guild_permissions.ban_members:
        await message.channel.send("❌ You need the **Ban Members** permission to view the ban list.")
        return

    banned_users = [entry async for entry in message.guild.bans()]

    if not banned_users:
        await message.channel.send("🎉 There are currently **no banned users** in this server!")
        return

    ban_list = [
        f"• **{e.user.name}** (`ID: {e.user.id}`) — *{e.reason or 'No reason provided'}*"
        for e in banned_users
    ]
    response = "**🚫 Currently Banned Users:**\n" + "\n".join(ban_list)

    if len(response) > 2000:
        await message.channel.send(f"There are **{len(banned_users)}** banned users (list is too long to display).")
    else:
        await message.channel.send(response)

async def handle_dice(message, limit_str):
    if not limit_str:
        await message.channel.send("🎲 **`?dice` Command Guide** 🎲\nRolls a random number from 1 up to your chosen limit!\n\n**Usage:** `?dice<limit>`\n**Example:** `?dice6` or `?dice20` *(Max: 1,000,000)*")
        return

    try:
        limit = int(limit_str)
    except ValueError:
        await message.channel.send("❌ Please enter a valid number! Example: `?dice6`")
        return

    if limit < 1:
        await message.channel.send("❌ The number must be at least **1**!")
        return

    if limit > 1000000:
        await message.channel.send("❌ The maximum limit is **1,000,000**!")
        return

    roll = random.randint(1, limit)
    await message.channel.send(f"🎲 You rolled a **{roll:,}** (out of **{limit:,}**)!")

async def handle_nonsense(message, length_str):
    if not length_str:
        await message.channel.send("✨ **`?nonsense` Command Guide** ✨\nGenerates a random mix of letters, numbers, and symbols!\n\n**Usage:** `?nonsense<length>`\n**Example:** `?nonsense12` or `?nonsense100` *(Max: 2,000 characters)*")
        return

    try:
        length = int(length_str)
    except ValueError:
        await message.channel.send("❌ Please provide a valid number! Example: `?nonsense15`")
        return

    if length < 1:
        await message.channel.send("❌ Length must be at least **1**!")
        return

    if length > 2000:
        await message.channel.send("❌ Maximum length is **2,000** characters (Discord limit)!")
        return

    chars = string.ascii_letters + string.digits + string.punctuation
    junk = "".join(random.choices(chars, k=length))

    await message.channel.send(junk)

async def handle_uwu(message, text):
    if not text:
        await message.channel.send("✨ **`?uwu` Command Guide** ✨\nConvewwts youww text into uwu language! :3\n\n**Usage:** `?uwu_(youww text hewe)`\n**Exampwe:** `?uwu_(Hello there!)` -> `Hewwo thewe! :3`")
        return

    uwu_text = text.replace('r', 'w').replace('R', 'W').replace('l', 'w').replace('L', 'W')
    await message.channel.send(f"{uwu_text} :3")

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    content = message.content.strip()

    if (message.guild and not message.author.guild_permissions.manage_messages and mod.contains_slur(content)):
        await handle_slur(message)
        return

    if not content.startswith(PREFIX):
        return

    lower = content.lower()

    if lower in ("?banlist", "?bans"):
        await handle_banlist(message)
        return

    if lower in ("?testwarn", "?testweekban", "?testpermban", "?testunban"):
        await handle_test(message, lower.lstrip("?"))
        return

    m = _MOD_RE.match(content)
    if m:
        await handle_manual_mod(message, m.group(1).lower(), m.group(2))
        return

    m = _RULE_RE.match(content)
    if m:
        await handle_rule(message, m.group(1).strip())
        return

    m = _MEOW_RE.match(content)
    if m:
        await handle_meow(message, m.group(1).strip() if m.group(1) else "")
        return

    m = _EMOJI_RE.match(content)
    if m:
        await handle_emoji(message, m.group(1).strip())
        return

    m = _DICE_RE.match(content)
    if m:
        await handle_dice(message, m.group(1))
        return

    m = _NONSENSE_RE.match(content)
    if m:
        await handle_nonsense(message, m.group(1))
        return

    m = _UWU_RE.match(content)
    if m:
        await handle_uwu(message, m.group(1))
        return

def main():
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN is not set.")
    keep_alive()
    client.run(TOKEN, log_handler=None)

if __name__ == "__main__":
    main()
