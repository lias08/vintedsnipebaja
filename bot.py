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
        # Deine Callback-Logik, die sofort die neuen Artikel an Discord sendet
        upload_ts = get_upload_timestamp(item)
        upload_text = f"<t:{upload_ts}:R>" if upload_ts else "Unbekannt"
        
        embed = discord.Embed(
            title=f"🔥 {item.get('title')}",
            url=item.get("url", ""),
            color=0x09b1ba
        )

        embed.add_field(name="💶 Preis", value=f"{item['price']['amount']} {item['price']['currency']}", inline=True)
        embed.add_field(name="🕒 Hochgeladen", value=upload_text, inline=True)

        # Sende Embed zu Discord
        client.loop.create_task(
            interaction.channel.send(embed=embed)
        )

    sniper = VintedSniper(url, on_item)
    active_snipers[channel_id] = sniper
    await sniper.run()  # Wir starten den Sniper asynchron

    await interaction.followup.send("🟢 Sniper gestartet!", ephemeral=True)
