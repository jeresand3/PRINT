import discord
from discord.ext import commands
import http.server
import threading
import os

# 1. Create a tiny heartbeat web server to stop Railway from killing the bot
class HeartbeatHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"SYSTEM ONLINE")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = http.server.HTTPServer(('0.0.0.0', port), HeartbeatHandler)
    server.serve_forever()

# Start the web heartbeat in a background loop thread
threading.Thread(target=run_web_server, daemon=True).start()

# 2. Setup access privileges using standard dictionary mapping
intents = discord.Intents.default()
setattr(intents, 'members', True)
setattr(intents, 'message_content', True)

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    current_user = bot.user
    if current_user is not None:
        print(f"⚡ SYSTEM ACTIVE: {current_user.name} is online!")
        print("Connected successfully to Discord.")
        print("==================================================")

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

# Securely grab the token from Railway's environment variables
bot.run(os.environ.get("DISCORD_TOKEN"))
