import os
import discord
from discord import app_commands
from sniper import VintedSniper

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# =========================
# URL → API URL
# =========================
def convert_url(url: str) -> str:
    if "api/v2/catalog/items" in url:
        return url
    return "https://www.vinted.de/api/v2/catalog/items?" + url.split("?", 1)[1]

# =========================
# DISCORD CLIENT
# =========================
intents = discord.Intents.default()

class SniperBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.active_snipers = {}

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.clear_commands(guild=guild)      # ALLE alten Commands weg
        await self.tree.sync(guild=guild)           # leeren Sync
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)           # neuer Sync
        print("🌍 Slash Commands (GUILD) synchronisiert")

client = SniperBot()

@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    # Alte Commands löschen
    for cmd in await client.tree.fetch_commands(guild=guild):
        if cmd.name == "start":
            await client.tree.delete_command(cmd.id, guild=guild)
            print(f"❌ /start gelöscht")
    await client.tree.sync(guild=guild)
    print("🌍 Commands synchronisiert")


# =========================
# /scan
# =========================
@client.tree.command(
    name="scan",
    description="Starte einen Vinted Scan mit URL",
    guild=discord.Object(id=GUILD_ID)
)
async def scan(interaction: discord.Interaction, url: str):

    channel_id = interaction.channel_id

    if channel_id in client.active_snipers:
        try:
            await interaction.response.send_message(
                "⚠️ In diesem Channel läuft bereits ein Scan.",
                ephemeral=True
            )
        except:
            pass
        return

    # SOFORT antworten (oder fallback)
    try:
        await interaction.response.send_message("🔍 Scan gestartet!")
    except:
        await interaction.channel.send("🔍 Scan gestartet!")

    def send_item(item):
        client.loop.create_task(
            interaction.channel.send(
                f"🔥 **{item.get('title')}**\n{item.get('url')}"
            )
        )

    sniper = VintedSniper(convert_url(url), send_item)
    sniper.start()
    client.active_snipers[channel_id] = sniper

# =========================
# /stop
# =========================
@client.tree.command(
    name="scan",
    description="Starte einen Vinted Scan mit URL",
    guild=discord.Object(id=GUILD_ID)
)
async def scan(interaction: discord.Interaction, url: str):
    await interaction.response.send_message(f"🔍 Scan gestartet für: {url}")
:

    channel_id = interaction.channel_id
    sniper = client.active_snipers.pop(channel_id, None)

    if sniper:
        sniper.stop()
        try:
            await interaction.response.send_message("🛑 Scan gestoppt.")
        except:
            await interaction.channel.send("🛑 Scan gestoppt.")
    else:
        try:
            await interaction.response.send_message(
                "❌ Kein Scan aktiv.",
                ephemeral=True
            )
        except:
            pass

# =========================
# BOT START
# =========================
client.run(TOKEN)
