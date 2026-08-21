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
# SERVER RULES DICTIONARY
# ---------------------------------------------------------
SERVER_RULES = {
    1: "Be respectful to all members. No harassment, hate speech, or personal attacks.",
    2: "No spamming messages, emojis, or attachments in public channels.",
    3: "Keep discussions relevant to the respective channel topics.",
    4: "No NSFW or sexually explicit content is allowed.",
    5: "Follow Discord's Terms of Service and Community Guidelines at all times.",
    6: "Respect staff decisions and do not argue with moderators in public channels.",
    7: "No self-promotion or advertising without prior staff approval.",
    8: "Do not post personal or private information of others (no doxxing).",
    9: "Use appropriate content warnings when discussing potentially sensitive topics.",
    10: "Have fun and contribute positively to the community!"
}

# ---------------------------------------------------------
# BOT SETUP & TRACKING STATE
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")  # Removes default help command to allow custom ?help

# Track warnings and stats (resets when bot restarts)
user_warnings = {}
message_counts = {}
file_counts = {}

# Automod Regex Pattern
PROFANITY_PATTERN = re.compile(r"\b(slur_pattern_1|slur_pattern_2)\b", re.IGNORECASE)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

# ---------------------------------------------------------
# AUTOMOD & TRACKER LISTENER
# ---------------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Track message and file stats
    user_id = message.author.id
    message_counts[user_id] = message_counts.get(user_id, 0) + 1
    if message.attachments:
        file_counts[user_id] = file_counts.get(user_id, 0) + len(message.attachments)

    # Dynamic ?falseban_<name> check
    if message.content.lower().startswith("?falseban_"):
        target_name = message.content[10:].strip()
        if target_name:
            await message.channel.send(
                f"🚨 **SYSTEM NOTICE:** User **{target_name}** has been permanently banned from the server. *(Reason: Unspecified Violation)*"
            )
            await asyncio.sleep(2)
            await message.channel.send("Just kidding! It was a prank. 😜")
        return

    # Dynamic ?uwu_<text> check
    if message.content.lower().startswith("?uwu_"):
        raw_text = message.content[5:]
        uwu_text = raw_text.replace("r", "w").replace("l", "w").replace("R", "W").replace("L", "W") + " uwu"
        await message.channel.send(uwu_text)
        return

    # Automod Slur Check
    normalized_content = message.content.lower()
    if PROFANITY_PATTERN.search(normalized_content):
        await message.delete()
        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
        warnings_count = user_warnings[user_id]

        if warnings_count == 1:
            await message.channel.send(f"{message.author.mention}, that language is prohibited! **(Warning 1/3)**")
        elif warnings_count == 2:
            await message.channel.send(f"{message.author.mention}, final warning! Next offense results in a ban. **(Warning 2/3)**")
        elif warnings_count >= 3:
            try:
                await message.guild.ban(message.author, reason="Automod: 3 warnings reached.")
                await message.channel.send(f"**{message.author}** was automatically banned for accumulating 3 warnings.")
            except discord.Forbidden:
                await message.channel.send("Failed to ban user due to missing bot permissions!")
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
        "• `?warn @User [reason]` - Warns a user (with a 10s delay).\n"
        "• `?tensecban @User [reason]` or `?10secban` - Temporary 10-second ban.\n"
        "• `?weekban @User [reason]` - 7-day server ban.\n"
        "• `?permban @User [reason]` - Permanent server ban.\n"
        "• `?unban <User ID / Name>` - Unbans a user.\n"
        "• `?banlist` or `?bans` - Views all banned users.\n"
        "• `?falseban_(name)` - Sends a fake ban prank message.\n"
        "• `?clearcommands <number>` - Clears N pairs of command calls and bot replies.\n\n"
        "📊 **STATS & TRACKING COMMANDS**\n"
        "• `?messages [@User]` - Checks total messages sent since bot went online.\n"
        "• `?files [@User]` - Checks total files/attachments uploaded since bot went online.\n\n"
        "📜 **SERVER INFO COMMANDS**\n"
        "• `?rule <1-10>` or `?rule<1-10>` - Displays specific server rule.\n"
        "• `?botinfo` - Displays information about the bot and moderation policy.\n"
        "• `?serverinfo` - Displays details and statistics about this server.\n\n"
        "🎉 **FUN & UTILITY COMMANDS**\n"
        "• `?meow [count]` - Sends meows (max 50).\n"
        "• `?dice<limit>` - Rolls a dice up to specified limit.\n"
        "• `?nonsense<length>` - Generates random string of text (max 125).\n"
        "• `?uwu_(text)` - Translates text to uwu format.\n"
        "• `?emoji<count>` - Sends random emojis up to specified count (max 50)."
    )
    await ctx.send(cmd_text)

@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send(
        "For bot info, the command list, and more, go to https://discord.com/channels/1460078014724440151/1533263896595398796"
    )

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def warn_user(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await asyncio.sleep(10)
    user_id = member.id
    user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
    await ctx.send(f"⚠️ {member.mention} has been warned! Reason: **{reason}** (Total warnings: {user_warnings[user_id]})")

@bot.command(name="tensecban", aliases=["10secban"])
@commands.has_permissions(ban_members=True)
async def ten_sec_ban(ctx, member: discord.Member, *, reason: str = "10-second temporary ban"):
    await ctx.guild.ban(member, reason=reason)
    await ctx.send(f"⛔ {member.mention} has been banned for 10 seconds.")
    await asyncio.sleep(10)
    await ctx.guild.unban(member, reason="10-second ban expired")
    await ctx.send(f"✅ {member.mention} has been unbanned.")

@bot.command(name="weekban")
@commands.has_permissions(ban_members=True)
async def week_ban(ctx, member: discord.Member, *, reason: str = "7-day server ban"):
    await ctx.guild.ban(member, reason=reason)
    await ctx.send(f"⛔ {member.mention} has been banned for 7 days.")

@bot.command(name="permban")
@commands.has_permissions(ban_members=True)
async def perm_ban(ctx, member: discord.Member, *, reason: str = "Permanent server ban"):
    await ctx.guild.ban(member, reason=reason)
    await ctx.send(f"⛔ {member.mention} has been permanently banned.")

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban_user(ctx, *, user_info: str):
    banned_users = [entry async for entry in ctx.guild.bans()]
    for ban_entry in banned_users:
        user = ban_entry.user
        if str(user.id) == user_info or user.name.lower() == user_info.lower():
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned **{user.name}#{user.discriminator}**.")
            return
    await ctx.send(f"User `{user_info}` was not found in the ban list.")

@bot.command(name="banlist", aliases=["bans"])
@commands.has_permissions(ban_members=True)
async def ban_list(ctx):
    banned_users = [entry async for entry in ctx.guild.bans()]
    if not banned_users:
        await ctx.send("There are currently no banned users.")
        return
    
    ban_text = "**Banned Users:**\n" + "\n".join(f"• {b.user.name} ({b.user.id})" for b in banned_users[:20])
    await ctx.send(ban_text)

@bot.command(name="clearcommands")
@commands.has_permissions(manage_messages=True)
async def clear_commands(ctx, amount: int = 10):
    def is_bot_or_command(m):
        return m.author == bot.user or m.content.startswith("?")

    deleted = await ctx.channel.purge(limit=amount * 2, check=is_bot_or_command)
    await ctx.send(f"Cleaned up command activity.", delete_after=3)

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
@bot.command(name="rule")
async def show_rule(ctx, num: int):
    if num in SERVER_RULES:
        await ctx.send(f"📜 **Rule {num}:** {SERVER_RULES[num]}")
    else:
        await ctx.send("Invalid rule number! Please choose between 1 and 10.")

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

# Fallback handler for unspaced commands like ?dice20 or ?rule5
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        cmd = ctx.message.content[1:]
        
        # Check for ?rule<1-10>
        rule_match = re.match(r"^rule(\d+)$", cmd, re.IGNORECASE)
        if rule_match:
            r_num = int(rule_match.group(1))
            if r_num in SERVER_RULES:
                await ctx.send(f"📜 **Rule {r_num}:** {SERVER_RULES[r_num]}")
                return
            
        # Check for ?dice<limit>
        dice_match = re.match(r"^dice(\d+)$", cmd, re.IGNORECASE)
        if dice_match:
            limit = int(dice_match.group(1))
            if limit > 0:
                result = random.randint(1, limit)
                await ctx.send(f"🎲 You rolled a **{result}** (out of {limit})!")
                return

        # Check for ?nonsense<length>
        nonsense_match = re.match(r"^nonsense(\d+)$", cmd, re.IGNORECASE)
        if nonsense_match:
            length = min(int(nonsense_match.group(1)), 125)
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
            rand_str = "".join(random.choice(chars) for _ in range(length))
            await ctx.send(f"🔤 `{rand_str}`")
            return

        # Check for ?emoji<count>
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