import discord
from discord.ext import commands
from discord import app_commands
from database import get_user

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stats", description="Посмотреть красивую профильную статистику")
    async def stats(self, interaction: discord.Interaction, member: discord.Member = None):
        # Если пользователь не указан, показываем стату того, кто вызвал команду
        member = member or interaction.user
        
        # Получаем данные из твоей MySQL базы
        user_data = await get_user(member.id)
        
        if not user_data:
            return await interaction.response.send_message("❌ Пользователь пока не зарегистрирован в базе данных.", ephemeral=True)

        # Вывод в консоль для проверки индексов (удали эту строку, когда настроишь)
        print(f"Данные из БД для {member.display_name}: {user_data}")

        # --- НАСТРОЙКА ИНДЕКСОВ БД ---
        # Поменяй цифры в скобках на те, что соответствуют колонкам в твоей БД,
        # опираясь на то, что выведется в консоль.
        money = user_data[1] if len(user_data) > 1 else 0
        level = user_data[2] if len(user_data) > 2 else 1
        xp = user_data[3] if len(user_data) > 3 else 0
        partner_id = user_data[7] if len(user_data) > 7 else 0

        # Формируем статус отношений
        if partner_id != 0:
            partner_text = f"<@{partner_id}> 💍"
        else:
            partner_text = "Одинок(а) 💔"

        # Цвет берется из высшей роли пользователя на сервере
        embed_color = member.color if member.color != discord.Color.default() else discord.Color.blurple()
        
        embed = discord.Embed(
            title=f"📊 Профиль: {member.display_name}",
            description="Статистика и информация об игроке.",
            color=embed_color
        )
        
        # Аватарка в правом верхнем углу
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        # Блок "Финансы и Прогресс"
        embed.add_field(name="💰 Баланс", value=f"**{money}** монет", inline=True)
        embed.add_field(name="🏆 Уровень", value=f"**{level}** lvl (XP: {xp})", inline=True)
        
        # Пустое поле для ровного отображения сетки
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        # Блок "Социальная жизнь"
        embed.add_field(name="❤️ Отношения", value=partner_text, inline=True)
        
        # Блок "Серверная инфа"
        joined_at = member.joined_at.strftime("%d.%m.%Y") if member.joined_at else "Неизвестно"
        embed.add_field(name="📅 На сервере с", value=joined_at, inline=True)

        # Футер
        request_avatar = interaction.user.avatar.url if interaction.user.avatar else None
        embed.set_footer(text=f"Запросил: {interaction.user.display_name}", icon_url=request_avatar)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(StatsCog(bot))