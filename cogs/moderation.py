import discord
from discord.ext import commands

def is_authorized_staff(member: discord.Member) -> bool:
    allowed_roles = {"owner", "administrator", "sub administrator", "staff access"}
    return any(role.name.lower() in allowed_roles for role in member.roles)

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="lock")
    async def lock(self, ctx: commands.Context):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        if not is_authorized_staff(ctx.author):
            await ctx.send("❌ Permission denied!")
            return

        current_channel = ctx.channel
        if not isinstance(current_channel, discord.TextChannel):
            return

        try:
            await current_channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=f"Channel locked by {ctx.author.name}")
            await ctx.send(f"🔒 **{current_channel.mention} has been locked down.**")
        except discord.Forbidden:
            await ctx.send("❌ I lack the required permissions to lock this channel.")

    @commands.command(name="unlock")
    async def unlock(self, ctx: commands.Context):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        if not is_authorized_staff(ctx.author):
            await ctx.send("❌ Permission denied!")
            return

        current_channel = ctx.channel
        if not isinstance(current_channel, discord.TextChannel):
            return

        try:
            await current_channel.set_permissions(ctx.guild.default_role, send_messages=None, reason=f"Channel unlocked by {ctx.author.name}")
            await ctx.send(f"🔓 **{current_channel.mention} is now unlocked.**")
        except discord.Forbidden:
            await ctx.send("❌ I lack the required permissions to unlock this channel.")

    @commands.command(name="nuke")
    async def nuke(self, ctx: commands.Context):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        if ctx.author != ctx.guild.owner:
            await ctx.send("❌ Security Access Denied: Only the Server Owner can use `$nuke`!")
            return

        current_channel = ctx.channel
        if not isinstance(current_channel, discord.TextChannel):
            return

        announcements_channel = discord.utils.get(ctx.guild.text_channels, name="announcements")
        new_channel = await current_channel.clone(reason=f"Channel nuked by {ctx.author.name}")
        await new_channel.edit(position=current_channel.position)
        await current_channel.delete(reason="Nuke command executed.")

        if announcements_channel is not None:
            await announcements_channel.send(
                f"🔔 **Attention:** #{new_channel.name} has been cleared. Head over here -> {new_channel.mention}!"
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
