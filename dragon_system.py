"""
Dragon Rider Game System for Discord Bot
Complete game with hatching, training, battling, exploring, breeding
"""

import sqlite3
import random
import uuid
from datetime import datetime, timedelta
import json

DB_PATH = "bot_data.db"

class DragonSystem:
    """Complete Dragon Rider game system"""
    
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
    
    EXPLORE_REWARDS = {
        "Coins": [50, 150],
        "Fish": [1, 5],
        "Ancient Relics": [1, 3],
        "Dragon Egg": [1, 1],
        "Trash": [0, 0]
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
            CREATE TABLE IF NOT EXISTS dragon_cooldowns (
                user_id INTEGER,
                action TEXT,
                cooldown_until TIMESTAMP,
                PRIMARY KEY (user_id, action)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dragon_battles (
                battle_id TEXT PRIMARY KEY,
                user_id INTEGER,
                opponent_id INTEGER,
                user_dragon_id TEXT,
                opponent_dragon_id TEXT,
                winner_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def create_first_egg(user_id: int, guild_id: int) -> dict:
        """Create the user's first egg (hatches instantly)"""
        egg_id = str(uuid.uuid4())
        rarity = "Rare"  # First egg is always Rare
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dragon_eggs (egg_id, user_id, guild_id, rarity, hatch_time, is_first_egg)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (egg_id, user_id, guild_id, rarity, datetime.utcnow()))
        conn.commit()
        conn.close()
        
        # Automatically hatch first egg
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
        
        # Get base stats and add variation
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
        
        # Update player stats
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
        """Get all dragons for a user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dragon_id, name, species, rarity, level, xp, attack, defense, speed, intelligence, bond_level
            FROM dragons
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        dragons = cursor.fetchall()
        conn.close()
        return dragons
    
    @staticmethod
    def explore(user_id: int, guild_id: int, dragon_id: str) -> dict:
        """Dragon explores and finds rewards (4 min cooldown)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check cooldown
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
        
        # Get dragon rarity for better loot
        cursor.execute("SELECT rarity FROM dragons WHERE dragon_id = ? AND user_id = ?", (dragon_id, user_id))
        dragon = cursor.fetchone()
        if not dragon:
            conn.close()
            return {"error": "Dragon not found"}
        
        rarity = dragon[0]
        
        # Determine rewards based on rarity
        reward_type = random.choices(
            list(DragonSystem.EXPLORE_REWARDS.keys()),
            weights=[30, 25, 15, 20, 10]  # Coins, Fish, Relics, Eggs, Trash
        )[0]
        
        amount = random.randint(*DragonSystem.EXPLORE_REWARDS[reward_type])
        
        # Rare dragons find better loot
        if rarity in ["Rare", "Epic", "Legendary", "Alpha"]:
            amount = int(amount * 1.5)
        
        # Update rewards
        if reward_type in ["Coins", "Fish", "Relics"]:
            cursor.execute(f"""
                UPDATE player_dragons
                SET {reward_type.lower()} = {reward_type.lower()} + ?
                WHERE user_id = ?
            """, (amount, user_id))
        elif reward_type == "Dragon Egg":
            # Create new egg from exploring
            new_egg = DragonSystem.hatch_new_egg(user_id, guild_id)
            amount = "1 Egg"
        
        # Set cooldown (4 minutes)
        cooldown_time = datetime.utcnow() + timedelta(minutes=4)
        cursor.execute("""
            INSERT INTO dragon_cooldowns (user_id, action, cooldown_until)
            VALUES (?, 'explore', ?)
            ON CONFLICT(user_id, action) DO UPDATE SET cooldown_until = ?
        """, (user_id, cooldown_time, cooldown_time))
        
        conn.commit()
        conn.close()
        
        return {
            "reward": reward_type,
            "amount": amount,
            "rarity": rarity
        }
    
    @staticmethod
    def train_dragon(user_id: int, dragon_id: str) -> dict:
        """Train a dragon to improve stats"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check cooldown (1 hour between training)
        cursor.execute("""
            SELECT cooldown_until FROM dragon_cooldowns
            WHERE user_id = ? AND action = 'train'
        """, (user_id,))
        cooldown = cursor.fetchone()
        
        if cooldown:
            remaining = datetime.fromisoformat(cooldown[0]) - datetime.utcnow()
            if remaining.total_seconds() > 0:
                conn.close()
                return {"error": f"Train again in {int(remaining.total_seconds() / 60)} minutes"}
        
        # Get dragon
        cursor.execute("""
            SELECT attack, defense, speed, intelligence FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (dragon_id, user_id))
        stats = cursor.fetchone()
        
        if not stats:
            conn.close()
            return {"error": "Dragon not found"}
        
        # Random stat boost
        stat_names = ["attack", "defense", "speed", "intelligence"]
        boosted_stat = random.choice(stat_names)
        boost = random.randint(1, 4)
        
        cursor.execute(f"""
            UPDATE dragons
            SET {boosted_stat} = {boosted_stat} + ?, xp = xp + 50
            WHERE dragon_id = ?
        """, (boost, dragon_id))
        
        # Set cooldown
        cooldown_time = datetime.utcnow() + timedelta(hours=1)
        cursor.execute("""
            INSERT INTO dragon_cooldowns (user_id, action, cooldown_until)
            VALUES (?, 'train', ?)
            ON CONFLICT(user_id, action) DO UPDATE SET cooldown_until = ?
        """, (user_id, cooldown_time, cooldown_time))
        
        conn.commit()
        conn.close()
        
        return {
            "stat": boosted_stat.capitalize(),
            "boost": boost
        }
    
    @staticmethod
    def battle_pve(user_id: int, dragon_id: str) -> dict:
        """Battle a random enemy dragon"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get player dragon
        cursor.execute("""
            SELECT attack, defense, speed, intelligence, level FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (dragon_id, user_id))
        player_dragon = cursor.fetchone()
        
        if not player_dragon:
            conn.close()
            return {"error": "Dragon not found"}
        
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
        
        # Calculate winner based on stats
        player_power = sum(player_dragon[:4]) + (player_dragon[4] * 5)
        enemy_power = sum(enemy_stats.values()) + (enemy_level * 5)
        
        # Add randomness
        player_power += random.randint(-20, 20)
        enemy_power += random.randint(-20, 20)
        
        player_wins = player_power > enemy_power
        
        # Give rewards
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
        
        return {
            "enemy": enemy_species,
            "enemy_level": enemy_level,
            "result": result,
            "winner": "player" if player_wins else "enemy"
        }
    
    @staticmethod
    def battle_pvp(user_id: int, opponent_id: int, user_dragon_id: str, opponent_dragon_id: str) -> dict:
        """Battle another player's dragon"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get both dragons
        cursor.execute("""
            SELECT attack, defense, speed, intelligence, level, rarity FROM dragons
            WHERE dragon_id = ? AND user_id = ?
        """, (user_dragon_id, user_id))
        user_dragon = cursor.fetchone()
        
        cursor.execute("""
            SELECT attack, defense, speed, intelligence, level, rarity FROM dragons
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
        
        # Add randomness
        user_power += random.randint(-30, 30)
        opponent_power += random.randint(-30, 30)
        
        user_wins = user_power > opponent_power
        
        # Give rewards
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
        
        conn.commit()
        conn.close()
        
        return {
            "result": result,
            "winner": user_id if user_wins else opponent_id
        }
    
    @staticmethod
    def breed_dragons(user_id: int, dragon1_id: str, dragon2_id: str, guild_id: int) -> dict:
        """Breed two dragons to create offspring"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get both dragons
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
        
        # Offspring is random parent or hybrid
        offspring_rarity = dragon1[1] if random.random() > 0.5 else dragon2[1]
        offspring_species = dragon1[0] if random.random() > 0.5 else dragon2[0]
        
        # Rare chance of hybrid with better rarity
        if random.random() < 0.05:  # 5% chance
            rarities = ["Common", "Rare", "Epic", "Legendary", "Alpha"]
            offspring_rarity = random.choice(rarities)
            offspring_species = f"{dragon1[0]} + {dragon2[0]}"
        
        # Create egg for offspring
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
        cursor.execute("DELETE FROM dragon_cooldowns WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return True
