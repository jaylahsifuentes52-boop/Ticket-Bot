import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord import app_commands
from discord.ext import commands


# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

SERVER_IDS = [
    1538740748709658694,
    1551388740616855612
]

PORT = int(os.getenv("PORT", "10000"))


# =========================
# RENDER PORT SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Discord bot is online!")

    def log_message(self, format, *args):
        pass


def start_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


threading.Thread(
    target=start_server,
    daemon=True
).start()


# =========================
# DISCORD BOT
# =========================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


def allowed_server(guild):
    return guild is not None and guild.id in SERVER_IDS


# =========================
# TICKET BUTTON
# =========================

class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        emoji="🎫",
        style=discord.ButtonStyle.green,
        custom_id="create_ticket"
    )
    async def create_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not allowed_server(interaction.guild):
            await interaction.response.send_message(
                "❌ This bot is not configured for this server.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        channel_name = f"ticket-{interaction.user.id}"

        existing = discord.utils.get(
            interaction.guild.text_channels,
            name=channel_name
        )

        if existing:
            await interaction.followup.send(
                f"🎫 You already have a ticket: {existing.mention}",
                ephemeral=True
            )
            return

        guild = interaction.guild
        bot_member = guild.me

        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                ),

            bot_member:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True
                )
        }

        try:
            channel = await guild.create_text_channel(
                channel_name,
                overwrites=overwrites
            )

            await channel.send(
                f"🎫 Welcome {interaction.user.mention}!\n\n"
                "Please explain what you need help with.\n\n"
                "Use `/rename-ticket` to rename this ticket.\n"
                "Use `/close` when you are finished."
            )

            await interaction.followup.send(
                f"✅ Your ticket was created: {channel.mention}",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to create channels.",
                ephemeral=True
            )


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    bot.add_view(TicketView())

    for server_id in SERVER_IDS:

        guild = discord.Object(id=server_id)

        try:
            synced = await bot.tree.sync(guild=guild)

            print(
                f"Synced {len(synced)} commands "
                f"to server {server_id}"
            )

        except Exception as error:
            print(
                f"Sync error for {server_id}: {error}"
            )


# =========================
# /TICKET
# =========================

@bot.tree.command(
    name="ticket",
    description="Create a private support ticket."
)
async def ticket(interaction: discord.Interaction):

    if not allowed_server(interaction.guild):
        await interaction.response.send_message(
            "❌ This bot is not configured for this server.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    channel_name = f"ticket-{interaction.user.id}"

    existing = discord.utils.get(
        interaction.guild.text_channels,
        name=channel_name
    )

    if existing:
        await interaction.followup.send(
            f"🎫 You already have a ticket: {existing.mention}",
            ephemeral=True
        )
        return

    guild = interaction.guild
    bot_member = guild.me

    overwrites = {
        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        interaction.user:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),

        bot_member:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )
    }

    try:

        channel = await guild.create_text_channel(
            channel_name,
            overwrites=overwrites
        )

        await channel.send(
            f"🎫 Welcome {interaction.user.mention}!\n\n"
            "Please explain what you need help with.\n\n"
            "Use `/rename-ticket` to rename this ticket.\n"
            "Use `/close` when you are finished."
        )

        await interaction.followup.send(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.followup.send(
            "❌ I don't have permission to create channels.",
            ephemeral=True
        )


# =========================
# /PANEL
# =========================

@bot.tree.command(
    name="panel",
    description="Send the ticket panel."
)
async def panel(interaction: discord.Interaction):

    if not allowed_server(interaction.guild):
        await interaction.response.send_message(
            "❌ This bot is not configured for this server.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🎫 Support Tickets",
        description=(
            "Need help?\n\n"
            "Click **Create Ticket** below "
            "to open a private ticket."
        ),
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(
        embed=embed,
        view=TicketView()
    )


# =========================
# /RENAME-TICKET
# =========================

@bot.tree.command(
    name="rename-ticket",
    description="Rename the current ticket."
)
@app_commands.describe(
    new_name="The new name for the ticket."
)
async def rename_ticket(
    interaction: discord.Interaction,
    new_name: str
):

    if not allowed_server(interaction.guild):
        await interaction.response.send_message(
            "❌ This bot is not configured for this server.",
            ephemeral=True
        )
        return

    channel = interaction.channel

    if not isinstance(
        channel,
        discord.TextChannel
    ) or not channel.name.startswith("ticket-"):

        await interaction.response.send_message(
            "❌ This is not a ticket channel.",
            ephemeral=True
        )
        return

    new_name = new_name.strip().lower().replace(" ", "-")

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789-_"
    )

    new_name = "".join(
        char for char in new_name
        if char in allowed
    )[:90]

    if not new_name:
        await interaction.response.send_message(
            "❌ Please enter a valid ticket name.",
            ephemeral=True
        )
        return

    if not new_name.startswith("ticket-"):
        new_name = f"ticket-{new_name}"

    try:

        await channel.edit(
            name=new_name,
            reason=f"Ticket renamed by {interaction.user}"
        )

        await interaction.response.send_message(
            f"✅ Ticket renamed to **{new_name}**."
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to rename channels.",
            ephemeral=True
        )


# =========================
# /CLOSE
# =========================

@bot.tree.command(
    name="close",
    description="Close the current ticket."
)
async def close(interaction: discord.Interaction):

    if not allowed_server(interaction.guild):
        await interaction.response.send_message(
            "❌ This bot is not configured for this server.",
            ephemeral=True
        )
        return

    channel = interaction.channel

    if not isinstance(
        channel,
        discord.TextChannel
    ) or not channel.name.startswith("ticket-"):

        await interaction.response.send_message(
            "❌ This is not a ticket channel.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🔒 Closing ticket..."
    )

    await channel.delete(
        reason=f"Ticket closed by {interaction.user}"
    )


# =========================
# START BOT
# =========================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is not set in Render."
    )

bot.run(TOKEN)
