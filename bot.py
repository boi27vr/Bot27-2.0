import random
import discord
from discord.ext import commands

# ---------------------------------------------------------
# QUEER TERMS DICTIONARY (Simple, Natural Definitions)
# ---------------------------------------------------------
QUEER_TERMS = {
    # Core & Popular Terms
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
    "ambiamorous": "Someone who is happy and comfortable in either polyamorous or monogamous relationships.",
}

# ---------------------------------------------------------
# EMOJI CATEGORIES DICTIONARY
# ---------------------------------------------------------
EMOJI_LIBRARY = {
    "chaos": ["🔥", "💥", "🦝", "🤪", "⚡", "😈", "💣", "💀", "🚨", "🌀", "🗿", "👁️", "⚔️", "🔪"],
    "vibes": ["✨", "💫", "🌟", "🌸", "🌙", "🔮", "🍃", "🍄", "🪩", "☕", "🫧", "🌊", "🛋️", "🎧"],
    "animals": ["🐱", "🐶", "🦊", "🐻", "🐼", "🐸", "🐍", "🪿", "🦉", "🐙", "🦈", "🦔", "🦖", "🦥"],
    "food": ["🍕", "🧋", "🧃", "🍩", "🍣", "🌮", "🥞", "🍪", "🍜", "🍿", "🥐", "🧇", "🍨", "🍓"],
    "pride": ["🏳️‍🌈", "🏳️‍⚧️", "💖", "💛", "💙", "💜", "🖤", "🤍", "🤎", "❤️‍🔥", "🌈", "🦄", "👑"],
    "gaming": ["🎮", "🕹️", "🎲", "👾", "🎯", "🤖", "⚔️", "🛡️", "🏆", "🧩", "📡", "🚀"],
}

# ---------------------------------------------------------
# BOT SETUP
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


# ---------------------------------------------------------
# ?emoji COMMAND (Random or Categorized Emoji)
# ---------------------------------------------------------
@bot.command(name="emoji")
async def send_emoji(ctx, category: str = None):
    if category:
        cat_key = category.lower()
        if cat_key in EMOJI_LIBRARY:
            selected_emoji = random.choice(EMOJI_LIBRARY[cat_key])
            await ctx.send(f"{selected_emoji} *(Category: {cat_key.capitalize()})*")
        else:
            valid_cats = ", ".join(f"`{c}`" for c in EMOJI_LIBRARY.keys())
            await ctx.send(
                f"Category **'{category}'** not found!\nAvailable categories: {valid_cats}"
            )
    else:
        # Pick from all available emojis
        all_emojis = [e for group in EMOJI_LIBRARY.values() for e in group]
        await ctx.send(random.choice(all_emojis))


# ---------------------------------------------------------
# ?queer COMMAND (Random Term)
# ---------------------------------------------------------
@bot.command(name="queer")
async def queer_random(ctx):
    term, definition = random.choice(list(QUEER_TERMS.items()))
    embed = discord.Embed(
        title=f"🏳️‍🌈 Pride Term: {term.capitalize()}",
        description=definition,
        color=discord.Color.magenta(),
    )
    await ctx.send(embed=embed)


# ---------------------------------------------------------
# DYNAMIC ?queer_<term> HANDLER
# ---------------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check for ?queer_<term> custom commands
    if message.content.lower().startswith("?queer_"):
        raw_term = message.content[7:].strip().lower()

        if raw_term in QUEER_TERMS:
            embed = discord.Embed(
                title=f"🏳️‍🌈 Pride Term: {raw_term.capitalize()}",
                description=QUEER_TERMS[raw_term],
                color=discord.Color.magenta(),
            )
            await message.channel.send(embed=embed)
        else:
            available_terms = ", ".join(f"`{t}`" for t in QUEER_TERMS.keys())
            await message.channel.send(
                f"Term **'{raw_term}'** not found.\nAvailable terms: {available_terms}"
            )
        return

    # Keep all standard command processing active
    await bot.process_commands(message)