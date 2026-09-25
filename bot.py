import os
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

# PUT YOUR DISCORD SERVER ID HERE
SERVER_ID = 1538740748709658694

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    guild = discord.Object(id=SERVER_ID)

    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to server {SERVER_ID}")
    except Exception as e:
        print(f"Sync error: {e}")


@bot.tree.command(
    name="ticket",
    description="Create a ticket."
)
async def ticket(interaction: discord.Interaction):
    if interaction.guild is None or interaction.guild.id != SERVER_ID:
        await interaction.response.send_message(
            "❌ This bot is not configured for this server.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🎫 Ticket command works!",
        ephemeral=True
    )


@bot.tree.command(
    name="panel",
    description="Open the ticket panel."
)
async def panel(interaction: discord.Interaction):
    if interaction.guild is None or interaction.guild.id != SERVER_ID:
        await interaction.response.send_message(
            "❌ This bot is not configured for this server.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🎫 Ticket Panel",
        ephemeral=True
    )


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in Render.")

bot.run(TOKEN)
