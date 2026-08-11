import discord
from discord.ext import commands
from discord import app_commands
import random
import time
from database import get_user, update_user

JOBS = {
    "Шахтер": {"min": 50, "max": 150, "risk": 5},
    "Хакер": {"min": 200, "max": 500, "risk": 40},
    "Бизнесмен": {"min": 100, "max": 300, "risk": 15}
}

class AdvancedEconomy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Получить ежедневную награду (раз в 24 часа)")
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id) # Кулдаун 24 часа
    async def daily(self, interaction: discord.Interaction):
        user = await get_user(interaction.user.id)
        if not user:
            return await interaction.response.send_message("❌ Вы еще не зарегистрированы в базе. Напишите сообщение в чат!", ephemeral=True)
            
        reward = random.randint(100, 250)
        await update_user(interaction.user.id, "balance", user[2] + reward)
        await interaction.response.send_message(f"🎁 Вы успешно забрали ежедневную награду: **{reward}** 🪙! Возвращайтесь завтра.")

    @app_commands.command(name="balance", description="Проверить свой баланс или баланс другого игрока")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user_data = await get_user(target.id)
        
        if not user_data:
            return await interaction.response.send_message(f"❌ {target.display_name} еще не зарегистрирован в базе.", ephemeral=True)
            
        wallet = user_data[2] if user_data[2] is not None else 0
        bank = user_data[10] if user_data[10] is not None else 0
        
        embed = discord.Embed(title=f"💳 Баланс: {target.display_name}", color=0x2b2d31)
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
        embed.add_field(name="Наличные", value=f"**{wallet}** 🪙", inline=True)
        embed.add_field(name="В банке", value=f"**{bank}** 🏦", inline=True)
        embed.add_field(name="Общий капитал", value=f"**{wallet + bank}** 💰", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Перевести свои монеты другому пользователю")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ Сумма перевода должна быть больше нуля.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Нельзя перевести деньги самому себе.", ephemeral=True)
            
        sender_data = await get_user(interaction.user.id)
        receiver_data = await get_user(member.id)
        
        if not sender_data or sender_data[2] < amount:
            return await interaction.response.send_message("❌ Недостаточно наличных средств для перевода.", ephemeral=True)
        if not receiver_data:
            return await interaction.response.send_message("❌ Получатель не зарегистрирован в базе.", ephemeral=True)
            
        await update_user(interaction.user.id, "balance", sender_data[2] - amount)
        await update_user(member.id, "balance", receiver_data[2] + amount)
        await interaction.response.send_message(f"💸 Вы успешно перевели **{amount}** 🪙 игроку {member.mention}!")

    @app_commands.command(name="deposit", description="Положить деньги в банк (Пассивный доход 5% в день)")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        user = await get_user(interaction.user.id)
        if not user or amount <= 0 or user[2] < amount:
            return await interaction.response.send_message("❌ Недостаточно наличных средств.", ephemeral=True)
            
        current_time = int(time.time())
        current_bank = user[10] if user[10] is not None else 0
        
        await update_user(interaction.user.id, "balance", user[2] - amount)
        await update_user(interaction.user.id, "bank", current_bank + amount)
        await update_user(interaction.user.id, "deposit_time", current_time)
        
        await interaction.response.send_message(f"🏦 Вы положили **{amount}** 🪙 в банк.")

    @app_commands.command(name="withdraw", description="Снять монеты со счета в банке")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        user = await get_user(interaction.user.id)
        current_bank = user[10] if user and user[10] is not None else 0
        
        if not user or amount <= 0 or current_bank < amount:
            return await interaction.response.send_message("❌ Недостаточно средств в банке.", ephemeral=True)
            
        await update_user(interaction.user.id, "bank", current_bank - amount)
        await update_user(interaction.user.id, "balance", user[2] + amount)
        await interaction.response.send_message(f"🏧 Вы сняли **{amount}** 🪙 со своего банковского счета.")

    @app_commands.command(name="coinflip", description="Сыграть в орлянку на монеты")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Орел", value="орел"),
        app_commands.Choice(name="Решка", value="решка")
    ])
    async def coinflip(self, interaction: discord.Interaction, amount: int, choice: app_commands.Choice[str]):
        if amount <= 0:
            return await interaction.response.send_message("❌ Ставка должна быть больше нуля.", ephemeral=True)
            
        user = await get_user(interaction.user.id)
        if not user or user[2] < amount:
            return await interaction.response.send_message("❌ У вас недостаточно наличных для такой ставки.", ephemeral=True)
            
        # Забираем ставку
        await update_user(interaction.user.id, "balance", user[2] - amount)
        
        result = random.choice(["орел", "решка"])
        if choice.value == result:
            win_amount = amount * 2
            await update_user(interaction.user.id, "balance", (user[2] - amount) + win_amount)
            await interaction.response.send_message(f"🪙 Выпал **{result}**! Вы угадали и выиграли **{win_amount}** 🪙!")
        else:
            await interaction.response.send_message(f"🪙 Выпал **{result}**... Вы проиграли свою ставку в **{amount}** 🪙.")

    @app_commands.command(name="work", description="Поработать и получить монеты (зависит от профессии)")
    @app_commands.checks.cooldown(1, 3600, key=lambda i: i.user.id) # Кулдаун 1 час
    async def work(self, interaction: discord.Interaction):
        user = await get_user(interaction.user.id)
        if not user:
            return await interaction.response.send_message("❌ Вы еще не зарегистрированы в базе.", ephemeral=True)
            
        job = user[12]
        if job == 'Безработный' or job is None:
            return await interaction.response.send_message("❌ Вы безработный! Сначала устройтесь на работу через `/setjob`.", ephemeral=True)
            
        job_data = JOBS.get(job)
        if not job_data:
            return await interaction.response.send_message("❌ Ошибка профессии.", ephemeral=True)
        
        if random.randint(1, 100) <= job_data["risk"]:
            penalty = random.randint(50, 100)
            await update_user(interaction.user.id, "balance", max(0, user[2] - penalty))
            return await interaction.response.send_message(f"🚨 Вас поймали на работе ({job})! Штраф: **{penalty}** 🪙.", color=discord.Color.red())
            
        salary = random.randint(job_data["min"], job_data["max"])
        await update_user(interaction.user.id, "balance", user[2] + salary)
        await interaction.response.send_message(f"💼 Вы успешно поработали ({job}) и заработали **{salary}** 🪙!")

    @app_commands.command(name="setjob", description="Выбрать профессию")
    @app_commands.choices(job=[
        app_commands.Choice(name="⛏️ Шахтер (Низкий риск, стабильный доход)", value="Шахтер"),
        app_commands.Choice(name="💻 Хакер (Высокий риск, огромный доход)", value="Хакер"),
        app_commands.Choice(name="👔 Бизнесмен (Средний риск, средний доход)", value="Бизнесмен")
    ])
    async def setjob(self, interaction: discord.Interaction, job: app_commands.Choice[str]):
        await update_user(interaction.user.id, "job", job.value)
        await interaction.response.send_message(f"✅ Вы успешно устроились на должность: **{job.value}**!", ephemeral=True)

    # === ОБРАБОТЧИК ОШИБОК ДЛЯ ВСЕХ КОМАНД ЭКОНОМИКИ ===
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            # Переводим оставшиеся секунды в часы, минуты и секунды
            minutes, seconds = divmod(int(error.retry_after), 60)
            hours, minutes = divmod(minutes, 60)
            
            if hours > 0:
                time_str = f"**{hours} ч {minutes} мин**"
            else:
                time_str = f"**{minutes} мин {seconds} сек**"
                
            await interaction.response.send_message(f"⏳ Команда пока недоступна. Попробуйте снова через {time_str}.", ephemeral=True)
        else:
            # Если произошла какая-то другая ошибка
            print(f"[Экономика] Ошибка: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Произошла непредвиденная ошибка при выполнении команды.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdvancedEconomy(bot))