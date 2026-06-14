"""
Enhanced Dragon Rider Game System
Includes: Unique abilities, training items, PvP battles
"""

import sqlite3
import random
import uuid
from datetime import datetime, timedelta
import json

DB_PATH = "bot_data.db"

class DragonSystem:
    """Complete Dragon Rider game system with abilities and items"""
    
    DRAGON_ABILITIES = {
        "Gronckle": {
            "name": "Rock Throw",
            "description": "Hurls boulders at opponents",
            "power": 65,
            "accuracy": 85
        },
        "Terrible Terror": {
            "name": "Venomous Bite",
            "description": "Quick venom bite attack",
            "power": 55,
            "accuracy": 90
        },
        "Hideous Zippleback": {
            "name": "Twin Flame Blast",
            "description": "Dual dragon fire attack",
            "power": 75,
            "accuracy": 80
        },
        "Night Fury": {
            "name": "Plasma Blast",
            "description": "Devastating plasma explosion",
            "power": 95,
            "accuracy": 88
        },
        "Deadly Nadder": {
            "name": "Spike Barrage",
            "description": "Shoots razor-sharp spikes",
            "power": 70,
            "accuracy": 85
        },
        "Monstrous Nightmare": {
            "name": "Inferno Breath",
            "description": "Intense fire breath attack",
            "power": 80,
            "accuracy": 82
        },
        "Rumblehorn": {
            "name": "Sonic Stomp",
            "description": "Devastating shockwave",
            "power": 75,
            "accuracy": 80
        },
        "Stormcutter": {
            "name": "Lightning Strike",
            "description": "Calls down lightning",
            "power": 85,
            "accuracy": 83
        },
        "Skrill": {
            "name": "Electrical Discharge",
            "description": "Powerful electrical attack",
            "power": 88,
            "accuracy": 85
        },
        "Snow Wraith": {
            "name": "Blizzard Breath",
            "description": "Freezing ice attack",
            "power": 82,
            "accuracy": 84
        },
        "Bewilderbeast": {
            "name": "Sonic Roar",
            "description": "Devastating sonic blast",
            "power": 92,
            "accuracy": 86
        },
        "Red Death": {
            "name": "Inferno Storm",
            "description": "Catastrophic fire explosion",
            "power": 98,
            "accuracy": 85
        },
        "Screaming Death": {
            "name": "Earthshaker",
            "description": "Massive ground explosion",
            "power": 95,
            "accuracy": 84
        },
        "Titan Wing Night Fury": {
            "name": "Ultimate Plasma",
            "description": "Super-charged plasma blast",
            "power": 100,
            "accuracy": 90
        },
        "Alpha Bewilderbeast": {
            "name": "Alpha Roar",
            "description": "Unmatched sonic power",
            "power": 100,
            "accuracy": 92
        }
    }
    
    TRAINING_ITEMS = {
        "Common": ["Dragon Scales", "Fire Stones", "Meat Scraps"],
        "Rare": ["Mithril Ore", "Dragon Teeth", "Enchanted Herbs"],
        "Epic": ["Legendary Gems", "Phoenix Feathers", "Ancient Bones"],
        "Legendary": ["Stardust", "Divine Crystals", "Mythril Bars"],
        "Alpha": ["Celestial Cores", "Eternal Stones", "Divine Essence"]
    }
    
    DRAGON_SPECIES = {
        "Common": ["Gronckle", "Terrible Terror", "Hideous Zippleback"],
        "Rare": ["Deadly Nadder", "Monstrous Nightmare", "Rumblehorn"],
        "Epic": ["Stormcutter", "Skrill", "Snow Wraith"],
        "Legendary": ["Bewilderbeast", "Red Death", "Screaming Death"],
        "Alpha": ["Titan Wing Night Fury", "Alpha Bewilderbeast"]
    }
    
    DRAGON_STATS = {
        "Night Fury": {"attack": 84, "defense": 72, "speed": 97, "intelligence": 88},
        "Gronckle": {"attack": 70, "defense": 85, "speed": 45, "intelligence": 60},
        "Terrible Terror": {"attack": 65, "defense": 60, "speed": 88, "intelligence": 70},
        "Hideous Zippleback": {"attack": 75, "defense": 75, "speed": 70, "intelligence": 75},
        "Deadly Nadder": {"attack": 78, "defense": 70, "speed": 82, "intelligence": 75},
        "Monstrous Nightmare": {"attack": 80, "defense": 80, "speed": 75, "intelligence": 72},
        "Rumblehorn": {"attack": 76, "defense": 88, "speed": 65, "intelligence": 70},
        "Stormcutter": {"attack": 85, "defense": 75, "speed": 80, "intelligence": 86},
        "Skrill": {"attack": 88, "defense": 68, "speed": 90, "intelligence": 82},
        "Snow Wraith": {"attack": 82, "defense": 78, "speed": 85, "intelligence": 80},
        "Bewilderbeast": {"attack": 90, "defense": 92, "speed": 60, "intelligence": 88},
        "Red Death": {"attack": 95, "defense": 85, "speed": 70, "intelligence": 85},
        "Screaming Death": {"attack": 92, "defense": 88, "speed": 75, "intelligence": 82},
        "Titan Wing Night Fury": {"attack": 95, "defense": 88, "speed": 98, "intelligence": 92},
        "Alpha Bewilderbeast": {"attack": 98, "defense": 98, "speed": 65, "intelligence": 95},
    }
    
    @staticmethod
    def init_tables():
        """Initialize all dragon-related database tables"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dragons (
                dragon_id TEXT PRIMARY KEY,
                user_id INTEGER,
                guild_id INTEGER,
                name TEXT,
                species TEXT,
                rarity TEXT,
                attack INTEGER,
                defense INTEGER,
                speed INTEGER,
                intelligence INTEGER,
                bond_level INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                ability_level INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dragon_eggs (
                egg_id TEXT PRIMARY KEY,
                user_id INTEGER,
                guild_id INTEGER,
                rarity TEXT,
                hatch_time TIMESTAMP,
                is_first_egg INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_dragons (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                coins INTEGER DEFAULT 0,
                fish INTEGER DEFAULT 0,
                relics INTEGER DEFAULT 0,
                total_dragons INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_items (
                item_id TEXT PRIMARY KEY,
                user_id INTEGER,
                item_name TEXT,
                rarity TEXT,
                quantity INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dragon_cooldowns (
                user_id INTEGER,
                action TEXT,
                cooldown_until TIMESTAMP,
                PRIMARY KEY (user_id, action)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pvp_battles (
                battle_id TEXT PRIMARY KEY,
                player1_id INTEGER,
                player2_id INTEGER,
                player1_dragon_id TEXT,
                player2_dragon_id TEXT,
                winner_id INTEGER,
                player1_damage INTEGER DEFAULT 0,
                player2_damage INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def create_first_egg(user_id: int, guild_id: int) -> dict:
        """Create the user's first egg (hatches instantly)"""
        egg_id = str(uuid.uuid4())
        rarity = "Rare"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dragon_eggs (egg_id, user_id, guild_id, rarity, hatch_time, is_first_egg)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (egg_id, user_id, guild_id, rarity, datetime.utcnow()))
        conn.commit()
        conn.close()
        
        return DragonSystem.hatch_egg_instantly(user_id, guild_id, egg_id)
    
    @staticmethod
    def hatch_egg_instantly(user_id: int, guild_id: int, egg_id: str) -> dict:
        """Instantly hatch an egg into a dragon"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT rarity FROM dragon_eggs WHERE egg_id = ? AND user_id = ?", (egg_id, user_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
        
        rarity = result[0]
        species = random.choice(DragonSystem.DRAGON_SPECIES[rarity])
        
        base_stats = DragonSystem.DRAGON_STATS.get(species, {
            "attack": random.randint(60, 85),
            "defense": random.randint(60, 85),
            "speed": random.randint(60, 85),
            "intelligence": random.randint(60, 85)
        })
        
        stats = {k: v + random.randint(-5, 5) for k, v in base_stats.items()}
        
        dragon_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO dragons (dragon_id, user_id, guild_id, name, species, rarity, attack, defense, speed, intelligence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dragon_id, user_id, guild_id, species, species, rarity,
              stats["attack"], stats["defense"], stats["speed"], stats["intelligence"]))
        
        cursor.execute("DELETE FROM dragon_eggs WHERE egg_id = ?", (egg_id,))
        
        cursor.execute("""
            INSERT INTO player_dragons (user_id, guild_id, total_dragons)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET total_dragons = total_dragons + 1
        """, (user_id, guild_id))
        
        conn.commit()
        conn.close()
        
        return {
            "dragon_id": dragon_id,
            "species": species,
            "rarity": rarity,
            "stats": stats
        }
    
    @staticmethod
    def hatch_new_egg(user_id: int, guild_id: int) -> dict:
        """Create a new egg (hatches in 5 minutes)"""
        rarities = {
            "Common": 60,
            "Rare": 25,
            "Epic": 10,
            "Legendary": 4,
            "Alpha": 1
        }
        
        rand = random.randint(1, 100)
        rarity = "Common"
        for r, chance in rarities.items():
            if rand <= chance:
                rarity = r
                break
        
        egg_id = str(uuid.uuid4())
        hatch_time = datetime.utcnow() + timedelta(minutes=5)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dragon_eggs (egg_id, user_id, guild_id, rarity, hatch_time, is_first_egg)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (egg_id, user_id, guild_id, rarity, hatch_time))
        conn.commit()
        conn.close()
        
        return {"egg_id": egg_id, "rarity": rarity, "hatch_time": hatch_time}
    
    @staticmethod
    def get_eggs(user_id: int) -> list:
        """Get all eggs for a user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT egg_id, rarity, hatch_time, is_first_egg
            FROM dragon_eggs
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        eggs = cursor.fetchall()
        conn.close()
        return eggs
    
    @staticmethod
    def get_dragons(user_id: int) -> list:
        """Get all dragons for a user with HP calculations"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dragon_id, name, species, rarity, level, xp, attack, defense, speed, intelligence, bond_level, ability_level
            FROM dragons
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        dragons = cursor.fetchall()
        conn.close()
        
        # Add HP to each dragon
        dragons_with_hp = []
        for dragon in dragons:
            dragon_id, name, species, rarity, level, xp, attack, defense, speed, intelligence, bond_level, ability_level = dragon
            hp = DragonSystem.calculate_dragon_hp(level, defense, rarity)
            dragons_with_hp.append(dragon + (hp,))
        
        return dragons_with_hp
    
    @staticmethod
    def explore(user_id: int, guild_id: int, dragon_id: str) -> dict:
        """Dragon explores and finds rewards (4 min cooldown)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cooldown_until FROM dragon_cooldowns
            WHERE user_id = ? AND action = 'explore'
        """, (user_id,))
        cooldown = cursor.fetchone()
        
        if cooldown:
            remaining = datetime.fromisoformat(cooldown[0]) - datetime.utcnow()
            if remaining.total_seconds() > 0:
                conn.close()
                return {"error": f"Explore again in {int(remaining.total_seconds())} seconds"}
        
        cursor.execute("SELECT rarity FROM dragons WHERE dragon_id = ? AND user_id = ?", (dragon_id, user_id))
        dragon = cursor.fetchone()
        if not dragon:
            conn.close()
            return {"error": "Dragon not found"}
        
        rarity = dragon[0]
        
        # Determine rewards based on rarity
        reward_chances = {
            "Coins": 30,
            "Fish": 25,
            "Relics": 15,
            "Training Item": 20,
            "Dragon Egg": 10
        }
        
        rand = random.randint(1, 100)
        cumulative = 0
        reward_type = "Coins"
        
        for reward, chance in reward_chances.items():
            cumulative += chance
            if rand <= cumulative:
                reward_type = reward
                break
        
        amount = 0
        item_name = None
        
        if reward_type == "Coins":
            amount = random.randint(50, 150)
            if rarity in ["Rare", "Epic", "Legendary", "Alpha"]:
                amount = int(amount * 1.5)
        elif reward_type == "Fish":
            amount = random.randint(1, 5)
            if rarity in ["Rare", "Epic", "Legendary", "Alpha"]:
                amount = int(amount * 1.5)
        elif reward_type == "Relics":
            amount = random.randint(1, 3)
            if rarity in ["Rare", "Epic", "Legendary", "Alpha"]:
                amount = int(amount * 1.5)
        elif reward_type == "Training Item":
            item_name = random.choice(DragonSystem.TRAINING_ITEMS[rarity])
            amount = random.randint(1, 3)
            cursor.execute("""
                INSERT INTO training_items (item_id, user_id, item_name, rarity, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), user_id, item_name, rarity, amount))
        elif reward_type == "Dragon Egg":
            amount = 1
            new_egg = DragonSystem.hatch_new_egg(user_id, guild_id)
        
        # Update rewards
        if reward_type in ["Coins", "Fish", "Relics"]:
            cursor.execute(f"""
                UPDATE player_dragons
                SET {reward_type.lower()} = {reward_type.lower()} + ?
                WHERE user_id = ?
            """, (amount, user_id))
        
        # Set cooldown (4 minutes)
        cooldown_time = datetime.utcnow() + timedelta(minutes=4)
        cursor.execute("""
            INSERT INTO dragon_cooldowns (user_id, action, cooldown_until)
            VALUES (?, 'explore', ?)
            ON CONFLICT(user_id, action) DO UPDATE SET cooldown_until = ?
        """, (user_id, cooldown_time, cooldown_time))
        
        conn.commit()
        conn.close()
        
        result = {
            "reward": reward_type,
            "amount": amount,
            "rarity": rarity
        }
        
        if item_name:
            result["item_name"] = item_name
        
        return result
    
    @staticmethod
    def train_dragon(user_id: int, dragon_id: str, item_name: str = None) -> dict:
        """Train a dragon using training items"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get dragon
        cursor.execute("""
            SELECT attack, defense, speed, intelligence, rarity, ability_level FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (dragon_id, user_id))
        dragon = cursor.fetchone()
        
        if not dragon:
            conn.close()
            return {"error": "Dragon not found"}
        
        attack, defense, speed, intelligence, rarity, ability_level = dragon
        
        # Determine required item based on rarity and ability level
        required_item = DragonSystem.TRAINING_ITEMS[rarity][min(ability_level, len(DragonSystem.TRAINING_ITEMS[rarity]) - 1)]
        
        if not item_name:
            item_name = required_item
        
        # Check if player has the item
        cursor.execute("""
            SELECT quantity FROM training_items
            WHERE user_id = ? AND item_name = ?
        """, (user_id, item_name))
        item = cursor.fetchone()
        
        if not item or item[0] < 1:
            conn.close()
            return {"error": f"You need **{required_item}** to train this dragon! You don't have any."}
        
        # Use the item
        cursor.execute("""
            UPDATE training_items
            SET quantity = quantity - 1
            WHERE user_id = ? AND item_name = ?
        """, (user_id, item_name))
        
        # Train the dragon
        stat_names = ["attack", "defense", "speed", "intelligence"]
        boosted_stat = random.choice(stat_names)
        boost = random.randint(2, 5)
        
        cursor.execute(f"""
            UPDATE dragons
            SET {boosted_stat} = {boosted_stat} + ?, xp = xp + 50, ability_level = ability_level + 1
            WHERE dragon_id = ?
        """, (boost, dragon_id))
        
        conn.commit()
        conn.close()
        
        return {
            "stat": boosted_stat.capitalize(),
            "boost": boost,
            "item_used": item_name,
            "ability_level_up": True
        }
    
    @staticmethod
    def battle_pve(user_id: int, dragon_id: str) -> dict:
        """Battle a random enemy dragon"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT attack, defense, speed, intelligence, level, rarity, species FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (dragon_id, user_id))
        player_dragon = cursor.fetchone()
        
        if not player_dragon:
            conn.close()
            return {"error": "Dragon not found"}
        
        player_attack, player_defense, player_speed, player_intelligence, player_level, player_rarity, player_species = player_dragon
        
        # Create random enemy
        enemy_level = random.randint(1, 5)
        enemy_species = random.choice(list(DragonSystem.DRAGON_STATS.keys()))
        enemy_base = DragonSystem.DRAGON_STATS[enemy_species]
        
        enemy_stats = {
            "attack": enemy_base["attack"] + (enemy_level * 2),
            "defense": enemy_base["defense"] + (enemy_level * 2),
            "speed": enemy_base["speed"] + (enemy_level * 1),
            "intelligence": enemy_base["intelligence"] + (enemy_level * 1)
        }
        
        # Calculate battle power
        player_power = (player_attack + player_defense + player_speed + player_intelligence) + (player_level * 5)
        enemy_power = (enemy_stats["attack"] + enemy_stats["defense"] + enemy_stats["speed"] + enemy_stats["intelligence"]) + (enemy_level * 5)
        
        player_power += random.randint(-20, 20)
        enemy_power += random.randint(-20, 20)
        
        player_wins = player_power > enemy_power
        
        if player_wins:
            coins = random.randint(50, 150)
            xp = random.randint(30, 80)
            cursor.execute("""
                UPDATE dragons SET xp = xp + ? WHERE dragon_id = ?
            """, (xp, dragon_id))
            cursor.execute("""
                UPDATE player_dragons SET coins = coins + ? WHERE user_id = ?
            """, (coins, user_id))
            result = f"🎉 You won! +{xp} XP, +{coins} Coins"
        else:
            coins = random.randint(10, 50)
            xp = random.randint(5, 20)
            cursor.execute("""
                UPDATE dragons SET xp = xp + ? WHERE dragon_id = ?
            """, (xp, dragon_id))
            cursor.execute("""
                UPDATE player_dragons SET coins = coins + ? WHERE user_id = ?
            """, (coins, user_id))
            result = f"😢 You lost! +{xp} XP, +{coins} Coins (consolation)"
        
        conn.commit()
        conn.close()
        
        player_ability = DragonSystem.DRAGON_ABILITIES.get(player_species, {})
        
        return {
            "enemy": enemy_species,
            "enemy_level": enemy_level,
            "result": result,
            "winner": "player" if player_wins else "enemy",
            "player_ability": player_ability.get("name", "Unknown"),
            "enemy_ability": DragonSystem.DRAGON_ABILITIES.get(enemy_species, {}).get("name", "Unknown")
        }
    
    @staticmethod
    def battle_pvp(user_id: int, opponent_id: int, user_dragon_id: str, opponent_dragon_id: str) -> dict:
        """Battle another player's dragon"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT attack, defense, speed, intelligence, level, rarity, species FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (user_dragon_id, user_id))
        user_dragon = cursor.fetchone()
        
        cursor.execute("""
            SELECT attack, defense, speed, intelligence, level, rarity, species FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (opponent_dragon_id, opponent_id))
        opponent_dragon = cursor.fetchone()
        
        if not user_dragon or not opponent_dragon:
            conn.close()
            return {"error": "Dragon not found"}
        
        # Calculate power with rarity bonus
        rarity_bonus = {"Common": 1.0, "Rare": 1.2, "Epic": 1.4, "Legendary": 1.6, "Alpha": 1.8}
        
        user_power = (sum(user_dragon[:4]) + (user_dragon[4] * 5)) * rarity_bonus.get(user_dragon[5], 1.0)
        opponent_power = (sum(opponent_dragon[:4]) + (opponent_dragon[4] * 5)) * rarity_bonus.get(opponent_dragon[5], 1.0)
        
        user_power += random.randint(-30, 30)
        opponent_power += random.randint(-30, 30)
        
        user_wins = user_power > opponent_power
        
        if user_wins:
            coins = random.randint(100, 300)
            xp = random.randint(50, 150)
            cursor.execute("""
                UPDATE dragons SET xp = xp + ? WHERE dragon_id = ?
            """, (xp, user_dragon_id))
            cursor.execute("""
                UPDATE player_dragons SET coins = coins + ? WHERE user_id = ?
            """, (coins, user_id))
            result = f"🏆 You won! +{xp} XP, +{coins} Coins"
        else:
            coins = random.randint(30, 100)
            xp = random.randint(20, 50)
            cursor.execute("""
                UPDATE dragons SET xp = xp + ? WHERE dragon_id = ?
            """, (xp, user_dragon_id))
            cursor.execute("""
                UPDATE player_dragons SET coins = coins + ? WHERE user_id = ?
            """, (coins, user_id))
            result = f"😢 You lost! +{xp} XP, +{coins} Coins (consolation)"
        
        # Record battle
        battle_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO pvp_battles (battle_id, player1_id, player2_id, player1_dragon_id, player2_dragon_id, winner_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (battle_id, user_id, opponent_id, user_dragon_id, opponent_dragon_id, user_id if user_wins else opponent_id))
        
        conn.commit()
        conn.close()
        
        user_ability = DragonSystem.DRAGON_ABILITIES.get(user_dragon[6], {})
        opponent_ability = DragonSystem.DRAGON_ABILITIES.get(opponent_dragon[6], {})
        
        return {
            "user_dragon": user_dragon[6],
            "opponent_dragon": opponent_dragon[6],
            "user_ability": user_ability.get("name", "Unknown"),
            "opponent_ability": opponent_ability.get("name", "Unknown"),
            "result": result,
            "winner": user_id if user_wins else opponent_id,
            "user_power": int(user_power),
            "opponent_power": int(opponent_power)
        }
    
    @staticmethod
    def calculate_dragon_hp(level: int, defense: int, rarity: str) -> int:
        """Calculate total HP for a dragon based on level and defense"""
        rarity_bonus = {"Common": 1.0, "Rare": 1.2, "Epic": 1.4, "Legendary": 1.6, "Alpha": 1.8}
        bonus = rarity_bonus.get(rarity, 1.0)
        hp = int((level * 20 + defense) * bonus)
        return max(50, hp)  # Minimum 50 HP
    
    @staticmethod
    def calculate_ability_damage(species: str, ability_name: str, attack: int, level: int, speed: int, intelligence: int) -> int:
        """Calculate damage for a specific ability based on dragon stats"""
        if species not in DragonSystem.DRAGON_ABILITIES:
            return 0
        
        ability = DragonSystem.DRAGON_ABILITIES[species]
        base_power = ability.get("power", 50)
        
        # Damage calculation based on stats
        # Attack contributes 40%, Level contributes 30%, Speed contributes 20%, Intelligence contributes 10%
        damage = (attack * 0.4) + (level * 3 * 0.3) + (speed * 0.2) + (intelligence * 0.1)
        damage = int(damage + base_power)
        
        # Add randomness (±15%)
        variance = int(damage * 0.15)
        damage = damage + random.randint(-variance, variance)
        
        return max(10, damage)  # Minimum 10 damage
    
    @staticmethod
    def simulate_battle_turn(attacker_stats: dict, defender_stats: dict, ability_power: int) -> dict:
        """Simulate a single turn of battle"""
        # Calculate accuracy
        accuracy = random.randint(1, 100)
        
        # Base accuracy for abilities is 80-90%
        if accuracy > 85:
            # Miss!
            return {
                "hit": False,
                "damage": 0,
                "message": "❌ Attack missed!"
            }
        
        # Calculate damage
        damage = ability_power
        
        # Defense reduces damage by 10-20%
        damage_reduction = int(damage * (attacker_stats.get("defense", 50) / 100) * 0.2)
        final_damage = max(5, damage - damage_reduction)
        
        return {
            "hit": True,
            "damage": final_damage,
            "message": f"💥 Hit for **{final_damage}** damage!"
        }
    
    @staticmethod
    def breed_dragons(user_id: int, dragon1_id: str, dragon2_id: str, guild_id: int) -> dict:
        """Breed two dragons to create offspring"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT species, rarity FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (dragon1_id, user_id))
        dragon1 = cursor.fetchone()
        
        cursor.execute("""
            SELECT species, rarity FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (dragon2_id, user_id))
        dragon2 = cursor.fetchone()
        
        if not dragon1 or not dragon2:
            conn.close()
            return {"error": "Dragons not found"}
        
        offspring_rarity = dragon1[1] if random.random() > 0.5 else dragon2[1]
        offspring_species = dragon1[0] if random.random() > 0.5 else dragon2[0]
        
        if random.random() < 0.05:
            rarities = ["Common", "Rare", "Epic", "Legendary", "Alpha"]
            offspring_rarity = random.choice(rarities)
            offspring_species = f"{dragon1[0]} + {dragon2[0]}"
        
        egg = DragonSystem.hatch_new_egg(user_id, guild_id)
        
        conn.close()
        
        return {
            "species": offspring_species,
            "rarity": offspring_rarity,
            "egg_id": egg["egg_id"],
            "message": "🐣 Hybrid dragon egg created!" if "+" in offspring_species else "🐣 Dragon egg created!"
        }
    
    @staticmethod
    def reset_progress(user_id: int) -> bool:
        """Reset all progress for a user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM dragons WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM dragon_eggs WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM player_dragons WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM training_items WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM dragon_cooldowns WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def get_inventory(user_id: int) -> dict:
        """Get player inventory including training items"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT coins, fish, relics FROM player_dragons WHERE user_id = ?
        """, (user_id,))
        resources = cursor.fetchone()
        
        cursor.execute("""
            SELECT item_name, rarity, quantity FROM training_items WHERE user_id = ?
        """, (user_id,))
        items = cursor.fetchall()
        
        conn.close()
        
        return {
            "coins": resources[0] if resources else 0,
            "fish": resources[1] if resources else 0,
            "relics": resources[2] if resources else 0,
            "training_items": items or []
        }
