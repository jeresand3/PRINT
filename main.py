import datetime
import http.server
import io
import os
import re
import threading
import urllib.request
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


# 1. Heartbeat web server to keep Render active
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
        # Open your template background card file locally
        base_img = Image.open("image_bb317f75.png").convert("RGBA")
        
        # Initialize the drawing canvas layer
        draw = ImageDraw.Draw(base_img)
        
        # Load fallback built-in fonts (guaranteed not to crash Render Linux servers)
        font = ImageFont.load_default()
        
        # --- DRAW THE DYNAMIC TEXT ON THE IMAGE ---
        # 1. Target User Name & ID
        draw.text((550, 215), f"USER: @{member.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((550, 255), f"ID: {member.id}", fill="#a0a0a0", font=font, anchor="mm")
        
        # 2. Lower Data Boxes (Moderator, Duration, Reason)
        draw.text((215, 415), f"@{ctx.author.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((550, 415), f"{duration_str}", fill="#ffffff", font=font, anchor="mm")
        draw.text((885, 415), f"{reason}", fill="#ffffff", font=font, anchor="mm")

        # --- DYNAMIC PROFILE PICTURE INJECTION ---
        try:
            # Download target user's real live profile picture using Python's built-in urllib tool
            avatar_url = member.display_avatar.with_format("png").with_size(128).url
            req = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as pfp_res:
                pfp_img = Image.open(io.BytesIO(pfp_res.read())).convert("RGBA")
            
            # Resize avatar to fit perfectly into your top-right circular frame coordinates
            pfp_img = pfp_img.resize((100, 100))
            
            # Create a clean round mask circle for the portrait cut
            mask = Image.new("L", (100, 100), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 100, 100), fill=255)
            
            # Paste the circular avatar into your card's top-right circle placeholder location
            base_img.paste(pfp_img, (830, 60), mask=mask)
        except Exception as pfp_error:
            print(f"Skipping profile avatar drawing layer: {pfp_error}")

        # --- PACKAGE AND SEND THE GRAPHIC ---
        final_buffer = io.BytesIO()
        base_img.save(final_buffer, format="PNG")
        final_buffer.seek(0)
        discord_file = discord.File(fp=final_buffer, filename="dynamic_timeout.png")

        embed = discord.Embed(color=0x2b2d31)
        embed.set_image(url="attachment://dynamic_timeout.png")

        await ctx.send(file=discord_file, embed=embed, view=TimeoutButtons(member))

    except Exception as e:
        await ctx.send(f"⚠️ System Error compiling canvas: `{str(e)}`", view=TimeoutButtons(member))


bot.run(os.environ["DISCORD_TOKEN"])

import datetime
import http.server
import io
import os
import re
import threading
import urllib.request
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


# 1. Heartbeat web server to keep Render active
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
        
        try:
            member_to_untimeout: discord.Member = getattr(self, "target_member")
            await member_to_untimeout.timeout(None)
            await interaction.response.send_message(f"✅ {member_to_untimeout.mention} untimed out early by {interaction.user.mention}!")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot doesn't have permissions to untimeout this user!", ephemeral=True)


@bot.command()
async def timeout(ctx: commands.Context, member: discord.Member, duration_str: str, *, reason: str = "No reason provided"):
    if ctx.guild is None or not isinstance(ctx.author, discord.Member):
        return
    if not is_authorized_staff(ctx.author):
        await ctx.send("❌ Permission denied!")
        return
    
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("❌ Cannot timeout this member! Their role level is equal to or higher than the bot's role.")
        return
    if member == ctx.guild.owner:
        await ctx.send("❌ Cannot timeout the Server Owner!")
        return

    time_delta = parse_duration(duration_str)
    if not time_delta:
        await ctx.send("❌ Use formats like `10h` or `30m`.")
        return

    try:
        await member.timeout(time_delta, reason=reason)
    except discord.Forbidden:
        await ctx.send("❌ Discord API denied this action. Check bot role permissions.")
        return

    try:
        base_img = Image.open("image_bb317f75.png").convert("RGBA")
        draw = ImageDraw.Draw(base_img)
        font = ImageFont.load_default()
        
        # --- DRAW THE DYNAMIC TEXT ON THE IMAGE ---
        draw.text((550, 215), f"USER: @{member.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((550, 255), f"ID: {member.id}", fill="#a0a0a0", font=font, anchor="mm")
        
        draw.text((215, 415), f"@{ctx.author.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((550, 415), f"{duration_str}", fill="#ffffff", font=font, anchor="mm")
        draw.text((885, 415), f"{reason}", fill="#ffffff", font=font, anchor="mm")

        # --- DYNAMIC PROFILE PICTURE INJECTION ---
        try:
            avatar_url = member.display_avatar.with_format("png").with_size(128).url
            req = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as pfp_res:
                pfp_img = Image.open(io.BytesIO(pfp_res.read())).convert("RGBA")
            
            pfp_img = pfp_img.resize((100, 100))
            mask = Image.new("L", (100, 100), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 100, 100), fill=255)
            base_img.paste(pfp_img, (830, 60), mask=mask)
        except Exception as pfp_error:
            print(f"Skipping profile avatar drawing layer: {pfp_error}")

        final_buffer = io.BytesIO()
        base_img.save(final_buffer, format="PNG")
        final_buffer.seek(0)
        discord_file = discord.File(fp=final_buffer, filename="dynamic_timeout.png")

        embed = discord.Embed(color=0x2b2d31)
        embed.set_image(url="attachment://dynamic_timeout.png")

        await ctx.send(file=discord_file, embed=embed, view=TimeoutButtons(member))

    except Exception as e:
        await ctx.send(f"⚠️ System Error compiling canvas: `{str(e)}`", view=TimeoutButtons(member))


# ==================================================
# 💥 EXCLUSIVE OWNER-ONLY NUKE COMMAND
# ==================================================
@bot.command()
async def nuke(ctx: commands.Context):
    if ctx.guild is None or not isinstance(ctx.author, discord.Member):
        return

    # Check if the person using the command is the Server Owner
    if ctx.author != ctx.guild.owner:
        await ctx.send("❌ Security Access Denied: Only the Server Owner can use `$nuke`!")
        return

    current_channel = ctx.channel
    if not isinstance(current_channel, discord.TextChannel):
        return

    # 1. Clone the configuration of the current channel
    new_channel = await current_channel.clone(reason=f"Channel nuked by {ctx.author.name}")
    
    # 2. Place the new clean channel at the exact same location/position
    await new_channel.edit(position=current_channel.position)

    # 3. Permanently erase the old clogged chat history channel
    await current_channel.delete(reason="Nuke command executed.")

    # 4. Post a cool victory confirmation block in the new copy
    embed = discord.Embed(
        title="💥 Channel Nuked",
        description=f"This channel was completely wiped and recreated by {ctx.author.mention}.",
        color=discord.Color.from_str("#00e676")
    )
    embed.set_image(url="https://imgur.com")
    
    # Sends it and auto-deletes the message after 10 seconds to keep it perfectly clean
    await new_channel.send(embed=embed, delete_after=10)


bot.run(os.environ["DISCORD_TOKEN"])
