import discord
from discord.ext import commands
from discord import app_commands

# === МОДАЛЬНЫЕ ОКНА ДЛЯ ВВОДА ТЕКСТА ===

class RenameModal(discord.ui.Modal, title='Изменить название комнаты'):
    name_input = discord.ui.TextInput(
        label='Новое название',
        placeholder='Например: Чилл зона',
        min_length=1,
        max_length=30
    )

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if vc:
            await vc.edit(name=self.name_input.value)
            await interaction.response.send_message(f"✅ Название изменено на **{self.name_input.value}**", ephemeral=True)

class LimitModal(discord.ui.Modal, title='Изменить лимит пользователей'):
    limit_input = discord.ui.TextInput(
        label='Количество слотов (0 - без лимита)',
        placeholder='Например: 5',
        min_length=1,
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel if interaction.user.voice else None
        if vc:
            try:
                limit = int(self.limit_input.value)
                limit = max(0, min(99, limit)) # Лимит Дискорда от 0 до 99
                await vc.edit(user_limit=limit)
                await interaction.response.send_message(f"✅ Лимит слотов установлен на **{limit}**", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("❌ Ошибка: Введите число!", ephemeral=True)

# === ПАНЕЛЬ КНОПОК ===

class VoiceControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # timeout=None делает кнопки "вечными"

    # Внутренняя проверка: в войсе ли юзер и его ли это комната?
    async def check_owner(self, interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Вы не находитесь в голосовом канале!", ephemeral=True)
            return None
            
        vc = interaction.user.voice.channel
        # Проверяем права юзера именно в этом канале
        if not vc.permissions_for(interaction.user).manage_channels:
            await interaction.response.send_message("❌ Вы не являетесь владельцем этой комнаты!", ephemeral=True)
            return None
        return vc

    @discord.ui.button(label="Закрыть", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="vc_lock")
    async def btn_lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.check_owner(interaction)
        if vc:
            await vc.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message("🔒 Комната закрыта. Теперь к вам нельзя зайти без приглашения.", ephemeral=True)

    @discord.ui.button(label="Открыть", style=discord.ButtonStyle.success, emoji="🔓", custom_id="vc_unlock")
    async def btn_unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.check_owner(interaction)
        if vc:
            await vc.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.response.send_message("🔓 Комната открыта для всех.", ephemeral=True)

    @discord.ui.button(label="Скрыть", style=discord.ButtonStyle.secondary, emoji="👁️", custom_id="vc_hide")
    async def btn_hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.check_owner(interaction)
        if vc:
            await vc.set_permissions(interaction.guild.default_role, view_channel=False)
            await interaction.response.send_message("👁️ Комната скрыта из общего списка каналов.", ephemeral=True)

    @discord.ui.button(label="Название", style=discord.ButtonStyle.primary, emoji="✏️", custom_id="vc_rename")
    async def btn_rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.check_owner(interaction)
        if vc:
            await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="Слоты", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="vc_limit")
    async def btn_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.check_owner(interaction)
        if vc:
            await interaction.response.send_modal(LimitModal())


# === ОСНОВНОЙ КЛАСС КОГА ===

class PrivateVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ================= НАСТРОЙКИ =================
        self.category_id = "1531975980522934382"      # ID категории, где будут создаваться румы
        self.create_channel_id = "1536786972276949003" # ID голосового канала "Создать комнату ➕"
        # =============================================

    @app_commands.command(name="setup_voice_panel", description="Установить панель управления приватными комнатами")
    @app_commands.default_permissions(administrator=True)
    async def setup_voice_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎛️ Управление комнатой", color=0x2b2d31)
        embed.description = "Используйте кнопки ниже для настройки вашего приватного канала."
        
        await interaction.channel.send(embed=embed, view=VoiceControlView())
        await interaction.response.send_message("✅ Панель управления успешно установлена!", ephemeral=True)

    # Событие: Отслеживаем входы и выходы из войсов
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        
        # 1. СОЗДАНИЕ КОМНАТЫ
        if after.channel and after.channel.id == self.create_channel_id:
            category = self.bot.get_channel(self.category_id)
            if not category:
                return

            # Выдаем права: всем можно заходить (по умолчанию), а создателю - полное управление
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(connect=True),
                member: discord.PermissionOverwrite(manage_channels=True, connect=True, move_members=True)
            }
            
            # Создаем сам канал
            new_channel = await member.guild.create_voice_channel(
                name=f"Комната {member.display_name}",
                category=category,
                overwrites=overwrites
            )
            
            # Перекидываем туда юзера
            try:
                await member.move_to(new_channel)
            except discord.HTTPException:
                # Если юзер успел отключиться до создания канала, удаляем пустой канал
                await new_channel.delete()

        # 2. УДАЛЕНИЕ КОМНАТЫ, ЕСЛИ ОНА ПУСТАЯ
        if before.channel and before.channel.category_id == self.category_id:
            # Убеждаемся, что мы не удаляем стартовый канал-генератор
            if before.channel.id != self.create_channel_id:
                if len(before.channel.members) == 0:
                    try:
                        await before.channel.delete()
                    except discord.HTTPException:
                        pass

# Регистрация кога и "вечных" кнопок
async def setup(bot):
    # Добавляем View в бота, чтобы кнопки работали даже после рестарта кода
    bot.add_view(VoiceControlView())
    await bot.add_cog(PrivateVoice(bot))
