import discord
from discord.ext import commands
from discord import app_commands

class PollView(discord.ui.View):
    def __init__(self, question, options):
        super().__init__(timeout=None)
        self.question = question
        self.options = options
        self.votes = {i: set() for i in range(len(options))}
        
        for i, option in enumerate(options):
            btn = discord.ui.Button(label=option, custom_id=f"poll_{i}", style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            # Удаляем старый голос пользователя, если он переголосовал
            for i in self.votes:
                self.votes[i].discard(user_id)
            # Добавляем новый голос
            self.votes[index].add(user_id)
            
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)
        return callback

    def generate_embed(self):
        total_votes = sum(len(v) for v in self.votes.values())
        embed = discord.Embed(title=f"📊 Голосование: {self.question}", color=discord.Color.blurple())
        
        for i, option in enumerate(self.options):
            count = len(self.votes[i])
            percent = int((count / total_votes) * 100) if total_votes > 0 else 0
            bar = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
            embed.add_field(name=f"{option} — {count} голос(ов) ({percent}%)", value=f"`{bar}`", inline=False)
            
        embed.set_footer(text=f"Всего голосов: {total_votes}")
        return embed

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Создать голосование")
    async def poll(self, interaction: discord.Interaction, question: str, opt1: str, opt2: str, opt3: str = None, opt4: str = None):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ У вас нет прав для создания голосований.", ephemeral=True)
            
        options = [opt for opt in [opt1, opt2, opt3, opt4] if opt is not None]
        view = PollView(question, options)
        await interaction.response.send_message(embed=view.generate_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Polls(bot))
