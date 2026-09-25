
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

SERVER_ID = 1538740748709658694

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

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This can only be used in a server.",
                ephemeral=True
            )
            return

        if interaction.guild.id != SERVER_ID:
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
# /VERIFY OTP
# =========================

VERIFY_OTP = os.getenv("VERIFY_OTP")
VERIFIED_ROLE_NAME = "Verified"

@bot.tree.command(name="verify", description="Verify yourself with an OTP.")
@app_commands.describe(otp="Enter your verification OTP.")
async def verify(interaction: discord.Interaction, otp: str):
    if interaction.guild is None:
        await interaction.response.send_message("❌ Use this inside a server.", ephemeral=True)
        return

    if interaction.guild.id != SERVER_ID:
        await interaction.response.send_message("❌ This bot is not configured for this server.", ephemeral=True)
        return

    if not VERIFY_OTP:
        await interaction.response.send_message("❌ Verification is not configured yet.", ephemeral=True)
        return

    if otp.strip() != VERIFY_OTP.strip():
        await interaction.response.send_message("❌ Incorrect or expired OTP.", ephemeral=True)
        return

    role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
    if role is None:
        try:
            role = await interaction.guild.create_role(
                name=VERIFIED_ROLE_NAME,
                reason="Created for bot verification"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to create the Verified role.",
                ephemeral=True
            )
            return

    if role in interaction.user.roles:
        await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
        return

    try:
        await interaction.user.add_roles(role, reason="Successful OTP verification")
        await interaction.response.send_message(
            "✅ Verification successful! You now have the Verified role.",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I can't give you the Verified role. Make sure my bot role is above the Verified role.",
            ephemeral=True
        )

# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    bot.add_view(TicketView())

    guild = discord.Object(id=SERVER_ID)

    try:

        synced = await bot.tree.sync(guild=guild)

        print(
            f"Synced {len(synced)} commands "
            f"to server {SERVER_ID}"
        )

    except Exception as error:

        print(f"Sync error: {error}")


# =========================
# /TICKET
# =========================

@bot.tree.command(
    name="ticket",
    description="Create a private support ticket."
)
async def ticket(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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
            "Please explain what you need help with."
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

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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
# /CLOSE
# =========================

@bot.tree.command(
    name="close",
    description="Close the current ticket."
)
async def close(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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

bot.run(TOKEN)import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord import app_commands
from discord.ext import commands


# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

SERVER_ID = 1538740748709658694

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

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This can only be used in a server.",
                ephemeral=True
            )
            return

        if interaction.guild.id != SERVER_ID:
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
# /VERIFY OTP
# =========================

VERIFY_OTP = os.getenv("VERIFY_OTP")
VERIFIED_ROLE_NAME = "Verified"

@bot.tree.command(name="verify", description="Verify yourself with an OTP.")
@app_commands.describe(otp="Enter your verification OTP.")
async def verify(interaction: discord.Interaction, otp: str):
    if interaction.guild is None:
        await interaction.response.send_message("❌ Use this inside a server.", ephemeral=True)
        return

    if interaction.guild.id != SERVER_ID:
        await interaction.response.send_message("❌ This bot is not configured for this server.", ephemeral=True)
        return

    if not VERIFY_OTP:
        await interaction.response.send_message("❌ Verification is not configured yet.", ephemeral=True)
        return

    if otp.strip() != VERIFY_OTP.strip():
        await interaction.response.send_message("❌ Incorrect or expired OTP.", ephemeral=True)
        return

    role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
    if role is None:
        try:
            role = await interaction.guild.create_role(
                name=VERIFIED_ROLE_NAME,
                reason="Created for bot verification"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to create the Verified role.",
                ephemeral=True
            )
            return

    if role in interaction.user.roles:
        await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
        return

    try:
        await interaction.user.add_roles(role, reason="Successful OTP verification")
        await interaction.response.send_message(
            "✅ Verification successful! You now have the Verified role.",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I can't give you the Verified role. Make sure my bot role is above the Verified role.",
            ephemeral=True
        )

# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    bot.add_view(TicketView())

    guild = discord.Object(id=SERVER_ID)

    try:

        synced = await bot.tree.sync(guild=guild)

        print(
            f"Synced {len(synced)} commands "
            f"to server {SERVER_ID}"
        )

    except Exception as error:

        print(f"Sync error: {error}")


# =========================
# /TICKET
# =========================

@bot.tree.command(
    name="ticket",
    description="Create a private support ticket."
)
async def ticket(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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
            "Please explain what you need help with."
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

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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
# /CLOSE
# =========================

@bot.tree.command(
    name="close",
    description="Close the current ticket."
)
async def close(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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

bot.run(TOKEN)import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord import app_commands
from discord.ext import commands


# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

SERVER_ID = 1538740748709658694

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

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This can only be used in a server.",
                ephemeral=True
            )
            return

        if interaction.guild.id != SERVER_ID:
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
# /VERIFY OTP
# =========================

VERIFY_OTP = os.getenv("VERIFY_OTP")
VERIFIED_ROLE_NAME = "Verified"

@bot.tree.command(name="verify", description="Verify yourself with an OTP.")
@app_commands.describe(otp="Enter your verification OTP.")
async def verify(interaction: discord.Interaction, otp: str):
    if interaction.guild is None:
        await interaction.response.send_message("❌ Use this inside a server.", ephemeral=True)
        return

    if interaction.guild.id != SERVER_ID:
        await interaction.response.send_message("❌ This bot is not configured for this server.", ephemeral=True)
        return

    if not VERIFY_OTP:
        await interaction.response.send_message("❌ Verification is not configured yet.", ephemeral=True)
        return

    if otp.strip() != VERIFY_OTP.strip():
        await interaction.response.send_message("❌ Incorrect or expired OTP.", ephemeral=True)
        return

    role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
    if role is None:
        try:
            role = await interaction.guild.create_role(
                name=VERIFIED_ROLE_NAME,
                reason="Created for bot verification"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to create the Verified role.",
                ephemeral=True
            )
            return

    if role in interaction.user.roles:
        await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
        return

    try:
        await interaction.user.add_roles(role, reason="Successful OTP verification")
        await interaction.response.send_message(
            "✅ Verification successful! You now have the Verified role.",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I can't give you the Verified role. Make sure my bot role is above the Verified role.",
            ephemeral=True
        )

# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    bot.add_view(TicketView())

    guild = discord.Object(id=SERVER_ID)

    try:

        synced = await bot.tree.sync(guild=guild)

        print(
            f"Synced {len(synced)} commands "
            f"to server {SERVER_ID}"
        )

    except Exception as error:

        print(f"Sync error: {error}")


# =========================
# /TICKET
# =========================

@bot.tree.command(
    name="ticket",
    description="Create a private support ticket."
)
async def ticket(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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
            "Please explain what you need help with."
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

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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
# /CLOSE
# =========================

@bot.tree.command(
    name="close",
    description="Close the current ticket."
)
async def close(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside a server.",
            ephemeral=True
        )
        return

    if interaction.guild.id != SERVER_ID:
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
