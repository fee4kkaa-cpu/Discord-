import discord
from discord.ext import commands

# ================= НАСТРОЙКИ СВИДАНИЙ =================
# ID голосового канала, при перекидывании в который бот будет создавать руму
TRIGGER_CHANNEL_ID = "" 
# ID категории, где будут появляться эти румы
CATEGORY_ID = "" 
# ID роли Трибунера (чтобы бот всегда давал им доступ к этим закрытым румам)
HOST_ROLE_ID = "" 
# ID канала для отправки логов
LOG_CHANNEL_ID = ""
# ======================================================

class LoveDates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        
        # --- 1. АВТОМАТИЧЕСКОЕ СОЗДАНИЕ И ЛОГИРОВАНИЕ ---
        if after.channel and after.channel.id == TRIGGER_CHANNEL_ID:
            guild = member.guild
            category = guild.get_channel(CATEGORY_ID)
            host_role = guild.get_role(HOST_ROLE_ID)
            
            if not category:
                print("❌ Ошибка: Категория для свиданий не найдена (неверный ID)!")
                return

            # Настраиваем права для новой комнаты
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False), 
                member: discord.PermissionOverwrite(connect=True, speak=True), 
            }
            
            # Даем трибунерам права видеть комнату и перекидывать туда вторую половинку
            if host_role:
                overwrites[host_role] = discord.PermissionOverwrite(
                    connect=True, view_channel=True, move_members=True
                )

            try:
                # Создаем саму руму
                new_channel = await guild.create_voice_channel(
                    name=f"💖 Свидание {member.display_name}",
                    category=category,
                    overwrites=overwrites
                )
                
                # Автоматически перекидываем человека
                await member.move_to(new_channel)

                # Отправляем ЛОГ о создании
                log_channel = guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    embed = discord.Embed(
                        title="💘 Создана Лав-Рума", 
                        description=f"Трибунер перекинул пользователя {member.mention} в канал создания.\n**Комната:** {new_channel.mention}",
                        color=0xff69b4
                    )
                    await log_channel.send(embed=embed)
                
            except discord.HTTPException:
                pass 

        # --- 2. АВТОМАТИЧЕСКОЕ УДАЛЕНИЕ И ЛОГИРОВАНИЕ ---
        if before.channel and before.channel.category_id == CATEGORY_ID:
            # Игнорируем сам канал-триггер
            if before.channel.id != TRIGGER_CHANNEL_ID:
                # Если в канале больше никого не осталось
                if len(before.channel.members) == 0:
                    try:
                        channel_name = before.channel.name
                        await before.channel.delete(reason="Свидание закончилось, все вышли")

                        # Отправляем ЛОГ об удалении
                        log_channel = before.channel.guild.get_channel(LOG_CHANNEL_ID)
                        if log_channel:
                            embed = discord.Embed(
                                title="💔 Удалена Лав-Рума", 
                                description=f"Комната **{channel_name}** была автоматически удалена (все участники вышли).",
                                color=0x2f3136
                            )
                            await log_channel.send(embed=embed)

                    except discord.NotFound:
                        pass 

async def setup(bot):
    await bot.add_cog(LoveDates(bot))

