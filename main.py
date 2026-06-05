@bot.command()
async def timeout(ctx: commands.Context, member: discord.Member, duration_str: str, *, reason: str = "No reason provided"):
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
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
        # Opens your newly uploaded blank card template
        base_img = Image.open("mog.png").convert("RGBA")
        draw = ImageDraw.Draw(base_img)
        font = ImageFont.load_default()
        
        # --- ADJUSTED DYNAMIC TEXT ALIGNMENT & POSITIONS ---
        # 1. Target User Main Center Box (Shifted down and slightly left to center inside its ornate border)
        draw.text((495, 395), f"USER: @{member.name}", fill="#00e676", font=font, anchor="mm")
        draw.text((495, 435), f"ID: {member.id}", fill="#a0a0a0", font=font, anchor="mm")
        
        # 2. Bottom Row Metric Blocks (Calculated to fall precisely within the boundaries of each individual layout box)
        # Left Box: Moderator Profile Name Info
        draw.text((220, 680), f"MODERATOR:\n@{ctx.author.name}", fill="#00e676", font=font, anchor="mm")
        
        # Center Box: Temporal Penalization Span Duration
        draw.text((495, 680), f"DURATION:\n{duration_str}", fill="#ffffff", font=font, anchor="mm")
        
        # Right Box: Disciplinary Infraction Cause Reason
        draw.text((770, 680), f"REASON:\n{reason}", fill="#ffffff", font=font, anchor="mm")

        # --- DYNAMIC PROFILE PICTURE ALIGNMENT (Top-Right Frame Circle) ---
        try:
            avatar_url = member.display_avatar.with_format("png").with_size(256).url
            req = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as pfp_res:
                pfp_img = Image.open(io.BytesIO(pfp_res.read())).convert("RGBA")
            
            # Resized to fill the decorative portrait frame properly
            pfp_size = (112, 112)
            pfp_img = pfp_img.resize(pfp_size)
            
            # Mask generation for clean circular cropping boundary corners
            mask = Image.new("L", pfp_size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, pfp_size[0], pfp_size[1]), fill=255)
            
            # Positioned to align perfectly over the dark circle layer in the upper-right corner
            base_img.paste(pfp_img, (838, 62), mask=mask)
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
