import os
import random
import string
import discord
from discord.ext import commands, tasks
from aiohttp import web
import moderation

# --- BOT CONFIGURATION ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

TARGET_CHANNEL_ID = 1460084752274165823
historical_bans = set()
message_counts = {}
file_counts = {}

# --- WEB SERVER FOR RENDER ---
async def handle_health(request):
    return web.Response(text="Bot is online!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- HELPER FUNCTIONS ---
def parse_duration(duration_str: str):
    if not duration_str or duration_str.lower() in ["perm", "permanent"]:
        return None
    unit = duration_str[-1].lower()
    if unit not in ["s", "m", "h", "d"]:
        return None
    try:
        val = int(duration_str[:-1])
        mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return val * mult[unit]
    except ValueError:
        return None

async def apply_role_ban(guild: discord.Guild, member: discord.Member, reason: str = "Unspecified"):
    banned_role = discord.utils.get(guild.roles, name="Banned")
    if not banned_role:
        try:
            banned_role = await guild.create_role(name="Banned", color=discord.Color.dark_gray())
        except discord.Forbidden:
            return False, "Missing permissions to create 'Banned' role."
    
    roles_to_remove = [r for r in member.roles if r != guild.default_role and r < guild.me.top_role]
    try:
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Banned: {reason}")
        await member.add_roles(banned_role, reason=f"Banned: {reason}")
        return True, None
    except discord.Forbidden:
        return False, "Missing permissions to modify user roles."

# --- INTERACTIVE ROLE BUTTON PANEL ---
class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Notifications", style=discord.ButtonStyle.primary, custom_id="role_notifs")
    async def toggle_notifs(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Notifications")
        if not role:
            return await interaction.response.send_message("❌ Role 'Notifications' does not exist.", ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("Removed Notifications role!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Added Notifications role!", ephemeral=True)

# --- BOT EVENTS ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    if not hasattr(bot, 'web_server_started'):
        bot.loop.create_task(start_web_server())
        bot.web_server_started = True
    if not check_ban_expirations.is_running():
        check_ban_expirations.start()

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # Track message and file stats
    uid = message.author.id
    message_counts[uid] = message_counts.get(uid, 0) + 1
    if message.attachments:
        file_counts[uid] = file_counts.get(uid, 0) + len(message.attachments)

    # Slur Detection
    if moderation.contains_slur(message.content):
        try:
            await message.delete()
        except Exception:
            pass
        action, count = moderation.next_action(message.guild.id, message.author.id)
        ch = message.guild.get_channel(TARGET_CHANNEL_ID) or message.channel
        
        if action == "warn":
            await ch.send(f"⚠️ {message.author.mention} **WARNING (Strike 1/3)**: Prohibited language detected.")
        elif action == "weekban":
            await apply_role_ban(message.guild, message.author, "Slur - Strike 2")
            moderation.schedule_unban(message.guild.id, message.author.id, 7 * 86400)
            await ch.send(f"🚨 **AUTOMATIC 7-DAY BAN (Strike 2/3)** for {message.author.mention}.")
        elif action == "permban":
            await apply_role_ban(message.guild, message.author, "Slur - Strike 3")
            moderation.cancel_pending_unban(message.guild.id, message.author.id)
            await ch.send(f"🚨 **AUTOMATIC PERMANENT BAN (Strike 3/3)** for {message.author.mention}.")
        return

    await bot.process_commands(message)

# --- ERROR HANDLER ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing required argument! Usage: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, (commands.MissingPermissions, commands.CheckFailure)):
        await ctx.send("❌ You do not have permission to execute this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ Invalid user or argument provided.")
    else:
        print(f"Error in {ctx.command}: {error}")

# --- UNBAN TASK LOOP ---
@tasks.loop(seconds=10)
async def check_ban_expirations():
    due = moderation.pop_due_unbans()
    for item in due:
        guild = bot.get_guild(item["guild_id"])
        if guild:
            member = guild.get_member(item["user_id"])
            if member:
                role = discord.utils.get(guild.roles, name="Banned")
                if role and role in member.roles:
                    try:
                        await member.remove_roles(role)
                        ch = guild.get_channel(TARGET_CHANNEL_ID)
                        if ch:
                            await ch.send(f"✅ {member.mention}'s temporary restriction has expired!")
                    except Exception:
                        pass

# ==========================================
# 👑 ADMIN & MODERATION COMMANDS
# ==========================================

@bot.command(name="commands")
async def show_commands_list(ctx):
    embed = discord.Embed(title="👑 ADMIN & MODERATION COMMANDS", color=discord.Color.gold())
    embed.description = (
        "• `?commands` - Displays this full command list.\n"
        "• `?help` - Shows link for bot info and command details.\n"
        "• `?roles` - Posts the interactive button panel for server roles.\n"
        "• `?addrole @User <Role>` - Manually adds a role to a user.\n"
        "• `?removerole @User <Role>` - Manually removes a role from a user.\n"
        "• `?warn @User [reason]` - Warns a user immediately.\n"
        "• `?unwarn @User` - Clears all warnings from a user.\n"
        "• `?tensecban @User [reason]` - Temporary 10-second ban.\n"
        "• `?weekban @User [reason]` - 7-day server ban.\n"
        "• `?permban @User [reason]` - Permanent server ban.\n"
        "• `?ban @User [duration] [reason]` - Restricts user with `@Banned` role.\n"
        "• `?unban <@User>` - Unbans a user.\n"
        "• `?banlist` or `?bans` - Views all current and past banned users.\n"
        "• `?falseban @User [reason]` - Sends a fake ban prank message.\n"
        "• `?loop` - Triggers rapid 50-message loop (Admin only).\n"
        "• `?clearcommands <number>` - Clears N pairs of command calls and bot replies."
    )
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send("ℹ️ **Bot Info & Help:** For command details and moderation guidelines, check your server rules or contact staff.")

@bot.command(name="roles")
async def roles_cmd(ctx):
    embed = discord.Embed(title="🎭 Server Roles", description="Click below to toggle roles!", color=discord.Color.blue())
    await ctx.send(embed=embed, view=RoleView())

@bot.command(name="addrole")
@commands.has_permissions(manage_roles=True)
async def addrole_cmd(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Added **{role.name}** to {member.mention}.")

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def removerole_cmd(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"✅ Removed **{role.name}** from {member.mention}.")

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def warn_cmd(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    action, count = moderation.next_action(ctx.guild.id, member.id)
    await ctx.send(f"⚠️ Warned {member.mention} (Strike #{count}). Reason: {reason}")

@bot.command(name="unwarn")
@commands.has_permissions(manage_messages=True)
async def unwarn_cmd(ctx, member: discord.Member):
    moderation.reset_offender(ctx.guild.id, member.id)
    await ctx.send(f"✅ Cleared all warnings for {member.mention}.")

@bot.command(name="tensecban", aliases=["10secban"])
@commands.has_permissions(ban_members=True)
async def tensecban_cmd(ctx, member: discord.Member, *, reason: str = "10s Temp Ban"):
    await apply_role_ban(ctx.guild, member, reason)
    moderation.schedule_unban(ctx.guild.id, member.id, 10)
    await ctx.send(f"⏱️ {member.mention} restricted for 10 seconds. Reason: **{reason}**")

@bot.command(name="weekban")
@commands.has_permissions(ban_members=True)
async def weekban_cmd(ctx, member: discord.Member, *, reason: str = "7-Day Ban"):
    await apply_role_ban(ctx.guild, member, reason)
    moderation.schedule_unban(ctx.guild.id, member.id, 7 * 86400)
    await ctx.send(f"🗓️ {member.mention} restricted for 7 days. Reason: **{reason}**")

@bot.command(name="permban")
@commands.has_permissions(ban_members=True)
async def permban_cmd(ctx, member: discord.Member, *, reason: str = "Permanent Ban"):
    await apply_role_ban(ctx.guild, member, reason)
    moderation.cancel_pending_unban(ctx.guild.id, member.id)
    await ctx.send(f"⛔ {member.mention} permanently restricted. Reason: **{reason}**")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_cmd(ctx, member: discord.Member, duration_str: str = "perm", *, reason: str = "Unspecified"):
    secs = parse_duration(duration_str)
    success, err = await apply_role_ban(ctx.guild, member, reason)
    if not success:
        return await ctx.send(f"❌ {err}")
    historical_bans.add(f"{member.name} ({member.id})")
    if secs:
        moderation.schedule_unban(ctx.guild.id, member.id, secs)
        await ctx.send(f"⛔ {member.mention} restricted for **{duration_str}**. Reason: **{reason}**")
    else:
        moderation.cancel_pending_unban(ctx.guild.id, member.id)
        await ctx.send(f"⛔ {member.mention} permanently restricted. Reason: **{reason}**")

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban_cmd(ctx, member: discord.Member):
    moderation.cancel_pending_unban(ctx.guild.id, member.id)
    moderation.reset_offender(ctx.guild.id, member.id)
    role = discord.utils.get(ctx.guild.roles, name="Banned")
    if role and role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"✅ Unbanned {member.mention} and reset strikes!")
    else:
        await ctx.send(f"User {member.mention} is not restricted.")

@bot.command(name="banlist", aliases=["bans"])
async def banlist_cmd(ctx):
    if not historical_bans:
        return await ctx.send("📜 No tracked bans recorded in this session.")
    await ctx.send("📜 **Recorded Bans:**\n" + "\n".join(f"• {b}" for b in historical_bans))

@bot.command(name="falseban")
async def falseban_cmd(ctx, member: discord.Member, *, reason: str = "Trolling"):
    await ctx.send(f"🚨 **SYSTEM NOTICE:** {member.mention} has been **PERMANENTLY BANNED** from the server. Reason: `{reason}`\n*(Just kidding! 😜)*")

@bot.command(name="loop")
@commands.has_permissions(administrator=True)
async def loop_cmd(ctx):
    for i in range(1, 51):
        await ctx.send(f"🔄 Loop Message #{i}")

@bot.command(name="clearcommands")
@commands.has_permissions(manage_messages=True)
async def clearcommands_cmd(ctx, amount: int = 5):
    await ctx.channel.purge(limit=(amount * 2) + 1)

# ==========================================
# 📊 STATS & TRACKING COMMANDS
# ==========================================

@bot.command(name="messages")
async def messages_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = message_counts.get(target.id, 0)
    await ctx.send(f"📊 {target.mention} has sent **{count}** messages since the bot went online.")

@bot.command(name="files")
async def files_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = file_counts.get(target.id, 0)
    await ctx.send(f"📁 {target.mention} has uploaded **{count}** files/attachments.")

# ==========================================
# 📜 SERVER INFO COMMANDS
# ==========================================

@bot.command(name="rule")
async def rule_cmd(ctx, number: int = 1):
    rules = {
        1: "Be respectful to everyone in the server.",
        2: "No spamming or self-promotion.",
        3: "No hate speech, slurs, or harassment.",
        4: "Keep topics in their designated channels.",
        5: "Follow Discord Terms of Service at all times."
    }
    msg = rules.get(number, f"Follow staff instructions and common sense.")
    await ctx.send(f"📜 **Rule {number}:** {msg}")

@bot.command(name="botinfo")
async def botinfo_cmd(ctx):
    await ctx.send("🤖 **Bot Info:** Running custom moderation suite, slur detection, and role management.")

@bot.command(name="serverinfo")
async def serverinfo_cmd(ctx):
    await ctx.send(f"🏰 **Server Info:** `{ctx.guild.name}` | Total Members: **{ctx.guild.member_count}**")

# ==========================================
# 🎉 FUN & UTILITY COMMANDS
# ==========================================

@bot.command(name="meow")
async def meow_cmd(ctx, count: int = 1):
    count = min(max(1, count), 50)
    await ctx.send(" ".join(["meow"] * count) + " :3")

@bot.command(name="dice")
async def dice_cmd(ctx, limit: int = 6):
    limit = max(1, limit)
    await ctx.send(f"🎲 Rolled a **{random.randint(1, limit)}** (1-{limit})")

@bot.command(name="nonsense")
async def nonsense_cmd(ctx, length: int = 10):
    length = min(max(1, length), 125)
    rand_str = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=length))
    await ctx.send(f"🔣 `{rand_str}`")

@bot.command(name="uwu")
async def uwu_cmd(ctx, *, text: str = "hello world"):
    translated = text.replace("r", "w").replace("l", "w").replace("R", "W").replace("L", "W") + " :3"
    await ctx.send(translated)

@bot.command(name="queer")
async def queer_cmd(ctx, *, term: str = None):
    terms = {
        "lesbian": "Non-men attracted to non-men.",
        "gay": "Men attracted to men, or a general term for attraction to the same gender.",
        "bi": "Attraction to two or more genders.",
        "trans": "Having a gender identity that differs from the sex assigned at birth.",
        "ace": "Experiencing little to no sexual attraction."
    }
    if term and term.lower() in terms:
        await ctx.send(f"🏳️‍🌈 **{term.capitalize()}:** {terms[term.lower()]}")
    else:
        key = random.choice(list(terms.keys()))
        await ctx.send(f"🏳️‍🌈 **{key.capitalize()}:** {terms[key]}")

@bot.command(name="emoji")
async def emoji_cmd(ctx, count: int = 1):
    emojis = ["😃", "😂", "🔥", "✨", "🎉", "💀", "🤖", "🍕", "⭐", "👾"]
    count = min(max(1, count), 50)
    await ctx.send("".join(random.choices(emojis, k=count)))

bot.run(os.getenv("DISCORD_TOKEN"))