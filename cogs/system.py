import discord
from discord.ext import commands
from discord import app_commands
import sys
import os

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="restart", description="Перезапустить бота (Только для руководства)")
    @app_commands.default_permissions(administrator=True) # Доступно только админам!
    async def restart(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔄 **Выполняю перезапуск системы...** Пожалуйста, подождите пару секунд.", ephemeral=True)
        
        # Эта команда "убивает" текущий процесс и запускает файл main.py заново
        os.execv(sys.executable, ['python'] + sys.argv)

async def setup(bot):
    await bot.add_cog(SystemCog(bot))
