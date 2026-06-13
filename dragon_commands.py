# Dragon Rider Commands Module
# Add these commands to your bot.py

async def setup_dragon_commands(bot):
    """Setup all dragon rider game commands"""
    
    @bot.tree.command(name="dragon", description="Dragon Rider game system")
    @app_commands.describe(
        action="Action: info, hatch, eggs, dragons, explore, train, battle, duel, breed, reset, island"
    )
    async def dragon(interaction: discord.Interaction, action: str = "info"):
        """Dragon Rider game - hatch, train, and battle dragons!"""
        
        try:
            action = action.lower()
            user_id = interaction.user.id
            guild_id = interaction.guild.id
            
            if action == "info":
                embed = discord.Embed(
                    title="🐉 Dragon Rider Game Guide",
                    description="A long-term collection and progression game where you hatch, train, and battle dragons!",
                    color=discord.Color.red()
                )
                
                embed.add_field(
                    name="🥚 Getting Started",
                    value="`/dragon hatch` - Get a dragon egg (5 min hatch)\n`/dragon eggs` - View your eggs",
                    inline=False
                )
                
                embed.add_field(
                    name="🐲 Main Commands",
                    value="`/dragon dragons` - View your dragons\n`/dragon island` - View your stats\n`/dragon reset` - Reset all progress",
                    inline=False
                )
                
                embed.add_field(
                    name="⚔️ Action Commands",
                    value="`/dragon explore` - Find rewards (4 min cooldown)\n`/dragon train` - Improve stats (1 hr cooldown)\n`/dragon battle` - Fight PvE enemy\n`/dragon duel @user` - Battle player",
                    inline=False
                )
                
                embed.add_field(
                    name="👶 Breeding",
                    value="`/dragon breed` - Breed two dragons for offspring",
                    inline=False
                )
                
                embed.add_field(
                    name="💎 Egg Rarities",
                    value="**Common** (60%) | **Rare** (25%) | **Epic** (10%) | **Legendary** (4%) | **Alpha** (1%)",
                    inline=False
                )
                
                embed.add_field(
                    name="🏆 Endgame Goals",
                    value="Collect every dragon species • Discover rare hybrids • Max dragon stats • Obtain Alpha Dragons • Become Dragon Master",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "hatch":
                # Check if user has first dragon
                import sqlite3
                conn = sqlite3.connect("bot_data.db")
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM dragons WHERE user_id = ?", (user_id,))
                dragon_count = cursor.fetchone()[0]
                conn.close()
                
                if dragon_count == 0:
                    # First dragon - hatch instantly
                    result = DragonSystem.create_first_egg(user_id, guild_id)
                    embed = discord.Embed(
                        title="🎉 First Dragon Hatched!",
                        description=f"Species: **{result['species']}**\nRarity: **{result['rarity']}**",
                        color=discord.Color.gold()
                    )
                    embed.add_field(name="⚔️ Attack", value=result['stats']['attack'], inline=True)
                    embed.add_field(name="🛡️ Defense", value=result['stats']['defense'], inline=True)
                    embed.add_field(name="⚡ Speed", value=result['stats']['speed'], inline=True)
                    embed.add_field(name="🧠 Intelligence", value=result['stats']['intelligence'], inline=True)
                else:
                    # Regular egg (hatches in 5 min)
                    egg = DragonSystem.hatch_new_egg(user_id, guild_id)
                    embed = discord.Embed(
                        title="🥚 Dragon Egg Received!",
                        description=f"**Rarity:** {egg['rarity']}\n**Hatches in:** 5 minutes",
                        color=discord.Color.gold()
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "eggs":
                eggs = DragonSystem.get_eggs(user_id)
                
                if not eggs:
                    embed = discord.Embed(
                        title="🥚 No Eggs",
                        description="Use `/dragon hatch` to get an egg!",
                        color=discord.Color.blue()
                    )
                else:
                    embed = discord.Embed(
                        title="🥚 Your Dragon Eggs",
                        description=f"Total: **{len(eggs)}**",
                        color=discord.Color.blue()
                    )
                    
                    for i, egg in enumerate(eggs[:10], 1):
                        egg_id, rarity, hatch_time, is_first = egg
                        if is_first:
                            status = "✅ Ready to Hatch!"
                        else:
                            import sqlite3
                            from datetime import datetime
                            remaining = (datetime.fromisoformat(hatch_time) - datetime.utcnow()).total_seconds()
                            if remaining > 0:
                                mins = int(remaining / 60)
                                status = f"⏳ {mins} min remaining"
                            else:
                                status = "✅ Ready to Hatch!"
                        
                        embed.add_field(name=f"{i}. {rarity} Egg", value=status, inline=False)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "dragons":
                dragons = DragonSystem.get_dragons(user_id)
                
                if not dragons:
                    embed = discord.Embed(
                        title="🐉 No Dragons Yet",
                        description="Hatch an egg with `/dragon hatch`!",
                        color=discord.Color.blue()
                    )
                else:
                    embed = discord.Embed(
                        title="🐉 Your Dragons",
                        description=f"Total: **{len(dragons)}**",
                        color=discord.Color.red()
                    )
                    
                    for i, dragon in enumerate(dragons[:10], 1):
                        dragon_id, name, species, rarity, level, xp, attack, defense, speed, intelligence, bond = dragon
                        embed.add_field(
                            name=f"{i}. {species} - {rarity} (Lvl {level})",
                            value=f"⚔️ {attack} | 🛡️ {defense} | ⚡ {speed} | 🧠 {intelligence}",
                            inline=False
                        )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "explore":
                dragons = DragonSystem.get_dragons(user_id)
                if not dragons:
                    embed = discord.Embed(
                        title="❌ No Dragons",
                        description="You need a dragon to explore!",
                        color=discord.Color.red()
                    )
                else:
                    dragon_id = dragons[0][0]  # Use first dragon
                    result = DragonSystem.explore(user_id, guild_id, dragon_id)
                    
                    if "error" in result:
                        embed = discord.Embed(
                            title="⏳ Cooldown",
                            description=result["error"],
                            color=discord.Color.orange()
                        )
                    else:
                        embed = discord.Embed(
                            title="🌍 Dragon Explored!",
                            description=f"Found: **{result['reward']}** x{result['amount']}",
                            color=discord.Color.green()
                        )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "train":
                dragons = DragonSystem.get_dragons(user_id)
                if not dragons:
                    embed = discord.Embed(
                        title="❌ No Dragons",
                        description="You need a dragon to train!",
                        color=discord.Color.red()
                    )
                else:
                    dragon_id = dragons[0][0]
                    result = DragonSystem.train_dragon(user_id, dragon_id)
                    
                    if "error" in result:
                        embed = discord.Embed(
                            title="⏳ Cooldown",
                            description=result["error"],
                            color=discord.Color.orange()
                        )
                    else:
                        embed = discord.Embed(
                            title="🏋️ Dragon Trained!",
                            description=f"{result['stat']} +{result['boost']}",
                            color=discord.Color.green()
                        )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "battle":
                dragons = DragonSystem.get_dragons(user_id)
                if not dragons:
                    embed = discord.Embed(
                        title="❌ No Dragons",
                        description="You need a dragon to battle!",
                        color=discord.Color.red()
                    )
                else:
                    dragon_id = dragons[0][0]
                    result = DragonSystem.battle_pve(user_id, dragon_id)
                    
                    embed = discord.Embed(
                        title="⚔️ Battle Result",
                        description=f"Enemy: **{result['enemy']}** (Lvl {result['enemy_level']})\n\n{result['result']}",
                        color=discord.Color.red() if result['winner'] == 'enemy' else discord.Color.green()
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "duel":
                embed = discord.Embed(
                    title="⚠️ PvP Coming Soon",
                    description="Dragon dueling will be available soon!",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "breed":
                dragons = DragonSystem.get_dragons(user_id)
                if len(dragons) < 2:
                    embed = discord.Embed(
                        title="❌ Need 2 Dragons",
                        description="You need at least 2 dragons to breed!",
                        color=discord.Color.red()
                    )
                else:
                    dragon1_id = dragons[0][0]
                    dragon2_id = dragons[1][0]
                    result = DragonSystem.breed_dragons(user_id, dragon1_id, dragon2_id, guild_id)
                    
                    embed = discord.Embed(
                        title="👶 Breeding Successful!",
                        description=f"{result['message']}\n**Offspring:** {result['species']} ({result['rarity']})",
                        color=discord.Color.magenta()
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif action == "reset":
                # Confirmation
                view = discord.ui.View()
                
                async def confirm_reset(interaction: discord.Interaction):
                    DragonSystem.reset_progress(user_id)
                    embed = discord.Embed(
                        title="✅ Progress Reset",
                        description="Your dragon progress has been reset. Start fresh with `/dragon hatch`!",
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                
                async def cancel_reset(interaction: discord.Interaction):
                    embed = discord.Embed(
                        title="❌ Cancelled",
                        description="Reset cancelled!",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                
                button_confirm = discord.ui.Button(label="Yes, Reset", style=discord.ButtonStyle.danger)
                button_cancel = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
                
                button_confirm.callback = confirm_reset
                button_cancel.callback = cancel_reset
                
                view.add_item(button_confirm)
                view.add_item(button_cancel)
                
                embed = discord.Embed(
                    title="⚠️ Confirm Reset",
                    description="Are you sure? This will delete ALL your dragons and progress!",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
            elif action == "island":
                import sqlite3
                conn = sqlite3.connect("bot_data.db")
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT coins, fish, relics, total_dragons FROM player_dragons WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                conn.close()
                
                if not result:
                    coins, fish, relics, total = 0, 0, 0, 0
                else:
                    coins, fish, relics, total = result
                
                embed = discord.Embed(
                    title="🏝️ Your Dragon Island",
                    description=f"Total Dragons: **{total}**",
                    color=discord.Color.blue()
                )
                embed.add_field(name="💰 Coins", value=coins, inline=True)
                embed.add_field(name="🐟 Fish", value=fish, inline=True)
                embed.add_field(name="📿 Relics", value=relics, inline=True)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            else:
                embed = discord.Embed(
                    title="❌ Unknown Action",
                    description="Use: `info`, `hatch`, `eggs`, `dragons`, `explore`, `train`, `battle`, `breed`, `island`, or `reset`",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        
        except Exception as e:
            print(f"[DRAGON] Error: {str(e)}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


# Initialize dragon tables
DragonSystem.init_tables()
