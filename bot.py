import os
import discord
from discord import app_commands
from sniper import VintedSniper  # dein Sniper-Code aus sniper.py

# =========================
# Variablen aus Railway
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")  # Discord Bot Token
GUILD_ID = int(os.getenv("GUILD_ID"))  # Deine Server ID als Zahl

# =========================
# Discord Client
# =========================
intents = discord.Intents.default()

class SniperBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.active_snipers = {}  # channel_id → VintedSniper

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        # Alte Commands löschen (optional, falls noch /start existiert)
        for cmd in await self.tree.fetch_commands(guild=guild):
            if cmd.name == "start":
                await self.tree.delete_command(cmd.id, guild=guild)
                print("❌ /start gelöscht")
        await self.tree.sync(guild=guild)
        print("🌍 Slash Commands (GUILD) synchronisiert")

client = SniperBot()

# =========================
# Events
# =========================
@client.event
async def on_ready():
    print(f"✅ Bot online als {client.user}")
    cmds = await client.tree.fetch_commands(guild=discord.Object(id=GUILD_ID))
    print("🔹 Registrierte Slash Commands:")
    for c in cmds:
        print(f"- {c.name}")

# =========================
# /scan Command
# =========================
@client.tree.command(
    name="scan",
    description="Starte einen Vinted Scan mit einer URL",
    guild=discord.Object(id=GUILD_ID)
)
async def scan(interaction: discord.Interaction, url: str):
    channel_id = interaction.channel_id

    # Prüfen, ob im Channel schon ein Scan läuft
    if channel_id in client.active_snipers:
        try:
            await interaction.response.send_message(
                "⚠️ In diesem Channel läuft bereits ein Scan.",
                ephemeral=True
            )
        except:
            pass
        return

    # Antwort senden
    try:
        await interaction.response.send_message(f"🔍 Scan gestartet für: {url}")
    except:
        await interaction.channel.send(f"🔍 Scan gestartet für: {url}")

    # Funktion zum Senden von Items in den Channel
    def send_item(item):
        client.loop.create_task(
            interaction.channel.send(
                f"🔥 **{item.get('title')}**\n{item.get('url')}"
            )
        )

    # Sniper starten
    sniper = VintedSniper(url, send_item)
    sniper.start()
    client.active_snipers[channel_id] = sniper

# =========================
# /stop Command
# =========================
@client.tree.command(
    name="stop",
    description="Stoppe den Vinted Scan in diesem Channel",
    guild=discord.Object(id=GUILD_ID)
)
async def stop(interaction: discord.Interaction):
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
                "❌ Kein Scan aktiv in diesem Channel.",
                ephemeral=True
            )
        except:
            pass

# =========================
# Bot starten
# =========================
client.run(TOKEN)
