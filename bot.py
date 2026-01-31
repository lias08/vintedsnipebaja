import discord
from discord import app_commands
import os
import asyncio

from sniper import VintedSniper, get_upload_timestamp

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
            # Deine Callback-Logik, die sofort die neuen Artikel an Discord sendet
            upload_ts = get_upload_timestamp(item)
            upload_text = f"<t:{upload_ts}:R>" if upload_ts else "Unbekannt"
            
            # Versuche, die `currency` zu erhalten, ansonsten setze sie auf 'EUR'
            currency = item.get("price", {}).get("currency", "EUR")  # Fallback auf EUR, falls keine Währung angegeben
            price = item.get("price", {}).get("amount", "Unbekannt")  # Preis des Artikels

            # Versuche, die Größe zu bekommen (falls vorhanden)
            size = item.get("size_title", "Unbekannt")  # Fallback auf "Unbekannt", falls keine Größe angegeben

            # Versuche, das Bild zu bekommen (falls vorhanden)
            photos = item.get("photos", [])
            main_image_url = photos[0]["url"] if photos else None  # Das erste Bild als Hauptbild

            # Erstelle das Embed
            embed = discord.Embed(
                title=f"🔥 {item.get('title')}",
                url=item.get("url", ""),
                color=0x09b1ba
            )

            embed.add_field(name="💶 Preis", value=f"{price} {currency}", inline=True)
            embed.add_field(name="🕒 Hochgeladen", value=upload_text, inline=True)
            embed.add_field(name="📏 Größe", value=size, inline=True)  # Hier wird die Größe hinzugefügt

            # Füge das Hauptbild hinzu, wenn es vorhanden ist
            if main_image_url:
                embed.set_image(url=main_image_url)

            # Sende Embed zu Discord (stelle sicher, dass das asynchron ist)
            asyncio.run_coroutine_threadsafe(
                interaction.channel.send(embed=embed), client.loop
            )  # Wir verwenden asyncio.run_coroutine_threadsafe(), um den Event Loop korrekt zu verwenden

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
