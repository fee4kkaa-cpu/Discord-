import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# ================= НАСТРОЙКИ =================
DB_PATH = "nebula.db"
# =============================================

# Умный поиск колонки (id или user_id)
def get_id_col():
    conn = sqlite3.connect(DB_PATH)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    conn.close()
    return "user_id" if "user_id" in cols else "id"

# Проверка, существует ли юзер в базе, и создание его при необходимости
def ensure_user(uid):
    id_col = get_id_col()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE {id_col} = ?", (uid,))
    if not cur.fetchone():
        cur.execute(f"INSERT INTO users ({id_col}) VALUES (?)", (uid,))
        conn.commit()
    conn.close()
    return id_col


class EconomyAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 1. ВЫДАТЬ ДЕНЬГИ ---
    @app_commands.command(name="givemoney", description="Выдать монеты пользователю (Админ)")
    @app_commands.describe(member="Кому выдаем?", amount="Сколько монет выдать?")
    @app_commands.default_permissions(administrator=True) # Только для админов!
    async def givemoney(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ Сумма должна быть больше нуля!", ephemeral=True)

        id_col = ensure_user(member.id)
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET balance = balance + ? WHERE {id_col} = ?", (amount, member.id))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="💰 Выдача средств",
            description=f"Администратор {interaction.user.mention} выдал **{amount} 🪙** пользователю {member.mention}.",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)


    # --- 2. ЗАБРАТЬ ДЕНЬГИ ---
    @app_commands.command(name="removemoney", description="Забрать монеты у пользователя (Админ)")
    @app_commands.describe(member="У кого забираем?", amount="Сколько монет забрать?")
    @app_commands.default_permissions(administrator=True)
    async def removemoney(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ Сумма должна быть больше нуля!", ephemeral=True)

        id_col = ensure_user(member.id)
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Получаем текущий баланс, чтобы не уйти в минус
        cur.execute(f"SELECT balance FROM users WHERE {id_col} = ?", (member.id,))
        current_balance = cur.fetchone()[0]
        
        # Если забираем больше, чем есть у игрока, то ставим баланс в 0
        final_amount = amount if current_balance >= amount else current_balance
        
        cur.execute(f"UPDATE users SET balance = balance - ? WHERE {id_col} = ?", (final_amount, member.id))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="📉 Изъятие средств",
            description=f"Администратор {interaction.user.mention} изъял **{final_amount} 🪙** у пользователя {member.mention}.",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed)


    # --- 3. УСТАНОВИТЬ БАЛАНС ---
    @app_commands.command(name="setmoney", description="Установить точный баланс пользователю (Админ)")
    @app_commands.describe(member="Кому устанавливаем?", amount="Новый баланс (можно 0)")
    @app_commands.default_permissions(administrator=True)
    async def setmoney(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount < 0:
            return await interaction.response.send_message("❌ Баланс не может быть отрицательным!", ephemeral=True)

        id_col = ensure_user(member.id)
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET balance = ? WHERE {id_col} = ?", (amount, member.id))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="⚙️ Установка баланса",
            description=f"Баланс пользователя {member.mention} был установлен на **{amount} 🪙** администратором {interaction.user.mention}.",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(EconomyAdmin(bot))
