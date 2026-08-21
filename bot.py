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
    # Core & Common Terms
    "lesbian": "A woman who is attracted to other women.",
    "gay": "A man who is attracted to other men.",
    "bisexual": "Someone who is attracted to people of two or more genders.",
    "transgender": "Someone whose gender identity is different from the sex they were assigned at birth.",
    "queer": "An umbrella term for anyone who falls outside of heterosexual or cisgender norms.",
    "questioning": "Someone who is taking time to explore and figure out their gender or sexuality.",
    "intersex": "Someone born with physical traits or chromosomes that do not fit standard male or female categories.",
    "asexual": "Someone who experiences little to no sexual attraction to others.",
    "aromantic": "Someone who experiences little to no romantic attraction to others.",
    "pansexual": "Someone who is attracted to people regardless of their gender.",
    "nonbinary": "Someone whose gender identity sits outside the strict binary of being solely a man or a woman.",
    "genderfluid": "Someone whose gender identity changes and shifts over time.",
    "agender": "Someone who feels gender neutral or feels like they do not have a gender at all.",
    "demisexual": "Someone who only feels sexual attraction after building a strong emotional bond with someone.",
    "genderqueer": "An umbrella term for people whose gender identity does not align with traditional societal norms.",
    "bigender": "Someone who experiences two distinct genders simultaneously or moves between them.",
    "demiromantic": "Someone who only develops romantic feelings after forming a deep emotional connection.",
    "aroace": "Short for aromantic asexual, meaning someone who feels little to no romantic or sexual attraction.",
    "panromantic": "Someone who feels romantic attraction toward people regardless of their gender identity.",
    "omnisexual": "Attracted to people of all genders, though gender still plays a role in how they feel that attraction.",
    "omniromantic": "Romantically attracted to people of all genders, while still noticing and caring about gender identity.",

    # Popular & Moderate Niche
    "cisgender": "Someone whose gender identity aligns with the sex they were assigned at birth.",
    "androgyne": "Someone whose gender expression or identity blends both masculine and feminine traits, or sits between them.",
    "neutrois": "Someone who identifies as having a neutral or non existent gender identity.",
    "trigender": "Someone who experiences three distinct gender identities at the same time or moves between them.",
    "pangender": "Someone whose gender identity encompasses many or all genders at once.",
    "xenogender": "A nonbinary gender identity defined by concepts outside traditional human ideas of gender, like nature, space, or art.",
    "polyamorous": "Someone who desires or engages in open romantic or sexual relationships with more than one partner at a time, with everyone's consent.",
    "polysexual": "Someone who is attracted to many, but not necessarily all, genders.",
    "polyromantic": "Someone who is romantically attracted to many, but not necessarily all, genders.",
    "cupiosexual": "Someone on the asexual spectrum who does not feel sexual attraction, but still desires a sexual relationship.",
    "cupioromantic": "Someone on the aromantic spectrum who does not feel romantic attraction, but still desires a romantic relationship.",
    "apothisexual": "Someone on the asexual spectrum who feels sex repulsed and has no desire for sexual activity.",
    "apothiromantic": "Someone on the aromantic spectrum who feels romance repulsed and has no desire for romantic relationships.",
    "greysexual": "Someone who experiences sexual attraction very rarely, weakly, or only under specific circumstances.",
    "greyromantic": "Someone who experiences romantic attraction very rarely, weakly, or only under specific circumstances.",
    "abrosexual": "Someone whose sexual orientation fluctuates, changes, or fluidly shifts over time.",
    "abroromantic": "Someone whose romantic orientation fluctuates, changes, or fluidly shifts over time.",
    "sapphic": "An umbrella term for women or nonbinary individuals who feel romantic or sexual attraction to other women.",
    "achillean": "An umbrella term for men or nonbinary individuals who feel romantic or sexual attraction to other men.",
    "diamoric": "An umbrella term for romantic or sexual relationships involving at least one nonbinary person.",
    "toric": "A nonbinary person who is attracted to men.",
    "trixic": "A nonbinary person who is attracted to women.",
    "transmasculine": "A transgender person who was assigned female at birth but identifies more with masculinity or a male gender path.",
    "transmasc": "A transgender person who was assigned female at birth but identifies more with masculinity or a male gender path.",
    "transfeminine": "A transgender person who was assigned male at birth but identifies more with femininity or a female gender path.",
    "transfem": "A transgender person who was assigned male at birth but identifies more with femininity or a female gender path.",
    "aliqusexual": "Someone who only feels sexual attraction under specific, unique circumstances or conditions.",
    "aliquromantic": "Someone who only feels romantic attraction under specific, unique circumstances or conditions.",

    # Super Niche Terms
    "aegosexual": "Someone on the asexual spectrum who enjoys sexual content or ideas, but feels no desire to participate themselves.",
    "aegoromantic": "Someone on the aromantic spectrum who enjoys romantic stories or media, but feels no desire for a romantic relationship in real life.",
    "quoiromantic": "Someone who finds the concept of romantic attraction confusing or hard to distinguish from friendship.",
    "quoisexual": "Someone who feels sexual attraction is an unclear, confusing, or non applicable concept to them.",
    "reciprosextual": "Someone who only feels sexual attraction toward someone after knowing that person is attracted to them first.",
    "reciproromantic": "Someone who only feels romantic attraction toward someone after knowing that person has romantic feelings for them first.",
    "fraysexual": "Someone who experiences attraction only toward people they do not know well, which fades as a bond forms.",
    "frayromantic": "Someone who feels romantic attraction only toward strangers or acquaintances, which fades as they get closer.",
    "lithosexual": "Someone who feels sexual attraction toward others, but does not want that attraction returned or acted on.",
    "lithromantic": "Someone who feels romantic attraction toward others, but prefers that those feelings are not reciprocated.",
    "cassgender": "Someone who feels their gender identity is indifferent, unimportant, or irrelevant to who they are.",
    "demigender": "Someone who feels a partial connection to a specific gender, alongside a connection to another gender or no gender.",
    "demiboy": "Someone who identifies partially as a boy or man, but not completely.",
    "demigirl": "Someone who identifies partially as a girl or woman, but not completely.",
    "fluxgender": "Someone whose gender identity stays the same type, but varies in intensity over time.",
    "boyflux": "Someone whose connection to feeling male or masculine shifts in intensity from day to day.",
    "girlflux": "Someone whose connection to feeling female or feminine shifts in intensity from day to day.",
    "enbyflux": "Someone whose connection to nonbinary gender identities shifts in strength over time.",
    "androsexual": "Someone who feels attraction toward masculinity or men.",
    "gynesexual": "Someone who feels attraction toward femininity or women.",
    "ambiamorous": "Someone who is happy and comfortable in either polyamorous or monogamous relationships."
}

# ---------------------------------------------------------
# BOT SETUP & TRACKING STATE
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")

user_warnings = {}
message_counts = {}
file_counts = {}
historical_bans = set()

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

    user_id = message.author.id
    message_counts[user_id] = message_counts.get(user_id, 0) + 1
    if message.attachments:
        file_counts[user_id] = file_counts.get(user_id, 0) + len(message.attachments)

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

    if message.content.lower().startswith("?uwu_"):
        try:
            await message.delete()
        except discord.NotFound:
            pass
        
        raw_text = message.content[5:]
        uwu_text = raw_text.replace("r", "w").replace("l", "w").replace("R", "W").replace("L", "W") + " :3"
        await message.channel.send(uwu_text)
        return

    if message.content.lower().startswith("?queer_"):
        term = message.content[7:].strip().lower()
        if term in QUEER_DICT:
            await message.channel.send(f"🌈 **{term.capitalize()}**: {QUEER_DICT[term]}")
        else:
            await message.channel.send(f"Couldn't find `{term}` in the dictionary! Type `?queer` for a random term.")
        return

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
                await asyncio.sleep(604800)
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