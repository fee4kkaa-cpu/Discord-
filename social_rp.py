import discord
from discord.ext import commands
from discord import app_commands
import random
from database import get_user, update_user

# Ссылки на гифки для RP команд (можно заменить на свои)
GIFS = {
    "hug": ["https://media.giphy.com/media/3M4NpbLCTxBqU/giphy.gif", "https://media.giphy.com/media/lrr9VkGvBD5yU/giphy.gif"],
    "kiss": ["https://media.giphy.com/media/G3va31oGkPjQ4/giphy.gif", "https://media.giphy.com/media/nyGFcsP0kAobm/giphy.gif"],
    "slap": ["https://media.giphy.com/media/jLeyZWgtSvv5S/giphy.gif", "https://media.giphy.com/media/tX29X2Dx3sAXS/giphy.gif"],
    "beat": ["https://media.giphy.com/media/l1J3G5lf06vi58EIE/giphy.gif", "https://media.giphy.com/media/11HeubLHnQJSAU/giphy.gif"]
}

class MarriageView(discord.ui.View):
    def __init__(self, proposer: discord.Member, target: discord.Member):
        super().__init__(timeout=60)
        self.proposer = proposer
        self.target = target

    @discord.ui.button(label="Согласиться", style=discord.ButtonStyle.success, emoji="💍")
    async def btn_accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("❌ Это предложение не для вас!", ephemeral=True)
            
        # Записываем браки в БД
        await update_user(self.proposer.id, "partner_id", self.target.id)
        await update_user(self.target.id, "partner_id", self.proposer.id)
        
        embed = discord.Embed(
            title="💖 Новая пара на сервере!",
            description=f"{self.target.mention} сказала **ДА**! Теперь они с {self.proposer.mention} в браке 💍.",
            color=discord.Color.pink()
        )
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Отказать", style=discord.ButtonStyle.danger, emoji="💔")
    async def btn_decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("❌ Это предложение не для вас!", ephemeral=True)
            
        embed = discord.Embed(
            title="💔 Отказ",
            description=f"{self.target.mention} отказала {self.proposer.mention}... F в чат.",
            color=discord.Color.dark_gray()
        )
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


class SocialRP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_rp_embed(self, action: str, author: discord.Member, target: discord.Member, text: str, color: discord.Color):
        # Используем .mention для пинга пользователей вместо .display_name
        embed = discord.Embed(description=f"{author.mention} {text} {target.mention}", color=color)
        embed.set_image(url=random.choice(GIFS[action]))
        return embed

    @app_commands.command(name="hug", description="Обнять пользователя")
    async def hug(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(embed=self.create_rp_embed("hug", interaction.user, member, "крепко обнимает", discord.Color.green()))

    @app_commands.command(name="kiss", description="Поцеловать пользователя")
    async def kiss(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(embed=self.create_rp_embed("kiss", interaction.user, member, "страстно целует", discord.Color.purple()))

    @app_commands.command(name="slap", description="Дать пощечину пользователю")
    async def slap(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(embed=self.create_rp_embed("slap", interaction.user, member, "дает звонкую пощечину", discord.Color.red()))

    # Изменили name="отпиздить" на name="beat"
    @app_commands.command(name="beat", description="Отпиздить пользователя")
    async def beatup(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(embed=self.create_rp_embed("beat", interaction.user, member, "отпиздил", discord.Color.dark_red()))

    @app_commands.command(name="marry", description="Сделать предложение руки и сердца")
    async def marry(self, interaction: discord.Interaction, member: discord.Member):
        if member == interaction.user or member.bot:
            return await interaction.response.send_message("❌ Нельзя жениться на себе или боте.", ephemeral=True)
            
        proposer_data = await get_user(interaction.user.id)
        target_data = await get_user(member.id)
        
        # Индексы: 7 - partner_id (см. БД)
        if proposer_data[7] != 0:
            return await interaction.response.send_message("❌ Вы уже состоите в браке!", ephemeral=True)
        if target_data[7] != 0:
            return await interaction.response.send_message("❌ Этот пользователь уже состоит в браке!", ephemeral=True)
            
        embed = discord.Embed(
            title="💍 Предложение руки и сердца",
            description=f"{member.mention}, пользователь {interaction.user.mention} предлагает вам стать парой!\nВы согласны?",
            color=discord.Color.pink()
        )
        await interaction.response.send_message(content=member.mention, embed=embed, view=MarriageView(interaction.user, member))

    @app_commands.command(name="divorce", description="Разорвать брак")
    async def divorce(self, interaction: discord.Interaction):
        user_data = await get_user(interaction.user.id)
        partner_id = user_data[7]
        
        if partner_id == 0:
            return await interaction.response.send_message("❌ Вы не состоите в браке.", ephemeral=True)
            
        # Обнуляем партнеров
        await update_user(interaction.user.id, "partner_id", 0)
        await update_user(partner_id, "partner_id", 0)
        
        await interaction.response.send_message(f"💔 Вы разорвали брак с <@{partner_id}>. Свобода!")

async def setup(bot):
    await bot.add_cog(SocialRP(bot))

