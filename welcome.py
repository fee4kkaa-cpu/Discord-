import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # ЗАМЕНИТЬ НА ID РОЛИ И КАНАЛА:
        role_id = ""  
        channel_id = "" 
        
        role = member.guild.get_role(role_id)
        if role:
            await member.add_roles(role)

        channel = member.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(title="👋 Новый участник", color=0x2b2d31)
            embed.description = f"Пользователь {member.mention} присоединился к серверу."
            embed.add_field(name="Выдана роль", value=f"{role.mention}")
            embed.add_field(name="Верификация", value="Для быстрой верификации: `!в`\nИли вручную: `!вера @ник М/Ж`", inline=False)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))