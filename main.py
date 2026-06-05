import datetime
import http.server
import io
import os
import re
import traceback
import sys
import threading
import urllib.request
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


# ==================================================
# 🌐 WEB SERVER FOR RENDER HOSTING COMPLIANCE
# ==================================================
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
    print(f"🌐 Compliance Web Server listening on port {port}...")
    server.serve_forever()


threading.Thread(target=run_web_server, daemon=True).start()

# ==================================================
# ⚙️ BOT CORE CONFIGURATION & PERMISSIONS
# ==================================================
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

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
async def on_ready() -> None:
    if bot.user is not None:
        print(f"⚡ SYSTEM ACTIVE: {bot.user.name} is online and processing '$' commands!")


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
    print(f"❌ Command Error Detected: {error}")
    if isinstance(error, commands.CommandNotFound):
        return  
    try:
        await ctx.send(f"⚠️ **Bot Error:** `{str(error)}`")
    except discord.Forbidden:
        pass


class TimeoutButtons(discord.ui.View):
    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=None)
        self.target_member = target_member

    @discord.ui.button(label="Untimeout", style=discord.ButtonStyle.green)
    async def untimeout_callback(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        user_member = interaction.user
        if isinstance(user_member, discord.Member) and not is_authorized_staff(user_member):
            await interaction.response.send_message("❌ Staff only permission!", ephemeral=True)
            return
        
        try:
            await self.target_member.timeout(None)
            await interaction.response.send_message(f"✅ {self.target_member.mention} untimed out early by {interaction.user.mention}!")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot doesn't have permissions to untimeout this user!", ephemeral=True)


# ==================================================
# ⏰ PREFIX COMMAND: $TIMEOUT
# ==================================================
@bot.command()
async def timeout(ctx: commands.Context, member: discord.Member, duration_str: str, *, reason: str = "No reason provided") -> None:
    if ctx.guild is None or not isinstance(ctx.author, discord.Member):
        return
    
    if not is_authorized_staff(ctx.author):
        await ctx.send("❌ Permission denied! You do not have an authorized staff role.")
        return
    
    if ctx.guild.me is not None and member.top_role >= ctx.guild.me.top_role:
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
        
        draw.text((550, 215), f"USER: @{member.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((550, 255), f"ID: {member.id}", fill="#a0a0a0", font=font, anchor="mm")
        
        draw.text((215, 415), f"@{ctx.author.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((550, 415), f"{duration_str}", fill="#ffffff", font=font, anchor="mm")
        draw.text((885, 415), f"{reason}", fill="#ffffff", font=font, anchor="mm")

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
# 🔒 PREFIX COMMAND: $LOCK
# ==================================================
@bot.command()
async def lock(ctx: commands.Context, *, reason: str = "Spam/Inappropriate content cleanup") -> None:
    if ctx.guild is None or not isinstance(ctx.author, discord.Member) or not isinstance(ctx.channel, discord.TextChannel):
        return
    if not is_authorized_staff(ctx.author):
        await ctx.send("❌ Permission denied! You do not have an authorized staff role.")
        return

    try:
        default_role = ctx.guild.default_role
        overwrite = ctx.channel.overwrites_for(default_role)
        
        # Safe raw configuration layout bypasses editor warnings
        overwrite.update(send_messages=False)
        
        await ctx.channel.set_permissions(default_role, overwrite=overwrite, reason=f"Locked by {ctx.author.name}")
        
        embed = discord.Embed(
            title="🔒 Channel Locked", 
            description=f"This channel has been temporarily locked by staff.\n**Reason:** {reason}", 
            color=0xff5555
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ The bot does not have permissions to manage channel permissions.")
    except Exception as e:
        await ctx.send(f"⚠️ Lock Error: `{str(e)}`")


# ==================================================
# 🔓 PREFIX COMMAND: $UNLOCK
# ==================================================
@bot.command()
async def unlock(ctx: commands.Context) -> None:
    if ctx.guild is None or not isinstance(ctx.author, discord.Member) or not isinstance(ctx.channel, discord.TextChannel):
        return
    if not is_authorized_staff(ctx.author):
        await ctx.send("❌ Permission denied! You do not have an authorized staff role.")
        return

    try:
        default_role = ctx.guild.default_role
        overwrite = ctx.channel.overwrites_for(default_role)
        
        overwrite.update(send_messages=None)
        
        await ctx.channel.set_permissions(default_role, overwrite=overwrite, reason=f"Unlocked by {ctx.author.name}")
        
        embed = discord.Embed(
            title="🔓 Channel Unlocked", 
            description="Chat restrictions lifted. You may speak freely again.", 
            color=0x55ff55
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ The bot does not have permissions to manage channel permissions.")
    except Exception as e:
        await ctx.send(f"⚠️ Unlock Error: `{str(e)}`")


# ==================================================
# 💥 PREFIX COMMAND: $NUKE (SERVER OWNER ONLY)
# ==================================================
@bot.command()
async def nuke(ctx: commands.Context) -> None:
    if ctx.guild is None or ctx.author != ctx.guild.owner or not isinstance(ctx.channel, discord.TextChannel):
        return

    try:
        announcements_channel = discord.utils.get(ctx.guild.text_channels, name="announcements")
        new_channel = await ctx.channel.clone(reason=f"Channel nuked by {ctx.author.name}")
        
        await new_channel.edit(position=ctx.channel.position)
        await ctx.channel.delete(reason="Nuke command executed.")

        if announcements_channel is not None:
            await announcements_channel.send(
                f"🔔 **Attention:** #{new_channel.name} has been cleared. Head over here -> {new_channel.mention}!"
            )
    except Exception as e:
        print(f"Nuke error: {e}")


