import discord
from discord.ext import commands
from discord import app_commands
import random
from database import get_user, update_user, DB_PATH
import aiosqlite

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user) # 1 раз в 60 сек

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Проверка кулдауна на получение XP
        bucket = self.cooldowns.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return

        xp_to_add = random.randint(15, 25)
        user_data = await get_user(message.author.id)
        
        if not user_data:
            return
            
        current_xp = user_data[4]
        current_level = user_data[5]
        
        if current_xp is None:
            current_xp = 0
        if current_level is None:
            current_level = 0
            
        new_xp = current_xp + xp_to_add
        xp_needed = 5 * (current_level ** 2) + 50 * current_level + 100

        if new_xp >= xp_needed:
            new_level = current_level + 1
            new_xp -= xp_needed
            await update_user(message.author.id, "level", new_level)
            await message.channel.send(f"🎉 {message.author.mention} достиг **{new_level}** уровня!")

        await update_user(message.author.id, "xp", new_xp)

    @app_commands.command(name="rank", description="Посмотреть свой или чужой ранг")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user_data = await get_user(target.id)
        
        xp = user_data[4] if user_data and user_data[4] is not None else 0
        level = user_data[5] if user_data and user_data[5] is not None else 0
        
        xp_needed = 5 * (level ** 2) + 50 * level + 100

        embed = discord.Embed(title=f"🏆 Ранг: {target.display_name}", color=0x2b2d31)
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
        
        embed.add_field(name="Уровень", value=f"**{level}**", inline=True)
        embed.add_field(name="Опыт (XP)", value=f"**{xp} / {xp_needed}**", inline=True)
        
        progress = int((xp / xp_needed) * 10) if xp_needed > 0 else 0
        bar = "█" * progress + "░" * (10 - progress)
        embed.add_field(name="Прогресс", value=f"`{bar}`", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Посмотреть топ сервера по уровням или богатству")
    @app_commands.choices(category=[
        app_commands.Choice(name="🏆 По уровням (Активность)", value="level"),
        app_commands.Choice(name="💰 По богатству (Баланс + Банк)", value="wealth")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: app_commands.Choice[str]):
        await interaction.response.defer() # Бот "думает", чтобы успеть загрузить список из базы
        
        async with aiosqlite.connect(DB_PATH) as db:
            if category.value == "level":
                # Сортируем по уровню и опыту
                async with db.execute("SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC LIMIT 10") as cursor:
                    top_users = await cursor.fetchall()
                
                embed = discord.Embed(title="🏆 Топ 10 игроков по уровню", color=0x2b2d31)
                
                if not top_users:
                    embed.description = "Пока никто не получил опыта."
                else:
                    desc = ""
                    for i, row in enumerate(top_users, 1):
                        user_id, level, xp = row
                        user = interaction.guild.get_member(user_id)
                        name = user.display_name if user else f"Игрок (ID: {user_id})"
                        
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
                        desc += f"{medal} **{name}** — Уровень: **{level}** (XP: {xp})\n"
                    embed.description = desc

            elif category.value == "wealth":
                # Сортируем по общей сумме (наличные + банк)
                async with db.execute("SELECT user_id, balance, bank, (balance + bank) as total FROM users ORDER BY total DESC LIMIT 10") as cursor:
                    top_users = await cursor.fetchall()
                
                embed = discord.Embed(title="💰 Топ 10 самых богатых игроков", color=0xf1c40f)
                
                if not top_users:
                    embed.description = "В экономике пока нет богачей."
                else:
                    desc = ""
                    for i, row in enumerate(top_users, 1):
                        user_id, balance, bank, total = row
                        user = interaction.guild.get_member(user_id)
                        name = user.display_name if user else f"Игрок (ID: {user_id})"
                        
                        total_sum = total if total is not None else 0
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
                        desc += f"{medal} **{name}** — **{total_sum}** 🪙\n"
                    embed.description = desc
            
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Levels(bot))