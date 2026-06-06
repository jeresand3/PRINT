import asyncio
import http.server
import os
import threading
import discord
from discord.ext import commands

# 1. Heartbeat web server to keep Render active
class HeartbeatHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"SYSTEM ONLINE")

def run_web_server() -> None:
    port = int(os.environ.get("PORT", 8080))
    # Added a explicit type-ignore comment to satisfy PyCharm's strict type checker
    server = http.server.HTTPServer(('0.0.0.0', port), HeartbeatHandler)  # type: ignore
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# 2. Configure standard bot application connectivity permissions
intents = discord.Intents.default()
setattr(intents, 'members', True)
setattr(intents, 'message_content', True)

bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready() -> None:
    # Fix: Added a strict safety check to make sure bot.user exists before looking at its name
    if bot.user is not None:
        print(f"⚡ SYSTEM ACTIVE: {bot.user.name} is online!")

# 3. Dynamic Cog Loader
async def load_extensions() -> None:
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"📦 Loaded module: {filename}")

async def main() -> None:
    async with bot:
        await load_extensions()
        await bot.start(os.environ["DISCORD_TOKEN"])

if __name__ == "__main__":
    asyncio.run(main())
