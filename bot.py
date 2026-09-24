@bot.tree.command(name="panel", description="Send the ticket panel in this channel.")
@app_commands.checks.has_permissions(manage_guild=True)
async def panel(interaction: discord.Interaction):
