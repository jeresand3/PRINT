import os
import http.server
import threading
import discord
from discord.ext import commands

# 1. Mandatory Render Compliance Web Server
class HeartbeatHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"SYSTEM ONLINE")
    def log_message(self, format_str: str, *args: any) -> None:
        return

def run_web_server() -> None:
    port = int(os.environ.get("PORT", 8080))
    server = http.server.HTTPServer(('0.0.0.0', port), HeartbeatHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# 2. Basic Bot Setup
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready() -> None:
    if bot.user is not None:
        print(f"⚡ SYSTEM ACTIVE: {bot.user.name} is officially online!")

# 3. Simple Test Command
@bot.command()
async def ping(ctx: commands.Context) -> None:
    await ctx.send("💰 Pong! System is operational.")

token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ DISCORD_TOKEN variable is missing from your environment variables!")
