import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

# ================= НАСТРОЙКИ ВЫГОВОРОВ =================
WARNS_CHANNEL_ID = "1536794177067683920" # Замени на ID канала, куда будут падать логи выговоров
# =======================================================

# --- 2. Модальное окно для СНЯТИЯ ВЫГОВОРА ---
class WarnRemoveModal(discord.ui.Modal):
    def __init__(self, target: discord.Member):
        super().__init__(title=f"Снятие выговора: {target.name}")
        self.target = target

        self.reason = discord.ui.TextInput(
            label="Причина снятия",
            style=discord.TextStyle.paragraph,
            placeholder="Например: Отработал норму, истек срок (7 дней), амнистия...",
            required=True
        )

        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(WARNS_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("❌ Канал для логов не найден! Проверьте WARNS_CHANNEL_ID в коде.", ephemeral=True)

        embed = discord.Embed(
            title="[ ПРОТОКОЛ КОНТРОЛЯ: СНЯТИЕ ВЫГОВОРА ]",
            description=f"С администратора {self.target.mention} был официально **снят** выговор.",
            color=0x2ecc71, # Зеленый цвет
            timestamp=datetime.now()
        )
        
        embed.add_field(name="👤 Досье", value=f"**ID:** `{self.target.id}`\n**Сотрудник:** {self.target.mention}", inline=False)
        embed.add_field(name="🔓 Детали амнистии", value=f"**Причина снятия:** {self.reason.value}", inline=False)
        embed.add_field(name="⚖️ Инициатор", value=interaction.user.mention, inline=False)

        if self.target.avatar:
            embed.set_thumbnail(url=self.target.avatar.url)

        await channel.send(embed=embed)
        
        # Отправляем уведомление в ЛС сотруднику
        try:
            await self.target.send(f"🎉 Руководство сняло с вас один выговор! Причина: {self.reason.value}\nПродолжайте хорошую работу!")
        except discord.Forbidden:
            pass

        await interaction.response.send_message(f"✅ Выговор с **{self.target.name}** успешно снят!", ephemeral=True)


# --- 1. Модальное окно для ВЫДАЧИ ВЫГОВОРА ---
class WarnAddModal(discord.ui.Modal):
    def __init__(self, target: discord.Member, warn_type: str, color: int):
        super().__init__(title=f"Выдача выговора: {target.name}")
        self.target = target
        self.warn_type = warn_type
        self.embed_color = color

        self.reason = discord.ui.TextInput(
            label="Подробная причина",
            style=discord.TextStyle.paragraph,
            placeholder="Опишите, какое правило нарушил администратор...",
            required=True
        )
        self.evidence = discord.ui.TextInput(
            label="Доказательства (ссылки)",
            style=discord.TextStyle.paragraph,
            placeholder="Ссылки на скрины (Postimages/Imgur) или логи...",
            required=True
        )

        self.add_item(self.reason)
        self.add_item(self.evidence)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(WARNS_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("❌ Канал для логов не найден! Проверьте WARNS_CHANNEL_ID в коде.", ephemeral=True)

        embed = discord.Embed(
            title="[ ПРОТОКОЛ КОНТРОЛЯ: ВЫДАЧА ВЫГОВОРА ]",
            description=f"Администратору {self.target.mention} был выдан выговор.",
            color=self.embed_color,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="👤 Досье", value=f"**ID:** `{self.target.id}`\n**Сотрудник:** {self.target.mention}", inline=False)
        embed.add_field(name="🛑 Детали нарушения", value=f"**Тип:** {self.warn_type}\n**Причина:** {self.reason.value}", inline=False)
        embed.add_field(name="🗂️ Доказательства", value=self.evidence.value, inline=False)
        embed.add_field(name="⚖️ Инициатор", value=interaction.user.mention, inline=False)

        if self.target.avatar:
            embed.set_thumbnail(url=self.target.avatar.url)

        await channel.send(embed=embed)
        
        # Уведомляем сотрудника в ЛС о наказании
        try:
            await self.target.send(
                f"⚠️ **Уведомление о дисциплинарном взыскании** ⚠️\n"
                f"Вам был выдан **{self.warn_type}**. Пожалуйста, ознакомьтесь с причиной в админ-канале логов или свяжитесь с руководством.\n"
                f"**Причина:** {self.reason.value}"
            )
        except discord.Forbidden:
            pass
            
        await interaction.response.send_message(f"✅ Выговор сотруднику **{self.target.name}** успешно выдан!", ephemeral=True)


# --- Основной класс модуля ---
class StaffWarns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Команда 1: Выдать выговор
    @app_commands.command(name="warn_add", description="Выдать выговор сотруднику стаффа (Админ)")
    @app_commands.describe(
        target="Кому выдаем выговор?",
        warn_type="Выберите тип выговора"
    )
    @app_commands.choices(warn_type=[
        app_commands.Choice(name="1/2 - Устный выговор (Желтый)", value="устный"),
        app_commands.Choice(name="1/3 - Строгий выговор (Красный)", value="строгий")
    ])
    @app_commands.default_permissions(administrator=True) 
    async def warn_add(self, interaction: discord.Interaction, target: discord.Member, warn_type: app_commands.Choice[str]):
        # Желтый для устного, Красный для строгого
        color = 0xf1c40f if warn_type.value == "устный" else 0xe74c3c
        await interaction.response.send_modal(
            WarnAddModal(target=target, warn_type=warn_type.name, color=color)
        )

    # Команда 2: Снять выговор
    @app_commands.command(name="warn_remove", description="Снять выговор с сотрудника стаффа (Админ)")
    @app_commands.describe(target="Кому снимаем выговор?")
    @app_commands.default_permissions(administrator=True)
    async def warn_remove(self, interaction: discord.Interaction, target: discord.Member):
        await interaction.response.send_modal(WarnRemoveModal(target=target))

async def setup(bot):
    await bot.add_cog(StaffWarns(bot))
