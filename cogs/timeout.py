import datetime
import io
import re
import urllib.request
import discord
from discord.ext import commands
from PIL import Image, ImageDraw
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
        self.target_member: discord.Member = target_member

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
            base_img = Image.new("RGBA", (1000, 500), "#1e1f22")
            draw = ImageDraw.Draw(base_img)
            
            # Formatted with explicit floats to silence Python 3.14 sequence expectations
            draw.rectangle([10.0, 10.0, 990.0, 490.0], outline="#00e676", width=4)
            draw.line([40.0, 260.0, 960.0, 260.0], fill="#313338", width=3)
            
            draw.text((280, 110), f"ISOLATED: @{member.name}", fill="#00e676", anchor="lm")
            draw.text((280, 170), f"ID: {member.id}", fill="#949ba4", anchor="lm")
            
            draw.text((180, 330), "MODERATOR", fill="#00e676", anchor="mm")
            draw.text((180, 390), f"@{ctx.author.name}", fill="#ffffff", anchor="mm")
            
            draw.text((500, 330), "DURATION", fill="#00e676", anchor="mm")
            draw.text((500, 390), f"{duration_str}", fill="#ffffff", anchor="mm")
            
            draw.text((820, 330), "REASON", fill="#00e676", anchor="mm")
            draw.text((820, 390), f"{reason}", fill="#ffffff", anchor="mm")

            try:
                avatar_url = member.display_avatar.with_format("png").with_size(256).url
                req = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as pfp_res:
                    pfp_img = Image.open(io.BytesIO(pfp_res.read())).convert("RGBA")
                
                pfp_size = (150, 150)
                pfp_img = pfp_img.resize(pfp_size)
                
                mask = Image.new("L", pfp_size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0.0, 0.0, 150.0, 150.0), fill=255)
                
                base_img.paste(pfp_img, (80, 65), mask=mask)
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
