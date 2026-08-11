import discord
from discord.ext import commands
from discord import app_commands

# --- 1. КНОПКА ЗАПИСИ НА ИВЕНТ ---
class EventView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()

    @discord.ui.button(label="Пойду (0)", style=discord.ButtonStyle.success, emoji="✅", custom_id="event_attend_button")
    async def attend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if user_id in self.participants:
            self.participants.remove(user_id)
            msg = "Вы отменили свое участие в мероприятии."
        else:
            self.participants.add(user_id)
            msg = "Вы успешно записались на мероприятие! Ждем вас."

        button.label = f"Пойду ({len(self.participants)})"
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(msg, ephemeral=True)


# --- 2. ВСПЛЫВАЮЩАЯ АНКЕТА (MODAL) ---
class EventModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Создание афиши мероприятия")
        
        self.event_title = discord.ui.TextInput(
            label="Название мероприятия", 
            placeholder="Например: Массовая сходка автолюбителей", 
            max_length=100, 
            required=True
        )
        self.event_time = discord.ui.TextInput(
            label="Дата и время", 
            placeholder="Сегодня в 20:00 (МСК)", 
            max_length=50, 
            required=True
        )
        self.event_desc = discord.ui.TextInput(
            label="Описание", 
            style=discord.TextStyle.paragraph, 
            placeholder="Что будем делать, какие правила и призы...", 
            max_length=1500, 
            required=True
        )
        self.event_image = discord.ui.TextInput(
            label="Ссылка на картинку (Баннер)", 
            placeholder="https://... (необязательно)", 
            required=False
        )
        self.event_ping = discord.ui.TextInput(
            label="Упомянуть всех? (Да / Нет)", 
            placeholder="Напишите 'Да', если нужен пинг @everyone", 
            max_length=3,
            required=False
        )

        self.add_item(self.event_title)
        self.add_item(self.event_time)
        self.add_item(self.event_desc)
        self.add_item(self.event_image)
        self.add_item(self.event_ping)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🎉 {self.event_title.value}",
            description=self.event_desc.value,
            color=0x9b59b6
        )
        embed.add_field(name="⏰ Время проведения", value=f"`{self.event_time.value}`", inline=False)
        embed.add_field(name="👑 Организатор", value=interaction.user.mention, inline=False)
        
        img_url = self.event_image.value.strip()
        if img_url.startswith("http"):
            embed.set_image(url=img_url)
            
        embed.set_footer(text="N E B U L A • EVENTS", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

        ping_text = self.event_ping.value.strip().lower()
        content = "@everyone" if ping_text in ["да", "yes", "+"] else None

        await interaction.response.send_message("✅ Афиша успешно создана и отправлена в этот канал!", ephemeral=True)
        await interaction.channel.send(content=content, embed=embed, view=EventView())


# --- 3. ОСНОВНОЙ КОГ И КОМАНДЫ ---
class EventActionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Теперь это простая команда /creative без всяких групп
    @app_commands.command(name="creative", description="Создать и опубликовать афишу мероприятия (Для ведущих)")
    @app_commands.default_permissions(manage_messages=True)
    async def creative(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EventModal())


async def setup(bot):
    await bot.add_cog(EventActionCog(bot))
