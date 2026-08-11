import discord
from discord.ext import commands
from discord import app_commands
import random
import time
from database import get_user, update_user

class EconomyPlus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Получить ежедневную награду (раз в 24 часа)")
    async def daily(self, interaction: discord.Interaction):
        user = await get_user(interaction.user.id)
        last_daily = user[6] # 7-я колонка в БД (индекс 6)
        current_time = int(time.time())
        
        # 86400 секунд = 24 часа
        if current_time - last_daily < 86400:
            left = 86400 - (current_time - last_daily)
            hours, remainder = divmod(left, 3600)
            minutes, _ = divmod(remainder, 60)
            return await interaction.response.send_message(f"⏳ Вы уже получали бонус! Возвращайтесь через **{hours}ч {minutes}м**.", ephemeral=True)
            
        reward = random.randint(100, 500)
        await update_user(interaction.user.id, "balance", user[2] + reward)
        await update_user(interaction.user.id, "last_daily", current_time)
        
        await interaction.response.send_message(f"🎁 Вы получили ежедневный бонус: **{reward}** 🪙! Ваш новый баланс: **{user[2] + reward}** 🪙.")

    @app_commands.command(name="pay", description="Перевести монеты другому пользователю")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount <= 0 or member.bot or member == interaction.user:
            return await interaction.response.send_message("❌ Некорректный перевод.", ephemeral=True)
            
        sender = await get_user(interaction.user.id)
        if sender[2] < amount:
            return await interaction.response.send_message("❌ У вас недостаточно монет!", ephemeral=True)
            
        receiver = await get_user(member.id)
        
        # Списываем и начисляем
        await update_user(interaction.user.id, "balance", sender[2] - amount)
        await update_user(member.id, "balance", receiver[2] + amount)
        
        await interaction.response.send_message(f"💸 Вы успешно перевели **{amount}** 🪙 пользователю {member.mention}!")

    @app_commands.command(name="coinflip", description="Сыграть в орлянку на монеты")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Орел", value="орел"),
        app_commands.Choice(name="Решка", value="решка")
    ])
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: app_commands.Choice[str]):
        if bet <= 0:
            return await interaction.response.send_message("❌ Ставка должна быть больше нуля.", ephemeral=True)
            
        user = await get_user(interaction.user.id)
        if user[2] < bet:
            return await interaction.response.send_message("❌ Недостаточно средств для ставки.", ephemeral=True)
            
        result = random.choice(["орел", "решка"])
        if choice.value == result:
            win_amount = bet # Удваиваем ставку (чистая прибыль = bet)
            await update_user(interaction.user.id, "balance", user[2] + win_amount)
            await interaction.response.send_message(f"🎉 Выпал **{result}**! Вы выиграли **{win_amount}** 🪙! Ваш баланс: {user[2] + win_amount}")
        else:
            await update_user(interaction.user.id, "balance", user[2] - bet)
            await interaction.response.send_message(f"💀 Выпал **{result}**. Вы проиграли **{bet}** 🪙. Ваш баланс: {user[2] - bet}")

async def setup(bot):
    await bot.add_cog(EconomyPlus(bot))
