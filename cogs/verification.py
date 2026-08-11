import discord
from discord.ext import commands
from discord import app_commands

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ================= НАСТРОЙКА ID РОЛЕЙ И КАНАЛОВ =================
        self.role_m_id = ""            # ID роли Мужской ♂
        self.role_w_id = ""            # ID роли Женский ♀
        self.role_not_verified_id = ""  # ID роли новичка (@not verified)
        
        self.log_channel_id = ""        # СЮДА ID КАНАЛА ДЛЯ ЛОГОВ (#logs-вериф)
        # =================================================================

    # -----------------------------------------------------------------
    # 1. КОМАНДА /verify
    # -----------------------------------------------------------------
    @app_commands.command(name="verify", description="Верификация участника сервера")
    @app_commands.describe(member="Участник, которого нужно верифицировать", gender="Выберите пол участника")
    @app_commands.choices(gender=[
        app_commands.Choice(name="Мужской ♂", value="М"),
        app_commands.Choice(name="Женский ♀", value="Ж")
    ])
    async def verify(self, interaction: discord.Interaction, member: discord.Member, gender: str):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ У вас нет прав на использование этой команды.", ephemeral=True)

        # Откладываем ответ (модератор видит статус "думает", сообщение будет скрытым)
        await interaction.response.defer(ephemeral=True)

        role_m = interaction.guild.get_role(self.role_m_id)
        role_w = interaction.guild.get_role(self.role_w_id)
        role_not_verified = interaction.guild.get_role(self.role_not_verified_id)
        target_gender_role = role_m if gender == "М" else role_w

        if not target_gender_role:
            return await interaction.followup.send("❌ Ошибка: Роль указанного пола не найдена на сервере (проверь ID).")

        try:
            # Выдаем только роль пола
            await member.add_roles(target_gender_role)

            # Снимаем роль не верифицированного
            if role_not_verified and (role_not_verified in member.roles):
                await member.remove_roles(role_not_verified)

            # Отправка в ЛС пользователю
            dm_embed = discord.Embed(title="✅ Верификация пройдена", color=0x2b2d31)
            dm_embed.description = f"Вы были успешно верифицированы на сервере **{interaction.guild.name}**."
            dm_embed.add_field(name="Выдана роль", value=f"• {target_gender_role.mention}", inline=False)
            dm_embed.add_field(name="Модератор", value=interaction.user.name, inline=False)
            dm_embed.set_footer(text="Теперь вы можете пользоваться всеми возможностями сервера")
            
            try:
                await member.send(embed=dm_embed)
                dm_status = "📥 Отчёт отправлен в ЛС."
            except discord.Forbidden:
                dm_status = "⚠️ ЛС пользователя закрыты."

            # Подготовка лога для канала администрации
            server_embed = discord.Embed(title="✅ Верификация выполнена", color=0x2b2d31)
            server_embed.description = f"Пользователь {member.mention} успешно верифицирован."
            server_embed.add_field(name="👤 Пользователь", value=f"{member.name}\nID: {member.id}", inline=False)
            server_embed.add_field(name="⚧ Пол", value=target_gender_role.mention, inline=True)
            server_embed.add_field(name="👮 Модератор", value=interaction.user.mention, inline=True)
            server_embed.set_footer(text=f"Роль новичка снята | {dm_status}")
            
            # Находим канал логов
            log_channel = interaction.guild.get_channel(self.log_channel_id)
            
            if log_channel:
                await log_channel.send(embed=server_embed)
                await interaction.followup.send(f"✅ Успешно верифицирован. Лог отправлен в {log_channel.mention}.")
            else:
                await interaction.followup.send(embed=server_embed)
                await interaction.followup.send("⚠️ Предупреждение: Канал логов не найден! Проверь `log_channel_id`.")

        except discord.Forbidden:
            await interaction.followup.send("❌ Ошибка: Недостаточно прав для управления ролями у бота Cosmo!")

    # -----------------------------------------------------------------
    # 2. КОМАНДА /unverify
    # -----------------------------------------------------------------
    @app_commands.command(name="unverify", description="Снять верификацию с участника сервера")
    @app_commands.describe(member="Участник, с которого нужно снять верификацию", reason="Причина снятия верификации")
    async def unverify(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ У вас нет прав на использование этой команды.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        role_m = interaction.guild.get_role(self.role_m_id)
        role_w = interaction.guild.get_role(self.role_w_id)
        role_not_verified = interaction.guild.get_role(self.role_not_verified_id)

        roles_to_remove = []
        if role_m and role_m in member.roles: roles_to_remove.append(role_m)
        if role_w and role_w in member.roles: roles_to_remove.append(role_w)

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)

            if role_not_verified:
                await member.add_roles(role_not_verified)

            dm_embed = discord.Embed(title="⚠️ Верификация аннулирована", color=0x2b2d31)
            dm_embed.description = f"С вас была снята верификация на сервере **{interaction.guild.name}**."
            dm_embed.add_field(name="📋 Причина", value=reason, inline=False)
            dm_embed.set_footer(text="Если вы считаете это ошибкой, обратитесь к администрации сервера.")
            
            try:
                await member.send(embed=dm_embed)
                dm_status = "📥 Уведомление отправлено в ЛС."
            except discord.Forbidden:
                dm_status = "⚠️ ЛС пользователя закрыты."

            log_channel = interaction.guild.get_channel(self.log_channel_id)
            server_embed = discord.Embed(title="❌ Верификация снята", color=0x2b2d31)
            server_embed.description = f"Модератор {interaction.user.mention} аннулировал верификацию для {member.mention}."
            server_embed.add_field(name="👤 Пользователь", value=f"{member.name}\nID: {member.id}", inline=True)
            server_embed.add_field(name="👮 Модератор", value=interaction.user.mention, inline=True)
            server_embed.add_field(name="📋 Причина", value=reason, inline=False)
            
            removed_mentions = ", ".join([r.mention for r in roles_to_remove]) if roles_to_remove else "Ролей не обнаружено"
            server_embed.add_field(name="🗑️ Снятые роли", value=removed_mentions, inline=False)
            server_embed.set_footer(text=f"Роль новичка возвращена | {dm_status}")

            if log_channel:
                await log_channel.send(embed=server_embed)
                await interaction.followup.send(f"✅ Верификация успешно снята. Лог отправлен в {log_channel.mention}.")
            else:
                await interaction.followup.send(embed=server_embed)

        except discord.Forbidden:
            await interaction.followup.send("❌ Ошибка: Недостаточно прав для управления ролями у бота Cosmo!")

async def setup(bot):
    await bot.add_cog(Verification(bot))