import discord
from discord.ext import commands

# Use dictionary mapping to permanently force-inject intents past PyCharm settings
intents = discord.Intents.default()
setattr(intents, 'members', True)
setattr(intents, 'message_content', True)

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("====================================")
    current_user = bot.user
    if current_user is not None:
        print(f"🤖 SYSTEM ACTIVE: {current_user.name} is online!")
    print("Connected successfully to Discord.")
    print("====================================")


# noinspection SpellCheckingInspection
@bot.command()
async def inrole(ctx: commands.Context, *, role_name: str = "Status"):
    if ctx.guild is None:
        return

    current_guild = ctx.guild
    assert current_guild is not None

    role = discord.utils.find(lambda r: str(r.name).lower() == role_name.lower(), current_guild.roles)

    if not role:
        await ctx.send(f"❌ Role '{role_name}' not found. Make sure it exists in Discord Server Settings!")
        return

    server_members = list(role.members)

    if not server_members:
        embed = discord.Embed(
            title=f"👑 Status Directory: {str(role.name)}",
            description="Total active operators holding this tier: **0**\n\n*No members currently assigned.*",
            color=discord.Color.from_str("#00FFC4")
        )
        await ctx.send(embed=embed)
        return

    member_list = "\n".join([f"• {str(m.name)}" for m in server_members])

    embed = discord.Embed(
        title=f"👑 Status Directory: {str(role.name)}",
        description=f"Total active operators holding this tier: **{len(server_members)}**\n\n{member_list}",
        color=discord.Color.from_str("#00FFC4")
    )
    await ctx.send(embed=embed)


bot.run('MTUwNzkONTQ0NDcyMzczNDY0.GM9aeB.6OfJyZJehd79-FlAkkLl80ruUc8gXNBzQC4o-M')
