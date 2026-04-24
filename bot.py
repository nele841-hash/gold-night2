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

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---------------- MONGO ----------------
client = MongoClient(os.getenv("MONGO_URL"))
db = client["discordbot"]
users = db["users"]

# ---------------- SHOP ITEMS ----------------
shop_items = {
    "pistol": 15000,
    "knife": 5000,
    "zastita": 20000
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

# ---------------- PRIJAVA ----------------
@bot.command()
async def prijava(ctx):
    user_id = str(ctx.author.id)

    existing = users.find_one({"_id": user_id})

    if existing:
        return await ctx.reply("❌ Već imaš račun!", mention_author=False)

    users.insert_one({
        "_id": user_id,
        "cash": 100,
        "bank": 0,
        "dirty": 0,
        "inventory": [],
        "business": None,
        "last_pay": 0
    })

    await ctx.reply(f"✅ {ctx.author.mention} tvoj račun je uspješno kreiran!", mention_author=False)

@bot.command()
async def radi(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    now = int(time.time())

    # cooldown iz baze (ako ne postoji = 0)
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

    earnings = random.randint(500, 1500)

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

    embed.add_field(name="💰 Zarada", value=f"```{earnings}$```", inline=False)
    embed.add_field(name="💵 Novo stanje", value=f"```{updated_user['cash']}$```", inline=False)

    await ctx.reply(embed=embed, mention_author=False)

# ---------------- BANKA ----------------
@bot.command()
async def banka(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply(
            "❌ Moraš prvo otvoriti račun sa `!prijava` da bi koristio banku!",
            mention_author=False
        )

    cash = user.get("cash", 0)
    bank_money = user.get("bank", 0)
    dirty = user.get("dirty", 0)

    embed = discord.Embed(title="🏦 Vaš račun", color=discord.Color.gold())

    embed.add_field(
        name="👤 Korisnik",
        value=f"{ctx.author.name}",
        inline=False
    )

    embed.add_field(
        name="<:11998cashbagwhite:1497120094843699270> Novčanik",
        value=f"```{cash:,}$```",
        inline=True
    )

    embed.add_field(
        name="<:328827nubankcard:1497118079388483644> Banka",
        value=f"```{bank_money:,}$```",
        inline=True
    )

    embed.add_field(
        name="<:4115blackmoneybag:1497117936312123474> Prljav novac",
        value=f"```{dirty:,}$```",
        inline=True
    )

    # 📦 INVENTORY
    items = user.get("inventory", [])

    EMOJIS = {
        "zastita": "<:714625rolemodyellow:1497137037474660372>",
        "pistol": "<:1136_gun:1497137080919130112>",
        "knife": "<:1575knifescream:1497137058467024937>"
    }

    if items:
        counts = {"knife": 0, "pistol": 0, "zastita": 0}

        for i in items:
            if i in counts:
                counts[i] += 1

        inv_text = (
            f"{EMOJIS['knife']} x{counts['knife']}\n"
            f"{EMOJIS['pistol']} x{counts['pistol']}\n"
            f"{EMOJIS['zastita']} x{counts['zastita']}"
        )
    else:
        inv_text = "`Prazno`"

    embed.add_field(
        name="📦 Inventory",
        value=inv_text,
        inline=True
    )

    # 🏢 BIZNIS
    biznis = user.get("business")

    biz_names = {
        "kladionica": "🎰 Kladionica",
        "klaonica": "🥩 Klaonica",
        "kiosk": "🏪 Kiosk"
    }

    biz_text = biz_names.get(biznis, "Nemaš biznis")

    embed.add_field(
        name="🏢 Biznis",
        value=f"`{biz_text}`",
        inline=True
    )

    await ctx.reply(embed=embed)
# ---------------- PREBACI ----------------
@bot.command()
async def prebaci(ctx, amount: int):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    if amount < 1:
        return await ctx.reply("❌ Minimalan iznos je 1$", mention_author=False)

    cash = user.get("cash", 0)

    if cash < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca!", mention_author=False)

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {
                "cash": -amount,
                "bank": amount
            }
        }
    )

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(title="Transakcija", color=discord.Color.green())
    embed.add_field(name="💸 Prebačeno", value=f"```{amount}$```", inline=True)
    embed.add_field(name="🏦 Banka", value=f"```{updated.get('bank', 0)}$```", inline=True)

    await ctx.reply(embed=embed, mention_author=False)

# ---------------- PODIGNI ----------------
@bot.command()
async def podigni(ctx, amount: int):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    if amount < 1:
        return await ctx.reply("❌ Minimalan iznos je 1$", mention_author=False)

    bank = user.get("bank", 0)

    if bank < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca u banci!", mention_author=False)

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {
                "bank": -amount,
                "cash": amount
            }
        }
    )

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(title="Transakcija", color=discord.Color.red())
    embed.add_field(name="💸 Podignuto", value=f"```{amount}$```", inline=True)
    embed.add_field(name="💵 Novčanik", value=f"```{updated.get('cash', 0)}$```", inline=True)

    await ctx.reply(embed=embed, mention_author=False)
# ---------------- CRIME ----------------
@bot.command()
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

    earnings = random.randint(25000, 40000)

    inventory.remove("pistol")

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

    embed.add_field(name="🕵️ Prljav novac", value=f"```+{earnings:,}$```", inline=False)
    embed.add_field(name="🧾 Ukupno", value=f"```{updated.get('dirty', 0):,}$```", inline=False)
    embed.add_field(name="🔫 Status", value="Izgubio si pištolj", inline=False)

    await ctx.reply(embed=embed, mention_author=False)

@bot.command()
async def operipare(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    dirty = user.get("dirty", 0)

    if dirty <= 0:
        return await ctx.reply("❌ Nemaš prljavog novca!", mention_author=False)

    tax = int(dirty * 0.10)
    cleaned = dirty - tax

    users.update_one(
        {"_id": user_id},
        {
            "$set": {"dirty": 0},
            "$inc": {"cash": cleaned}
        }
    )

    embed = discord.Embed(
        title="PRANJE PARA",
        color=discord.Color.green()
    )

    embed.add_field(name="Prljav novac:", value=f"```{dirty}$```", inline=False)
    embed.add_field(name="Oprano:", value=f"```{cleaned}$```", inline=False)
    embed.add_field(name="Taksa (10%):", value=f"```{tax}$```", inline=False)

    await ctx.reply(embed=embed, mention_author=False)


@bot.command()
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

    reward = random.randint(1000, 5000)

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": reward},
            "$set": {"daily_cd": now}
        }
    )

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(
        title="DAILY REWARD",
        color=discord.Color.green()
    )

    embed.add_field(name="Dobio si:", value=f"```{reward}$```", inline=False)
    embed.add_field(name="Novo stanje:", value=f"```{updated.get('cash', 0)}$```", inline=False)

    await ctx.reply(embed=embed, mention_author=False)

@bot.command()
async def kredit(ctx):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    now = int(time.time())

    last_credit = user.get("credit_cd", 0)

    # 3 dana cooldown (259200 sekundi)
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

    amount = 10000

    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"cash": amount},
            "$set": {"credit_cd": now}
        }
    )

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(
        title="KREDIT",
        color=discord.Color.green()
    )

    embed.add_field(name="Dobio si:", value=f"```{amount}$```", inline=False)
    embed.add_field(name="Novo stanje:", value=f"```{updated.get('cash', 0)}$```", inline=False)

    await ctx.reply(embed=embed, mention_author=False)

#-------------PLJACKAJ-------------
@bot.command()
async def pljackaj(ctx, member: discord.Member):
    user_id = str(ctx.author.id)
    target_id = str(member.id)

    user = users.find_one({"_id": user_id})
    target = users.find_one({"_id": target_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    if not target:
        return await ctx.reply("❌ Taj korisnik nema račun!", mention_author=False)

    if user_id == target_id:
        return await ctx.reply("❌ Ne možeš sebe opljačkati!", mention_author=False)

    now = int(time.time())

    if now - user.get("rob_cd", 0) < 600:
        left = 600 - (now - user.get("rob_cd", 0))
        return await ctx.reply(f"⏳ Čekaj još {left//60}m {left%60}s", mention_author=False)

    attacker_inv = user.get("inventory", [])
    target_inv = target.get("inventory", [])

    # ❌ mora imati nož
    if "knife" not in attacker_inv:
        return await ctx.reply("❌ Treba ti nož za pljačku!", mention_author=False)

    # 🔪 UVIJEK izgubi nož
    attacker_inv.remove("knife")

    # 🛡️ ZAŠTITA
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
            name="Rezultat",
            value=(
                f"PLJAČKAŠ\n```{ctx.author}```\n"
                f"ŽRTVA\n```{member}```\n"
                f"ISHOD\n```Zaštita je blokirala pljačku```"
            ),
            inline=False
        )

        return await ctx.reply(embed=embed, mention_author=False)

    success = random.randint(1, 100) <= 60
    target_cash = target.get("cash", 0)

    if target_cash <= 0:
        users.update_one(
            {"_id": user_id},
            {"$set": {"inventory": attacker_inv, "rob_cd": now}}
        )

        return await ctx.reply("❌ Nema para! Izgubio si nož.", mention_author=False)

    # ✔️ USPJEH
    if success:
        stolen = int(target_cash * 0.30)

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
            name="Rezultat",
            value=(
                f"PLJAČKAŠ\n```{ctx.author}```\n"
                f"ŽRTVA\n```{member}```\n"
                f"UKRADENO\n```{stolen:,}$```"
            ),
            inline=False
        )

    # ❌ FAIL
    else:
        fine = random.randint(1000, 3000)

        users.update_one(
            {"_id": user_id},
            {
                "$inc": {"cash": -fine},
                "$set": {"inventory": attacker_inv, "rob_cd": now}
            }
        )

        embed = discord.Embed(
            title="💀 PLJAČKA NEUSPJEŠNA",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Rezultat",
            value=(
                f"PLJAČKAŠ\n```{ctx.author}```\n"
                f"ŽRTVA\n```{member}```\n"
                f"KAZNA\n```{fine:,}$```"
            ),
            inline=False
        )

    await ctx.reply(embed=embed, mention_author=False)
#-----------------SET-----------------------
@bot.command()
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
async def slot(ctx, amount: int):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`", mention_author=False)

    if amount < 1:
        return await ctx.reply("❌ Minimalan ulog je 1$", mention_author=False)

    cash = user.get("cash", 0)

    if cash < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca!", mention_author=False)

    symbols = ["🍒", "🍋", "🍇", "💎", "7️⃣"]

    r1 = random.choice(symbols)
    r2 = random.choice(symbols)
    r3 = random.choice(symbols)

    result = f"{r1} | {r2} | {r3}"

    win = 0

    # 🎰 WIN / LOSS LOGIKA
    if r1 == r2 == r3:
        if r1 == "💎":
            win = amount * 7
        elif r1 == "7️⃣":
            win = amount * 4
        else:
            win = amount * 2

        users.update_one(
            {"_id": user_id},
            {"$inc": {"cash": win}}
        )

        title = "Dobitak"
        color = discord.Color.green()
        change_text = f"+{win:,}$"

    elif r1 == r2 or r1 == r3 or r2 == r3:
        win = int(amount * 1.5)

        users.update_one(
            {"_id": user_id},
            {"$inc": {"cash": win}}
        )

        title = "Dobitak"
        color = discord.Color.gold()
        change_text = f"+{win:,}$"

    else:
        users.update_one(
            {"_id": user_id},
            {"$inc": {"cash": -amount}}
        )

        title = "Gubitak"
        color = discord.Color.red()
        change_text = f"-{amount:,}$"

    updated = users.find_one({"_id": user_id})

    embed = discord.Embed(
        title=title,
        color=color
    )

    embed.add_field(name="🎲 Rezultat", value=f"```{result}```", inline=False)
    embed.add_field(name="💸 Dob/Gub", value=f"```{change_text}```", inline=False)
    embed.add_field(name="💰 Stanje", value=f"```{updated.get('cash', 0):,}$```", inline=False)

    await ctx.reply(embed=embed, mention_author=False)

#-----------------RULET---------------
import asyncio
import random

@bot.command()
async def rulet(ctx, choice: str, amount: int):
    user_id = str(ctx.author.id)

    # 🟢 MONGO CHECK (UMJESTO registered_users)
    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply(
            "❌ Moraš prvo otvoriti račun sa `!prijava`",
            mention_author=False
        )

    if amount < 1:
        return await ctx.reply("❌ Minimalan ulog je 1$", mention_author=False)

    cash = user.get("cash", 0)

    if cash < amount:
        return await ctx.reply("❌ Nemaš dovoljno novca!", mention_author=False)

    # 🎰 START
    embed = discord.Embed(
        title="🎰 RULET SE VRTI...",
        description="⏳ Molimo sačekaj 10 sekundi...",
        color=discord.Color.orange()
    )

    msg = await ctx.reply(embed=embed)

    await asyncio.sleep(10)

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

    # 🎯 BROJ (25x)
    if choice.isdigit():
        if int(choice) == number:
            win = amount * 25
        cash += win if win else -amount
    else:
        # 🎨 BOJA
        if choice == color:
            if color == "green":
                win = amount * 36
            else:
                win = amount * 2

            cash += win
        else:
            cash -= amount

    # 💾 SAVE MONGO
    users.update_one(
        {"_id": user_id},
        {"$set": {"cash": cash}}
    )

    # 🎯 RESULT
    result_text = f"```{number} {color_map[color]}```"

    embed = discord.Embed(
        title="🎰 RULET REZULTAT",
        description=result_text,
        color=discord.Color.green() if win > 0 else discord.Color.red()
    )

    if win > 0:
        embed.add_field(name="Dobitak", value=f"```+{win:,}$```", inline=False)
    else:
        embed.add_field(name="Gubitak", value=f"```-{amount:,}$```", inline=False)

    embed.add_field(name="Stanje", value=f"```{cash:,}$```", inline=False)

    await msg.edit(embed=embed)
#-------------HELP-----------------
@bot.command()
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
async def biznisi(ctx):
    embed = discord.Embed(
        title="🏢 DOSTUPNI BIZNISI",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🎰 Kladionica",
        value="💰 Cijena: `1,000,000$`\n💸 Zarada: `100,000$ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🥩 Klaonica",
        value="💰 Cijena: `500,000$`\n💸 Zarada: `75,000$ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🏪 Kiosk",
        value="💰 Cijena: `200,000$`\n💸 Zarada: `30,000$ / 24h`",
        inline=False
    )

    embed.add_field(
        name="🛒 Kupovina",
        value="Koristi: `!kupibiz <ime>`\nPrimjer: `!kupibiz kiosk`",
        inline=False
    )

    await ctx.reply(embed=embed)

# ---------------- KUPI BIZNIS ----------------
@bot.command()
async def kupibiz(ctx, *, biznis: str):
    user_id = str(ctx.author.id)

    user = users.find_one({"_id": user_id})

    if not user:
        return await ctx.reply("❌ Moraš prvo otvoriti račun sa `!prijava`")

    biznis = biznis.lower().replace(" ", "")

    # 🏢 NOVI BIZNISI
    biz = {
        "kladionica": 1000000,
        "klaonica": 500000,
        "kiosk": 200000
    }

    names = {
        "kladionica": "🎰 Kladionica",
        "klaonica": "🥩 Klaonica",
        "kiosk": "🏪 Kiosk"
    }

    if biznis not in biz:
        return await ctx.reply("❌ Taj biznis ne postoji! Koristi !biznisi")

    user_cash = user.get("cash", 0)

    if user_cash < biz[biznis]:
        return await ctx.reply("❌ Nemaš dovoljno novca!")

    if user.get("business"):
        return await ctx.reply("❌ Već posjeduješ biznis!")

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
        name="Biznis",
        value=f"`{names[biznis]}`",
        inline=False
    )

    embed.add_field(
        name="Status",
        value="Kupljeno ✔️",
        inline=False
    )

    await ctx.reply(embed=embed)
# ---------------- UZMI PARE ----------------
@bot.command()
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

    # 🕒 COOLDOWN
    if now - last_pay < 86400:
        left = 86400 - (now - last_pay)
        hours = left // 3600
        minutes = (left % 3600) // 60

        embed = discord.Embed(
            title="🏢 BIZNIS",
            description=f"⏳ Sačekaj još **{hours}h {minutes}m** da bi mogao uzeti pare iz biznisa.",
            color=discord.Color.orange()
        )

        return await ctx.reply(embed=embed)

    # 💰 ZARADE
    earnings_map = {
        "kladionica": 100000,
        "klaonica": 75000,
        "kiosk": 30000
    }

    names = {
        "kladionica": "🎰 Kladionica",
        "klaonica": "🥩 Klaonica",
        "kiosk": "🏪 Kiosk"
    }

    earnings = earnings_map.get(biznis, 0)

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

    users.update_one(
        {"_id": sender_id},
        {"$inc": {"cash": -amount}}
    )

    users.update_one(
        {"_id": receiver_id},
        {"$inc": {"cash": receive_amount}}
    )

    embed = discord.Embed(
        title="💸 TRANSFER NOVCA",
        color=discord.Color.green()
    )

    embed.add_field(name="📤 Pošiljaoc", value=f"{ctx.author.mention}", inline=False)
    embed.add_field(name="📥 Primalac", value=f"{member.mention}", inline=False)
    embed.add_field(name="💰 Poslano", value=f"`{amount:,}$`", inline=False)
    embed.add_field(name="🏦 Tax (10%)", value=f"`{tax:,}$`", inline=False)
    embed.add_field(name="💵 Primalac dobija", value=f"`{receive_amount:,}$`", inline=False)

    await ctx.reply(embed=embed)


# ---------------- TOP10 ----------------
@bot.command()
async def top10(ctx):
    top_users = users.find().limit(100)  # uzmi više pa sortiraj ručno

    leaderboard = []

    for u in top_users:
        user_id = u["_id"]
        cash = u.get("cash", 0)
        bank = u.get("bank", 0)

        total = cash + bank  # 💰 KLJUČNA PROMJENA

        try:
            member = await bot.fetch_user(int(user_id))
            name = member.name
        except:
            name = "Unknown"

        leaderboard.append((name, total))

    # sort po ukupno
    leaderboard.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 TOP 10 NAJBOGATIJIH",
        color=discord.Color.gold()
    )

    text = ""

    medals = ["🥇", "🥈", "🥉"]

    for i, (name, total) in enumerate(leaderboard[:10], start=1):
        medal = medals[i-1] if i <= 3 else f"#{i}"
        text += f"{medal} **{name}**\n💰 `{total:,}$`\n\n"

    embed.add_field(
        name="📊 Rang lista",
        value=text or "❌ Nema podataka",
        inline=False
    )

    await ctx.reply(embed=embed)
# ---------------- RESET SVE (FULL WIPE) ----------------
@bot.command()
async def rr(ctx):
    OWNER_ID = 633262690139242507

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
# ---------------- RUN ----------------


import os

bot.run(os.getenv("DISCORD_TOKEN"))
