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
        try:
            # Versuche, die Währung und den Preis zu erhalten
            currency = item.get("price", {}).get("currency", "EUR")
            price = item.get("price", {}).get("amount", "Unbekannt")

            # Versuche, die Größe zu bekommen (falls vorhanden)
            size = item.get("size_title", "Unbekannt")

            # Zustand des Artikels
            status = get_clean_status(item)

            # Versuch, das Bild zu bekommen (falls vorhanden)
            photos = item.get("photos", [])
            main_image_url = photos[0]["url"] if photos else None

            # Erstelle das Embed
            embed = discord.Embed(
                title=f"🔥 {item.get('title')}",
                url=item.get("url", ""),
                color=0x09b1ba
            )

            embed.add_field(name="💶 Preis", value=f"{price} {currency}", inline=True)
            embed.add_field(name="📏 Größe", value=size, inline=True)
            embed.add_field(name="✨ Zustand", value=status, inline=True)

            # Füge das Hauptbild hinzu, wenn es vorhanden ist
            if main_image_url:
                embed.set_image(url=main_image_url)

            # Erstelle die Buttons für Nachricht schreiben und Favorisieren
            message_button = discord.ui.Button(style=discord.ButtonStyle.link, label="💬 Nachricht schreiben", url=item.get("url", ""))
            favorite_button = discord.ui.Button(style=discord.ButtonStyle.link, label="❤️ Favorisieren", url=f"https://www.vinted.de/items/{item['id']}")

            # Kombiniere die Buttons in einer View
            view = discord.ui.View()
            view.add_item(message_button)
            view.add_item(favorite_button)

            # Sende Embed zu Discord (stelle sicher, dass das asynchron ist)
            asyncio.run_coroutine_threadsafe(
                interaction.channel.send(embed=embed, view=view), client.loop
            )

        except Exception as e:
            print(f"❌ Fehler beim Senden des Items: {e}")

    sniper = VintedSniper(url, on_item)
    active_snipers[channel_id] = sniper
    sniper.start()  # Wir rufen jetzt start() auf, da VintedSniper von threading.Thread erbt

    await interaction.followup.send("🟢 Sniper gestartet!", ephemeral=True)


@client.event
async def on_ready():
    await tree.sync()  # Synchronisiert die Slash-Befehle mit Discord
    print(f"✅ Bot online als {client.user}")

client.run(TOKEN)
