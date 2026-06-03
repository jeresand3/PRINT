import datetime
import http.server
import io
import os
import re
import threading
import requests
import discord
from discord.ext import commands


# 1. Heartbeat web server to keep the hosting platform active
class HeartbeatHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"SYSTEM ONLINE")


# noinspection PyPep8Naming
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    # noinspection PyTypeChecker
    server = http.server.HTTPServer(('0.0.0.0', port), HeartbeatHandler)
    server.serve_forever()


threading.Thread(target=run_web_server, daemon=True).start()

# 2. Configure standard bot application connectivity permissions
intents = discord.Intents.default()
setattr(intents, 'members', True)
setattr(intents, 'message_content', True)

bot = commands.Bot(command_prefix="$", intents=intents)


def is_authorized_staff(member: discord.Member) -> bool:
    allowed_roles = {"owner", "administrator", "sub administrator", "staff access"}
    return any(role.name.lower() in allowed_roles for role in member.roles)


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


# Operational view structure providing a single early-release option button
class TimeoutButtons(discord.ui.View):
    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=None)
        self.target_member: discord.Member = target_member

    # noinspection PySpellChecking
    @discord.ui.button(label="Untimeout", style=discord.ButtonStyle.green)
    async def untimeout_callback(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            return
            
        if not is_authorized_staff(interaction.user):
            await interaction.response.send_message("❌ Staff only permission!", ephemeral=True)
            return
        
        member_to_untimeout: discord.Member = getattr(self, "target_member")
        await member_to_untimeout.timeout(None)
        await interaction.response.send_message(f"✅ {member_to_untimeout.mention} untimed out early by {interaction.user.mention}!")


@bot.command()
async def timeout(ctx: commands.Context, member: discord.Member, duration_str: str, *, reason: str = "No reason provided"):
    if ctx.guild is None or not isinstance(ctx.author, discord.Member):
        return
    if not is_authorized_staff(ctx.author):
        await ctx.send("❌ Permission denied!")
        return
    time_delta = parse_duration(duration_str)
    if not time_delta:
        await ctx.send("❌ Use formats like `10h` or `30m`.")
        return

    # Trigger native platform restriction APIs
    await member.timeout(time_delta, reason=reason)

    try:
        # 1. Fetch the raw asset image data into live system memory streams
        img_url = "https://githubusercontent.com"
        response = requests.get(img_url, timeout=10)
        
        # 2. Package the stream as a direct attachment to bypass Discord's URL cache glitch
        image_stream = io.BytesIO(response.content)
        discord_file = discord.File(fp=image_stream, filename="timeout_card.png")

        # 3. Embed references the direct attachment structure cleanly
        embed = discord.Embed(color=discord.Color.from_str("#0d0f11"))
        embed.set_image(url="attachment://timeout_card.png")

        # Post single image message container block along with the operational button
        await ctx.send(file=discord_file, embed=embed, view=TimeoutButtons(member))

    except Exception as e:
        print(f"Attachment processing fallback trigger: {e}")
        backup_embed = discord.Embed(description=f"**{member.name}** timed out.", color=discord.Color.from_str("#00e676"))
        await ctx.send(embed=backup_embed, view=TimeoutButtons(member))


bot.run(os.environ["DISCORD_TOKEN"])
