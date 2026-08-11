import discord
from discord.ext import commands

class VoiceRooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ID канала-хаба "➕ Создать комнату"
        self.hub_channel_id = 123456789012345678 
        self.active_rooms = []

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Если пользователь зашел в хаб
        if after.channel and after.channel.id == self.hub_channel_id:
            category = after.channel.category
            # Создаем приватный канал
            new_channel = await category.create_voice_channel(
                name=f"Комната {member.display_name}",
                user_limit=2 # Лимит по умолчанию
            )
            # Перемещаем пользователя
            await member.move_to(new_channel)
            self.active_rooms.append(new_channel.id)
            
            # В реальном проекте здесь отправляется Embed с панелью управления (Кнопки Lock, Rename, Kick) в текстовый чат

        # Если пользователь вышел из канала, и это была созданная нами комната
        if before.channel and before.channel.id in self.active_rooms:
            if len(before.channel.members) == 0:
                await before.channel.delete()
                self.active_rooms.remove(before.channel.id)

async def setup(bot):
    await bot.add_cog(VoiceRooms(bot))