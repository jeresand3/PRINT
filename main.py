# noinspection PyUnresolvedReferences
import datetime
import http.server
import os
import re
import threading
import discord
from discord.ext import commands

# 1. Create a tiny heartbeat web server to stop Railway from killing the bot
class HeartbeatHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"SYSTEM ONLINE")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    # noinspection PyTypeChecker
    server = http.server.HTTPServer(('0.0.0.0', port), HeartbeatHandler)
    server.serve_forever()

# Start the web heartbeat in a background loop thread
threading.Thread(target=run_web_server, daemon=True).start()

# 2. Setup access privileges using standard dictionary mapping
intents = discord.Intents.default()
setattr(intents, 'members', True)
setattr(intents, 'message_content', True)

# Changed prefix strictly to $ as requested
bot = commands.Bot(command_prefix="$", intents=intents)

# Helper function to parse human time formats like "10h", "30m", "1d" into actual time durations
def parse_duration(duration_str: str) -> datetime.timedelta | None:
    match = re.match(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    amount, unit = int(match.group(1)), match.group(2)
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    return datetime.timedelta(**{units[unit]: amount})

@bot.event
async def on_ready():
    current_user = bot.user
    if current_user is not None:
        print(f"⚡ SYSTEM ACTIVE: {current_user.name} is online!")
        print("Connected successfully to Discord.")
        print("==================================================")

# noinspection PySpellChecking
@bot.command()
async def inrole(ctx: commands.Context, *, role_name: str = "Status"):
    if ctx.guild is None:
        return
        
    current_guild = ctx.guild
    assert current_guild is not None
    
    role = discord.utils.find(lambda r: str(r.name).lower() == role_name.lower(), current_guild.roles)
    
    if not role:
        await ctx.send(f"❌ Role '{role_name}' not found. Make sure it exists in Discord Server Settings!")
        return
        
    server_members = list(role.members)
    
    if not server_members:
        embed = discord.Embed(
            title=f"👑 Status Directory: {str(role.name)}",
            description="Total active operators holding this tier: **0**\n\nNo members currently assigned.",
            color=discord.Color.from_str("#00FFC4")
        )
        await ctx.send(embed=embed)
        return
        
    member_list = "\n".join([f"• {str(m.name)}" for m in server_members])
    
    embed = discord.Embed(
        title=f"👑 Status Directory: {str(role.name)}",
        description=f"Total active operators holding this tier: **{len(server_members)}**\n\n{member_list}",
        color=discord.Color.from_str("#00FFC4")
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx: commands.Context, member: discord.Member, duration_str: str, *, reason: str = "No reason provided"):
    if ctx.guild is None:
        return

    time_delta = parse_duration(duration_str)
    if not time_delta:
        await ctx.send("❌ Invalid duration format! Use formats like `10h`, `30m`, or `1d`.")
        return

    # Apply native Discord timeout restrictions
    await member.timeout(time_delta, reason=reason)

    # Build the visual card layout
    embed = discord.Embed(
        title="⏱️ User Timed Out",
        description=f"**{member.name}** has been timed out.",
        color=discord.Color.from_str("#FEE75C")
    )
    embed.set_thumbnail(url="https://ibb.co") 
    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
    embed.add_field(name="Duration", value=duration_str, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Method", value="Staff Permission", inline=False)
    embed.set_footer(text=f"User ID: {member.id} | PRINT Bot")

    # Create interactive button click handlers
    class TimeoutButtons(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        # noinspection PySpellChecking
        @discord.ui.button(label="Untimeout", style=discord.ButtonStyle.green)
        async def untimeout_callback(self, interaction: discord.Interaction, _button: discord.ui.Button):
            if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message("❌ Staff only permission!", ephemeral=True)
                return
            
            await member.timeout(None) 
            await interaction.response.send_message(f"✅ {member.mention} has been untimed out early by {interaction.user.mention}!")

    await ctx.send(embed=embed, view=TimeoutButtons())

# Securely grab the token from the environment variable configuration
bot.run(os.environ["DISCORD_TOKEN"])
