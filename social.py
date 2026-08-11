import discord
from discord.ext import commands
from discord import app_commands
import random

ICEBREAKERS = [
    "Если бы тебе пришлось есть одно блюдо до конца жизни, что бы это было?",
    "Какой твой самый нелепый страх?",
    "Если бы ты мог переместиться в любую эпоху, куда бы ты отправился?",
    "Кошки или собаки? И почему?",
    "Какой фильм ты можешь пересматривать бесконечно?"
]

class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="icebreaker", description="Получить случайный вопрос для начала разговора")
    async def icebreaker(self, interaction: discord.Interaction):
        question = random.choice(ICEBREAKERS)
        embed = discord.Embed(
            title="🧊 Ледокол",
            description=f"**Вопрос:** {question}",
            color=discord.Color.teal()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="crash", description="Отправить анонимную валентинку/сообщение пользователю")
    async def crash(self, interaction: discord.Interaction, member: discord.Member, message: str):
        if member == interaction.user or member.bot:
            return await interaction.response.send_message("❌ Нельзя отправить признание себе или боту.", ephemeral=True)

        embed = discord.Embed(
            title="💌 Анонимная Краш-почта",
            description=f"Кто-то с сервера **{interaction.guild.name}** оставил вам послание:\n\n*«{message}»*",
            color=discord.Color.brand_red()
        )
        embed.set_footer(text="Отправитель остался анонимным. ❤️")

        try:
            await member.send(embed=embed)
            await interaction.response.send_message("✅ Ваше анонимное послание успешно доставлено!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ У пользователя закрыты личные сообщения.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Social(bot))