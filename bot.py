# BAN OVERHAUL 1.5
import os
import discord
from discord.ext import commands, tasks
from aiohttp import web
import moderation  # Import standalone moderation logic

# --- BOT CONFIGURATION ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents)

# Target Channel ID for all logs, alerts, and appeals
TARGET_CHANNEL_ID = 1460084752274165823

# Historical ban logging set
historical_bans = set()


# --- WEB SERVER FOR RENDER PORT CHECK ---
async def handle_health(request):
    return web.Response(text="Bot is online and healthy!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# --- DURATION PARSER HELPER ---
def parse_duration(duration_str: str):
    """Converts duration strings like '10s', '30m', '12h', '1d' into total seconds."""
    if not duration_str or duration_str.lower() in ["perm", "permanent"]:
        return None
    unit = duration_str[-1].lower()
    if unit not in ["s", "m", "h", "d"]:
        return None
    try:
        value = int(duration_str[:-1])
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return value * multipliers[unit]
    except ValueError:
        return None


# --- ROLE BAN HELPER ---
async def apply_role_ban(guild: discord.Guild, member: discord.Member, reason: str = "Unspecified"):
    """
    Strips all removable roles from the member and assigns the 'Banned' role.
    """
    banned_role = discord.utils.get(guild.roles, name="Banned")
    if not banned_role:
        try:
            banned_role = await guild.create_role(
                name="Banned",
                color=discord.Color.dark_gray(),
                reason="Auto-created Banned role for soft-ban restriction system."
            )
        except discord.Forbidden:
            return False, "Missing permissions to create the 'Banned' role."

    roles_to_remove = [r for r in member.roles if r != guild.default_role and r < guild.me.top_role]
    try:
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Banned: {reason}")
        await member.add_roles(banned_role, reason=f"Banned: {reason}")
        return True, None
    except discord.Forbidden:
        return False, "Missing permissions to modify roles for this user."


# --- APPEAL UI VIEW & THREAD CREATION ---
class AppealView(discord.ui.View):
    def __init__(self, target_user: discord.Member):
        super().__init__(timeout=300)
        self.target_user = target_user
        self.reason = None
        self.has_evidence = None
        self.evidence_kind = "None"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message("❌ This appeal menu is not for you.", ephemeral=True)
            return False
        return True

    @discord.ui.select(
        placeholder="Why should you be unbanned? (Required)",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="There was an error", value="There was an error", emoji="⚠️"),
            discord.SelectOption(label="They overexaggerated", value="They overexaggerated", emoji="⚖️"),
            discord.SelectOption(label="I admit mistake & learned my lesson", value="Admitted mistake", emoji="🙏"),
            discord.SelectOption(label="Account was compromised/hacked", value="Account compromised", emoji="🔒"),
            discord.SelectOption(label="Other reason", value="Other reason", emoji="❓"),
        ],
        row=0
    )
    async def select_reason(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.reason = select.values[0]
        await interaction.response.send_message(f"Selected reason: **{self.reason}**", ephemeral=True)

    @discord.ui.select(
        placeholder="Do you have evidence? (Required)",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="Yes", value="Yes", emoji="✅"),
            discord.SelectOption(label="Kinda", value="Kinda", emoji="🤔"),
            discord.SelectOption(label="No", value="No", emoji="❌"),
        ],
        row=1
    )
    async def select_has_evidence(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.has_evidence = select.values[0]
        await interaction.response.send_message(f"Selected evidence status: **{self.has_evidence}**", ephemeral=True)

    @discord.ui.select(
        placeholder="If so, what kind? (Optional)",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="Video", value="Video", emoji="📹"),
            discord.SelectOption(label="Screenshot", value="Screenshot", emoji="📸"),
            discord.SelectOption(label="Trustable Witness", value="Trustable Witness", emoji="👁️"),
            discord.SelectOption(label="Other", value="Other", emoji="📁"),
            discord.SelectOption(label="None / Not Applicable", value="None", emoji="🚫"),
        ],
        row=2
    )
    async def select_evidence_kind(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.evidence_kind = select.values[0]
        await interaction.response.send_message(f"Selected evidence type: **{self.evidence_kind}**", ephemeral=True)

    @discord.ui.button(label="Submit Appeal", style=discord.ButtonStyle.green, row=3)
    async def submit_appeal(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Validate that required questions are answered
        if not self.reason or not self.has_evidence:
            return await interaction.response.send_message(
                "⚠️ **Incomplete Appeal!** You must answer both **Why should you be unbanned?** and **Do you have evidence?** before submitting.",
                ephemeral=True
            )

        guild = interaction.guild
        boi_member = discord.utils.get(guild.members, name="boi27vr")
        boi_ping = boi_member.mention if boi_member else "@boi27vr"

        # Disable UI components
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            "✅ **Appeal Submitted!** A private thread has been created for your appeal.",
            ephemeral=True
        )

        # Create private thread attached to message
        target_channel = guild.get_channel(TARGET_CHANNEL_ID) or interaction.channel
        thread = await target_channel.create_thread(
            name=f"Appeal - {interaction.user.name}",
            type=discord.ChannelType.private_thread,
            auto_archive_duration=1440,
            reason=f"Ban appeal thread for {interaction.user}"
        )

        await thread.add_user(interaction.user)
        if boi_member:
            await thread.add_user(boi_member)

        embed = discord.Embed(
            title="📋 Ban Appeal Submitted",
            description=f"Appeal created for {interaction.user.mention}.",
            color=discord.Color.blue(),
            timestamp=interaction.created_at
        )
        embed.add_field(name="Reason Stated", value=self.reason, inline=False)
        embed.add_field(name="Has Evidence?", value=self.has_evidence, inline=True)
        embed.add_field(name="Evidence Type", value=self.evidence_kind, inline=True)

        await thread.send(
            content=f"🚨 {boi_ping} — A new ban appeal thread has been created for {interaction.user.mention}!",
            embed=embed
        )

        await thread.send(
            f"Hello {interaction.user.mention},\n\n"
            "Please use this private thread to **elaborate on what happened** and **provide any relevant evidence** "
            f"(screenshots, videos, or witnesses corresponding to your choice: *{self.evidence_kind}*)."
        )


# --- BOT EVENTS ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    
    if not hasattr(bot, 'web_server_started'):
        bot.loop.create_task(start_web_server())
        bot.web_server_started = True

    if not check_ban_expirations.is_running():
        check_ban_expirations.start()


@bot.event
async def on_member_join(member: discord.Member):
    unbans = moderation._read(moderation._UNBANS, [])
    is_pending = any(x["guild_id"] == member.guild.id and x["user_id"] == member.id for x in unbans)
    
    if is_pending:
        guild = member.guild
        boi_member = discord.utils.get(guild.members, name="boi27vr")
        boi_ping = boi_member.mention if boi_member else "@boi27vr"

        banned_role = discord.utils.get(guild.roles, name="Banned")
        if banned_role:
            roles_to_remove = [r for r in member.roles if r != guild.default_role]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Ban evasion prevention")
            await member.add_roles(banned_role, reason="Re-applied soft ban on rejoin")

            moderation.schedule_unban(guild.id, member.id, 86400)
            
            target_channel = guild.get_channel(TARGET_CHANNEL_ID)
            if target_channel:
                await target_channel.send(
                    f"🚨 {boi_ping} **BAN EVASION DETECTED** 🚨\n"
                    f"{member.mention} (`{member.id}`) attempted to evade a soft ban by leaving and rejoining!\n"
                    f"⏱️ **Penalty Added:** +1 Day added to unban schedule."
                )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    if moderation.contains_slur(message.content):
        guild = message.guild
        member = message.author
        boi_member = discord.utils.get(guild.members, name="boi27vr")
        boi_ping = boi_member.mention if boi_member else "@boi27vr"

        try:
            await message.delete()
        except discord.NotFound:
            pass

        action, count = moderation.next_action(guild.id, member.id)
        target_channel = guild.get_channel(TARGET_CHANNEL_ID) or message.channel

        if action == "warn":
            await target_channel.send(
                f"⚠️ {member.mention} **WARNING (Strike 1/3)**: Prohibited language detected.\n"
                f"Further violations will result in automated temporary or permanent bans."
            )
        elif action == "weekban":
            success, err = await apply_role_ban(guild, member, "Slur detection - Strike 2 (7-Day Ban)")
            if success:
                WEEK_IN_SECONDS = 7 * 86400
                moderation.schedule_unban(guild.id, member.id, WEEK_IN_SECONDS)
                historical_bans.add(f"{member.name} ({member.id})")
                await target_channel.send(
                    f"🚨 {boi_ping} **AUTOMATIC 7-DAY BAN (Strike 2/3)** 🚨\n"
                    f"User {member.mention} (`{member.id}`) was restricted for 7 days."
                )
        elif action == "permban":
            success, err = await apply_role_ban(guild, member, "Slur detection - Strike 3 (Permanent Ban)")
            if success:
                moderation.cancel_pending_unban(guild.id, member.id)
                historical_bans.add(f"{member.name} ({member.id})")
                await target_channel.send(
                    f"🚨 {boi_ping} **AUTOMATIC PERMANENT BAN (Strike 3/3)** 🚨\n"
                    f"User {member.mention} (`{member.id}`) was permanently restricted."
                )
        return

    await bot.process_commands(message)


# --- ERROR HANDLING ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ **Missing Argument:** You forgot to mention a member! Example: `{ctx.prefix}{ctx.command.name} @member`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found. Please make sure you tag a valid user in this server.")
    else:
        print(f"Unhandled Command Error: {error}")


# --- PERSISTENT UNBAN PROCESSOR ---
@tasks.loop(seconds=10)
async def check_ban_expirations():
    due_unbans = moderation.pop_due_unbans()
    
    for item in due_unbans:
        guild_id = item["guild_id"]
        user_id = item["user_id"]
        
        guild = bot.get_guild(guild_id)
        if guild:
            member = guild.get_member(user_id)
            if member:
                banned_role = discord.utils.get(guild.roles, name="Banned")
                if banned_role and banned_role in member.roles:
                    try:
                        await member.remove_roles(banned_role, reason="Scheduled ban expired")
                        target_channel = guild.get_channel(TARGET_CHANNEL_ID)
                        if target_channel:
                            await target_channel.send(f"✅ {member.mention}'s temporary restriction has expired!")
                    except discord.Forbidden:
                        pass


@check_ban_expirations.before_loop
async def before_check_bans():
    await bot.wait_until_ready()


# --- COMMANDS ---
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_cmd(ctx, member: discord.Member, duration_str: str = "perm", *, reason: str = "Unspecified Violation"):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

    seconds = parse_duration(duration_str)
    success, err = await apply_role_ban(ctx.guild, member, reason)
    if not success:
        return await ctx.send(f"❌ Failed to ban {member.mention}: {err}")

    historical_bans.add(f"{member.name} ({member.id})")
    target_channel = ctx.guild.get_channel(TARGET_CHANNEL_ID) or ctx.channel

    if seconds:
        moderation.schedule_unban(ctx.guild.id, member.id, seconds)
        await target_channel.send(f"⛔ {member.mention} has been restricted for **{duration_str}**. Reason: **{reason}**")
    else:
        moderation.cancel_pending_unban(ctx.guild.id, member.id)
        await target_channel.send(f"⛔ {member.mention} has been permanently restricted. Reason: **{reason}**")


@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban_user(ctx, member: discord.Member):
    moderation.cancel_pending_unban(ctx.guild.id, member.id)
    moderation.reset_offender(ctx.guild.id, member.id)

    target_channel = ctx.guild.get_channel(TARGET_CHANNEL_ID) or ctx.channel
    banned_role = discord.utils.get(ctx.guild.roles, name="Banned")

    if banned_role and banned_role in member.roles:
        try:
            await member.remove_roles(banned_role, reason="Unbanned by admin command")
            await target_channel.send(f"✅ Successfully unbanned {member.mention}, cleared strikes, and removed `@Banned`!")
        except discord.Forbidden:
            await ctx.send("❌ Permission denied while removing the Banned role.")
    else:
        await ctx.send(f"{member.mention} does not have the **Banned** role.")


@bot.command(name="appeal")
@commands.has_permissions(administrator=True)
async def prompt_appeal(ctx, member: discord.Member):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

    embed = discord.Embed(
        title="📋 Ban Appeal Form",
        description=(
            f"Hello {member.mention},\n\n"
            "An administrator has opened an appeal form for you. Please select your choices in the dropdown options below "
            "and click **Submit Appeal** to open your private appeal thread."
        ),
        color=discord.Color.blue()
    )
    
    view = AppealView(target_user=member)
    target_channel = ctx.guild.get_channel(TARGET_CHANNEL_ID) or ctx.channel
    await target_channel.send(content=member.mention, embed=embed, view=view)


@bot.command(name="commands", aliases=["help_menu"])
async def show_commands(ctx):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

    embed = discord.Embed(
        title="🤖 Bot Command List & Moderation Guide",
        description="Here is the complete list of available moderation and management commands.",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="⛔ `?ban <@member> [duration] [reason]`",
        value=(
            "Restricts a member by removing their roles and giving them `@Banned`.\n"
            "• **Duration Examples:** `10s`, `30m`, `12h`, `1d`, or `perm` (default).\n"
            "• **Example:** `?ban @user 1d Misbehavior`"
        ),
        inline=False
    )

    embed.add_field(
        name="✅ `?unban <@member>`",
        value="Removes `@Banned`, cancels pending temp-unban timers, and resets slur strike counts.",
        inline=False
    )

    embed.add_field(
        name="📋 `?appeal <@member>` *(Admin Only)*",
        value="Spawns the interactive appeal UI form for a restricted user inside the target channel.",
        inline=False
    )

    embed.add_field(
        name="🛡️ Automatic Security Systems",
        value=(
            "• **Slur Escalation:** Strike 1 = Warning, Strike 2 = 7-Day Ban, Strike 3 = Permanent Ban.\n"
            "• **Ban Evasion:** Re-applies `@Banned` on rejoin, adds a **+1 day penalty**, and alerts `@boi27vr`."
        ),
        inline=False
    )

    embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

    target_channel = ctx.guild.get_channel(TARGET_CHANNEL_ID) or ctx.channel
    await target_channel.send(embed=embed)


# RUN THE BOT
bot.run(os.getenv("DISCORD_TOKEN"))