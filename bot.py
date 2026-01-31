import discord
from discord import app_commands
import os
import asyncio
import json

from sniper import VintedSniper, get_upload_timestamp, get_clean_status

TOKEN = os.getenv("DISCORD_TOKEN")  # Dein Discord-Token aus der Umgebung

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Initialisiere den Command Tree
tree = app_commands.CommandTree(client)

active_snipers = {}  # channel_id → sniper

@tree.command(name="scan", description="Starte Vinted Scan mit URL")
@app_commands.describe(url="Vinted Such-URL")
async def scan(interaction: discord.Interaction, url: str):
    channel_id = interaction.channel_id

    if channel_id in active_snipers:
        await interaction.response.send_message(
            "⚠️ In diesem Channel läuft bereits ein Scan.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    def on_item(item):
        # Ändere on_item, damit es nun die asynchrone Funktion verwendet
        asyncio.run_coroutine_threadsafe(on_item(interaction, item), client.loop)

    sniper = VintedSniper(url, on_item)
    active_snipers[channel_id] = sniper
    sniper.start()  # Wir rufen jetzt start() auf, da VintedSniper von threading.Thread erbt

    await interaction.followup.send("🟢 Sniper gestartet!", ephemeral=True)


@client.event
async def on_ready():
    await tree.sync()  # Synchronisiert die Slash-Befehle mit Discord
    print(f"✅ Bot online als {client.user}")

client.run(TOKEN)
