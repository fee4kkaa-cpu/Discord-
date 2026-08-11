import discord
from discord.ext import commands
from discord import app_commands

# ================= НАСТРОЙКИ СИСТЕМЫ НАБОРА =================
LOG_CHANNEL_ID = 1536788494037557289 # ОБНОВЛЕННЫЙ Канал логов заявок

# Словарь: Должность -> ID роли, которую нужно ПИНГОВАТЬ при новой заявке
SENIOR_ROLES = {
    "Support": "",
    "Helper": "",
    "Control": "",
    "Moderator": "",
    "Creative": "",
    "EventsMod": "",
    "CloseMod": "",
    "ContentMaker": "",
    "Broadcaster": "",
    "Headliners": "",
}
# ============================================================

# --- 3. Модальное окно (Сама анкета) ---
class ApplicationModal(discord.ui.Modal):
    def __init__(self, position: str):
        super().__init__(title=f"Заявка на должность: {position}")
        self.position = position

        self.name_age = discord.ui.TextInput(
            label="Ваше имя и реальный возраст", 
            placeholder="Например: Ростик, 17 лет", 
            max_length=50,
            required=True
        )
        self.time = discord.ui.TextInput(
            label="Сколько времени готовы уделять серверу?", 
            placeholder="Например: 2-3 часа в день", 
            max_length=50,
            required=True
        )
        self.experience = discord.ui.TextInput(
            label="Ваш опыт в данной сфере", 
            style=discord.TextStyle.paragraph, 
            placeholder="Опишите, где работали раньше, что умеете делать...", 
            required=True
        )
        self.reason = discord.ui.TextInput(
            label="Почему мы должны взять именно вас?", 
            style=discord.TextStyle.paragraph, 
            placeholder="Расскажите о своих сильных сторонах...", 
            required=True
        )

        self.add_item(self.name_age)
        self.add_item(self.time)
        self.add_item(self.experience)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("❌ Ошибка: Канал для логов заявок не найден. Сообщите администратору!", ephemeral=True)

        embed = discord.Embed(title=f"📝 Новая заявка: {self.position}", color=0xb39ddb)
        embed.add_field(name="Кандидат", value=interaction.user.mention, inline=True)
        embed.add_field(name="ID Discord", value=interaction.user.id, inline=True)
        embed.add_field(name="Имя и возраст", value=self.name_age.value, inline=False)
        embed.add_field(name="Онлайн в день", value=self.time.value, inline=False)
        embed.add_field(name="Опыт", value=self.experience.value, inline=False)
        embed.add_field(name="Почему он/она", value=self.reason.value, inline=False)
        
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        role_id = SENIOR_ROLES.get(self.position)
        ping_text = f"<@&{role_id}>" if role_id else "⚠️ **Внимание: Роль не настроена**"

        # Создаем кнопки одобрения/отклонения и вшиваем в них ID кандидата
        view = discord.ui.View(timeout=None)
        approve_btn = discord.ui.Button(
            label="Одобрить", 
            style=discord.ButtonStyle.success, 
            emoji="✅",
            custom_id=f"staff_approve_{interaction.user.id}"
        )
        reject_btn = discord.ui.Button(
            label="Отклонить", 
            style=discord.ButtonStyle.danger, 
            emoji="✖️",
            custom_id=f"staff_reject_{interaction.user.id}"
        )
        view.add_item(approve_btn)
        view.add_item(reject_btn)

        await channel.send(content=f"🔔 {ping_text}, поступила новая заявка на рассмотрение!", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ваша заявка на должность **{self.position}** успешно отправлена! Ожидайте ответа.", ephemeral=True)


# --- 2. Выпадающее меню для выбора должности ---
class PositionSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", description="Верификация участников", emoji="🛡️"),
            discord.SelectOption(label="Helper", description="Бампы сервера", emoji="📈"),
            discord.SelectOption(label="Control", description="Модерация текстовых каналов", emoji="💬"),
            discord.SelectOption(label="Moderator", description="Модерация голосовых каналов", emoji="🎙️"),
            discord.SelectOption(label="EventsMod", description="Проведение мероприятий", emoji="🎉"),
            discord.SelectOption(label="Creative", description="Творческие мероприятия", emoji="🎨"),
            discord.SelectOption(label="CloseMod", description="Организация игровых клозов", emoji="🎮"),
            discord.SelectOption(label="ContentMaker", description="Создание контента", emoji="🎬"),
            discord.SelectOption(label="Broadcaster", description="Развлекательные трибуны", emoji="🎤"),
            discord.SelectOption(label="Headliners", description="Интеллектуальные игры и ЧГК", emoji="🧠")
        ]
        super().__init__(placeholder="На какую должность подаем заявку?", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_position = self.values[0]
        await interaction.response.send_modal(ApplicationModal(position=selected_position))

class PositionSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PositionSelect())


# --- 1. Основной класс и команда создания панели ---
class RecruitmentPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_staff_panel", description="Отправить панель набора в стафф (Админ)")
    @app_commands.default_permissions(administrator=True)
    async def setup_staff_panel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed_text = discord.Embed(
            title="Открыт набор на стафф сервера",
            color=0xb39ddb 
        )

        embed_text.description = (
            "Множество людей хотели бы побывать на определенной должности на нашем сервере.\n"
            "Поэтому мы **открываем Набор** на следующие должности:\n\n"
            "> <@&1527428942921728050> — занимаются верификацией участников.\n"
            "> <@&1527428864697962558> — занимаются бампами сервера.\n"
            "> <@&1527428852257652888> — занимаются модерацией текстовых каналов на сервере.\n"
            "> <@&1527428848419999744> — занимаются модерацией голосовых каналов на сервере.\n"
            "> <@&1527428982218293309> — творческие личности, отвечающие за мини мероприятия.\n"
            "> <@&1527428860818493545> — занимаются проведением мероприятий.\n"
            "> <@&1527428978359537704> — организуют игровые клозы.\n"
            "> <@&1527428839867682827> — организуют развлекательные трибуны.\n"
            "> <@&1527429048056283197> — создают привлекательный контент.\n"
            "> <@&1527696119553851502> — занимаются интеллектуальными играми и ЧГК.\n\n"
        )

        embed_text.description += (
            "**Что от вас требуется?**\n"
            "> Быть готовым уделять серверу 2-3 часа в день\n"
            "> 16 полных лет\n"
            "> Знание и понимание правил сервера и дискорда\n"
            "> Иметь опыт в выбранной должности\n\n"
            "При неадекватном заполнении заявки, мы будем выдавать наказания"
        )

        view = discord.ui.View(timeout=None)
        btn = discord.ui.Button(
            label="Подать заявку", 
            style=discord.ButtonStyle.success, 
            emoji="📝",
            custom_id="apply_staff_button"
        )
        view.add_item(btn)

        await interaction.channel.send(embed=embed_text, view=view)
        await interaction.followup.send("✅ Панель набора успешно отправлена!", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type == discord.InteractionType.component:
            return
            
        custom_id = interaction.data.get('custom_id', '')
        
        # 1. Открытие модального окна выбора должности
        if custom_id == "apply_staff_button":
            await interaction.response.send_message(
                "👇 Выберите желаемую должность из списка ниже, чтобы перейти к заполнению анкеты:", 
                view=PositionSelectView(), 
                ephemeral=True
            )
            return

        # 2. Логика кнопки "Одобрить"
        if custom_id.startswith("staff_approve_"):
            user_id = int(custom_id.split("_")[2])
            candidate = interaction.guild.get_member(user_id)
            
            # Обновляем эмбед заявки
            embed = interaction.message.embeds[0]
            position_name = embed.title.replace("📝 Новая заявка: ", "")
            embed.color = discord.Color.green()
            embed.title = f"✅ Заявка Одобрена: {position_name}"
            embed.add_field(name="Вердикт", value=f"Одобрил: {interaction.user.mention}", inline=False)
            
            await interaction.response.defer()
            await interaction.message.edit(embed=embed, view=None) # view=None убирает кнопки
            
            # Отправка сообщения в ЛС кандидату
            if candidate:
                try:
                    await candidate.send(
                        f"🎉 Поздравляем! Ваша заявка на должность **{position_name}** была успешно **одобрена**!\n\n"
                        f"Пожалуйста, напишите администратору {interaction.user.mention} (`{interaction.user.name}`) "
                        f"в личные сообщения для прохождения инструктажа и получения роли."
                    )
                    await interaction.followup.send(f"✅ Заявка одобрена. Кандидат **{candidate.name}** уведомлен в ЛС!", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send(f"⚠️ Заявка одобрена, но у кандидата **{candidate.name}** закрыты личные сообщения. Свяжитесь с ним на сервере.", ephemeral=True)
            else:
                await interaction.followup.send("⚠️ Заявка одобрена, но кандидат уже покинул сервер.", ephemeral=True)

        # 3. Логика кнопки "Отклонить"
        elif custom_id.startswith("staff_reject_"):
            user_id = int(custom_id.split("_")[2])
            candidate = interaction.guild.get_member(user_id)
            
            embed = interaction.message.embeds[0]
            position_name = embed.title.replace("📝 Новая заявка: ", "")
            embed.color = discord.Color.red()
            embed.title = f"❌ Заявка Отклонена: {position_name}"
            embed.add_field(name="Вердикт", value=f"Отклонил: {interaction.user.mention}", inline=False)
            
            await interaction.response.defer()
            await interaction.message.edit(embed=embed, view=None)

            if candidate:
                try:
                    await candidate.send(f"😔 Здравствуйте. К сожалению, ваша заявка на должность **{position_name}** была **отклонена**.")
                    await interaction.followup.send(f"❌ Заявка отклонена. Кандидат **{candidate.name}** уведомлен в ЛС.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send(f"❌ Заявка отклонена. ЛС кандидата закрыто.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Заявка отклонена. Кандидат покинул сервер.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RecruitmentPanel(bot))
