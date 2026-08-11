import discord
from discord.ext import commands
from discord import app_commands
import datetime

# --- 1. МОДАЛЬНОЕ ОКНО ДЛЯ ВВОДА ДАННЫХ ---
class ModerationModal(discord.ui.Modal):
    def __init__(self, action, target_member):
        super().__init__(title=f"Действие: {action.upper()}")
        self.action = action
        self.target = target_member
        
        self.reason = discord.ui.TextInput(
            label="Причина наказания",
            placeholder="Введите причину...",
            style=discord.TextStyle.long,
            required=True
        )
        self.add_item(self.reason)

        if action == "mute":
            self.duration = discord.ui.TextInput(
                label="Длительность (в минутах)",
                placeholder="Например: 60",
                required=True
            )
            self.add_item(self.duration)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value
        
        if self.action == "mute":
            duration = int(self.duration.value)
            await self.target.timeout(datetime.timedelta(minutes=duration), reason=reason)
            await interaction.response.send_message(f"🔇 {self.target.mention} в муте на {duration} мин. Причина: {reason}", ephemeral=True)
            
        elif self.action == "kick":
            await self.target.kick(reason=reason)
            await interaction.response.send_message(f"👢 {self.target.mention} выгнан. Причина: {reason}", ephemeral=True)
            
        elif self.action == "ban":
            await self.target.ban(reason=reason)
            await interaction.response.send_message(f"🔨 {self.target.mention} забанен. Причина: {reason}", ephemeral=True)
            
        elif self.action == "warn":
            await interaction.response.send_message(f"⚠️ {self.target.mention} выдан варн. Причина: {reason}", ephemeral=True)

# --- 2. ПАНЕЛЬ С КНОПКАМИ ---
class ActionView(discord.ui.View):
    def __init__(self, target_member):
        super().__init__(timeout=60)
        self.target = target_member

    @discord.ui.button(label="Мут", style=discord.ButtonStyle.secondary, emoji="🔇")
    async def mute_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModerationModal("mute", self.target))

    @discord.ui.button(label="Кик", style=discord.ButtonStyle.secondary, emoji="👢")
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModerationModal("kick", self.target))

    @discord.ui.button(label="Бан", style=discord.ButtonStyle.danger, emoji="🔨")
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModerationModal("ban", self.target))

    @discord.ui.button(label="Варн", style=discord.ButtonStyle.primary, emoji="⚠️")
    async def warn_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModerationModal("warn", self.target))

# --- 3. КОГ МОДЕРАЦИИ ---
class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="action", description="Открыть панель модерации для пользователя")
    @app_commands.describe(member="Выберите пользователя для действий")
    @app_commands.default_permissions(moderate_members=True)
    async def action(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title="🛠 Панель Модерации",
            description=f"Выбран пользователь: {member.mention}\nВыберите действие, которое хотите совершить:",
            color=0x2f3136
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        await interaction.response.send_message(embed=embed, view=ActionView(member), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
