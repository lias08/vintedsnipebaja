import discord
from discord import app_commands
import os

from sniper import VintedSniper, get_upload_timestamp

TOKEN = os.getenv("DISCORD_TOKEN")  # Dein Discord-Token aus der Umgebung

intents = discord.Intents.default()
client = discord.Client(intents=intents)
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
        upload_ts = get_upload_timestamp(item)
        upload_text = f"<t:{upload_ts}:R>" if upload_ts else "Unbekannt"

        price = item.get("price", {}).get("amount", "N/A")
        currency = item.get("price", {}).get("currency", "EUR")

        brand = item.get("brand_title", "Keine Marke")
        size = item.get("size_title", "N/A")

        status_map = {
            1: "Neu ohne Etikett ✨",
            2: "Sehr gut 👌",
            3: "Gut 👍",
            4: "Zufriedenstellend 🆗",
            6: "Neu mit Etikett ✨"
        }
        status = status_map.get(item.get("status_id"), "Unbekannt")

        photos = item.get("photos", [])
        image_url = None
        if photos:
            image_url = photos[0].get("url", "").replace("/medium/", "/full/")

        item_url = item.get("url") or f"https://www.vinted.de/items/{item.get('id')}"

        embed = discord.Embed(
            title=f"🔥 {item.get('title')}",
            url=item_url,
            color=0x09b1ba
        )

        embed.add_field(name="💶 Preis", value=f"{price} {currency}", inline=True)
        embed.add_field(name="🏷️ Marke", value=brand, inline=True)
        embed.add_field(name="📏 Größe", value=size, inline=True)
        embed.add_field(name="✨ Zustand", value=status, inline=True)
        embed.add_field(name="🕒 Hochgeladen", value=upload_text, inline=True)

        if image_url:
            embed.set_image(url=image_url)

        embed.set_footer(text="Vinted Sniper • Live")

        client.loop.create_task(
            interaction.channel.send(embed=embed)
        )

    sniper = VintedSniper(url, on_item)
    active_snipers[channel_id] = sniper
    sniper.start()

    await interaction.followup.send("🟢 Sniper gestartet!", ephemeral=True)


@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online als {client.user}")


client.run(TOKEN)
