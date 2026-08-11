import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import re
import datetime

def parse_time(time_str: str):
    """Конвертирует строку (10m, 1h, 2d) в секунды"""
    regex = re.compile(r"(\d+)([smhd])")
    match = regex.match(time_str.lower())
    if not match:
        return None
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    if unit == 's': return amount
    if unit == 'm': return amount * 60
    if unit == 'h': return amount * 3600
    if unit == 'd': return amount * 86400
    return None

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Храним активные розыгрыши, чтобы их можно было досрочно завершить
        self.active_giveaways = {} 

    async def finish_giveaway(self, channel: discord.TextChannel, message_id: int, prize: str, winners_count: int):
        """Внутренняя функция завершения розыгрыша"""
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return # Сообщение было удалено вручную

        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if not reaction:
            return
        
        users = [user async for user in reaction.users() if not user.bot]

        # Если никто не участвовал
        if len(users) == 0:
            embed = message.embeds[0]
            embed.title = "😔 РОЗЫГРЫШ ОТМЕНЕН"
            embed.description = "В розыгрыше никто не участвовал."
            embed.color = discord.Color.red()
            await message.edit(embed=embed)
            await channel.send("😔 Розыгрыш отменен, так как не было участников.")
            return

        # Выбираем случайных победителей
        actual_winners = min(winners_count, len(users))
        winners_list = random.sample(users, actual_winners)
        winners_mentions = ", ".join([w.mention for w in winners_list])

        # Обновляем старое сообщение розыгрыша
        embed = message.embeds[0]
        embed.title = "🎉 **РОЗЫГРЫШ ЗАВЕРШЕН** 🎉"
        embed.description = (
            f"Разыгрывалось: **{prize}**\n"
            f"Победители: {winners_mentions}"
        )
        embed.color = 0x2ecc71
        await message.edit(embed=embed)

        # Отправляем уведомление
        await channel.send(
            f"🎊 Поздравляем {winners_mentions}! Вы выиграли **{prize}**!\n"
            f"[Перейти к розыгрышу]({message.jump_url})"
        )

    async def giveaway_timer(self, channel, message_id, seconds, prize, winners):
        """Таймер, который ждет окончания розыгрыша"""
        try:
            await asyncio.sleep(seconds)
            await self.finish_giveaway(channel, message_id, prize, winners)
        except asyncio.CancelledError:
            # Ожидание было прервано командой /gend, таймер просто тихо отключается
            pass
        finally:
            self.active_giveaways.pop(message_id, None)

    @app_commands.command(name="gstart", description="Запустить розыгрыш (Giveaway)")
    @app_commands.describe(
        duration="Время (например: 1m, 10m, 1h, 2d)", 
        prize="Что разыгрываем?", 
        winners="Количество победителей (по умолчанию 1)"
    )
    @app_commands.default_permissions(administrator=True) # Только для стаффа
    async def gstart(self, interaction: discord.Interaction, duration: str, prize: str, winners: int = 1):
        seconds = parse_time(duration)
        
        if not seconds:
            return await interaction.response.send_message("❌ Неверный формат времени! Используйте `s`, `m`, `h` или `d`. Пример: `10m`", ephemeral=True)
        if winners < 1:
            return await interaction.response.send_message("❌ Количество победителей должно быть минимум 1.", ephemeral=True)

        end_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        end_timestamp = int(end_time.timestamp())

        embed = discord.Embed(
            title="🎉 **РОЗЫГРЫШ** 🎉", 
            description=(
                f"Разыгрывается: **{prize}**\n\n"
                f"Нажмите на реакцию 🎉, чтобы участвовать!\n"
                f"Победителей: **{winners}**\n"
                f"Заканчивается: <t:{end_timestamp}:R> (<t:{end_timestamp}:f>)"
            ), 
            color=0x9b59b6
        )
        embed.set_footer(text="Cosmo Giveaways")

        await interaction.response.send_message("✅ Розыгрыш успешно запущен!", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("🎉")

        # Создаем задачу таймера и сохраняем ее
        task = asyncio.create_task(self.giveaway_timer(interaction.channel, message.id, seconds, prize, winners))
        self.active_giveaways[message.id] = {
            "task": task,
            "prize": prize,
            "winners": winners,
            "channel": interaction.channel
        }

    @app_commands.command(name="gend", description="Досрочно завершить активный розыгрыш")
    @app_commands.describe(message_id="ID сообщения с розыгрышем")
    @app_commands.default_permissions(administrator=True)
    async def gend(self, interaction: discord.Interaction, message_id: str):
        try:
            msg_id = int(message_id)
        except ValueError:
            return await interaction.response.send_message("❌ ID сообщения должен состоять только из цифр.", ephemeral=True)

        giveaway = self.active_giveaways.get(msg_id)
        if not giveaway:
            return await interaction.response.send_message("❌ Активный розыгрыш с таким ID не найден (возможно, он уже завершен или бот был перезапущен).", ephemeral=True)

        # Отменяем таймер (чтобы он не сработал второй раз)
        giveaway["task"].cancel()
        
        # Сразу завершаем розыгрыш
        await interaction.response.send_message("✅ Завершаю розыгрыш досрочно...", ephemeral=True)
        await self.finish_giveaway(giveaway["channel"], msg_id, giveaway["prize"], giveaway["winners"])

    @app_commands.command(name="greroll", description="Выбрать новых победителей в завершенном розыгрыше")
    @app_commands.describe(message_id="ID сообщения с розыгрышем", winners="Сколько победителей перевыбрать (по умолчанию 1)")
    @app_commands.default_permissions(administrator=True)
    async def greroll(self, interaction: discord.Interaction, message_id: str, winners: int = 1):
        try:
            msg_id = int(message_id)
            message = await interaction.channel.fetch_message(msg_id)
        except (ValueError, discord.NotFound):
            return await interaction.response.send_message("❌ Сообщение с таким ID не найдено в этом канале.", ephemeral=True)

        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if not reaction:
            return await interaction.response.send_message("❌ На этом сообщении нет реакции 🎉.", ephemeral=True)
        
        users = [user async for user in reaction.users() if not user.bot]
        if len(users) == 0:
            return await interaction.response.send_message("❌ В этом розыгрыше никто не участвовал, реролл невозможен.", ephemeral=True)

        actual_winners = min(winners, len(users))
        winners_list = random.sample(users, actual_winners)
        winners_mentions = ", ".join([w.mention for w in winners_list])

        await interaction.response.send_message(
            f"🎲 **РЕРОЛЛ РОЗЫГРЫША** 🎲\n"
            f"Новые победители: {winners_mentions}!\n"
            f"[Перейти к сообщению]({message.jump_url})"
        )

async def setup(bot):
    await bot.add_cog(Giveaways(bot))