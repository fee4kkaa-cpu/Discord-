import discord
from discord.ext import commands
import re

# Список запрещенных слов (добавь свои)
BAD_WORDS = ["дурак", "спам", "scam", "казино"] 

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_regex = re.compile(r"(https?://\S+)")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Игнорируем администраторов
        if message.author.guild_permissions.manage_messages:
            return

        content_lower = message.content.lower()

        # 1. Анти-мат / Плохие слова
        if any(word in content_lower for word in BAD_WORDS):
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, пожалуйста, следите за языком!", delete_after=5)
            except discord.Forbidden:
                pass
            return

        # 2. Анти-реклама (Ссылки на другие Discord серверы)
        if "discord.gg/" in content_lower or "discord.com/invite/" in content_lower:
            try:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, реклама других серверов запрещена!", delete_after=5)
            except discord.Forbidden:
                pass
            return

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
