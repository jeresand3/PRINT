import datetime
import io
import re
import urllib.request
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from typing import Any

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
            # 1. Load your raw template image layer
            raw_img = Image.open("mog.png").convert("RGBA")
            
            # 2. Scale cleanly to crisp 16:9 widescreen dimensions
            target_size = (1920, 1080)
            base_img = raw_img.resize(target_size, Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(base_img)
            font = ImageFont.load_default()
            
            # --- PRECISE POSITIONING COORDINATES FOR 1920x1080 CANVAS ---
            # Center USER box text placement coordinates
            draw.text((1120, 605), f"@{member.name}", fill="#00e676", font=font, anchor="mm")
            draw.text((1120, 655), f"ID: {member.id}", fill="#a0a0a0", font=font, anchor="mm")
            
            # Bottom row modular meta boxes text placement coordinates
            draw.text((580, 890), f"@{ctx.author.name}", fill="#ffffff", font=font, anchor="mm")
            draw.text((965, 890), f"{duration_str}", fill="#ffffff", font=font, anchor="mm")
            draw.text((1350, 890), f"{reason}", fill="#ffffff", font=font, anchor="mm")

            # --- TOP-RIGHT AVATAR GENERATION FRAME LAYER ---
            try:
                avatar_url = member.display_avatar.with_format("png").with_size(512).url
                req = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as pfp_res:
                    pfp_img = Image.open(io.BytesIO(pfp_res.read())).convert("RGBA")
                
                # Scaled to fit perfectly into the top-right frame circle area
                pfp_size = (215, 215)
                pfp_img = pfp_img.resize(pfp_size, Image.Resampling.LANCZOS)
                
                mask = Image.new("L", pfp_size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0.0, 0.0, 215.0, 215.0), fill=255)
                
                # Position coordinates centered directly over the circle graphic vector
                base_img.paste(pfp_img, (1572, 100), mask=mask)
            except Exception as pfp_error:
                print(f"Skipping profile avatar drawing layer: {pfp_error}")

            final_buffer = io.BytesIO()
            base_img.save(final_buffer, format="PNG")
            final_buffer.seek(0)
            discord_file = discord.File(fp=final_buffer, filename="dynamic_timeout.png")

            embed = discord.Embed(color=0x2b2d31)
            embed.set_image(url="attachment://dynamic_timeout.png")

            await ctx.send(embed=embed, file=discord_file, view=TimeoutButtons(member))

        except Exception as e:
            await ctx.send(f"⚠️ System Error compiling canvas: `{str(e)}`", view=TimeoutButtons(member))

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TimeoutCog(bot))
