import os
import discord
from discord import app_commands
from sniper import VintedSniper

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# URL → API URL
# =========================
def convert_url(url: str) -> str:
    if "api/v2/catalog/items" in url:
        return url
    base = "https://www.vinted.de/api/v2/catalog/items?"
    return base + url.split("?", 1)[1]

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
        await self.tree.sync()
        print("🌍 Slash Commands synchronisiert")

client = SniperBot()

@client.event
async def on_ready():
    print(f"✅ Bot online als {client.user}")

# =========================
# /start
# =========================
@client.tree.command(
    name="start",
    description="Starte einen Vinted Sniper mit einer URL"
)
async def start(interaction: discord.Interaction, url: str):

    channel_id = interaction.channel_id

    if channel_id in client.active_snipers:
        await interaction.response.send_message(
            "⚠️ In diesem Channel läuft bereits ein Sniper.",
            ephemeral=True
        )
        return

    # Sofort Antwort, dann Sniper im Hintergrund
    await interaction.response.send_message("🎯 Sniper wird gestartet!")

    def send_item(item):
        client.loop.create_task(
            interaction.channel.send(
                f"🔥 **{item.get('title')}**\n{item.get('url')}"
            )
        )

    # Sniper in Thread starten → blockiert Discord nicht
    sniper = VintedSniper(convert_url(url), send_item)
    sniper.start()
    client.active_snipers[channel_id] = sniper

    # Optionale Folge-Nachricht, wenn Sniper gestartet ist
    client.loop.create_task(
        interaction.channel.send("✅ Sniper erfolgreich gestartet und läuft im Hintergrund!")
    )


# =========================
# /stop
# =========================
@client.tree.command(
    name="stop",
    description="Stoppe den Sniper in diesem Channel"
)
async def stop(interaction: discord.Interaction):

    channel_id = interaction.channel_id
    sniper = client.active_snipers.pop(channel_id, None)

    if sniper:
        sniper.stop()
        await interaction.response.send_message("🛑 Sniper gestoppt.")
    else:
        await interaction.response.send_message(
            "❌ In diesem Channel läuft kein Sniper.",
            ephemeral=True
        )

# =========================
# BOT START
# =========================
client.run(TOKEN)
