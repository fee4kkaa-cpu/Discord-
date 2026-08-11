import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

# ================= НАСТРОЙКИ ЧС =================
BLACKLIST_CHANNEL_ID = "" # Замени на ID канала, куда будут падать логи ЧС
BLACKLIST_ROLE_ID = 0 # Замени на ID роли "ЧС Стаффа" (если оставить 0, роль выдаваться/сниматься не будет)
# ================================================

# --- 2. Модальное окно для СНЯТИЯ ЧС ---
class BlacklistRemoveModal(discord.ui.Modal):
    def __init__(self, target: discord.Member):
        super().__init__(title=f"Амнистия: {target.name}")
        self.target = target

        # Поля для ввода
        self.reason = discord.ui.TextInput(
            label="Причина выноса из ЧС",
            style=discord.TextStyle.paragraph,
            placeholder="Например: Одобрена амнистия, истек срок наказания, ошибочная выдача...",
            required=True
        )
        self.conditions = discord.ui.TextInput(
            label="Условия возвращения (необязательно)",
            placeholder="Например: Без восстановления / Начинает с должности Support",
            required=False
        )

        self.add_item(self.reason)
        self.add_item(self.conditions)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(BLACKLIST_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("❌ Канал для ЧС не найден! Проверьте BLACKLIST_CHANNEL_ID в коде.", ephemeral=True)

        # Собираем зеленый Embed (протокол амнистии)
        embed = discord.Embed(
            title="[ ПРОТОКОЛ БЕЗОПАСНОСТИ: АМНИСТИЯ / СНЯТИЕ ЧС ]",
            description=f"Пользователь {self.target.mention} был официально **вынесен** из Черного Списка стаффа.",
            color=0x2ecc71, # Зеленый цвет
            timestamp=datetime.now()
        )
        
        conditions_text = self.conditions.value if self.conditions.value else "Без особых условий"
        
        embed.add_field(name="👤 Досье пользователя", value=f"**ID:** `{self.target.id}`\n**Пользователь:** {self.target.mention}", inline=False)
        embed.add_field(name="🔓 Детали амнистии", value=f"**Причина снятия:** {self.reason.value}\n**Условия:** {conditions_text}", inline=False)
        embed.add_field(name="⚖️ Инициатор запроса", value=interaction.user.mention, inline=False)

        if self.target.avatar:
            embed.set_thumbnail(url=self.target.avatar.url)

        # Снятие системной роли ЧС
        role_removed = False
        if BLACKLIST_ROLE_ID != 0:
            role = interaction.guild.get_role(BLACKLIST_ROLE_ID)
            if role and role in self.target.roles:
                try:
                    await self.target.remove_roles(role, reason=f"Снятие ЧС Стаффа. Инициатор: {interaction.user.name}")
                    role_removed = True
                except discord.Forbidden:
                    pass

        # Отправляем в канал логов
        await channel.send(embed=embed)
        
        # Уведомляем админа
        msg = f"✅ Пользователь **{self.target.name}** успешно вынесен из ЧС!"
        if role_removed:
            msg += " Системная роль ЧС успешно снята."
            
        await interaction.response.send_message(msg, ephemeral=True)


# --- 1. Модальное окно для ВНЕСЕНИЯ В ЧС ---
class BlacklistAddModal(discord.ui.Modal):
    def __init__(self, target: discord.Member, severity: str, color: int):
        super().__init__(title=f"Занесение в ЧС: {target.name}")
        self.target = target
        self.severity = severity
        self.embed_color = color

        # Поля для ввода
        self.former_position = discord.ui.TextInput(
            label="Бывшая должность",
            placeholder="Например: Support / Event Maker",
            max_length=50,
            required=False 
        )
        self.reason = discord.ui.TextInput(
            label="Подробная причина",
            style=discord.TextStyle.paragraph,
            placeholder="Опишите, что именно нарушил данный человек...",
            required=True
        )
        self.evidence = discord.ui.TextInput(
            label="Доказательства (ссылки)",
            style=discord.TextStyle.paragraph,
            placeholder="Ссылки на Imgur, Postimages, YouTube, логи...",
            required=True
        )

        self.add_item(self.former_position)
        self.add_item(self.reason)
        self.add_item(self.evidence)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(BLACKLIST_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("❌ Канал для ЧС не найден! Проверьте BLACKLIST_CHANNEL_ID в коде.", ephemeral=True)

        embed = discord.Embed(
            title="[ ПРОТОКОЛ БЕЗОПАСНОСТИ: ВНЕСЕНИЕ В ЧС ]",
            description=f"Пользователь {self.target.mention} был официально занесен в Черный Список стаффа.",
            color=self.embed_color,
            timestamp=datetime.now()
        )
        
        position = self.former_position.value if self.former_position.value else "Не указана"
        
        embed.add_field(name="👤 Досье на нарушителя", value=f"**ID:** `{self.target.id}`\n**Бывшая должность:** {position}", inline=False)
        embed.add_field(name="🛑 Детали инцидента", value=f"**Тип ЧС:** {self.severity}\n**Причина:** {self.reason.value}", inline=False)
        embed.add_field(name="🗂️ Доказательная база", value=self.evidence.value, inline=False)
        embed.add_field(name="⚖️ Инициатор запроса", value=interaction.user.mention, inline=False)

        if self.target.avatar:
            embed.set_thumbnail(url=self.target.avatar.url)

        # Выдача системной роли ЧС
        role_assigned = False
        if BLACKLIST_ROLE_ID != 0:
            role = interaction.guild.get_role(BLACKLIST_ROLE_ID)
            if role:
                try:
                    await self.target.add_roles(role, reason=f"ЧС Стаффа. Инициатор: {interaction.user.name}")
                    role_assigned = True
                except discord.Forbidden:
                    pass

        await channel.send(embed=embed)
        
        msg = f"✅ Пользователь **{self.target.name}** успешно занесен в ЧС!"
        if role_assigned:
            msg += " Системная роль изоляции автоматически выдана."
            
        await interaction.response.send_message(msg, ephemeral=True)


# --- Основной класс модуля ---
class StaffBlacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Команда 1: Добавить в ЧС
    @app_commands.command(name="blacklist_add", description="Занести пользователя в Черный Список стаффа (Админ)")
    @app_commands.describe(
        target="Кого заносим в ЧС?",
        severity="Выберите степень тяжести (цвет ЧС)"
    )
    @app_commands.choices(severity=[
        app_commands.Choice(name="🟡 Желтый (1-3 месяца) - Легкие нарушения", value="yellow"),
        app_commands.Choice(name="🟠 Оранжевый (3-6 месяцев) - Блат / Превышение полномочий", value="orange"),
        app_commands.Choice(name="🔴 Красный (Перманентный) - Слив / Грубое вредительство", value="red"),
    ])
    @app_commands.default_permissions(administrator=True) 
    async def blacklist_add(self, interaction: discord.Interaction, target: discord.Member, severity: app_commands.Choice[str]):
        colors = {
            "yellow": 0xf1c40f,
            "orange": 0xe67e22,
            "red": 0xe74c3c
        }
        await interaction.response.send_modal(
            BlacklistAddModal(target=target, severity=severity.name, color=colors[severity.value])
        )

    # Команда 2: Вынести из ЧС
    @app_commands.command(name="blacklist_remove", description="Снять Черный Список стаффа с пользователя (Админ)")
    @app_commands.describe(target="Кого выносим из ЧС?")
    @app_commands.default_permissions(administrator=True)
    async def blacklist_remove(self, interaction: discord.Interaction, target: discord.Member):
        await interaction.response.send_modal(BlacklistRemoveModal(target=target))

async def setup(bot):
    await bot.add_cog(StaffBlacklist(bot))