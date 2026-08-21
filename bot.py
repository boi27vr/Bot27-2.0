import os
import re
import random
import asyncio
import threading
import datetime
from flask import Flask
import discord
from discord.ext import commands

# ---------------------------------------------------------
# KEEP-ALIVE WEB SERVER FOR RENDER
# ---------------------------------------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.start()

# ---------------------------------------------------------
# QUEER DICTIONARY
# ---------------------------------------------------------
QUEER_DICT = {
    "queer": "An umbrella term used by people who are not heterosexual or cisgender.",
    "lesbian": "A woman or non-binary person who is attracted to women/non-binary people.",
    "gay": "An umbrella term or specifically a man/non-binary person attracted to men.",
    "bisexual": "Attracted to two or more genders.",
    "transgender": "Having a gender identity that differs from the sex assigned at birth.",
    "transmasc": "A trans person who identifies more with masculinity or male identity.",
    "transfem": "A trans person who identifies more with femininity or female identity.",
    "pansexual": "Attracted to people regardless of their gender identity.",
    "asexual": "Experiencing little to no sexual attraction to others.",
    "aromantic": "Experiencing little to no romantic attraction to others.",
    "nonbinary": "Having a gender identity that doesn't fit strictly into male or female.",
    "genderfluid": "Having a gender identity that changes over time.",
    "agender": "Identifying as having no gender or being gender neutral.",
    "demisexual": "Experiencing sexual attraction only after forming a strong emotional bond."
}

# ---------------------------------------------------------
# BOT SETUP & TRACKING STATE
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")  # Allows custom ?help command

# User tracking memory
user_warnings = {}
message_counts = {}
file_counts = {}
historical_bans = set()  # Permanent record of banned users (survives unbans)

# Regex pattern catching base slurs and common leetspeak/symbol bypasses (1/!/| for i, 3 for e, @/4 for a, 0 for o)
PROFANITY_PATTERN = re.compile(
    r"[n|n][i1!\|l]gg[a@4]|[n|n][i1!\|l]gg[e3]r|[f|f][a@4]gg[o0]t", 
    re.IGNORECASE
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

# ---------------------------------------------------------
# AUTOMOD & LISTENER
# ---------------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Track message and file counts
    user_id = message.author.id
    message_counts[user_id] = message_counts.get(user_id, 0) + 1
    if message.attachments:
        file_counts[user_id] = file_counts.get(user_id, 0) + len(message.attachments)

    # Dynamic ?falseban @User [reason] check
    if message.content.lower().startswith("?falseban"):
        try:
            await message.delete()
        except discord.NotFound:
            pass
        
        args = message.content.split(maxsplit=2)
        target = args[1] if len(args) > 1 else "@User"
        reason = args[2] if len(args) > 2 else "Unspecified Violation"
        
        notice = await message.channel.send(
            f"🚨 **SYSTEM NOTICE:** {target} will be permanently banned in 10 secs. "
            f"For support and/or ban appealing, dm @boi27vr. Reason: {reason}"
        )
        await asyncio.sleep(2)
        await notice.edit(content=f"🚨 **SYSTEM NOTICE:** {target} will be permanently banned in 10 secs...\n\njk lol you're fine 😜")
        return

    # Dynamic ?uwu_(text) check
    if message.content.lower().startswith("?uwu_"):
        try:
            await message.delete()
        except discord.NotFound:
            pass
        
        raw_text = message.content[5:]
        uwu_text = raw_text.replace("r", "w").replace("l", "w").replace("R", "W").replace("L", "W") + " :3"
        await message.channel.send(uwu_text)
        return

    # Dynamic ?queer_<term> lookup
    if message.content.lower().startswith("?queer_"):
        term = message.content[7:].strip().lower()
        if term in QUEER_DICT:
            await message.channel.send(f"🌈 **{term.capitalize()}**: {QUEER_DICT[term]}")
        else:
            await message.channel.send(f"Couldn't find `{term}` in the dictionary! Type `?queer` for a random term.")
        return

    # Automod Slur Escalation Check
    normalized_content = message.content.lower()
    if PROFANITY_PATTERN.search(normalized_content):
        try:
            await message.delete()
        except discord.NotFound:
            pass

        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
        strike = user_warnings[user_id]

        if strike == 1:
            await message.channel.send(f"⚠️ {message.author.mention} has been warned for prohibited language! **(Strike 1/4)**")
        elif strike == 2:
            try:
                await message.guild.kick(message.author, reason="Automod: Strike 2 (Prohibited language)")
                await message.channel.send(f"👞 {message.author.mention} was kicked from the server. **(Strike 2/4)**")
            except discord.Forbidden:
                await message.channel.send("Failed to kick user due to missing permissions!")
        elif strike == 3:
            try:
                historical_bans.add(f"{message.author.name} ({message.author.id})")
                await message.guild.ban(message.author, reason="Automod: Strike 3 (7-day ban)")
                await message.channel.send(f"⛔ **{message.author}** has been banned for 7 days. **(Strike 3/4)**")
                await asyncio.sleep(604800)  # 7 days
                await message.guild.unban(message.author, reason="7-day automod ban expired")
            except discord.Forbidden:
                await message.channel.send("Failed to ban user due to missing permissions!")
        elif strike >= 4:
            try:
                historical_bans.add(f"{message.author.name} ({message.author.id})")
                await message.guild.ban(message.author, reason="Automod: Strike 4 (Permanent ban)")
                await message.channel.send(f"⛔ **{message.author}** has been permanently banned from the server. **(Strike 4/4)**")
            except discord.Forbidden:
                await message.channel.send("Failed to ban user due to missing permissions!")
        return

    await bot.process_commands(message)

# ---------------------------------------------------------
# ADMIN & MODERATION COMMANDS
# ---------------------------------------------------------
@bot.command(name="commands")
async def show_commands(ctx):
    cmd_text = (
        "👑 **ADMIN & MODERATION COMMANDS**\n"
        "• `?commands` - Displays this full command list.\n"
        "• `?help` - Shows link for bot info and command details.\n"
        "• `?warn @User [reason]` - Warns a user immediately.\n"
        "• `?unwarn @User` - Clears all warnings from a user.\n"
        "• `?tensecban @User [reason]` or `?10secban` - Temporary 10-second ban.\n"
        "• `?weekban @User [reason]` - 7-day server ban after 10s.\n"
        "• `?permban @User [reason]` - Permanent server ban after 10s.\n"
        "• `?unban <User ID / Name>` - Unbans a user.\n"
        "• `?banlist` or `?bans` - Views all current and past banned users.\n"
        "• `?falseban @User [reason]` - Sends a fake ban prank message.\n"
        "• `?clearcommands<number>` - Clears N pairs of command calls and bot replies.\n\n"
        "📊 **STATS & TRACKING COMMANDS**\n"
        "• `?messages [@User]` - Checks total messages sent since bot went online.\n"
        "• `?files [@User]` - Checks total files/attachments uploaded since bot went online.\n\n"
        "📜 **SERVER INFO COMMANDS**\n"
        "• `?rule<1-10>` - Direct link to server rules channel.\n"
        "• `?botinfo` - Displays information about the bot and moderation policy.\n"
        "• `?serverinfo` - Displays details and statistics about this server.\n\n"
        "🎉 **FUN & UTILITY COMMANDS**\n"
        "• `?meow [count]` - Sends meows (max 50).\n"
        "• `?dice<limit>` - Rolls a dice up to specified limit.\n"
        "• `?nonsense<length>` - Generates random string of text (max 125).\n"
        "• `?uwu_(text)` - Translates text to uwu format with :3.\n"
        "• `?queer` or `?queer_<term>` - Random or targeted LGBTQ+ dictionary lookup.\n"
        "• `?emoji<count>` - Sends random emojis up to specified count (max 50)."
    )
    await ctx.send(cmd_text)

@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send(
        "For bot info, the command list, and more, go to https://discord.com/channels/1460078014724440151/1533263896595398796"
    )

@bot.command(name="queer")
async def queer_cmd(ctx):
    term, definition = random.choice(list(QUEER_DICT.items()))
    await ctx.send(f"🌈 **{term.capitalize()}**: {definition}")

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def warn_user(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass
    
    user_id = member.id
    user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
    await ctx.send(f"⚠️ {member.mention} has been warned! Reason: **{reason}** (Total warnings: {user_warnings[user_id]})")

@bot.command(name="unwarn")
@commands.has_permissions(manage_messages=True)
async def unwarn_user(ctx, member: discord.Member):
    user_warnings[member.id] = 0
    await ctx.send(f"✅ Removed all warnings for {member.mention}.")

@bot.command(name="tensecban", aliases=["10secban"])
@commands.has_permissions(ban_members=True)
async def ten_sec_ban(ctx, member: discord.Member, *, reason: str = "Unspecified Violation"):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

    historical_bans.add(f"{member.name} ({member.id})")
    await ctx.send(
        f"🚨 **SYSTEM NOTICE:** {member.mention} will be banned for 10 seconds in 10 secs. "
        f"For support and/or ban appealing, dm @boi27vr Reason: {reason}"
    )
    await asyncio.sleep(10)
    await ctx.guild.ban(member, reason=reason)
    await asyncio.sleep(10)
    await ctx.guild.unban(member, reason="10-second ban expired")

@bot.command(name="weekban")
@commands.has_permissions(ban_members=True)
async def week_ban(ctx, member: discord.Member, *, reason: str = "Unspecified Violation"):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

    historical_bans.add(f"{member.name} ({member.id})")
    await ctx.send(
        f"🚨 **SYSTEM NOTICE:** {member.mention} will be banned for 7 days in 10 secs. "
        f"For support and/or ban appealing, dm @boi27vr Reason: {reason}"
    )
    await asyncio.sleep(10)
    await ctx.guild.ban(member, reason=reason)

@bot.command(name="permban")
@commands.has_permissions(ban_members=True)
async def perm_ban(ctx, member: discord.Member, *, reason: str = "Unspecified Violation"):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

    historical_bans.add(f"{member.name} ({member.id})")
    await ctx.send(
        f"🚨 **SYSTEM NOTICE:** {member.mention} will be permanently banned in 10 secs. "
        f"For support and/or ban appealing, dm @boi27vr Reason: {reason}"
    )
    await asyncio.sleep(10)
    await ctx.guild.ban(member, reason=reason)

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban_user(ctx, *, user_info: str):
    clean_info = user_info.replace("<@", "").replace(">", "").strip()
    banned_users = [entry async for entry in ctx.guild.bans()]
    for ban_entry in banned_users:
        user = ban_entry.user
        if str(user.id) == clean_info or user.name.lower() == clean_info.lower():
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned **{user.name}**.")
            return
    await ctx.send(f"User `{user_info}` was not found in active bans.")

@bot.command(name="banlist", aliases=["bans"])
@commands.has_permissions(ban_members=True)
async def ban_list(ctx):
    if not historical_bans:
        await ctx.send("No users have been recorded in the ban log yet.")
        return
    
    ban_text = "**Historical Ban Log (Including Unbanned Users):**\n" + "\n".join(f"• {user}" for user in historical_bans)
    await ctx.send(ban_text)

# ---------------------------------------------------------
# STATS & TRACKING COMMANDS
# ---------------------------------------------------------
@bot.command(name="messages")
async def check_messages(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = message_counts.get(target.id, 0)
    await ctx.send(f"📊 **{target.display_name}** has sent **{count}** messages since the bot last restarted.")

@bot.command(name="files")
async def check_files(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = file_counts.get(target.id, 0)
    await ctx.send(f"📁 **{target.display_name}** has uploaded **{count}** attachments since the bot last restarted.")

# ---------------------------------------------------------
# SERVER INFO COMMANDS
# ---------------------------------------------------------
@bot.command(name="botinfo")
async def bot_info(ctx):
    await ctx.send(
        "Hello! We use a simple bot to moderate, assist, and add fun to our server. "
        "Don't worry, we aren't spying, it simply checks if any slurs are used. "
        "Admins can also use it to manually moderate users. "
        "Check https://discord.com/channels/1460078014724440151/1533263896595398796 for more info."
    )

@bot.command(name="serverinfo")
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"🏰 {guild.name} Info", color=discord.Color.green())
    embed.add_field(name="Total Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="Server ID", value=str(guild.id), inline=True)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    await ctx.send(embed=embed)

# ---------------------------------------------------------
# FUN & UTILITY COMMANDS
# ---------------------------------------------------------
@bot.command(name="meow")
async def meow_cmd(ctx, count: int = 1):
    count = max(1, min(count, 50))
    await ctx.send(" ".join(["meow"] * count))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        cmd = ctx.message.content[1:]

        clear_match = re.match(r"^clearcommands(\d+)$", cmd, re.IGNORECASE)
        if clear_match:
            try:
                await ctx.message.delete()
            except discord.NotFound:
                pass
            
            bundles = int(clear_match.group(1))
            limit = bundles * 2
            
            def is_command_or_reply(m):
                return m.author == bot.user or m.content.startswith("?")
            
            await ctx.channel.purge(limit=limit, check=is_command_or_reply)
            return

        rule_match = re.match(r"^rule(\d+)$", cmd, re.IGNORECASE)
        if rule_match:
            r_num = int(rule_match.group(1))
            if 1 <= r_num <= 10:
                await ctx.send(f"📜 Check out rule **#{r_num}** here: https://discord.com/channels/1460078014724440151/1460078118797840607")
            else:
                await ctx.send("Please specify a rule number between 1 and 10.")
            return

        dice_match = re.match(r"^dice(\d+)$", cmd, re.IGNORECASE)
        if dice_match:
            limit = int(dice_match.group(1))
            if limit > 0:
                result = random.randint(1, limit)
                await ctx.send(f"🎲 You rolled a **{result}** (out of {limit})!")
                return

        nonsense_match = re.match(r"^nonsense(\d+)$", cmd, re.IGNORECASE)
        if nonsense_match:
            length = min(int(nonsense_match.group(1)), 125)
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
            rand_str = "".join(random.choice(chars) for _ in range(length))
            await ctx.send(f"🔤 `{rand_str}`")
            return

        emoji_match = re.match(r"^emoji(\d+)$", cmd, re.IGNORECASE)
        if emoji_match:
            count = min(int(emoji_match.group(1)), 50)
            emojis = ["🔥", "💥", "✨", "💫", "🐱", "🐶", "🍕", "🧋", "🎮", "🎲", "👑", "🚀"]
            res = "".join(random.choice(emojis) for _ in range(count))
            await ctx.send(res)
            return

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions to execute this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required parameters for that command.")
    else:
        print(f"Unhandled Error: {error}")

# ---------------------------------------------------------
# STARTUP
# ---------------------------------------------------------
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("ERROR: DISCORD_TOKEN environment variable not set!")