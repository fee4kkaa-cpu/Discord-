import discord
from discord.ext import commands
from discord import app_commands

class TicketControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Тикет закрывается...")
        await interaction.channel.delete()

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Связь с администрацией", description="Вопросы, жалобы, предложения", emoji="🎫", value="support"),
            discord.SelectOption(label="Апелляция наказания", description="Если вы получили варн/мут по ошибке", emoji="⚖️", value="appeal")
        ]
        super().__init__(placeholder="Выберите тип обращения...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Тикеты") # Обязательно создай категорию "Тикеты" на сервере
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_type = "Апелляция" if self.values[0] == "appeal" else "Поддержка"
        channel = await guild.create_text_channel(name=f"{ticket_type}-{interaction.user.name}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"Тикет: {ticket_type}", 
            description=f"{interaction.user.mention}, подробно опишите вашу ситуацию. Администрация скоро ответит.",
            color=discord.Color.red() if self.values[0] == "appeal" else discord.Color.blue()
        )
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ваш тикет создан: {channel.mention}", ephemeral=True)

class MainTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class AdvancedTickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_tickets", description="[Admin] Разместить панель тикетов")
    @app_commands.default_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Центр Поддержки", 
            description="Выберите нужную категорию в меню ниже, чтобы открыть приватный чат с модерацией.",
            color=0x2b2d31
        )
        await interaction.channel.send(embed=embed, view=MainTicketView())
        await interaction.response.send_message("Панель успешно установлена.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdvancedTickets(bot))
