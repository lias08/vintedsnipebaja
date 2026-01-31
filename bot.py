import os
import discord
from discord import app_commands
from sniper import VintedSniper

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

def convert_url(url: str) -> str:
    if "api/v2/catalog/items" in url:
        return url
    return "https://www.vinted.de/api/v2/catalog/items?" + url.split("?", 1)[1]

intents = discord.Intents.default()

class SniperBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.active_snipers = {}

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("🌍 Slash Commands (GUILD) synchronisiert")

client = SniperBot()

@client.event
async def on_ready():
    print(f"✅ Bot online als {client.user}")

# =====================
# /start
# =====================
@client.tree.command(
    name="start",
    description="Starte einen Vinted Sniper",
    guild=discord.Object(id=GUILD_ID)
)
async def start(interaction: discord.Interaction, url: str):

    channel_id = interaction.channel_id

    if channel_id in client.active_snipers:
        try:
            await interaction.response.send_message(
                "⚠️ Hier läuft bereits ein Sniper.", ephemeral=True
            )
        except:
            pass
        return

    # TRY interaction response – aber erzwingen wir es NICHT
    try:
        await interaction.response.send_message("🎯 Sniper gestartet!")
    except:
        await interaction.channel.send("🎯 Sniper gestartet!")

    def send_item(item):
        client.loop.create_task(
            interaction.channel.send(
                f"🔥 **{item.get('title')}**\n{item.get('url')}"
            )
        )

    sniper = VintedSniper(convert_url(url), send_item)
    sniper.start()
    client.active_snipers[channel_id] = sniper

# =====================
# /stop
# =====================
@client.tree.command(
    name="stop",
    description="Stoppe den Sniper",
    guild=discord.Object(id=GUILD_ID)
)
async def stop(interaction: discord.Interaction):

    channel_id = interaction.channel_id
    sniper = client.active_snipers.pop(channel_id, None)

    if sniper:
        sniper.stop()
        try:
            await interaction.response.send_message("🛑 Sniper gestoppt.")
        except:
            await interaction.channel.send("🛑 Sniper gestoppt.")
    else:
        try:
            await interaction.response.send_message(
                "❌ Kein Sniper aktiv.", ephemeral=True
            )
        except:
            pass

client.run(TOKEN)
