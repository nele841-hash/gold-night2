import discord
from discord.ext import commands
import time
import random
import os
from pymongo import MongoClient


EMOJIS = {
    "pistol": "<:1136_gun:1497137080919130112>",
    "knife": "<:1575knifescream:1497137058467024937>",
    "zastita": "<:714625rolemodyellow:1497137037474660372>"
}


intents = discord.Intents.default()
intents.message_content = True
intents.members = True  

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

#-----------------------kazino only-----------------
KAZINO_CHANNEL_ID = 1500745787716403280

def kazino_only():
    async def predicate(ctx):
        return ctx.channel.id == KAZINO_CHANNEL_ID
    return commands.check(predicate)
# ---------------- MONGO ----------------
client = MongoClient(os.getenv("MONGO_URL"))
db = client["discordbot"]
users = db["users"]

# ---------------- SHOP ITEMS ----------------
shop_items = {
    "pistol": 5000,
    "knife": 1000,
    "zastita": 10000
}

# ---------------- USER INIT ----------------
def get_user(user_id):
    user = users.find_one({"_id": user_id})

    if not user:
        users.insert_one({
            "_id": user_id,
            "cash": 100,
            "bank": 0,
            "dirty": 0,
            "inventory": [],
            "business": None,
            "last_pay": 0
        })
        user = users.find_one({"_id": user_id})

    return user
@bot.event
async def on_ready():
    print(f"✅ Bot je online kao {bot.user}")
    print("🚂 Railway deployment active")

#--------------welcome---------------------
@bot.event
async def on_member_join(member):
    channel_id = 1483475608003678278  # welcome kanal
    rules_channel_id = 1483475314272112784
    roles_channel_id = 1483475963684720751

    channel = bot.get_channel(channel_id)
    if not channel:
        return

    member_count = member.guild.member_count

    embed = discord.Embed(
        description=(
            f"**・Dobrodošao {member.mention}**\n\n"
            f"・Pročitaj pravila u <#{rules_channel_id}>\n"
            f"・Izaberi role u <#{roles_channel_id}>\n\n"
            f"**・Server trenutno broji `{member_count}` članova**"
        ),
        color=discord.Color.gold()
    )

    embed.set_author(
        name="GOLD NIGHT",
        icon_url=member.guild.icon.url if member.guild.icon else None
    )

    embed.set_thumbnail(
        url=member.avatar.url if member.avatar else member.default_avatar.url
    )

    await channel.send(embed=embed)
# ---------------- PRIJAVA ----------------
@bot.command()
@kazino_only()
async def prijava(ctx):
    user_id = str(ctx.author.id)

    existing = users.find_one({"_id": user_id})

    if existing:
        return await ctx.reply("❌ Već imaš račun!", mention_author=False)

    users.insert_one({
        "_id": user_id,
        "cash": 0,
        "bank": 10000,
        "dirty": 0,
        "inventory": [],
        "business": None,
        "last_pay": 0
    })

    await ctx.reply(f"✅ {ctx.author.mention} tvoj račun je uspješno kreiran!", mention_author=False)
#---------radi-------------------------
@bot.command()
@kazino_only()
async def radi(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    now = int(time.time())

    last_work = user.get("work_cd", 0)

    if now - last_work < 3600:
        left = 3600 - (now - last_work)
        minutes = left // 60
        seconds = left % 60

        embed = discord.Embed(
            title="Posao",
            description=f"Moraš čekati **{minutes}m {seconds}s** prije ponovnog rada.",
            color=discord.Color.orange()
        )

        return await ctx.reply(embed=embed, mention_author=False)

    
    earnings = random.randint(200, 600)

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": earnings},
            "$set": {"work_cd": now}
        }
    )

    updated_user = users.find_one({"_id": user_id})

    embed = discord.Embed(
        title="💼 Posao završen",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="💰 Zarada",
        value=f"```{earnings:,}".replace(",", ".") + "€```",
        inline=False
    )

    embed.add_field(
        name="💵 Novo stanje",
        value=f"```{updated_user['cash']:,}".replace(",", ".") + "€```",
        inline=False
    )

    await ctx.reply(embed=embed, mention_author=False)
# ---------------- BANKA ----------------
@bot.command()
@kazino_only()
async def banka(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply(
            "❌ Moraš prvo otvoriti račun sa `!prijava` da bi koristio banku!",
            mention_author=False
        )

    def format_money(x):
        return f"{x:,}".replace(",", ".") + "€"

    cash = user.get("cash", 0)
    bank_money = user.get("bank", 0)
    dirty = user.get("dirty", 0)

    embed = discord.Embed(
        title="VAŠ RAČUN",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="👤 Korisnik",
        value=f"`{ctx.author.name}`",
        inline=False
    )

    embed.add_field(
        name="💵 Novčanik",
        value=f"```{format_money(cash)}```",
        inline=True
    )

    embed.add_field(
        name="🏦 Banka",
        value=f"```{format_money(bank_money)}```",
        inline=True
    )

    embed.add_field(
        name="🕵️ Prljav novac",
        value=f"```{format_money(dirty)}```",
        inline=True
    )

    # 📦 INVENTORY
    items = user.get("inventory", [])

    counts = {"knife": 0, "pistol": 0, "zastita": 0}

    for i in items:
        if i in counts:
            counts[i] += 1

    inv_text = (
        f"🔪 Nož: x{counts['knife']}\n"
        f"🔫 Pištolj: x{counts['pistol']}\n"
        f"🛡️ Zaštita: x{counts['zastita']}"
    )

    # 🏢 BIZNIS
    biznis = user.get("business")

    biz_names = {
        "diler": "👑 Diler",
        "klanicakarić": "🥩 Klaonica Karić",
        "kiosk": "🏪 Kiosk",
        "restoran": "🍔 Restoran",
        "autoservis": "🏭 Auto Servis",
        "trafika": "🚬 Trafika"
    }

    biz_text = f"`{biz_names.get(biznis, 'Nemaš biznis')}`" if biznis else "`Nemaš biznis`"

    # 📊 2 KOLONE (ISTI RED)
    embed.add_field(
        name="📦 Inventory",
        value=inv_text,
        inline=True
    )

    embed.add_field(
        name="🏢 Biznis",
        value=biz_text,
        inline=True
    )

    await ctx.reply(embed=embed)
# ---------------- PODIGNI ----------------
@bot.command()
@kazino_only()
async def podigni(ctx, amount: int):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    if amount < 1:
        return await ctx.reply("❌ Minimalan iznos je 1€", mention_author=False)

    bank = user.get("bank", 0)

    if bank < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca u banci!", mention_author=False)

    # 💣 HARD EKONOMIJA → 3% fee
    fee = int(amount * 0.03)
    final_amount = amount - fee

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {
                "bank": -amount,
                "cash": final_amount
            }
        }
    )

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(title="Transakcija", color=discord.Color.red())

    embed.add_field(
        name="💸 Podignuto",
        value=f"```{final_amount:,}".replace(",", ".") + "€```",
        inline=True
    )

    embed.add_field(
        name="💵 Novčanik",
        value=f"```{updated.get('cash', 0):,}".replace(",", ".") + "€```",
        inline=True
    )

    embed.add_field(
        name="💼 Naknada",
        value=f"```-{fee:,}".replace(",", ".") + "€```",
        inline=False
    )

    await ctx.reply(embed=embed, mention_author=False)
# ---------------- CRIME ----------------
@bot.command()
@kazino_only()
async def crime(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo uraditi !prijava", mention_author=False)

    now = int(time.time())

    last_crime = user.get("crime_cd", 0)

    # 24h cooldown
    if now - last_crime < 86400:
        left = 86400 - (now - last_crime)
        hours = left // 3600
        minutes = (left % 3600) // 60

        embed = discord.Embed(
            title="Kriminal",
            description=f"Moraš čekati **{hours}h {minutes}m**",
            color=discord.Color.orange()
        )
        return await ctx.reply(embed=embed, mention_author=False)

    inventory = user.get("inventory", [])

    # ❌ mora imati pištolj
    if "pistol" not in inventory:
        return await ctx.reply("❌ Treba ti pištolj za crime!", mention_author=False)

    # 💣 HARD: 50% šansa fail
    success = random.random() < 0.5

    # uvijek gubi pištolj
    inventory.remove("pistol")

    if success:
        # 💰 manja zarada nego prije
        earnings = random.randint(8000, 20000)

        users.update_one(
            {"_id": user_id},
            {
                "$inc": {"dirty": earnings},
                "$set": {
                    "inventory": inventory,
                    "crime_cd": now
                }
            }
        )

        updated = users.find_one({"_id": user_id})

        embed = discord.Embed(
            title="💀 Kriminal uspješan",
            color=discord.Color.dark_red()
        )

        embed.add_field(
            name="🕵️ Prljav novac",
            value=f"```+{earnings:,}".replace(",", ".") + "€```",
            inline=False
        )

        embed.add_field(
            name="🧾 Ukupno",
            value=f"```{updated.get('dirty', 0):,}".replace(",", ".") + "€```",
            inline=False
        )

        embed.add_field(
            name="🔫 Status",
            value="Izgubio si pištolj",
            inline=False
        )

    else:
        # ❌ FAIL → kazna
        penalty = random.randint(3000, 8000)

        users.update_one(
            {"_id": user_id},
            {
                "$inc": {"cash": -penalty},
                "$set": {
                    "inventory": inventory,
                    "crime_cd": now
                }
            }
        )

        updated = users.find_one({"_id": user_id})

        embed = discord.Embed(
            title="🚨 Kriminal propao",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Kazna",
            value=f"```-{penalty:,}".replace(",", ".") + "€```",
            inline=False
        )

        embed.add_field(
            name="💵 Novčanik",
            value=f"```{updated.get('cash', 0):,}".replace(",", ".") + "€```",
            inline=False
        )

        embed.add_field(
            name="🔫 Status",
            value="Policija te uhvatila i izgubio si pištolj",
            inline=False
        )

    await ctx.reply(embed=embed, mention_author=False)

#---------------pranjepara-------------------------------
@bot.command()
@kazino_only()
async def operipare(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    dirty = user.get("dirty", 0)

    if dirty <= 0:
        return await ctx.reply("❌ Nemaš prljavog novca!", mention_author=False)

    # 💣 HARD EKONOMIJA → veća taksa + šansa za gubitak
    tax = int(dirty * 0.25)  # 25% tax
    cleaned = dirty - tax

    # 🎲 20% šansa da izgubiš dio novca
    lose = random.random() < 0.2
    lost_amount = 0

    if lose:
        lost_amount = int(cleaned * 0.30)  # izgubi 30% od ostatka
        cleaned -= lost_amount

    users.update_one(
        {"_id": user_id},
        {
            "$set": {"dirty": 0},
            "$inc": {"cash": cleaned}
        }
    )

    embed = discord.Embed(
        title="PRANJE PARA",
        color=discord.Color.green() if not lose else discord.Color.red()
    )

    embed.add_field(
        name="Prljav novac:",
        value=f"```{dirty:,}".replace(",", ".") + "€```",
        inline=False
    )

    embed.add_field(
        name="Oprano:",
        value=f"```{cleaned:,}".replace(",", ".") + "€```",
        inline=False
    )

    embed.add_field(
        name="Taksa (25%):",
        value=f"```{tax:,}".replace(",", ".") + "€```",
        inline=False
    )

    if lose:
        embed.add_field(
            name="⚠️ Gubitak",
            value=f"```-{lost_amount:,}".replace(",", ".") + "€```",
            inline=False
        )

    await ctx.reply(embed=embed, mention_author=False)

#-----------------daily--------------------
@bot.command()
@kazino_only()
async def daily(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo uraditi !prijava", mention_author=False)

    now = int(time.time())

    last_daily = user.get("daily_cd", 0)

    # 24h cooldown
    if now - last_daily < 86400:
        left = 86400 - (now - last_daily)
        hours = left // 3600
        minutes = (left % 3600) // 60

        embed = discord.Embed(
            title="DAILY",
            description=f"⏳ Moraš čekati **{hours}h {minutes}m**",
            color=discord.Color.orange()
        )

        return await ctx.reply(embed=embed, mention_author=False)

    # 💣 HARD EKONOMIJA
    reward = random.randint(300, 1200)

    # 🎲 15% šansa da dobiješ bonus
    bonus = 0
    if random.random() < 0.15:
        bonus = random.randint(500, 1500)
        reward += bonus

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": reward},
            "$set": {"daily_cd": now}
        }
    )

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(
        title="DAILY",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Dobio si:",
        value=f"```{reward:,}".replace(",", ".") + "€```",
        inline=False
    )

    if bonus > 0:
        embed.add_field(
            name="🎁 Bonus",
            value=f"```+{bonus:,}".replace(",", ".") + "€```",
            inline=False
        )

    embed.add_field(
        name="Novo stanje:",
        value=f"```{updated.get('cash', 0):,}".replace(",", ".") + "€```",
        inline=False
    )

    await ctx.reply(embed=embed, mention_author=False)

#-------------------------KREDIT--------------------------
@bot.command()
@kazino_only()
async def kredit(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    now = int(time.time())

    last_credit = user.get("credit_cd", 0)

    # 3 dana cooldown
    if now - last_credit < 259200:
        left = 259200 - (now - last_credit)
        hours = left // 3600
        minutes = (left % 3600) // 60

        embed = discord.Embed(
            title="KREDIT",
            description=f"⏳ Moraš čekati **{hours}h {minutes}m**",
            color=discord.Color.orange()
        )
        return await ctx.reply(embed=embed, mention_author=False)

    # 💣 HARD EKONOMIJA
    amount = 5000  # manji kredit
    interest = int(amount * 0.30)  # 30% kamata
    total_debt = amount + interest

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": amount},
            "$set": {
                "credit_cd": now,
                "debt": user.get("debt", 0) + total_debt
            }
        }
    )

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(
        title="KREDIT",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Dobio si:",
        value=f"```{amount:,}".replace(",", ".") + "€```",
        inline=False
    )

    embed.add_field(
        name="Kamata (30%)",
        value=f"```{interest:,}".replace(",", ".") + "€```",
        inline=False
    )

    embed.add_field(
        name="Ukupan dug",
        value=f"```{updated.get('debt', 0):,}".replace(",", ".") + "€```",
        inline=False
    )

    embed.add_field(
        name="Novo stanje:",
        value=f"```{updated.get('cash', 0):,}".replace(",", ".") + "€```",
        inline=False
    )

    await ctx.reply(embed=embed, mention_author=False)

#-------------------vrati dug-------------------------
@bot.command()
@kazino_only()
async def vratidug(ctx, amount: int):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    debt = user.get("debt", 0)
    cash = user.get("cash", 0)

    if debt <= 0:
        return await ctx.reply("❌ Nemaš nikakav dug!", mention_author=False)

    if amount < 1:
        return await ctx.reply("❌ Minimalan iznos je 1€", mention_author=False)

    if cash < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca u novčaniku!", mention_author=False)

    if amount > debt:
        amount = debt  # ne možeš platiti više nego što duguješ

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {
                "cash": -amount,
                "debt": -amount
            }
        }
    )

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(
        title="💳 Otplata duga",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Plaćeno",
        value=f"```{amount:,}".replace(",", ".") + "€```",
        inline=False
    )

    embed.add_field(
        name="Preostali dug",
        value=f"```{updated.get('debt', 0):,}".replace(",", ".") + "€```",
        inline=False
    )

    embed.add_field(
        name="Novčanik",
        value=f"```{updated.get('cash', 0):,}".replace(",", ".") + "€```",
        inline=False
    )

    await ctx.reply(embed=embed, mention_author=False)
#-------------PLJACKAJ-------------
@bot.command()
@kazino_only()
async def pljackaj(ctx, member: discord.Member):
    user_id = str(ctx.author.id)
    target_id = str(member.id)

    user = users.find_one({"_id": user_id})
    target = users.find_one({"_id": target_id})

    if not user:
        return ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    if not target:
        return ctx.reply("❌ Taj korisnik nema račun!", mention_author=False)

    if user_id == target_id:
        return ctx.reply("❌ Ne možeš sebe opljačkati!", mention_author=False)

    now = int(time.time())

    if now - user.get("rob_cd", 0) < 600:
        left = 600 - (now - user.get("rob_cd", 0))
        return ctx.reply(f"⏳ Čekaj još {left//60}m {left%60}s", mention_author=False)

    attacker_inv = user.get("inventory", [])
    target_inv = target.get("inventory", [])

    if "knife" not in attacker_inv:
        return ctx.reply("❌ Treba ti nož za pljačku!", mention_author=False)

    # 🔪 uvijek gubi nož
    attacker_inv.remove("knife")

    # 🛡️ zaštita
    if "zastita" in target_inv:
        target_inv.remove("zastita")

        users.update_one(
            {"_id": user_id},
            {"$set": {"inventory": attacker_inv, "rob_cd": now}}
        )

        users.update_one(
            {"_id": target_id},
            {"$set": {"inventory": target_inv}}
        )

        embed = discord.Embed(
            title="🛡️ ZAŠTITA AKTIVIRANA",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="PLJAČKAŠ",
            value=f"```{ctx.author}```",
            inline=True
        )

        embed.add_field(
            name="ŽRTVA",
            value=f"```{member}```",
            inline=True
        )

        embed.add_field(
            name="ISHOD",
            value="```Zaštita je blokirala pljačku```",
            inline=False
        )

        return ctx.reply(embed=embed, mention_author=False)

    # 💰 UVIJEK USPJEH (NO FAIL)
    stolen = int(target.get("cash", 0) * 0.25)

    users.update_one(
        {"_id": target_id},
        {"$inc": {"cash": -stolen}}
    )

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": stolen},
            "$set": {"inventory": attacker_inv, "rob_cd": now}
        }
    )

    embed = discord.Embed(
        title="💰 PLJAČKA USPJEŠNA",
        color=discord.Color.green()
    )

    embed.add_field(
        name="PLJAČKAŠ",
        value=f"```{ctx.author}```",
        inline=True
    )

    embed.add_field(
        name="ŽRTVA",
        value=f"```{member}```",
        inline=True
    )

    embed.add_field(
        name="UKRADENO",
        value=f"```{stolen:,}".replace(",", ".") + "€```",
        inline=False
    )

    ctx.reply(embed=embed, mention_author=False)
#-----------------SET-----------------------
@bot.command()
@kazino_only()
async def set(ctx, member: discord.Member, amount: int):
    OWNER_IDS = [
        1423978463290982470,
        633262690139242507,  # zamijeni drugim ID-om
        910227902166102068   # zamijeni trećim ID-om
    ]

    if ctx.author.id not in OWNER_IDS:
        return await ctx.reply("❌ Nemaš dozvolu!", mention_author=False)

    user_id = str(member.id)

    users.update_one(
        {"_id": user_id},
        {"$set": {"cash": amount}},
        upsert=True
    )

    embed = discord.Embed(
        title="💰 SET NOVCA",
        color=discord.Color.gold()
    )

    embed.add_field(name="👤 Korisnik", value=f"{member.mention}", inline=False)
    embed.add_field(name="💸 Novo stanje", value=f"```{amount:,}$```", inline=False)

    await ctx.reply(embed=embed, mention_author=False)

#-----------------SLOT-------------------
@bot.command()
@kazino_only()
async def slot(ctx, amount: int):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    if amount < 1:
        return await ctx.reply("❌ Minimalan ulog je 1€", mention_author=False)

    cash = user.get("cash", 0)

    if cash < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca!", mention_author=False)

    # 🚫 anti-spam cooldown
    now = int(time.time())
    last_slot = user.get("slot_cd", 0)

    if now - last_slot < 5:
        return await ctx.reply("⏳ Sačekaj malo prije ponovnog igranja slotova!", mention_author=False)

    users.update_one(
        {"_id": user_id},
        {"$set": {"slot_cd": now}}
    )

    symbols = ["🍒", "🍋", "🍇", "💎", "7️⃣"]

    # 🎰 START MESSAGE
    embed = discord.Embed(
        title="🎰 SLOT",
        description="⏳ Sačekajte 3 sekunde...",
        color=discord.Color.orange()
    )

    msg = await ctx.reply(embed=embed)

    await asyncio.sleep(3)

    r1 = random.choice(symbols)
    r2 = random.choice(symbols)
    r3 = random.choice(symbols)

    result = f"{r1} | {r2} | {r3}"

    win = 0

    # 💣 WIN LOGIKA
    if r1 == r2 == r3:
        if r1 == "💎":
            win = amount * 7
        else:
            win = amount * 2

        users.update_one(
            {"_id": user_id},
            {"$inc": {"cash": win}}
        )

        title = "🎉 Dobitak"
        color = discord.Color.green()
        change_text = f"+{win:,}".replace(",", ".") + "€"

    else:
        users.update_one(
            {"_id": user_id},
            {"$inc": {"cash": -amount}}
        )

        title = "💀 Gubitak"
        color = discord.Color.red()
        change_text = f"-{amount:,}".replace(",", ".") + "€"

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(
        title=title,
        color=color
    )

    embed.add_field(
        name="🎰 Slot",
        value=f"```{result}```",
        inline=False
    )

    embed.add_field(
        name="💸 Promjena",
        value=f"```{change_text}```",
        inline=False
    )

    embed.add_field(
        name="💰 Stanje",
        value=f"```{updated.get('cash', 0):,}".replace(",", ".") + "€```",
        inline=False
    )

    await msg.edit(embed=embed)
#-----------------RULET---------------
import asyncio
import random
import time

@bot.command()
@kazino_only()
async def rulet(ctx, choice: str, amount: int):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    if amount < 1:
        return await ctx.reply("❌ Minimalan ulog je 1$", mention_author=False)

    cash = user.get("cash", 0)

    if cash < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca!", mention_author=False)

    # 🚫 anti-spam cooldown
    now = int(time.time())
    last = user.get("rulet_cd", 0)

    if now - last < 5:
        return await ctx.reply("⏳ Sačekaj malo prije ponovnog ruleta!", mention_author=False)

    users.update_one(
        {"_id": user_id},
        {"$set": {"rulet_cd": now}}
    )

    # 🎰 START
    embed = discord.Embed(
        title="🎰 RULET SE VRTI...",
        description="⏳ Sačekajte 5 sekundi...",
        color=discord.Color.orange()
    )

    msg = await ctx.reply(embed=embed)

    await asyncio.sleep(5)

    # 🎲 BROJ
    number = random.randint(0, 36)

    red_numbers = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    black_numbers = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

    if number == 0:
        color = "green"
    elif number in red_numbers:
        color = "red"
    else:
        color = "black"

    color_map = {
        "red": "🔴",
        "black": "⚫️",
        "green": "🟢"
    }

    choice = choice.lower()
    win = 0

    # 🎯 BROJ = 25x
    if choice.isdigit():
        if int(choice) == number:
            win = amount * 25
        else:
            win = -amount

    else:
        # 🎨 BOJA
        if choice == color:
            if color == "green":
                win = amount * 36
            else:
                win = amount * 2
        else:
            win = -amount

    # 💾 CASH UPDATE
    new_cash = cash + win

    users.update_one(
        {"_id": user_id},
        {"$set": {"cash": new_cash}}
    )

    # 🎯 RESULT
    result_text = f"```{number} {color_map[color]}```"

    embed = discord.Embed(
        title="🎯 RULET REZULTAT",
        description=result_text,
        color=discord.Color.green() if win > 0 else discord.Color.red()
    )

    if win > 0:
        embed.add_field(name="Dobitak", value=f"```+{win:,}$```", inline=False)
    else:
        embed.add_field(name="Gubitak", value=f"```{win:,}$```", inline=False)

    embed.add_field(name="Stanje", value=f"```{new_cash:,}$```", inline=False)

    await msg.edit(embed=embed)
#-------------HELP-----------------
@bot.command()
@kazino_only()
async def help(ctx):
    embed = discord.Embed(
        title="💰 CASINO KOMANDE",
        description="Lista svih dostupnih komandi",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="💼 Osnovne komande",
        value=(
            "`!prijava` - otvara račun\n"
            "`!banka` - vidi stanje novca i inventory\n"
            "`!pay @user <iznos>` - šalje novac igraču\n"
            "`!shop` - lista itema za kupovinu\n"
            "`!kupi <item>` - kupi oružje / zaštitu\n"
            "`!daily` - dnevna nagrada\n"
        ),
        inline=False
    )

    embed.add_field(
        name="💀 Risk / Crime",
        value=(
            "`!pljackaj @user` - pljačka igrača\n"
            "`!crime` - kriminal (treba pištolj)\n"
            "`!operipare` - pranje prljavog novca\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🎰 Casino",
        value=(
            "`!slot <iznos>` - slot mašina\n"
            "`!rulet <color/broj> <iznos>` - rulet igra\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🏢 Biznis sistem",
        value=(
            "`!biznisi` - lista biznisa\n"
            "`!kupibiz <ime>` - kupi biznis\n"
            "`!uzmipare` - uzmi pare iz biznisa\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🏆 Statistika",
        value="`!top10` - najbogatiji igrači",
        inline=False
    )

    await ctx.reply(embed=embed)
#----------------SHOP----------------
@bot.command()
@kazino_only()
async def shop(ctx):
    embed = discord.Embed(
        title="🛒 SHOP",
        description="Dostupni itemi:",
        color=discord.Color.gold()
    )

    embed.add_field(
        name=f"{EMOJIS['pistol']} Pištolj",
        value=f"`{shop_items['pistol']:,}$`",
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['knife']} Nož",
        value=f"`{shop_items['knife']:,}$`",
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['zastita']} Zaštita",
        value=f"`{shop_items['zastita']:,}$`",
        inline=False
    )

    embed.set_footer(text="Kupovina: !kupi <pistolj/noz/zastita>")

    await ctx.reply(embed=embed)
#------------------BUY-----------------
@bot.command()
@kazino_only()
async def kupi(ctx, item: str):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply(
            f"❌ {ctx.author.mention} moraš prvo otvoriti račun sa `!prijava`",
            mention_author=False
        )

    item = item.lower()

    aliases = {
        "pistol": "pistol",
        "pištolj": "pistol",
        "pistolj": "pistol",

        "knife": "knife",
        "noz": "knife",
        "nož": "knife",

        "zastita": "zastita",
        "zaštita": "zastita"
    }

    names = {
        "pistol": "Pištolj",
        "knife": "Nož",
        "zastita": "Zaštita"
    }

    if item not in aliases:
        return await ctx.reply("❌ Item ne postoji! Koristi: pistolj/noz/zastita")

    item = aliases[item]

    if item not in shop_items:
        return await ctx.reply("❌ Taj item nije u shopu!")

    price = shop_items[item]

    cash = user.get("cash", 0)

    if cash < price:
        return await ctx.reply("❌ Nemaš dovoljno novca!")

    inventory = user.get("inventory", [])

    inventory.append(item)

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": -price},
            "$set": {"inventory": inventory}
        }
    )

    embed = discord.Embed(
        title="🛒 KUPOVINA USPJEŠNA",
        color=discord.Color.green()
    )

    embed.add_field(name="User", value=f"{ctx.author.mention}", inline=False)
    embed.add_field(name="Item", value=f"`{names[item]}`", inline=False)
    embed.add_field(name="Cijena", value=f"`{price:,}$`", inline=False)
    embed.add_field(name="Status", value="`Kupljeno ✔️`", inline=False)

    await ctx.reply(embed=embed)
# ---------------- BIZNISI ----------------
@bot.command()
@kazino_only()
async def biznisi(ctx):
    embed = discord.Embed(
        title="🏢 DOSTUPNI BIZNISI",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="👑 Diler",
        value="💰 Cijena: `2.000.000€`\n💸 Zarada: `100.000€ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🥩 Klaonica Karić",
        value="💰 Cijena: `2.000.000€`\n💸 Zarada: `100.000€ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🏪 Kiosk",
        value="💰 Cijena: `250.000€`\n💸 Zarada: `35.000€ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🍔 Restoran",
        value="💰 Cijena: `400.000€`\n💸 Zarada: `60.000€ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🏭 Auto Servis",
        value="💰 Cijena: `600.000€`\n💸 Zarada: `80.000€ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🚬 Trafika",
        value="💰 Cijena: `150.000€`\n💸 Zarada: `25.000€ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🛒 Kupovina",
        value="Koristi: `!kupibiz <ime>`",
        inline=False
    )

    await ctx.reply(embed=embed)

# ---------------- KUPI BIZNIS ----------------
@bot.command()
@kazino_only()
async def kupibiz(ctx, *, biznis: str):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`")

    biznis = biznis.lower().replace(" ", "")

    # 🏢 BIZNISI + CIJENE (TVOJI)
    biz = {
        "diler": 2000000,
        "klanicakarić": 2000000,
        "kiosk": 250000,
        "restoran": 400000,
        "autoservis": 600000,
        "trafika": 150000
    }

    names = {
        "diler": "👑 Diler",
        "klanicakarić": "🥩 Klaonica Karić",
        "kiosk": "🏪 Kiosk",
        "restoran": "🍔 Restoran",
        "autoservis": "🏭 Auto Servis",
        "trafika": "🚬 Trafika"
    }

    if biznis not in biz:
        return await ctx.reply("❌ Taj biznis ne postoji! Koristi !biznisi")

    user_cash = user.get("cash", 0)

    if user_cash < biz[biznis]:
        return await ctx.reply("❌ Nemaš dovoljno novca!")

    # 👑 UNIQUE BIZNISI (SAMO 1 VLASNIK NA SERVERU)
    unique_biz = ["diler", "klanicakarić"]

    if biznis in unique_biz:
        existing = users.find_one({"business": biznis})
        if existing:
            return await ctx.reply("❌ Ovaj biznis već ima vlasnika!")

    # ❌ već ima biznis
    if user.get("business"):
        return await ctx.reply("❌ Već posjeduješ biznis!")

    # 💰 KUPNJA
    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": -biz[biznis]},
            "$set": {
                "business": biznis,
                "business_last_pay": 0
            }
        }
    )

    embed = discord.Embed(
        title="🏢 KUPOVINA USPJEŠNA",
        color=discord.Color.green()
    )

    embed.add_field(
        name="📌 Biznis",
        value=f"`{names[biznis]}`",
        inline=False
    )

    embed.add_field(
        name="💰 Status",
        value="Kupljeno ✔️",
        inline=False
    )

    await ctx.reply(embed=embed)
# ---------------- UZMI PARE ----------------
@bot.command()
@kazino_only()
async def uzmipare(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`")

    biznis = user.get("business")

    if not biznis:
        return await ctx.reply("❌ Nemaš biznis!")

    now = int(time.time())
    last_pay = user.get("business_last_pay", 0)

    # 🕒 24h cooldown
    if now - last_pay < 86400:
        left = 86400 - (now - last_pay)
        hours = left // 3600
        minutes = (left % 3600) // 60

        embed = discord.Embed(
            title="🏢 BIZNIS",
            description=f"⏳ Sačekaj **{hours}h {minutes}m** za sljedeću isplatu.",
            color=discord.Color.orange()
        )

        return await ctx.reply(embed=embed)

    # 💰 ZARADE
    earnings_map = {
        "diler": 100000,
        "klanicakarić": 100000,
        "kladionica": 100000,
        "klaonica": 75000,
        "kiosk": 30000
    }

    names = {
        "diler": "👑 Diler",
        "klanicakarić": "🥩 Klaonica Karić",
        "kladionica": "🎰 Kladionica",
        "klaonica": "🥩 Klaonica",
        "kiosk": "🏪 Kiosk"
    }

    earnings = earnings_map.get(biznis, 0)

    if earnings <= 0:
        return await ctx.reply("❌ Ovaj biznis nema definisanu zaradu!")

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": earnings},
            "$set": {"business_last_pay": now}
        }
    )

    embed = discord.Embed(
        title="💰 DNEVNA ZARADA",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="🏢 Biznis",
        value=f"{names.get(biznis, biznis)}",
        inline=False
    )

    embed.add_field(
        name="💸 Zarada",
        value=f"```+{earnings:,}$```",
        inline=False
    )

    await ctx.reply(embed=embed)
# ---------------- PAY ----------------
@bot.command()
@kazino_only()
async def pay(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)

    sender = users.find_one({"_id": sender_id})
    receiver = users.find_one({"_id": receiver_id})

    if not sender:
        return await ctx.reply(f"❌ {ctx.author.mention} moraš prvo otvoriti račun sa `!prijava`")

    if not receiver:
        return await ctx.reply("❌ Taj korisnik nema račun!")

    if amount <= 0:
        return await ctx.reply("❌ Unesi validan iznos!")

    sender_cash = sender.get("cash", 0)

    if sender_cash < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca!")

    # 💸 TAX 10%
    tax = int(amount * 0.10)
    receive_amount = amount - tax

    # 💾 UPDATE
    users.update_one(
        {"_id": sender_id},
        {"$inc": {"cash": -amount}}
    )

    users.update_one(
        {"_id": receiver_id},
        {"$inc": {"cash": receive_amount}}
    )

    # 🧼 FORMAT FUNKCIJA (tačka umjesto zareza)
    def fmt(x):
        return f"{x:,}".replace(",", ".") + "$"

    embed = discord.Embed(
        title="💸 TRANSFER NOVCA",
        color=discord.Color.green()
    )

    embed.add_field(name="📤 Pošiljaoc", value=f"{ctx.author.mention}", inline=False)
    embed.add_field(name="📥 Primalac", value=f"{member.mention}", inline=False)
    embed.add_field(name="💰 Poslano", value=f"`{fmt(amount)}`", inline=False)
    embed.add_field(name="🏦 Tax (10%)", value=f"`{fmt(tax)}`", inline=False)
    embed.add_field(name="💵 Primalac dobija", value=f"`{fmt(receive_amount)}`", inline=False)

    await ctx.reply(embed=embed)


# ---------------- TOP10 ----------------
@bot.command()
@kazino_only()
async def top10(ctx):
    all_users = users.find()

    leaderboard = []

    def fmt(x):
        return f"{x:,}".replace(",", ".") + "$"

    for u in all_users:
        user_id = u["_id"]
        cash = u.get("cash", 0)
        bank = u.get("bank", 0)

        total = cash + bank

        try:
            member = await bot.fetch_user(int(user_id))
            name = member.name
        except:
            name = "Unknown"

        leaderboard.append((name, total))

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 TOP 10 NAJBOGATIJIH",
        color=discord.Color.gold()
    )

    medals = ["🥇", "🥈", "🥉"]

    text = ""

    for i, (name, total) in enumerate(leaderboard[:10], start=1):
        medal = medals[i-1] if i <= 3 else f"#{i}"

        text += (
            f"{medal} **{name}**\n"
            f"💰 `{fmt(total)}`\n"
            f"・\n"
        )

    embed.add_field(
        name="📊 Rang lista",
        value=text or "❌ Nema podataka",
        inline=False
    )

    embed.set_footer(text="💎 Kazino leaderboard sistem")

    await ctx.reply(embed=embed)
# ---------------- RESET SVE (FULL WIPE) ----------------
@bot.command()
@kazino_only()
async def rr(ctx):
    OWNER_ID = 910227902166102068

    if ctx.author.id != OWNER_ID:
        return await ctx.reply("❌ Nemaš dozvolu!", mention_author=False)

    # 🧨 BRIŠE SVE KORISNIKE (RESET PRIJAVA)
    users.delete_many({})

    embed = discord.Embed(
        title="🔄 FULL WIPE RESET",
        description="✔️ Svi računi su obrisani!\n🔐 Sada svi moraju ponovo `!prijava`",
        color=discord.Color.red()
    )

    await ctx.reply(embed=embed)

# ---------------- AVATAR ----------------
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author

    embed = discord.Embed(
        title=f"Profilna slika od {member.name}",
        color=discord.Color.blue()
    )

    embed.set_image(url=member.display_avatar.url)

    embed.set_footer(text=f"Traženo od {ctx.author.name}")

    await ctx.reply(embed=embed)

#---------------šamar---------------
@bot.command()
async def osamari(ctx, member: discord.Member = None):

    if member is None:
        return await ctx.reply("❌ Moraš nekoga tagovati!", mention_author=False)

    gif = "https://media1.tenor.com/m/wLgfcMfKkpoAAAAC/slap-chappelle-show.gif"

    embed = discord.Embed(
        title="💢 OŠAMARIO!",
        description=f"**{ctx.author.name}** je ošamario **{member.name}** 😂",
        color=discord.Color.red()
    )

    embed.set_image(url=gif)

    await ctx.send(embed=embed)

#-----------------------s---------------
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.reply(
            "Kazino komande rade samo u <#1500745787716403280>!",
            mention_author=False
        )
# ---------------- RUN ----------------


import os

bot.run(os.getenv("DISCORD_TOKEN"))
