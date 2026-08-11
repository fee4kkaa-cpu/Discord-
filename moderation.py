import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # === НАСТРОЙКИ (ВСТАВЬ СВОИ ID СЮДА) ===
        self.LOG_CHANNEL_ID = "" # ID канала логов
        
        # ID ролей СПЕЦ-НАКАЗАНИЙ (Муты и Баны теперь системные, им роли не нужны)
        self.ROLE_EVENT_BAN = ""
        self.ROLE_MAFIA_BAN = ""
        self.ROLE_CHILL_BAN = ""
        self.ROLE_CLOSE_BAN = ""
        self.ROLE_NO_VERIFY = "" # Недопуск к верификации
        # =======================================

    async def send_log(self, guild: discord.Guild, action: str, moderator: discord.Member, target: discord.Member, reason: str, color: discord.Color, extra: str = None):
        log_channel = guild.get_channel(self.LOG_CHANNEL_ID)
        if not log_channel:
            return

        embed = discord.Embed(title=f"🛠️ Лог модерации: {action}", color=color, timestamp=datetime.datetime.now())
        embed.add_field(name="Модератор", value=moderator.mention, inline=True)
        embed.add_field(name="Нарушитель", value=target.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        
        if extra:
            embed.add_field(name="Дополнительно", value=extra, inline=False)
            
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"ID Нарушителя: {target.id}")
        
        await log_channel.send(embed=embed)

    # --- КОМАНДА: MUTE (СИСТЕМНЫЙ ТАЙМ-АУТ) ---
    @app_commands.command(name="mute", description="Выдать системный мут (Тайм-аут)")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.choices(duration=[
        app_commands.Choice(name="10 минут", value=10),
        app_commands.Choice(name="1 час", value=60),
        app_commands.Choice(name="1 день", value=1440),
        app_commands.Choice(name="1 неделя", value=10080)
    ])
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: app_commands.Choice[int], reason: str = "Причина не указана"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Вы не можете наказать этого пользователя.", ephemeral=True)
            
        try:
            # Переводим минуты в формат времени Discord (timedelta)
            time_delta = datetime.timedelta(minutes=duration.value)
            
            # Выдаем встроенный тайм-аут Discord (блокирует и текст, и войс)
            await member.timeout(time_delta, reason=f"{interaction.user}: {reason}")
            
            await interaction.response.send_message(f"✅ Пользователь {member.mention} получил **Тайм-аут** на {duration.name}. Причина: {reason}")
            await self.send_log(interaction.guild, "Мут (Тайм-аут)", interaction.user, member, reason, discord.Color.orange(), extra=f"Срок: {duration.name}")

        except discord.Forbidden:
            await interaction.response.send_message("❌ У меня нет прав на выдачу тайм-аута. Проверь иерархию ролей!", ephemeral=True)


    # --- КОМАНДА: RESTRICT (Спец-баны и недопуск) ---
    @app_commands.command(name="restrict", description="Выдать специальное ограничение (Ивенты, Мафия, Верификация и др.)")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.choices(ban_type=[
        app_commands.Choice(name="Event Ban", value="eventban"),
        app_commands.Choice(name="Mafia Ban", value="mafiaban"),
        app_commands.Choice(name="Chill Ban", value="chillban"),
        app_commands.Choice(name="Close Ban", value="closeban"),
        app_commands.Choice(name="Не допуск к верификации", value="no_verify")
    ])
    async def restrict(self, interaction: discord.Interaction, member: discord.Member, ban_type: app_commands.Choice[str], reason: str = "Причина не указана"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Вы не можете ограничить этого пользователя.", ephemeral=True)
            
        roles_map = {
            "eventban": self.ROLE_EVENT_BAN,
            "mafiaban": self.ROLE_MAFIA_BAN,
            "chillban": self.ROLE_CHILL_BAN,
            "closeban": self.ROLE_CLOSE_BAN,
            "no_verify": self.ROLE_NO_VERIFY
        }
        
        role_id = roles_map.get(ban_type.value)
        ban_role = interaction.guild.get_role(role_id)
        
        if not ban_role:
            return await interaction.response.send_message(f"❌ Роль (ID: {role_id}) не найдена на сервере!", ephemeral=True)

        try:
            await member.add_roles(ban_role, reason=f"{interaction.user}: {reason}")
            await interaction.response.send_message(f"🚫 Пользователь {member.mention} получил ограничение **{ban_type.name}**. Причина: {reason}")
            await self.send_log(interaction.guild, f"Ограничение ({ban_type.name})", interaction.user, member, reason, discord.Color.dark_red())
        except discord.Forbidden:
            await interaction.response.send_message("❌ У меня нет прав на выдачу этой роли.", ephemeral=True)


    # --- КОМАНДА: BAN (СИСТЕМНЫЙ БАН) ---
    @app_commands.command(name="ban", description="Выдать НАСТОЯЩИЙ БАН (пользователь будет выгнан с сервера)")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Причина не указана"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Вы не можете забанить этого пользователя.", ephemeral=True)
            
        try:
            # Пытаемся отправить сообщение в ЛС нарушителю перед баном
            try:
                await member.send(f"🔨 Вы были забанены на сервере **{interaction.guild.name}**.\n**Причина:** {reason}")
            except discord.Forbidden:
                pass # Если ЛС закрыта, просто игнорируем
                
            # Системный бан
            await member.ban(reason=f"Забанен модератором {interaction.user}: {reason}")
            
            await interaction.response.send_message(f"🔨 Пользователь {member.mention} был **ЗАБАНЕН**. Причина: {reason}")
            await self.send_log(interaction.guild, "Системный Бан", interaction.user, member, reason, discord.Color.red())
        except discord.Forbidden:
            await interaction.response.send_message("❌ У меня нет прав забанить этого пользователя. Поднимите мою роль выше!", ephemeral=True)


    # --- КОМАНДА: UNPUNISH (Снятие Тайм-аута и ролевых ограничений) ---
    @app_commands.command(name="unpunish", description="Снять системный мут (Тайм-аут) и все ролевые ограничения")
    @app_commands.default_permissions(moderate_members=True)
    async def unpunish(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Амнистия"):
        removed_actions = []
        
        # 1. Снимаем системный тайм-аут, если он есть
        if member.is_timed_out():
            try:
                await member.timeout(None, reason=f"Амнистия от {interaction.user}")
                removed_actions.append("Тайм-аут")
            except discord.Forbidden:
                pass

        # 2. Снимаем ролевые ограничения
        punishment_roles_ids = [
            self.ROLE_EVENT_BAN, self.ROLE_MAFIA_BAN, 
            self.ROLE_CHILL_BAN, self.ROLE_CLOSE_BAN, self.ROLE_NO_VERIFY
        ]
        
        roles_to_remove = []
        for role_id in punishment_roles_ids:
            role = interaction.guild.get_role(role_id)
            if role and role in member.roles:
                roles_to_remove.append(role)

        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason=f"Снятие ограничений от {interaction.user}")
                removed_actions.extend([r.name for r in roles_to_remove])
            except discord.Forbidden:
                pass

        if not removed_actions:
            return await interaction.response.send_message(f"❌ У {member.mention} нет активных тайм-аутов или ролевых ограничений.", ephemeral=True)

        removed_text = ", ".join(removed_actions)
        await interaction.response.send_message(f"✅ С {member.mention} сняты наказания: **{removed_text}**.")
        await self.send_log(interaction.guild, "Снятие наказаний (Unpunish)", interaction.user, member, reason, discord.Color.green(), extra=f"Снято: {removed_text}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))