import discord
from discord.ext import commands
from discord import app_commands

# === МОДАЛЬНОЕ ОКНО (САМА АНКЕТА) ===
class RecruitmentModal(discord.ui.Modal, title='Заявка в персонал'):
    name = discord.ui.TextInput(
        label='Ваше имя / Никнейм', 
        placeholder='Например: Ростик', 
        min_length=2, 
        max_length=30
    )
    age = discord.ui.TextInput(
        label='Ваш возраст', 
        placeholder='16', 
        min_length=1, 
        max_length=2
    )
    experience = discord.ui.TextInput(
        label='Был ли опыт работы?', 
        style=discord.TextStyle.paragraph, 
        placeholder='Опишите ваш опыт (на каких проектах работали)...', 
        required=False 
    )
    reason = discord.ui.TextInput(
        label='Почему мы должны взять именно вас?', 
        style=discord.TextStyle.paragraph,
        placeholder='Расскажите о своих сильных сторонах...'
    )

    def __init__(self, target_channel_id: int):
        super().__init__()
        self.target_channel_id = target_channel_id 

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.target_channel_id)
        
        if not channel:
            return await interaction.response.send_message("❌ Ошибка: Канал для заявок был удален или не найден.", ephemeral=True)
        
        embed = discord.Embed(title="📩 Новая заявка на рассмотрение!", color=0xf1c40f)
        embed.set_author(name=f"От: {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        embed.add_field(name="Имя / Ник", value=self.name.value, inline=True)
        embed.add_field(name="Возраст", value=self.age.value, inline=True)
        embed.add_field(name="Опыт работы", value=self.experience.value or "Опыт отсутствует", inline=False)
        embed.add_field(name="Почему он?", value=self.reason.value, inline=False)
        
        embed.set_footer(text=f"ID пользователя: {interaction.user.id} | @{interaction.user.name}")

        view = discord.ui.View()
        # В кастомный ID кнопок вшиваем ID пользователя, подавшего заявку
        view.add_item(discord.ui.Button(label="Принять", style=discord.ButtonStyle.success, custom_id=f"accept_{interaction.user.id}"))
        view.add_item(discord.ui.Button(label="Отклонить", style=discord.ButtonStyle.danger, custom_id=f"deny_{interaction.user.id}"))

        await channel.send(content=f"Упоминание: {interaction.user.mention}", embed=embed, view=view)
        await interaction.response.send_message("✅ Ваша заявка успешно отправлена на рассмотрение! Ожидайте ответа администрации.", ephemeral=True)


# === КЛАСС КОГОВ (КОМАНДЫ И СЛУШАТЕЛЬ КНОПОК) ===
class Recruitment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_recruitment", description="Установить панель подачи заявок")
    @app_commands.describe(log_channel="Скрытый канал, куда будут приходить анкеты от игроков")
    @app_commands.default_permissions(administrator=True) 
    async def setup_recruitment(self, interaction: discord.Interaction, log_channel: discord.TextChannel):
        
        embed = discord.Embed(
            title="📋 Открыт набор в персонал сервера!",
            description=(
                "Хочешь стать частью нашей команды? Нажми на кнопку ниже и заполни анкету.\n\n"
                "**Требования:**\n"
                "🔹 Адекватность и знание правил\n"
                "🔹 Наличие свободного времени\n"
                "🔹 Желание помогать серверу"
            ),
            color=0x2b2d31
        )
        
        view = discord.ui.View(timeout=None)
        button = discord.ui.Button(
            label="Подать заявку", 
            style=discord.ButtonStyle.primary, 
            emoji="📝",
            custom_id=f"recruit_btn_{log_channel.id}" 
        )
        view.add_item(button)

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Панель установлена! Заявки будут приходить в канал {log_channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type == discord.InteractionType.component:
            return
            
        custom_id = interaction.data.get('custom_id', '')
        
        # 1. Если нажали кнопку "Подать заявку"
        if custom_id.startswith("recruit_btn_"):
            try:
                channel_id = int(custom_id.split("_")[2])
                await interaction.response.send_modal(RecruitmentModal(target_channel_id=channel_id))
            except Exception as e:
                print(f"[Recruitment] Ошибка открытия модалки: {e}")

        # 2. Если админ нажал "Принять"
        elif custom_id.startswith("accept_"):
            applicant_id = int(custom_id.split("_")[1])
            embed = interaction.message.embeds[0]
            
            embed.color = discord.Color.green()
            embed.title = "✅ ЗАЯВКА ПРИНЯТА"
            
            old_footer = embed.footer.text if embed.footer else ""
            embed.set_footer(text=f"{old_footer} | Принял: {interaction.user.display_name}")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            # --- ОТПРАВКА ЛС КАНДИДАТУ ---
            applicant = interaction.guild.get_member(applicant_id)
            if applicant:
                try:
                    dm_embed = discord.Embed(
                        title="🎉 Ваша заявка в персонал одобрена!",
                        description=f"Здравствуйте, {applicant.mention}!\n\nВаша анкета была успешно рассмотрена и **одобрена**.\n\nПожалуйста, свяжитесь с администратором {interaction.user.mention} в личных сообщениях для прохождения небольшого собеседования и получения дальнейших инструкций.",
                        color=discord.Color.green()
                    )
                    await applicant.send(embed=dm_embed)
                except discord.Forbidden:
                    # Если у кандидата закрыты ЛС, бот уведомит админа
                    await interaction.followup.send(f"⚠️ {interaction.user.mention}, заявка принята, но у пользователя {applicant.mention} закрыты личные сообщения. Свяжитесь с ним самостоятельно.", ephemeral=True)

        # 3. Если админ нажал "Отклонить"
        elif custom_id.startswith("deny_"):
            applicant_id = int(custom_id.split("_")[1])
            embed = interaction.message.embeds[0]
            
            embed.color = discord.Color.red()
            embed.title = "❌ ЗАЯВКА ОТКЛОНЕНА"
            
            old_footer = embed.footer.text if embed.footer else ""
            embed.set_footer(text=f"{old_footer} | Отклонил: {interaction.user.display_name}")
            
            await interaction.response.edit_message(embed=embed, view=None)

            # --- ОТПРАВКА ЛС КАНДИДАТУ ---
            applicant = interaction.guild.get_member(applicant_id)
            if applicant:
                try:
                    dm_embed = discord.Embed(
                        title="😔 Заявка отклонена",
                        description=f"Здравствуйте, {applicant.mention}.\n\nК сожалению, ваша заявка в персонал сервера была **отклонена** администратором {interaction.user.mention}.\n\nНе расстраивайтесь, возможно, вам повезет в следующий раз!",
                        color=discord.Color.red()
                    )
                    await applicant.send(embed=dm_embed)
                except discord.Forbidden:
                    pass # При отказе можно проигнорировать закрытые ЛС

async def setup(bot):
    await bot.add_cog(Recruitment(bot))