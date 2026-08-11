import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import random

# --- Модальное окно для ввода причины ---
class ReportModal(discord.ui.Modal):
    def __init__(self, target: discord.Member, channel_id: int):
        super().__init__(title="Отправка жалобы")
        self.target = target
        self.channel_id = channel_id
        
        self.reason = discord.ui.TextInput(
            label="Причина", 
            style=discord.TextStyle.paragraph, 
            placeholder="Опишите, что нарушил данный игрок...",
            required=True
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Ошибка: Канал для репортов был удален или не найден!", ephemeral=True)

        report_id = random.randint(1000, 9999)

        embed = discord.Embed(title=f"🚨 Жалоба #{report_id}", color=discord.Color.red())
        embed.add_field(name="Нарушитель", value=f"{self.target.mention} (ID: {self.target.id})", inline=True)
        embed.add_field(name="Автор", value=f"{interaction.user.mention} (ID: {interaction.user.id})", inline=True)
        embed.add_field(name="Причина", value=self.reason.value, inline=False)
        embed.add_field(name="Статус", value="Ожидает модератора", inline=False)
        
        view = discord.ui.View(timeout=None)
        btn = discord.ui.Button(
            label="Взять жалобу", 
            style=discord.ButtonStyle.primary, 
            emoji="🛠️", 
            custom_id=f"takereport_{self.target.id}_{interaction.user.id}_{report_id}"
        )
        view.add_item(btn)

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ваша жалоба **#{report_id}** успешно отправлена модераторам!", ephemeral=True)


# --- Основной ког ---
class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "nebula.db"

    async def cog_load(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS config (guild_id INTEGER PRIMARY KEY, report_channel_id INTEGER)")
            await db.commit()

    @app_commands.command(name="set_report_channel", description="Установить канал для получения жалоб")
    @app_commands.default_permissions(administrator=True)
    async def set_report_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO config (guild_id, report_channel_id) VALUES (?, ?)", 
                             (interaction.guild.id, channel.id))
            await db.commit()
        await interaction.response.send_message(f"✅ Канал для жалоб установлен на {channel.mention}", ephemeral=True)

    @app_commands.command(name="report", description="Пожаловаться на участника")
    async def report(self, interaction: discord.Interaction, member: discord.Member):
        if member.bot:
            return await interaction.response.send_message("❌ Нельзя пожаловаться на бота!", ephemeral=True)
        if member == interaction.user:
            return await interaction.response.send_message("❌ Нельзя пожаловаться на самого себя!", ephemeral=True)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT report_channel_id FROM config WHERE guild_id = ?", (interaction.guild.id,)) as cursor:
                row = await cursor.fetchone()
        
        if not row or not row[0]:
            return await interaction.response.send_message("❌ Админы еще не настроили канал для жалоб!", ephemeral=True)
        
        await interaction.response.send_modal(ReportModal(member, row[0]))

    # --- СЛУШАТЕЛЬ НАЖАТИЯ КНОПОК ---
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type == discord.InteractionType.component:
            return
            
        custom_id = interaction.data.get('custom_id', '')
        
        # 1. ЕСЛИ МОДЕРАТОР БЕРЕТ ЖАЛОБУ
        if custom_id.startswith("takereport_"):
            if not interaction.user.guild_permissions.manage_messages:
                return await interaction.response.send_message("❌ У вас нет прав для работы с жалобами.", ephemeral=True)

            parts = custom_id.split("_")
            target_id = int(parts[1])
            author_id = int(parts[2])
            report_id = parts[3]

            target_member = interaction.guild.get_member(target_id)
            author_member = interaction.guild.get_member(author_id)

            await interaction.response.defer(ephemeral=True)

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=False),
                interaction.user: discord.PermissionOverwrite(connect=True, view_channel=True, manage_channels=True)
            }
            if target_member: overwrites[target_member] = discord.PermissionOverwrite(connect=True, view_channel=True)
            if author_member: overwrites[author_member] = discord.PermissionOverwrite(connect=True, view_channel=True)

            category = interaction.channel.category
            try:
                new_vc = await interaction.guild.create_voice_channel(
                    name=f"Разбор-Жалобы-{report_id}",
                    category=category,
                    overwrites=overwrites
                )
            except discord.Forbidden:
                return await interaction.followup.send("❌ У бота нет прав на создание голосовых каналов!", ephemeral=True)

            moved_users = []
            for member, name in [(interaction.user, interaction.user.name), 
                                 (target_member, target_member.name if target_member else None), 
                                 (author_member, author_member.name if author_member else None)]:
                if member and member.voice and member.voice.channel:
                    try:
                        await member.move_to(new_vc)
                        moved_users.append(name)
                    except: pass

            # Создаем кнопку ЗАКРЫТИЯ жалобы, вшивая в нее ID созданного войса
            close_view = discord.ui.View(timeout=None)
            close_btn = discord.ui.Button(
                label="Закрыть жалобу", 
                style=discord.ButtonStyle.danger, 
                emoji="🔒", 
                custom_id=f"closereport_{new_vc.id}_{report_id}"
            )
            close_view.add_item(close_btn)

            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = f"🟢 Жалоба #{report_id} в работе"
            
            # Обновляем поле статуса
            for i, field in enumerate(embed.fields):
                if field.name == "Статус":
                    embed.set_field_at(i, name="Статус", value=f"Взял модератор: {interaction.user.mention}\nКомната: {new_vc.mention}", inline=False)
            
            await interaction.message.edit(embed=embed, view=close_view)

            report_msg = f"✅ Приватная комната {new_vc.mention} успешно создана."
            if moved_users: report_msg += f"\nПеремещены: **{', '.join(moved_users)}**."
            await interaction.followup.send(report_msg, ephemeral=True)

        # 2. ЕСЛИ МОДЕРАТОР ЗАКРЫВАЕТ ЖАЛОБУ
        elif custom_id.startswith("closereport_"):
            if not interaction.user.guild_permissions.manage_messages:
                return await interaction.response.send_message("❌ У вас нет прав для работы с жалобами.", ephemeral=True)

            parts = custom_id.split("_")
            vc_id = int(parts[1])
            report_id = parts[2]

            await interaction.response.defer(ephemeral=True)

            # Удаляем голосовой канал
            vc = interaction.guild.get_channel(vc_id)
            if vc:
                try:
                    await vc.delete()
                except discord.HTTPException:
                    pass

            # Обновляем сообщение в логах
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.light_grey()
            embed.title = f"☑️ Жалоба #{report_id} закрыта"
            
            for i, field in enumerate(embed.fields):
                if field.name == "Статус":
                    embed.set_field_at(i, name="Статус", value=f"Закрыл: {interaction.user.mention}", inline=False)
            
            # Убираем все кнопки
            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send(f"✅ Жалоба #{report_id} успешно закрыта, комната удалена.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reports(bot))