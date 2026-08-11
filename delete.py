import discord
from discord.ext import commands

class DeleteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Проверяем, что реакция — это мусорный бак
        if str(payload.emoji) == "🗑️":
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            
            # Проверяем, что сообщение отправил бот
            if message.author.id == self.bot.user.id:
                # Удаляем сообщение
                await message.delete()

async def setup(bot):
    await bot.add_cog(DeleteCog(bot))
