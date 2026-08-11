import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

# Словарь-маппинг. Ключ - то, что выбираем в меню, Значение - (Основная роль, Роль "Отвечает")
STAFF_ROLES = {
    "moderator": ("・Moderator", "・Отвечает | Moderator"),
    "helper": ("・Helper", "・Отвечает | Helper"),
    "control": ("・Control", "・Отвечает | Control"),
    "support": ("・Support", "・Отвечает | Support"),
    "eventsmod": ("・EventsMod", "・Отвечает | EventsMod"),
    "broadcaster": ("・Broadcaster", "・Отвечает | Broadcaster"),
    "creative": ("・Creative", "・Отвечает | Creative"),
    "contentmaker": ("・ContentMaker", "・Отвечает | ContentMaker"),
    "closemod": ("・CloseMod", "・Отвечает | CloseMod"),
    "headliner": ("・Headliner", "・Отвечает | Headliners")
}

class StaffCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setstaff", description="Выдать пользователю должность, роль 'Отвечает' и роль Staff")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        member="Кому выдать должность",
        position="Какую должность выдать"
    )
    @app_commands.choices(position=[
        Choice(name="Moderator", value="moderator"),
        Choice(name="Helper", value="helper"),
        Choice(name="Control", value="control"),
        Choice(name="Support", value="support"),
        Choice(name="EventsMod", value="eventsmod"),
        Choice(name="Broadcaster", value="broadcaster"),
        Choice(name="Creative", value="creative"),
        Choice(name="ContentMaker", value="contentmaker"),
        Choice(name="CloseMod", value="closemod"),
        Choice(name="Headliner", value="headliner"),
    ])
    async def setstaff(self, interaction: discord.Interaction, member: discord.Member, position: str):
        # Получаем названия специфических ролей из словаря
        role_names = STAFF_ROLES.get(position)
        
        if not role_names:
            return await interaction.response.send_message("❌ Неизвестная должность.", ephemeral=True)

        primary_name, secondary_name = role_names
        
        # === НАСТРОЙКА ОБЩЕЙ РОЛИ СТАФФА ===
        STAFF_BASE_ROLE = "Staff" 
        
        # Ищем все 3 роли на сервере
        primary_role = discord.utils.get(interaction.guild.roles, name=primary_name)
        secondary_role = discord.utils.get(interaction.guild.roles, name=secondary_name)
        base_staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_BASE_ROLE)

        roles_to_add = []
        error_msgs = []

        # Проверяем основную роль
        if primary_role:
            roles_to_add.append(primary_role)
        else:
            error_msgs.append(f"❌ Роль `{primary_name}` не найдена.")

        # Проверяем роль "Отвечает"
        if secondary_role:
            roles_to_add.append(secondary_role)
        else:
            error_msgs.append(f"❌ Роль `{secondary_name}` не найдена.")

        # Проверяем общую роль Staff
        if base_staff_role:
            if base_staff_role not in member.roles:
                roles_to_add.append(base_staff_role)
        else:
            error_msgs.append(f"❌ Общая роль `{STAFF_BASE_ROLE}` не найдена.")

        # Если вообще ни одной роли не нашли
        if not roles_to_add:
            return await interaction.response.send_message("\n".join(error_msgs), ephemeral=True)

        # Пытаемся выдать роли
        try:
            await member.add_roles(*roles_to_add, reason=f"Назначен админом {interaction.user.display_name}")
            
            embed = discord.Embed(
                title="✅ Назначение на должность",
                description=f"Сотрудник {member.mention} успешно получил новые права!",
                color=discord.Color.green()
            )
            
            added_roles_text = "\n".join([f"• {r.mention}" for r in roles_to_add])
            embed.add_field(name="Выданы роли:", value=added_roles_text)
            
            if error_msgs:
                embed.add_field(name="⚠️ Внимание:", value="\n".join(error_msgs), inline=False)
                
            request_avatar = interaction.user.display_avatar.url if interaction.user.display_avatar else None
            embed.set_footer(text=f"Выдал: {interaction.user.display_name}", icon_url=request_avatar)

            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ **Ошибка прав!** У бота нет прав выдавать эти роли. \n"
                "Зайди в Настройки сервера -> Роли, и перетащи роль твоего бота **ВЫШЕ**, чем должности, которые он должен выдавать.", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Произошла ошибка: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StaffCommands(bot))