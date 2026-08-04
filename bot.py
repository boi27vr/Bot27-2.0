import os
import re
import random
import string
import asyncio
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

user_message_counts = {}
user_file_counts = {}

SERVER_RULES = {
    1: "Absolutely no hate speech, toxicity, or bullying! Any form of hate, including, but not limited to, homopbia, transphobia, xenophobia, sexism, or racism can result in a permanent ban!",
    2: "No offensive content. Dark humor is allowed but make sure nobody gets offended.",
    3: "Be respectful. You don't have to be all sunshine and rainbows but no harassment, over the top swearing, or personal attacks.\n✅️ \"What the ####\"\n❌️ \"Shut the #### up\"",
    4: "No inappropriate content! It doesn't have to be exactly family friendly, but don't act crazy. NSFW of any kind is not allowed. This includes, but is not limited to, nudity, extreme gore, excessive horror, etc.",
    5: "Follow Discord's Terms of Service",
    6: "Use channels properly. No spam. We have meme and spam channels for that. Also, please stay on topic. There is an off topic channel.",
    7: "Listen to staff. In order to keep a friendly and safe environment, please listen to staff and do what they say.",
    8: "No impersonating. This includes staff, helpers, or anyone else in charge.",
    9: "Keep drama out. It is unbelievably annoying...",
    10: "Have common sense. If it feels like it might cause problems, just don't do it!"
}

EMOJI_POOL = [
    "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "🥹", "☺️", "😊", "😇", "🙂", "🙃", "😉",
    "😌", "😍", "🥰", "😘", "😗", "😙", "😚", "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓",
    "😎", "🥸", "🤩", "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣", "😖", "😫",
    "😩", "🥺", "😢", "😭", "😮‍💨", "😤", "😠", "😡", "🤬", "🤯", "😳", "🥵", "🥶", "😱", "😨",
    "😰", "😥", "😓", "🫣", "🤗", "🫡", "🤔", "🫣", "🤭", "🥱", "👻", "💀", "☠️", "👽", "🤖",
    "💩", "🎉", "🔥", "✨", "🌟", "💫", "💥", "❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤"
]

_MOD_RE = re.compile(r"^\?(warn|weekban|permban|unban|tensecban|10secban)(?:\s+(.+))?$", re.IGNORECASE)
_RULE_RE = re.compile(r"^\?rule\s*(\d*)?$", re.IGNORECASE)
_MEOW_RE = re.compile(r"^\?meow\s*(\d*)?(?:\s+(.+))?$", re.IGNORECASE)
_EMOJI_RE = re.compile(r"^\?emoji\s*(\d*)?$", re.IGNORECASE)
_DICE_RE = re.compile(r"^\?dice\s*(\d*)?$", re.IGNORECASE)
_NONSENSE_RE = re.compile(r"^\?nonsense\s*(\d*)?$", re.IGNORECASE)
_UWU_RE = re.compile(r"^\?uwu(?:\_\((.+)\))?$", re.IGNORECASE)
_FALSEBAN_RE = re.compile(r"^\?falseban(?:\_\((.+)\))?$", re.IGNORECASE)
_MESSAGES_RE = re.compile(r"^\?messages(?:\s+(.+))?$", re.IGNORECASE)
_FILES_RE = re.compile(r"^\?files(?:\s+(.+))?$", re.IGNORECASE)

async def auto_unban_10s(guild, user, channel):
    await asyncio.sleep(10)
    try:
        await guild.unban(user, reason="10-second temp ban expired.")
        await channel.send(f"✅ **{user.name}**'s 10-second ban has expired and they have been unbanned!")
    except discord.Forbidden:
        await channel.send(f"⚠️ Tried to auto-unban **{user.name}**, but I lack permissions.")
    except discord.HTTPException:
        pass

async def handle_manual_mod(message, action, target_and_reason):
    if not message.author.guild_permissions.ban_members and action in ("weekban", "permban", "unban", "tensecban", "10secban"):
        await message.channel.send("❌ You need **Ban Members** permissions to use this command.")
        return

    if not target_and_reason:
        await message.channel.send(f"⚠️ **Usage:** `?{action} @User [reason]`")
        return

    parts = target_and_reason.split(" ", 1)
    raw_target = parts[0]
    reason = parts[1] if len(parts) > 1 else "No reason provided."

    member = None
    if message.mentions:
        member = message.mentions[0]
    elif raw_target.isdigit():
        member = message.guild.get_member(int(raw_target))

    if action == "warn":
        target_name = member.mention if member else raw_target
        await message.channel.send(f"⚠️ **{target_name}** will receive a warning in **10 seconds**...\n**Reason:** {reason}")
        await asyncio.sleep(10)
        await message.channel.send(f"⚠️ **{target_name}** has been officially warned!\n**Reason:** {reason}")

    elif action in ("tensecban", "10secban"):
        if not member:
            await message.channel.send(f"❌ Could not find member `{raw_target}` in this server.")
            return

        user = member
        await message.channel.send(f"⏱️ **{user.name}** will be banned for 10 seconds starting in **10 seconds**...\n**Reason:** {reason}")
        await asyncio.sleep(10)

        try:
            await member.ban(reason=f"[10-Sec Ban] {reason}", delete_message_days=0)
            await message.channel.send(f"⏱️ **{user.name}** has now been banned for **10 seconds**!\n**Reason:** {reason}")
            asyncio.create_task(auto_unban_10s(message.guild, user, message.channel))
        except discord.Forbidden:
            await message.channel.send("❌ **Failed:** My role is lower than this user, or I lack **Ban Members** permission.")
        except discord.HTTPException:
            await message.channel.send("❌ An error occurred while attempting to ban this user.")

    elif action == "permban":
        if not member:
            await message.channel.send(f"❌ Could not find member `{raw_target}` in this server.")
            return

        await message.channel.send(f"⏱️ **{member.name}** will be **permanently banned** in **10 seconds**...\n**Reason:** {reason}")
        await asyncio.sleep(10)

        try:
            await member.ban(reason=reason, delete_message_days=0)
            await message.channel.send(f"🚫 **{member.name}** has been permanently banned from the server.\n**Reason:** {reason}")
        except discord.Forbidden:
            await message.channel.send("❌ **Failed:** My role is lower than this user, or I lack **Ban Members** permission.")

    elif action == "weekban":
        if not member:
            await message.channel.send(f"❌ Could not find member `{raw_target}` in this server.")
            return

        await message.channel.send(f"⏱️ **{member.name}** will be **banned for 7 days** in **10 seconds**...\n**Reason:** {reason}")
        await asyncio.sleep(10)

        try:
            await member.ban(reason=f"[7-Day Ban] {reason}", delete_message_days=7)
            await message.channel.send(f"⏳ **{member.name}** has been banned for 7 days.\n**Reason:** {reason}")
        except discord.Forbidden:
            await message.channel.send("❌ **Failed:** I lack permissions to ban this user.")

    elif action == "unban":
        banned_users = [entry async for entry in message.guild.bans()]
        user_to_unban = None

        for entry in banned_users:
            if raw_target in (str(entry.user.id), entry.user.name, f"{entry.user.name}#{entry.user.discriminator}"):
                user_to_unban = entry.user
                break

        if not user_to_unban:
            await message.channel.send(f"❌ Could not find `{raw_target}` in the server ban list.")
            return

        try:
            await message.guild.unban(user_to_unban, reason=reason)
            await message.channel.send(f"✅ **{user_to_unban.name}** has been unbanned.")
        except discord.Forbidden:
            await message.channel.send("❌ I lack permissions to unban users.")

async def handle_commands_list(message):
    if not (message.author.guild_permissions.administrator or message.author.guild_permissions.ban_members):
        await message.channel.send("🔒 **Access Denied:** You must be an Administrator or Moderator to view the command list.")
        return

    commands_text = (
        "👑 **ADMIN & MODERATION COMMANDS**\n"
        "• `?commands` or `?help` - Displays this admin command list.\n"
        "• `?warn @User [reason]` - Warns a user (with a 10s delay).\n"
        "• `?tensecban @User [reason]` - Temporary 10-second ban.\n"
        "• `?weekban @User [reason]` - 7-day server ban.\n"
        "• `?permban @User [reason]` - Permanent server ban.\n"
        "• `?unban <User ID / Name>` - Unbans a user.\n"
        "• `?banlist` or `?bans` - Views all banned users.\n"
        "• `?falseban_(name)` - Sends a fake ban prank message.\n\n"
        "📊 **STATS & TRACKING COMMANDS**\n"
        "• `?messages [@User]` - Checks total messages sent since bot went online.\n"
        "• `?files [@User]` - Checks total files/attachments uploaded since bot went online.\n\n"
        "📜 **SERVER INFO COMMANDS**\n"
        "• `?rule <1-10>` or `?rule<1-10>` - Displays specific server rule.\n\n"
        "🎉 **FUN & UTILITY COMMANDS**\n"
        "• `?meow [count]` - Sends meows (max 50).\n"
        "• `?dice<limit>` - Rolls a dice up to specified limit.\n"
        "• `?nonsense<length>` - Generates random string of text.\n"
        "• `?uwu_(text)` - Translates text to uwu format.\n"
        "• `?emoji<count>` - Sends random emojis up to specified count (max 50)."
    )
    await message.channel.send(commands_text)

async def handle_rule(message, rule_num):
    if not rule_num:
        await message.channel.send("📜 **`?rule` Command Guide**\nUse `?rule <number>` or `?rule<number>` to view a server rule! (e.g. `?rule 7` or `?rule7`)")
        return

    try:
        num = int(rule_num)
        if num in SERVER_RULES:
            await message.channel.send(f"📜 **Rule #{num}:** {SERVER_RULES[num]}")
        else:
            await message.channel.send(f"No rule number {num}. Please enter a number between 1-10 after ?rule.")
    except ValueError:
        await message.channel.send("Please enter a valid number after ?rule.")

async def handle_meow(message, count_str, text):
    if count_str:
        try:
            count = int(count_str)
            if count > 50:
                await message.channel.send("Sowwy! Max meow is 50 :3")
                return
            if count >= 1:
                meows = " ".join(["meow"] * count)
                await message.channel.send(f"{meows} :3")
                return
        except ValueError:
            pass

    await message.channel.send("meow :3")

async def handle_emoji(message, count_str):
    if not count_str:
        await message.channel.send("😃 **`?emoji` Command Guide** 😃\nSends a set of random emojis!\n\n**Usage:** `?emoji<count>`\n**Example:** `?emoji13` or `?emoji 5` *(Max: 50)*")
        return

    try:
        count = int(count_str)
        if count < 1:
            await message.channel.send("❌ Please choose a number of at least **1**!")
            return
        if count > 50:
            await message.channel.send("❌ Maximum limit is **50** emojis!")
            return

        chosen_emojis = "".join(random.choices(EMOJI_POOL, k=count))
        await message.channel.send(chosen_emojis)
    except ValueError:
        await message.channel.send("❌ Please enter a valid number! Example: `?emoji13`")

async def handle_messages(message, target_str):
    target_user = message.author
    if message.mentions:
        target_user = message.mentions[0]
    
    count = user_message_counts.get(target_user.id, 0)
    await message.channel.send(f"💬 **{target_user.name}** has sent **{count:,}** message(s) since I was online!")

async def handle_files(message, target_str):
    target_user = message.author
    if message.mentions:
        target_user = message.mentions[0]
    
    count = user_file_counts.get(target_user.id, 0)
    await message.channel.send(f"📁 **{target_user.name}** has sent **{count:,}** file(s) since I was online!")

async def handle_test(message, test_type):
    await message.channel.send(f"🧪 **Test Executed:** `{test_type}` command test successful for {message.author.mention}!")

async def handle_banlist(message):
    if not message.author.guild_permissions.ban_members:
        await message.channel.send("❌ You need the **Ban Members** permission to view the ban list.")
        return

    try:
        banned_users = [entry async for entry in message.guild.bans()]
    except discord.Forbidden:
        await message.channel.send("❌ I don't have permission to view the server ban list.")
        return

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
        await message.channel.send("🎲 **Usage:** `?dice<limit>` (e.g. `?dice6` or `?dice20`)")
        return

    try:
        limit = int(limit_str)
    except ValueError:
        await message.channel.send("❌ Please enter a valid number! Example: `?dice6`")
        return

    if limit < 1 or limit > 1000000:
        await message.channel.send("❌ Limit must be between 1 and 1,000,000!")
        return

    roll = random.randint(1, limit)
    await message.channel.send(f"🎲 You rolled a **{roll:,}** (out of **{limit:,}**)!")

async def handle_nonsense(message, length_str):
    if not length_str:
        await message.channel.send("✨ **Usage:** `?nonsense<length>` (e.g. `?nonsense12`)")
        return

    try:
        length = int(length_str)
    except ValueError:
        await message.channel.send("❌ Please provide a valid number!")
        return

    if length < 1 or length > 2000:
        await message.channel.send("❌ Length must be between 1 and 2,000!")
        return

    chars = string.ascii_letters + string.digits + string.punctuation
    junk = "".join(random.choices(chars, k=length))
    await message.channel.send(junk)

async def handle_uwu(message, text):
    if not text:
        await message.channel.send("✨ **Usage:** `?uwu_(your text here)`")
        return

    uwu_text = text.replace('r', 'w').replace('R', 'W').replace('l', 'w').replace('L', 'W')
    await message.channel.send(f"{uwu_text} :3")

async def handle_falseban(message, target):
    if not target:
        await message.channel.send("✨ **Usage:** `?falseban_(username)`")
        return

    ban_msg = await message.channel.send(f"🚫 **{target}** has been permanently banned from the server.\n**Reason:** Manual action by {message.author.mention}")
    await asyncio.sleep(3)
    await ban_msg.edit(content=f"🚫 **{target}** has been permanently banned from the server.\n**Reason:** Manual action by {message.author.mention}\n\n*jk you're fine lol.*")

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    user_id = message.author.id
    user_message_counts[user_id] = user_message_counts.get(user_id, 0) + 1

    if message.attachments:
        user_file_counts[user_id] = user_file_counts.get(user_id, 0) + len(message.attachments)

    content = message.content.strip()

    if not content.startswith(PREFIX):
        return

    lower = content.lower()

    if lower in ("?commands", "?help"):
        await handle_commands_list(message)
        return

    if lower in ("?banlist", "?bans"):
        await handle_banlist(message)
        return

    if lower in ("?testwarn", "?testweekban", "?testpermban", "?testunban", "?testtensecban"):
        try:
            await message.delete()
        except (discord.HTTPException, discord.Forbidden):
            pass
        await handle_test(message, lower.lstrip("?"))
        return

    m = _RULE_RE.match(content)
    if m:
        await handle_rule(message, m.group(1))
        return

    m = _MOD_RE.match(content)
    if m:
        try:
            await message.delete()
        except (discord.HTTPException, discord.Forbidden):
            pass
        await handle_manual_mod(message, m.group(1).lower(), m.group(2))
        return

    m = _MESSAGES_RE.match(content)
    if m:
        await handle_messages(message, m.group(1))
        return

    m = _FILES_RE.match(content)
    if m:
        await handle_files(message, m.group(1))
        return

    m = _MEOW_RE.match(content)
    if m:
        await handle_meow(message, m.group(1), m.group(2).strip() if m.group(2) else "")
        return

    m = _EMOJI_RE.match(content)
    if m:
        await handle_emoji(message, m.group(1))
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

    m = _FALSEBAN_RE.match(content)
    if m:
        try:
            await message.delete()
        except (discord.HTTPException, discord.Forbidden):
            pass
        await handle_falseban(message, m.group(1))
        return

def main():
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN is not set.")
    keep_alive()
    client.run(TOKEN, log_handler=None)

if __name__ == "__main__":
    main()
