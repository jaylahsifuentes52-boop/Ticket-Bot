# Discord Ticket Bot for Render

Commands:
- `/panel` — posts a ticket panel with a **Create Ticket** button. Requires Manage Server.
- `/ticket` — immediately creates a private ticket.
- **Close Ticket** button — deletes the ticket channel.

## Render
Create a Python Web Service and use:

Build Command:
`pip install -r requirements.txt`

Start Command:
`python bot.py`

Add this environment variable in Render:

Key:
`DISCORD_TOKEN`

Value:
your Discord bot token

The token is NOT stored in the code.

## Discord bot permissions
Invite the bot with the `bot` and `applications.commands` scopes.
The bot needs permissions including:
- Manage Channels
- View Channels
- Send Messages
- Read Message History
- Embed Links

After inviting it, use `/panel` in the channel where you want the panel.
