import discord
from discord import app_commands
import os

from sniper import VintedSniper, get_upload_timestamp

TOKEN = os.getenv("DISCORD_TOKEN")

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

        embed = discord.Embed(
            title=f"🔥 {item.get('title')}",
            url=item.get("url", ""),
            color=0x09b1ba
        )

        embed.add_field(name="💶 Preis", value=f"{item['price']['amount']} €", inline=True)
        embed.add_field(name="🕒 Hochgeladen", value=upload_text, inline=True)
        embed.add_field(name="📏 Größe", value=item.get("size_title", "N/A"), inline=True)

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
