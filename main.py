import asyncio
import http.server
import os
import threading
import traceback
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
    if bot.user is not None:
        print(f"⚡ SYSTEM ACTIVE: {bot.user.name} is online!")

# 3. Safe Dynamic Cog Loader
async def load_extensions() -> None:
    if not os.path.exists("./cogs"):
        print("❌ CRITICAL: 'cogs' folder not found!")
        return

    for filename in os.listdir("./cogs"):
        # SAFETY SHIELD: Ignore main.py or non-python files if they are accidentally inside 'cogs'
        if filename == "main.py" or not filename.endswith(".py"):
            continue
            
        try:
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"📦 Successfully loaded module: {filename}")
        except Exception as e:
            print(f"❌ ERROR loading module {filename}:")
            traceback.print_exc()

async def main() -> None:
    async with bot:
        await load_extensions()
        if "DISCORD_TOKEN" not in os.environ:
            print("❌ CRITICAL: DISCORD_TOKEN variable is missing from Render environment configuration!")
            return
        await bot.start(os.environ["DISCORD_TOKEN"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as startup_error:
        print("❌ CRITICAL CRASH ON STARTUP:")
        traceback.print_exc()
