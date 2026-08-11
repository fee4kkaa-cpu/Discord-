import discord
from discord.ext import commands
import os
import asyncio
from database import init_db

# ID твоего сервера для мгновенной синхронизации команд
MY_GUILD = discord.Object(id=1527080134094360657) 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

class NebulaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=intents, 
            help_command=None,
            application_id=None # Если бот не видит слэш-команды, вставь сюда ID приложения (Application ID)
        )

    async def setup_hook(self):
        # Инициализация БД
        await init_db()
        print("--- База данных инициализирована ---")

        # Загрузка всех расширений из папки cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"Загружен ког: {filename}")
                except Exception as e:
                    print(f"Ошибка при загрузке {filename}: {e}")
        
        # Синхронизация дерева команд
        try:
            self.tree.copy_global_to(guild=MY_GUILD)
            synced = await self.tree.sync(guild=MY_GUILD)
            print(f"--- Синхронизировано команд: {len(synced)} ---")
        except Exception as e:
            print(f"Ошибка синхронизации: {e}")

bot = NebulaBot()

# Токен бота (лучше использовать переменные окружения)
TOKEN = "MTUzNjc3NTA3OTA4NDQzMzQ5OQ.GdC43h.1w49vHbJpkT_S9OEMlX9iFjM_XxUBjOCSaU27M" 

if __name__ == "__main__":
    bot.run(TOKEN)
