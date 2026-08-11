import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from database import get_user, update_user

TRIVIA_QUESTIONS = [
    {"q": "Какой язык программирования назван в честь комик-группы?", "opts": ["Python", "Java", "C++", "Ruby"], "ans": 0},
    {"q": "В каком году вышел Discord?", "opts": ["2013", "2015", "2017", "2018"], "ans": 1},
    {"q": "Какая компания разработала игру Minecraft?", "opts": ["Valve", "Epic Games", "Mojang", "Blizzard"], "ans": 2}
]

class TriviaView(discord.ui.View):
    def __init__(self, q_data):
        super().__init__(timeout=30)
        self.ans_idx = q_data["ans"]
        
        for i, opt in enumerate(q_data["opts"]):
            btn = discord.ui.Button(label=opt, custom_id=f"ans_{i}", style=discord.ButtonStyle.secondary)
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if index == self.ans_idx:
                user = await get_user(interaction.user.id)
                await update_user(interaction.user.id, "balance", user[2] + 100)
                await interaction.response.send_message(f"🎉 {interaction.user.mention} ответил правильно и заработал **100** 🪙!")
            else:
                await interaction.response.send_message(f"❌ {interaction.user.mention} ошибся! Правильный ответ был: **{self.children[self.ans_idx].label}**")
            
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)
        return callback

class FunUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LOG_DELETED_CHANNEL_ID = 1526720936315719730 # Замени на ID твоего канала логов

    # --- ВИКТОРИНА ---
    @app_commands.command(name="trivia", description="Сыграть в викторину на монеты")
    async def trivia(self, interaction: discord.Interaction):
        q_data = random.choice(TRIVIA_QUESTIONS)
        view = TriviaView(q_data)
        embed = discord.Embed(title="🧠 Викторина!", description=q_data["q"], color=discord.Color.brand_green())
        await interaction.response.send_message(embed=embed, view=view)

    # --- НАПОМИНАНИЯ ---
    @app_commands.command(name="remind", description="Создать напоминание (в минутах)")
    async def remind(self, interaction: discord.Interaction, minutes: int, text: str):
        if minutes <= 0 or minutes > 1440:
            return await interaction.response.send_message("❌ Время должно быть от 1 до 1440 минут (24 часа).", ephemeral=True)
            
        await interaction.response.send_message(f"✅ Я напомню вам об этом через **{minutes} мин.**", ephemeral=True)
        await asyncio.sleep(minutes * 60)
        try:
            await interaction.user.send(f"⏰ **НАПОМИНАНИЕ:** {text}")
        except discord.Forbidden:
            await interaction.channel.send(f"⏰ {interaction.user.mention}, напоминаю: **{text}**")

    # --- ЛОГИРОВАНИЕ УДАЛЕННЫХ СООБЩЕНИЙ ---
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
            
        log_channel = message.guild.get_channel(self.LOG_DELETED_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="🗑️ Сообщение удалено", color=discord.Color.red())
            embed.set_author(name=f"{message.author}", icon_url=message.author.display_avatar.url)
            embed.add_field(name="Канал", value=message.channel.mention, inline=False)
            embed.add_field(name="Контент", value=message.content[:1024] if message.content else "*Пусто (или вложение)*", inline=False)
            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FunUtils(bot))
