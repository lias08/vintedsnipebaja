import os
import discord
from discord.ext import commands
from sniper import VintedSniper

TOKEN = os.getenv("DISCORD_TOKEN")

def convert_url(url):
    base = "https://www.vinted.de/api/v2/catalog/items?"
    return base + url.split("?")[1]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

active_snipers = {}

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

@bot.command()
async def start(ctx, url: str):
    cid = ctx.channel.id

    if cid in active_snipers:
        await ctx.send("⚠️ Dieser Channel scannt bereits.")
        return

    def send_item(item):
        bot.loop.create_task(
            ctx.send(f"🔥 **{item.get('title')}**\n{item.get('url')}")
        )

    sniper = VintedSniper(convert_url(url), send_item)
    sniper.start()
    active_snipers[cid] = sniper

    await ctx.send("🎯 Sniper gestartet!")

@bot.command()
async def stop(ctx):
    cid = ctx.channel.id
    sniper = active_snipers.pop(cid, None)

    if sniper:
        sniper.stop()
        await ctx.send("🛑 Sniper gestoppt.")
    else:
        await ctx.send("❌ Kein aktiver Sniper.")

bot.run(TOKEN)
