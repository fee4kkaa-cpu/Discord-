import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import math

DB_PATH = "nebula.db"

def init_profile_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, bank INTEGER DEFAULT 0, 
        xp INTEGER DEFAULT 0, voice_time INTEGER DEFAULT 0, messages INTEGER DEFAULT 0,
        bio TEXT DEFAULT 'Я играю на NEBULA!', profile_color TEXT DEFAULT '2f3136'
    )""")
    
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    needed = {
        'balance': 'INTEGER DEFAULT 0', 'bank': 'INTEGER DEFAULT 0',
        'xp': 'INTEGER DEFAULT 0', 'voice_time': 'INTEGER DEFAULT 0', 'messages': 'INTEGER DEFAULT 0',
        'bio': "TEXT DEFAULT 'Я играю на NEBULA!'", 'profile_color': "TEXT DEFAULT '2f3136'"
    }
    for col, dtype in needed.items():
        if col not in columns:
            try: cur.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
            except: pass

    cur.execute("""CREATE TABLE IF NOT EXISTS user_rooms (
        user_id INTEGER PRIMARY KEY, room_name TEXT, channel_id INTEGER
    )""")
    conn.commit()
    conn.close()

def get_id_col():
    conn = sqlite3.connect(DB_PATH)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    conn.close()
    return "user_id" if "user_id" in cols else "id"

def get_user_data(uid):
    id_col = get_id_col()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT balance, bank, xp, voice_time, messages, bio, profile_color FROM users WHERE {id_col} = ?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute(f"INSERT INTO users ({id_col}) VALUES (?)", (uid,))
        conn.commit()
        row = (0, 0, 0, 0, 0, "Я играю на NEBULA!", "2f3136")
    conn.close()
    return row

def generate_xp_bar(xp):
    level = int(0.1 * math.sqrt(xp)) if xp > 0 else 0
    next_level_xp = ((level + 1) / 0.1) ** 2
    current_level_xp = (level / 0.1) ** 2
    progress = (xp - current_level_xp) / (next_level_xp - current_level_xp)
    filled_blocks = int(progress * 10)
    bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
    return level, f"`[{bar}] {int(progress * 100)}%`", int(next_level_xp)

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_profile_db()

    @app_commands.command(name="profile", description="Открыть свой или чужой профиль")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        
        balance, bank, xp, voice_time, messages, bio, profile_color = get_user_data(target.id)
        
        conn = sqlite3.connect(DB_PATH)
        room = conn.execute("SELECT room_name FROM user_rooms WHERE user_id = ?", (target.id,)).fetchone()
        conn.close()

        level, xp_bar, next_xp = generate_xp_bar(xp)
        hours = voice_time // 60
        minutes = voice_time % 60

        try: color = int(profile_color.replace("#", ""), 16)
        except: color = 0x2f3136 

        embed = discord.Embed(title=f"Удостоверение: {target.display_name}", description=f"*{bio}*", color=color)
        if target.avatar: embed.set_thumbnail(url=target.avatar.url)
        
        embed.add_field(name="💳 Финансы", value=f"**Наличные:** `{balance}` 🪙\n**В банке:** `{bank}` 🏦", inline=True)
        embed.add_field(name="📊 Статистика", value=f"**Сообщений:** `{messages}` 💬\n**В войсе:** `{hours}ч {minutes}м` 🎙️", inline=True)
        embed.add_field(name="🏠 Имущество", value=f"**Комната:** {room[0] if room else '`Нет`'}", inline=False)
        embed.add_field(name=f"✨ Уровень: {level}", value=f"{xp_bar} ({xp}/{next_xp} XP)", inline=False)
        embed.set_footer(text=f"ID: {target.id} • N E B U L A", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))

