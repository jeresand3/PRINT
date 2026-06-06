import datetime
import io
import re
import urllib.request
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from typing import Any, Optional

def is_authorized_staff(member: Any) -> bool:
    allowed_roles = {"owner", "administrator", "sub administrator", "staff access"}
    return any(role.name.lower() in allowed_roles for role in member.roles)

def parse_duration(duration_str: str) -> datetime.timedelta | None:
    match = re.match(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    amount, unit = int(match.group(1)), match.group(2)
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    return datetime.timedelta(**{units[unit]: amount})

class TimeoutButtons(discord.ui.View):
    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=None)
        self.target_member = target_member

    # noinspection PyUnusedLocal
    @discord.ui.button(label="Untimeout", style=discord.ButtonStyle.green)
    async def untimeout_callback(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
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

class TimeoutCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Fixed: Explicit type hinting tells PyCharm this can store byte data safely
        self.font_bytes: Optional[bytes] = None
        
        try:
            font_url = "https://github.com"
            req = urllib.request.Request(font_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                self.font_bytes = response.read()
            print("📥 Successfully loaded dynamic web font asset configuration package into local memory!")
        except Exception as font_load_error:
            print(f"⚠️ Dynamic remote asset handshake failure fallback engaged: {font_load_error}")

    @commands.command(name="timeout")
    async def timeout(self, ctx: Any, member: discord.Member, duration_str: str, *, reason: str = "No reason provided") -> None:
        if not ctx.guild or not ctx.author:
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
            raw_img = Image.open("Screenshot 2026-06-05 at 17.48.15.png").convert("RGBA")
            
            target_size = (1920, 1080)
            base_img = raw_img.resize(target_size, Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(base_img)
            
            # Fixed: Enforced strict validation guard check to guarantee that font_bytes is never None
            if self.font_bytes is not None:
                font_user = ImageFont.truetype(io.BytesIO(self.font_bytes), 45)
                font_id = ImageFont.truetype(io.BytesIO(self.font_bytes), 26)
                font_metrics = ImageFont.truetype(io.BytesIO(self.font_bytes), 40)
            else:
                font_user = font_id = font_metrics = ImageFont.load_default()

            # --- 🎯 100% EXACT COORDINATE GRID (PRECISE CENTER BALANCING) ---
            draw.text((865, 395), f"@{member.name}", fill="#00e676", font=font_user, anchor="mm")
            draw.text((865, 445), f"ID: {member.id}", fill="#a0a0a0", font=font_id, anchor="mm")
            
            draw.text((438, 700), f"@{ctx.author.name}", fill="#00e676", font=font_metrics, anchor="mm")
            draw.text((865, 700), f"{duration_str}", fill="#ffffff", font=font_metrics, anchor="mm")
            
            clean_reason = reason if len(reason) <= 22 else f"{reason[:19]}..."
            draw.text((1295, 700), f"{clean_reason}", fill="#ffffff", font=font_metrics, anchor="mm")

            # --- 🖼️ TOP-RIGHT CIRCULAR PORTRAIT AVATAR PLACEMENT ---
            try:
                avatar_url = member.display_avatar.with_format("png").with_size(512).url
                req = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as pfp_res:
                    pfp_img = Image.open(io.BytesIO(pfp_res.read())).convert("RGBA")
                
                pfp_size = (200, 200)
                pfp_img = pfp_img.resize(pfp_size, Image.Resampling.LANCZOS)
                
                mask = Image.new("L", pfp_size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0.0, 0.0, 200.0, 200.0), fill=255)
                
                base_img.paste(pfp_img, (1624, 116), mask=mask)
            except Exception as pfp_error:
                print(f"Skipping profile avatar drawing layer: {pfp_error}")

            final_buffer = io.BytesIO()
            base_img.save(final_buffer, format="PNG")
            final_buffer.seek(0)
            discord_file = discord.File(fp=final_buffer, filename="dynamic_timeout.png")

            await ctx.send(file=discord_file, view=TimeoutButtons(member))

        except Exception as e:
            await ctx.send(f"⚠️ System Error compiling canvas: `{str(e)}`", view=TimeoutButtons(member))

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TimeoutCog(bot))
