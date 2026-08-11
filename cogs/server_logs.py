import discord
from discord.ext import commands
import datetime

class ServerLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ================= НАСТРОЙКА ID КАНАЛОВ (ПО СТРУКТУРЕ СЕРВЕРА) =================
        self.log_punish_id = ""       # ⛔ наказания
        self.log_sponsors_id = ""     # 💎 спонсоры
        self.log_monitoring_id = ""   # 📋 логи-мониторинг (Входы/выходы из войсов)
        self.log_loverooms_id = ""    # 💍 лаврумы (Обычно обрабатывается в коге экономики/свадеб)
        self.log_verification_id = "" # 📁 логи-верификаций (Уже настроено в verification.py)
        self.log_custom_roles_id = "" # 🎀 личные-роли (Изменения ролей участников)
        self.log_private_rooms_id = ""# 🧸 личные-комнаты (Обрабатывается в private_voice.py)
        self.log_reviews_id = ""      # 📁 отзывы
        self.log_admin_id = ""        # 💔 действия-админов
        self.log_automod_id = ""      # 💫 автомод
        self.log_joins_id = ""        # 📊 зашедшие
        self.log_anticrash_id = ""    # 💫 антикраш (Для будущей системы защиты)
        # ===============================================================================

    # ---------------------------------------------------------
    # 1. ЗАШЕДШИЕ И ВЫШЕДШИЕ УЧАСТНИКИ (канал: зашедшие)
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = member.guild.get_channel(self.log_joins_id)
        if not channel: return
        
        embed = discord.Embed(title="📥 Участник присоединился", color=discord.Color.green(), timestamp=datetime.datetime.now())
        embed.add_field(name="Пользователь", value=f"{member.mention} ({member.name})", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        
        account_age = datetime.datetime.now(datetime.timezone.utc) - member.created_at
        embed.add_field(name="Возраст аккаунта", value=f"{account_age.days} дней", inline=False)
        
        if member.avatar: embed.set_thumbnail(url=member.avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = member.guild.get_channel(self.log_joins_id)
        if not channel: return
        
        embed = discord.Embed(title="📤 Участник покинул сервер", color=discord.Color.red(), timestamp=datetime.datetime.now())
        embed.add_field(name="Пользователь", value=f"{member.mention} ({member.name})", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        
        if member.joined_at:
            stay_duration = datetime.datetime.now(datetime.timezone.utc) - member.joined_at
            embed.add_field(name="Пробыл на сервере", value=f"{stay_duration.days} дней", inline=False)
            
        if member.avatar: embed.set_thumbnail(url=member.avatar.url)
        await channel.send(embed=embed)

    # ---------------------------------------------------------
    # 2. МОНИТОРИНГ ГОЛОСОВЫХ КАНАЛОВ (канал: логи-мониторинг)
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel: return # Игнорируем мут/размут
        
        channel = member.guild.get_channel(self.log_monitoring_id)
        if not channel: return

        if before.channel is None and after.channel is not None:
            # Зашел в войс
            embed = discord.Embed(title="🎙️ Вход в голосовой канал", color=0x2ecc71, timestamp=datetime.datetime.now())
            embed.description = f"{member.mention} зашел в канал {after.channel.mention}"
        elif before.channel is not None and after.channel is None:
            # Вышел из войса
            embed = discord.Embed(title="🚪 Выход из голосового канала", color=0xe74c3c, timestamp=datetime.datetime.now())
            embed.description = f"{member.mention} покинул канал {before.channel.mention}"
        elif before.channel is not None and after.channel is not None:
            # Перешел в другой канал
            embed = discord.Embed(title="🔄 Перемещение в другой канал", color=0x3498db, timestamp=datetime.datetime.now())
            embed.description = f"{member.mention} перешел из {before.channel.mention} в {after.channel.mention}"

        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(embed=embed)

    # ---------------------------------------------------------
    # 3. ИЗМЕНЕНИЯ УЧАСТНИКОВ: БУСТЫ И РОЛИ (спонсоры / личные-роли)
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Отслеживание бустов (Спонсоры)
        if before.premium_since is None and after.premium_since is not None:
            sponsor_channel = after.guild.get_channel(self.log_sponsors_id)
            if sponsor_channel:
                embed = discord.Embed(title="💎 Новый Буст Сервера!", color=0xf1c40f, timestamp=datetime.datetime.now())
                embed.description = f"Огромное спасибо, {after.mention}, за поддержку нашего проекта!"
                if after.avatar: embed.set_thumbnail(url=after.avatar.url)
                await sponsor_channel.send(embed=embed)

        # Отслеживание изменения ролей (Личные-роли)
        if before.roles != after.roles:
            role_channel = after.guild.get_channel(self.log_custom_roles_id)
            if role_channel:
                added_roles = [role for role in after.roles if role not in before.roles]
                removed_roles = [role for role in before.roles if role not in after.roles]
                
                if added_roles or removed_roles:
                    embed = discord.Embed(title="🏷️ Обновление ролей", color=0x9b59b6, timestamp=datetime.datetime.now())
                    embed.add_field(name="Участник", value=after.mention, inline=False)
                    
                    if added_roles:
                        embed.add_field(name="Выданы роли", value=", ".join([r.mention for r in added_roles]), inline=False)
                    if removed_roles:
                        embed.add_field(name="Сняты роли", value=", ".join([r.mention for r in removed_roles]), inline=False)
                    
                    await role_channel.send(embed=embed)

    # ---------------------------------------------------------
    # 4. ДЕЙСТВИЯ С СООБЩЕНИЯМИ (канал: действия-админов)
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        channel = message.guild.get_channel(self.log_admin_id)
        if not channel: return

        embed = discord.Embed(title="🗑️ Сообщение удалено", color=0xe67e22, timestamp=datetime.datetime.now())
        embed.add_field(name="Автор", value=message.author.mention, inline=True)
        embed.add_field(name="Канал", value=message.channel.mention, inline=True)
        
        content = message.content if message.content else "*Медиа-файл или Эмбед*"
        if len(content) > 1024: content = content[:1020] + "..."
        embed.add_field(name="Содержимое", value=content, inline=False)
        
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content: return
        channel = before.guild.get_channel(self.log_admin_id)
        if not channel: return

        embed = discord.Embed(title="✏️ Сообщение изменено", color=0x3498db, timestamp=datetime.datetime.now())
        embed.add_field(name="Автор", value=before.author.mention, inline=True)
        embed.add_field(name="Канал", value=before.channel.mention, inline=True)
        embed.add_field(name="Ссылка", value=f"[Перейти к сообщению]({after.jump_url})", inline=False)
        
        before_content = before.content[:1000] + "..." if len(before.content) > 1000 else before.content or "*Пусто*"
        after_content = after.content[:1000] + "..." if len(after.content) > 1000 else after.content or "*Пусто*"
        
        embed.add_field(name="Было", value=before_content, inline=False)
        embed.add_field(name="Стало", value=after_content, inline=False)
        
        await channel.send(embed=embed)

    # ---------------------------------------------------------
    # 5. ЧТЕНИЕ ЖУРНАЛА АУДИТА (НАКАЗАНИЯ И АДМИН-ДЕЙСТВИЯ)
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        
        # Наказания (Кик, Бан, Разбан)
        if entry.action in [discord.AuditLogAction.kick, discord.AuditLogAction.ban, discord.AuditLogAction.unban]:
            channel = entry.guild.get_channel(self.log_punish_id)
            if not channel: return
            
            action_name = {
                discord.AuditLogAction.kick: "👢 Участник выгнан (Кик)",
                discord.AuditLogAction.ban: "🔨 Участник забанен",
                discord.AuditLogAction.unban: "🕊️ Участник разбанен"
            }[entry.action]
            
            color = discord.Color.red() if entry.action != discord.AuditLogAction.unban else discord.Color.green()
            
            embed = discord.Embed(title=action_name, color=color, timestamp=datetime.datetime.now())
            embed.add_field(name="Модератор", value=f"{entry.user.mention}", inline=True)
            embed.add_field(name="Нарушитель", value=f"{entry.target.mention if hasattr(entry.target, 'mention') else entry.target}", inline=True)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason, inline=False)
            
            await channel.send(embed=embed)

        # Наказания (Мут / Таймаут)
        elif entry.action == discord.AuditLogAction.member_update:
            if hasattr(entry.after, 'timed_out_until'):
                channel = entry.guild.get_channel(self.log_punish_id)
                if not channel: return

                if entry.after.timed_out_until is not None:
                    embed = discord.Embed(title="🔇 Выдан мут (Таймаут)", color=discord.Color.orange(), timestamp=datetime.datetime.now())
                    embed.add_field(name="Модератор", value=f"{entry.user.mention}", inline=True)
                    embed.add_field(name="Нарушитель", value=f"{entry.target.mention}", inline=True)
                    embed.add_field(name="Снятие", value=f"<t:{int(entry.after.timed_out_until.timestamp())}:R>", inline=False)
                else:
                    embed = discord.Embed(title="🔊 Мут снят досрочно", color=discord.Color.green(), timestamp=datetime.datetime.now())
                    embed.add_field(name="Модератор", value=f"{entry.user.mention}", inline=True)
                    embed.add_field(name="Пользователь", value=f"{entry.target.mention}", inline=True)

                if entry.reason:
                    embed.add_field(name="Причина", value=entry.reason, inline=False)
                
                await channel.send(embed=embed)

        # Глобальные действия админов (Создание/Удаление каналов)
        elif entry.action in [discord.AuditLogAction.channel_create, discord.AuditLogAction.channel_delete]:
            channel = entry.guild.get_channel(self.log_admin_id)
            if not channel: return
            
            action_name = {
                discord.AuditLogAction.channel_create: "📁 Создан канал",
                discord.AuditLogAction.channel_delete: "🗑️ Удален канал"
            }[entry.action]
            
            embed = discord.Embed(title=action_name, color=0x3498db, timestamp=datetime.datetime.now())
            embed.add_field(name="Администратор", value=f"{entry.user.mention}", inline=True)
            
            # === ИСПРАВЛЕНИЕ ОШИБКИ ЗДЕСЬ ===
            target_name = getattr(entry.target, 'name', f"Удаленный канал (ID: {getattr(entry.target, 'id', 'Неизвестно')})")
            embed.add_field(name="Канал", value=target_name, inline=True)
            # ================================
            
            await channel.send(embed=embed)

    # ---------------------------------------------------------
    # 6. АВТОМОД (канал: автомод)
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_automod_action(self, execution: discord.AutoModAction):
        channel = execution.guild.get_channel(self.log_automod_id)
        if not channel: return
        
        embed = discord.Embed(title="🛡️ Сработал системный Автомод", color=0xf1c40f, timestamp=datetime.datetime.now())
        if execution.member:
            embed.add_field(name="Нарушитель", value=f"{execution.member.mention} ({execution.member.name})", inline=True)
        
        rule = await execution.guild.fetch_automod_rule(execution.rule_id)
        embed.add_field(name="Нарушенное правило", value=rule.name, inline=True)
        
        if execution.matched_content:
            embed.add_field(name="Сработавшее слово", value=f"`{execution.matched_content}`", inline=False)
            
        if execution.content:
            safe_content = execution.content[:1000] + "..." if len(execution.content) > 1000 else execution.content
            embed.add_field(name="Полный текст", value=safe_content, inline=False)

        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerLogs(bot))