"""Discord Rules & Moderation Bot."""

import os
import re
import random
import logging
import asyncio
import discord
from dotenv import load_dotenv

from keep_alive import keep_alive
import moderation as mod
from rules import RULES
from emojis import EMOJIS

load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
PREFIX = "?"
MAX_RULE = max(RULES.keys())
MAX_MEOW = 50
MAX_EMOJI = 50
BAN_DELAY_SEC = 10
WEEK_SECONDS = 7 * 24 * 60 * 60

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("rules-bot")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

_RULE_RE = re.compile(r"^\?rule\s*(.*)$", re.IGNORECASE)
_MEOW_RE = re.compile(r"^\?meow\s*(.*)$", re.IGNORECASE)
_EMOJI_RE = re.compile(r"^\?emoji\s*(.*)$", re.IGNORECASE)
_MOD_RE = re.compile(r"^\?(warn|weekban|permban|unban)[_\s]+(.+)$", re.IGNORECASE)


async def resolve_member(guild, key):
    key = key.strip()
    m = re.match(r"<@!?(\d+)>$", key)
    if m:
        return guild.get_member(int(m.group(1)))
    if key.isdigit():
        return guild.get_member(int(key))
    key_l = key.lower()
    for mem in guild.members:
        if mem.name.lower() == key_l or mem.display_name.lower() == key_l:
            return mem
        gn = getattr(mem, "global_name", None)
        if gn and gn.lower() == key_l:
            return mem
    return None


async def apply_action(channel, guild, target, target_name, action, reason,
                       delay=BAN_DELAY_SEC):
    if action == "warn":
        await channel.send(f"⚠️ {target_name} has been **warned**. Reason: {reason}")
        return
    if action == "weekban":
        await channel.send(f"⛔ {target_name} will be **banned for 1 week** in {delay} seconds. Reason: {reason}")
        await asyncio.sleep(delay)
        try:
            await guild.ban(target, reason=reason, delete_message_days=0)
            mod.schedule_unban(guild.id, target.id, WEEK_SECONDS)
            await channel.send(f"✅ {target_name} banned for 1 week.")
        except discord.Forbidden:
            await channel.send("❌ I don't have permission to ban that user.")
        except discord.HTTPException as e:
            await channel.send(f"❌ Ban failed: {e}")
        return
    if action == "permban":
        await channel.send(f"⛔ {target_name} will be **permanently banned** in {delay} seconds. Reason: {reason}")
        await asyncio.sleep(delay)
        try:
            await guild.ban(target, reason=reason, delete_message_days=0)
            mod.cancel_pending_unban(guild.id, target.id)
            await channel.send(f"✅ {target_name} permanently banned.")
        except discord.Forbidden:
            await channel.send("❌ I don't have permission to ban that user.")
        except discord.HTTPException as e:
            await channel.send(f"❌ Ban failed: {e}")


async def handle_rule(message, tail):
    if tail == "":
        await message.channel.send(
            f"Use `?rule` followed by a number to print a rule.\n"
            f"Example: `?rule1` — prints Rule 1.\n"
            f"Valid rule numbers: **1-{MAX_RULE}**.")
        return
    if not tail.isdigit():
        await message.channel.send(f"No rule number `{tail}`. Please enter a number between 1-{MAX_RULE} after `?rule`.")
        return
    n = int(tail)
    if n not in RULES:
        await message.channel.send(f"No rule number {n}. Please enter a number between 1-{MAX_RULE} after `?rule`.")
        return
    await message.channel.send(f"**Rule {n}:** {RULES[n]}")


async def handle_meow(message, tail):
    if tail == "":
        await message.channel.send("meow :3"); return
    if not tail.isdigit():
        await message.channel.send(f"Sowwy! Please put a number 1-{MAX_MEOW} after `?meow`."); return
    n = int(tail)
    if n < 1:
        await message.channel.send("Sowwy! Min meow is 1."); return
    if n > MAX_MEOW:
        await message.channel.send(f"Sowwy! Max meow is {MAX_MEOW}..."); return
    await message.channel.send(" ".join(["meow"] * n) + " :3")


async def handle_emoji(message, tail):
    if tail == "":
        await message.channel.send(random.choice(EMOJIS)); return
    if not tail.isdigit():
        await message.channel.send(f"Please put a number 1-{MAX_EMOJI} after `?emoji`."); return
    n = int(tail)
    if n < 1:
        await message.channel.send("Min emoji is 1"); return
    if n > MAX_EMOJI:
        await message.channel.send(f"Max emoji is {MAX_EMOJI}"); return
    await message.channel.send("".join(random.choices(EMOJIS, k=n)))


async def handle_slur(message):
    if message.guild is None:
        return
    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass
    action, count = mod.next_action(message.guild.id, message.author.id)
    await apply_action(message.channel, message.guild, message.author,
                       message.author.mention, action,
                       f"Slur detected (offense #{count})")


async def handle_test(message, kind):
    if not message.guild:
        await message.channel.send("Test commands only work in a server."); return
    if not message.author.guild_permissions.manage_guild:
        await message.channel.send("You need the **Manage Server** permission to run test commands."); return
    if kind == "testunban":
        mod.reset_offender(message.guild.id, message.author.id)
        mod.cancel_pending_unban(message.guild.id, message.author.id)
        bans = [b async for b in message.guild.bans(limit=None)]
        found = next((b for b in bans if b.user.id == message.author.id), None)
        if not found:
            await message.channel.send(f"{message.author.mention} is not currently banned. (Offender count reset.)")
            return
        await message.guild.unban(found.user, reason="Test unban")
        await message.channel.send(f"✅ Unbanned {message.author.mention}.")
        return
    action = {"testwarn": "warn", "testweekban": "weekban", "testpermban": "permban"}[kind]
    await apply_action(message.channel, message.guild, message.author,
                       message.author.mention, action, f"Test command `?{kind}`")


async def handle_manual_mod(message, action, target_key):
    if not message.guild:
        await message.channel.send("Moderation commands only work in a server."); return
    if not message.author.guild_permissions.ban_members:
        await message.channel.send("You need the **Ban Members** permission to run this command."); return
    member = await resolve_member(message.guild, target_key)
    if action == "unban":
        target_id = None
        target_name = target_key
        if member:
            target_id, target_name = member.id, member.mention
        else:
            bans = [b async for b in message.guild.bans(limit=None)]
            key_l = target_key.strip().lower()
            hit = next((b for b in bans
                        if b.user.name.lower() == key_l or str(b.user.id) == key_l), None)
            if hit:
                target_id, target_name = hit.user.id, str(hit.user)
        if target_id is None:
            await message.channel.send(f"Couldn't find user `{target_key}`."); return
        try:
            await message.guild.unban(discord.Object(id=target_id),
                                       reason=f"Manual by {message.author}")
            mod.cancel_pending_unban(message.guild.id, target_id)
            mod.reset_offender(message.guild.id, target_id)
            await message.channel.send(f"✅ Unbanned {target_name}.")
        except discord.NotFound:
            await message.channel.send(f"{target_name} is not banned.")
        except discord.Forbidden:
            await message.channel.send("❌ I don't have permission to unban.")
        return
    if not member:
        await message.channel.send(f"Couldn't find user `{target_key}` in this server."); return
    await apply_action(message.channel, message.guild, member, member.mention,
                       action, f"Manual by {message.author}")


@client.event
async def on_ready():
    log.info("Logged in as %s (id=%s). Serving %d rules.",
             client.user, client.user.id, MAX_RULE)
    client.loop.create_task(_unban_worker())


async def _unban_worker():
    await client.wait_until_ready()
    while not client.is_closed():
        for entry in mod.pop_due_unbans():
            g = client.get_guild(entry["guild_id"])
            if not g:
                continue
            try:
                await g.unban(discord.Object(id=entry["user_id"]),
                              reason="1-week ban expired")
                log.info("Auto-unbanned %s in guild %s",
                         entry["user_id"], entry["guild_id"])
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                log.warning("Auto-unban failed for %s: %s", entry["user_id"], e)
        await asyncio.sleep(30)


@client.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.strip()
    if (message.guild
            and not message.author.guild_permissions.manage_messages
            and mod.contains_slur(content)):
        await handle_slur(message); return
    if not content.startswith(PREFIX):
        return
    lower = content.lower()
    if lower in ("?testwarn", "?testweekban", "?testpermban", "?testunban"):
        await handle_test(message, lower.lstrip("?")); return
    m = _MOD_RE.match(content)
    if m:
        await handle_manual_mod(message, m.group(1).lower(), m.group(2)); return
    m = _RULE_RE.match(content)
    if m:
        await handle_rule(message, m.group(1).strip()); return
    m = _MEOW_RE.match(content)
    if m:
        await handle_meow(message, m.group(1).strip()); return
    m = _EMOJI_RE.match(content)
    if m:
        await handle_emoji(message, m.group(1).strip()); return


def main():
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN is not set.")
    keep_alive()
    client.run(TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
