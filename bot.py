import os
import discord
from discord import app_commands
from sniper import VintedSniper
import time

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()

class SniperBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.active = {}

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        await self.tree.sync(guild=guild)
        print("🌍 Slash Commands synchronisiert")

client = SniperBot()

@client.event
async def on_ready():
    print(f"✅ Bot online als {client.user}")

# =========================
# /scan
# =========================
@client.tree.command(
    name="scan",
    description="Starte einen Vinted Scan",
    guild=discord.Object(id=GUILD_ID)
)
async def scan(interaction: discord.Interaction, url: str):
    channel = interaction.channel

    if channel.id in client.active:
        await interaction.response.send_message(
            "⚠️ In diesem Channel läuft bereits ein Scan.",
            ephemeral=True
        )
        return

    await interaction.response.send_message("🔍 Scan gestartet!")

    async def send_item(item):
        price = float(item["price"]["amount"])
        total = round(price + 0.70 + price * 0.05 + 3.99, 2)

        item_url = item.get("url") or f"https://www.vinted.de/items/{item['id']}"
        brand = item.get("brand_title", "Keine Marke")
        size = item.get("size_title", "N/A")
        condition = item.get("status", "Unbekannt")

        photos = item.get("photos", [])
        image = photos[0]["url"].replace("/medium/", "/full/") if photos else None

        embed = discord.Embed(
            title=f"🔥 {item['title']}",
            url=item_url,
            color=0x09b1ba,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name="💶 Preis", value=f"{price:.2f} €", inline=True)
        embed.add_field(name="🚚 Gesamt ca.", value=f"{total:.2f} €", inline=True)
        embed.add_field(name="📏 Größe", value=size, inline=True)
        embed.add_field(name="🏷️ Marke", value=brand, inline=True)
        embed.add_field(name="✨ Zustand", value=str(condition), inline=True)
        embed.add_field(
            name="⚡ Aktionen",
            value=f"[🛒 Kaufen](https://www.vinted.de/transaction/buy/new?item_id={item['id']}) | "
                  f"[💬 Nachricht]({item_url}#message)",
            inline=False
        )

        if image:
            embed.set_image(url=image)

        await channel.send(embed=embed)

    sniper = VintedSniper(url, lambda item: client.loop.create_task(send_item(item)))
    sniper.start()
    client.active[channel.id] = sniper

# =========================
# /stop
# =========================
@client.tree.command(
    name="stop",
    description="Stoppe den Scan",
    guild=discord.Object(id=GUILD_ID)
)
async def stop(interaction: discord.Interaction):
    sniper = client.active.pop(interaction.channel.id, None)

    if sniper:
        sniper.stop()
        await interaction.response.send_message("🛑 Scan gestoppt.")
    else:
        await interaction.response.send_message(
            "❌ Kein Scan aktiv.",
            ephemeral=True
        )

client.run(TOKEN)
