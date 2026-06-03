import datetime
import http.server
import io
import os
import re
import threading
import requests
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


# 1. Heartbeat web server to keep the hosting platform active
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


# noinspection PySpellChecking
@bot.command()
async def inrole(ctx: commands.Context, *, role_name: str = "Status"):
    if ctx.guild is None:
        return
    current_guild = ctx.guild
    # noinspection PyProtectedMember
    role = discord.utils.find(lambda r: str(r.name).lower() == role_name.lower(), current_guild.roles)
    if not role:
        await ctx.send(f"❌ Role '{role_name}' not found.")
        return
    server_members = list(role.members)
    if not server_members:
        embed = discord.Embed(title=f"Directory: {str(role.name)}", description="0 operators active.", color=discord.Color.from_str("#00FFC4"))
        await ctx.send(embed=embed)
        return
    member_list = "\n".join([f"• {str(m.name)}" for m in server_members])
    embed = discord.Embed(title=f"Directory: {str(role.name)}", description=f"Total: {len(server_members)}\n\n{member_list}", color=discord.Color.from_str("#00FFC4"))
    await ctx.send(embed=embed)


# Operational view structure providing a single early-release option button
class TimeoutButtons(discord.ui.View):
    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=None)
        self.target_member: discord.Member = target_member

    # noinspection PySpellChecking
    @discord.ui.button(label="Untimeout", style=discord.ButtonStyle.green)
    async def untimeout_callback(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not is_authorized_staff(interaction.user):
            await interaction.response.send_message("❌ Staff only permission!", ephemeral=True)
            return
        await self.target_member.timeout(None)
        await interaction.response.send_message(f"✅ {self.target_member.mention} untimed out early by {interaction.user.mention}!")


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
        # Pull your newly uploaded card asset directly from the GitHub repository CDN path
        img_url = "https://githubusercontent.com"
        response = requests.get(img_url, timeout=10)
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
            small_font = ImageFont.truetype("DejaVuSans.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Dynamic overlay placement plots perfectly centered matching your box layout grids
        # 1. Main target user placement container fields
        draw.text((550, 215), f"@{member.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((550, 255), f"ID: {member.id}", fill="#ffffff", font=small_font, anchor="mm")
        
        # 2. Lower category container data slots (Moderator, Duration, Reason)
        draw.text((215, 415), f"@{ctx.author.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((550, 415), f"{duration_str}", fill="#ffffff", font=font, anchor="mm")
        draw.text((885, 415), f"{reason}", fill="#ffffff", font=small_font, anchor="mm")

        # Compile final structural frame buffer data arrays
        final_buffer = io.BytesIO()
        img.save(final_buffer, format="PNG")
        final_buffer.seek(0)
        discord_file = discord.File(final_buffer, filename="timeout_card_output.png")

        embed = discord.Embed(color=discord.Color.from_str("#0d0f11"))
        embed.set_image(url="attachment://timeout_card_output.png")

        await ctx.send(file=discord_file, embed=embed, view=TimeoutButtons(member))

    except Exception as e:
        print(f"Drawing pipeline error fallback log execution: {e}")
        backup_embed = discord.Embed(description=f"**{member.name}** timed out. Image failed.", color=discord.Color.from_str("#00e676"))
        await ctx.send(embed=backup_embed, view=TimeoutButtons(member))


bot.run(os.environ["DISCORD_TOKEN"])
