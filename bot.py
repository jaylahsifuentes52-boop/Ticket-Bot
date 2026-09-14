import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set.")

# Render web services need an open HTTP port.
PORT = int(os.getenv("PORT", "10000"))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Ticket bot is running.")

    def log_message(self, format, *args):
        return

def run_health_server():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.green,
        emoji="🎫",
        custom_id="ticket:create"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This button can only be used inside a server.",
                ephemeral=True
            )
            return

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.id}")
        if existing:
            await interaction.response.send_message(
                f"You already have a ticket: {existing.mention}",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            )
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            overwrites=overwrites,
            topic=f"Ticket opened by {interaction.user} ({interaction.user.id})"
        )

        await channel.send(
            f"🎫 Welcome {interaction.user.mention}!\n"
            "Please explain what you need help with. A staff member can assist you.\n\n"
            "Use the button below to close this ticket.",
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"Your ticket has been created: {channel.mention}",
            ephemeral=True
        )

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="ticket:close"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                "This is not a ticket channel.",
                ephemeral=True
            )
            return

        await interaction.response.send_message("🔒 Closing this ticket...")
        await asyncio.sleep(2)
        await channel.delete(reason=f"Ticket closed by {interaction.user}")

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}")
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Slash command sync error: {e}")

@bot.tree.command(name="panel", description="Send the ticket panel in this channel.")
@app_commands.checks.has_permissions(manage_guild=True)
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description="Need help? Click **Create Ticket** below to open a private support ticket.",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Ticket System")
    await interaction.response.send_message(embed=embed, view=TicketView())

@panel.error
async def panel_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "You need the **Manage Server** permission to use /panel.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Something went wrong while creating the panel.",
            ephemeral=True
        )

@bot.tree.command(name="ticket", description="Create a private support ticket.")
async def ticket(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This command can only be used inside a server.",
            ephemeral=True
        )
        return

    existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.id}")
    if existing:
        await interaction.response.send_message(
            f"You already have a ticket: {existing.mention}",
            ephemeral=True
        )
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            read_message_history=True
        )
    }

    channel = await guild.create_text_channel(
        name=f"ticket-{interaction.user.id}",
        overwrites=overwrites,
        topic=f"Ticket opened by {interaction.user} ({interaction.user.id})"
    )

    await channel.send(
        f"🎫 Welcome {interaction.user.mention}!\n"
        "Please explain what you need help with. A staff member can assist you.\n\n"
        "Use the button below to close this ticket.",
        view=CloseTicketView()
    )

    await interaction.response.send_message(
        f"Your ticket has been created: {channel.mention}",
        ephemeral=True
    )

bot.run(TOKEN)
