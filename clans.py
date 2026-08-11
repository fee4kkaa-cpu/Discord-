import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from database import DB_PATH, get_user, update_user

class Clans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    clan = app_commands.Group(name="clan", description="Система синдикатов и кланов")

    @clan.command(name="top", description="Рейтинг самых богатых кланов сервера")
    async def top(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name, balance, level FROM clans ORDER BY balance DESC, level DESC LIMIT 10") as cursor:
                top_clans = await cursor.fetchall()
                
        if not top_clans:
            return await interaction.response.send_message("❌ На сервере пока нет ни одного клана. Станьте первым!", ephemeral=True)

        desc = ""
        for i, (name, balance, level) in enumerate(top_clans, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            desc += f"{medal} **{name}** — 🪙 **{balance}** (Уровень: {level})\n"
            
        embed = discord.Embed(title="🏰 Топ 10 кланов сервера", description=desc, color=0x9b59b6)
        await interaction.response.send_message(embed=embed)

    @clan.command(name="create", description="Создать свой клан (Стоимость: 5000 монет)")
    async def create(self, interaction: discord.Interaction, name: str):
        cost = 5000
        user = await get_user(interaction.user.id)
        
        if not user:
            return await interaction.response.send_message("❌ Вы не зарегистрированы в базе.", ephemeral=True)
            
        if user[8] != 0:
            return await interaction.response.send_message("❌ Вы уже состоите в клане! Сначала покиньте его.", ephemeral=True)
            
        if user[2] < cost:
            return await interaction.response.send_message(f"❌ Недостаточно средств! Создание клана стоит **{cost}** 🪙.", ephemeral=True)
            
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT clan_id FROM clans WHERE name = ?", (name,)) as cursor:
                if await cursor.fetchone():
                    return await interaction.response.send_message("❌ Клан с таким названием уже существует!", ephemeral=True)
            
            await update_user(interaction.user.id, "balance", user[2] - cost)
            await db.execute("INSERT INTO clans (name, owner_id) VALUES (?, ?)", (name, interaction.user.id))
            await db.commit()
            
            async with db.execute("SELECT clan_id FROM clans WHERE name = ?", (name,)) as cursor:
                new_clan_id = (await cursor.fetchone())[0]
                
            await update_user(interaction.user.id, "clan_id", new_clan_id)

        embed = discord.Embed(title="🎉 Клан успешно создан!", description=f"Вы основали клан **«{name}»**.", color=0x2ecc71)
        await interaction.response.send_message(embed=embed)

    @clan.command(name="info", description="Посмотреть статистику вашего клана")
    async def info(self, interaction: discord.Interaction):
        user = await get_user(interaction.user.id)
        clan_id = user[8] if user and user[8] is not None else 0
        
        if clan_id == 0:
            return await interaction.response.send_message("❌ Вы не состоите в клане.", ephemeral=True)
            
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name, owner_id, balance, level FROM clans WHERE clan_id = ?", (clan_id,)) as cursor:
                clan_data = await cursor.fetchone()
                
            if not clan_data:
                return await interaction.response.send_message("❌ Ошибка: клан не найден в базе.", ephemeral=True)
                
            async with db.execute("SELECT COUNT(*) FROM users WHERE clan_id = ?", (clan_id,)) as cursor:
                members_count = (await cursor.fetchone())[0]

        name, owner_id, balance, level = clan_data
        
        embed = discord.Embed(title=f"🏰 Клан: {name}", color=0x3498db)
        embed.add_field(name="Владелец", value=f"<@{owner_id}>", inline=True)
        embed.add_field(name="Участников", value=f"👥 **{members_count}**", inline=True)
        embed.add_field(name="Уровень", value=f"⭐ **{level}**", inline=True)
        embed.add_field(name="Общак (Баланс)", value=f"🪙 **{balance}**", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @clan.command(name="deposit", description="Пожертвовать монеты в общак клана")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ Сумма должна быть больше нуля.", ephemeral=True)
            
        user = await get_user(interaction.user.id)
        clan_id = user[8] if user and user[8] is not None else 0
        
        if clan_id == 0:
            return await interaction.response.send_message("❌ Вы не состоите в клане.", ephemeral=True)
            
        if user[2] < amount:
            return await interaction.response.send_message("❌ Недостаточно наличных средств.", ephemeral=True)
            
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE clans SET balance = balance + ? WHERE clan_id = ?", (amount, clan_id))
            await db.commit()
            
        await update_user(interaction.user.id, "balance", user[2] - amount)
        await interaction.response.send_message(f"💸 Вы пожертвовали **{amount}** 🪙 в общак клана!")

    @clan.command(name="leave", description="Покинуть текущий клан")
    async def leave(self, interaction: discord.Interaction):
        user = await get_user(interaction.user.id)
        clan_id = user[8] if user and user[8] is not None else 0
        
        if clan_id == 0:
            return await interaction.response.send_message("❌ Вы и так не состоите в клане.", ephemeral=True)
            
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT owner_id, name FROM clans WHERE clan_id = ?", (clan_id,)) as cursor:
                clan_data = await cursor.fetchone()
                
        if clan_data:
            owner_id, clan_name = clan_data
            if owner_id == interaction.user.id:
                return await interaction.response.send_message("❌ Вы являетесь лидером клана! Вы не можете просто выйти. Чтобы распустить клан, используйте команду `/clan delete`.", ephemeral=True)
            
            await update_user(interaction.user.id, "clan_id", 0)
            await interaction.response.send_message(f"🚪 Вы успешно покинули клан **{clan_name}**.")
        else:
            await update_user(interaction.user.id, "clan_id", 0)
            await interaction.response.send_message("🚪 Вы покинули клан.", ephemeral=True)

    @clan.command(name="delete", description="Удалить (расформировать) свой клан")
    async def delete(self, interaction: discord.Interaction):
        user = await get_user(interaction.user.id)
        clan_id = user[8] if user and user[8] is not None else 0
        
        if clan_id == 0:
            return await interaction.response.send_message("❌ Вы не состоите в клане.", ephemeral=True)
            
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT owner_id, name FROM clans WHERE clan_id = ?", (clan_id,)) as cursor:
                clan_data = await cursor.fetchone()
                
            if not clan_data:
                return await interaction.response.send_message("❌ Ошибка: клан не найден.", ephemeral=True)
                
            owner_id, clan_name = clan_data
            
            if owner_id != interaction.user.id:
                return await interaction.response.send_message("❌ Только лидер может расформировать клан! Если вы хотите просто выйти, используйте `/clan leave`.", ephemeral=True)
                
            # 1. Выгоняем всех участников (обнуляем их clan_id)
            await db.execute("UPDATE users SET clan_id = 0 WHERE clan_id = ?", (clan_id,))
            # 2. Удаляем сам клан из базы
            await db.execute("DELETE FROM clans WHERE clan_id = ?", (clan_id,))
            await db.commit()
            
        embed = discord.Embed(
            title="💥 Клан расформирован", 
            description=f"Клан **«{clan_name}»** был навсегда удален, а все его участники распущены.", 
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Clans(bot))