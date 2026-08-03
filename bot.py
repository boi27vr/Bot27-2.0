import os
import re
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
        await handle_meow(message, m.group(1).strip())
        return

    m = _EMOJI_RE.match(content)
    if m:
        await handle_emoji(message, m.group(1).strip())
        return

def main():
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN is not set.")
    keep_alive()
    client.run(TOKEN, log_handler=None)

if __name__ == "__main__":
    main()
