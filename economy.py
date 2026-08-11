import discord
from discord.ext import commands
from discord import app_commands
import re

class CustomRoleModal(discord.ui.Modal, title="Создание кастомной роли"):
    role_name = discord.ui.TextInput(
        label="Название роли",
        placeholder="Введите название (макс. 32 символа)",
        max_length=32
    )
    
    role_color = discord.ui.TextInput(
        label="Цвет роли (HEX-код)",
        placeholder="Например: #FF0000 для красного",
        max_length=7,
        min_length=6
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Простая проверка HEX формата через регулярное выражение
        hex_match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', self.role_color.value)
        if not hex_match:
            return await interaction.response.send_message("Неверный формат цвета! Используйте формат #RRGGBB.", ephemeral=True)

        # Здесь должна быть проверка баланса Nebula coin пользователя в БД
        # Если коинов хватает - списываем их

        color = discord.Color.from_str(self.role_color.value)
        
        try:
            # Создаем роль
            new_role = await interaction.guild.create_role(
                name=self.role_name.value,
                color=color,
                reason=f"Покупка кастомной роли пользователем {interaction.user.name}"
            )
            # Выдаем пользователю
            await interaction.user.add_roles(new_role)
            await interaction.response.send_message(f"Роль {new_role.mention} успешно создана и выдана вам!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("У бота нет прав на создание ролей. Проверьте иерархию!", ephemeral=True)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_role", description="Купить кастомную роль за Nebula coin")
    async def buy_role(self, interaction: discord.Interaction):
        # Открываем модальное окно при вызове команды
        await interaction.response.send_modal(CustomRoleModal())

async def setup(bot):
    await bot.add_cog(Economy(bot))