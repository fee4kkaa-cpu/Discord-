import discord
from discord.ext import commands
from discord import app_commands
import random

class MafiaJoinView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Участвовать", style=discord.ButtonStyle.success, emoji="🎲")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cog.game_started:
            return await interaction.response.send_message("❌ Игра уже началась!", ephemeral=True)
            
        if interaction.user in self.cog.players:
            return await interaction.response.send_message("❌ Ты уже записан на игру!", ephemeral=True)
            
        self.cog.players.append(interaction.user)
        await interaction.response.send_message("✅ Ты успешно присоединился к игре!", ephemeral=True)
        
        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"Зарегистрировано игроков: {len(self.cog.players)}")
        await interaction.message.edit(embed=embed)


class MafiaGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = []
        self.alive_players = [] # Список живых
        self.roles = {}
        self.game_started = False
        self.phase = "day" # Может быть "day" или "night"
        
        # Словарь для записи ночных действий
        self.night_actions = {
            "kill": None,  # Кого убивает мафия
            "heal": None,  # Кого лечит доктор
            "block": None  # К кому идет путана (блокирует действие)
        }

    @app_commands.command(name="mafia_reg", description="Начать набор игроков в Мафию")
    async def mafia_reg(self, interaction: discord.Interaction):
        self.players = []
        self.alive_players = []
        self.roles = {}
        self.game_started = False
        self.phase = "day"
        
        embed = discord.Embed(
            title="🕵️ Регистрация на игру в Мафию",
            description="Нажмите на кнопку ниже, чтобы присоединиться!\nЖдем всех желающих.",
            color=discord.Color.dark_theme()
        )
        embed.set_footer(text="Зарегистрировано игроков: 0")
        await interaction.response.send_message(embed=embed, view=MafiaJoinView(self))

    @app_commands.command(name="mafia_start", description="Раздать роли и начать игру")
    async def mafia_start(self, interaction: discord.Interaction):
        if self.game_started:
            return await interaction.response.send_message("❌ Игра уже идет!", ephemeral=True)
            
        if len(self.players) < 4:
            return await interaction.response.send_message(f"❌ Слишком мало игроков ({len(self.players)}). Нужно минимум 4!", ephemeral=True)

        self.game_started = True
        self.alive_players = self.players.copy()
        
        available_roles = ["Дон мафии 🕴️", "Комиссар 👮", "Доктор 👨‍⚕️", "Путана 💋", "Мафия 🔫"]
        random.shuffle(self.players)
        
        for i, player in enumerate(self.players):
            if i < len(available_roles):
                self.roles[player] = available_roles[i]
            else:
                self.roles[player] = "Мирный житель 👱"

        await interaction.response.send_message("✅ **Игра началась!** Рассылаю роли в ЛС...")

        for player, role in self.roles.items():
            try:
                embed = discord.Embed(
                    title="🎭 Твоя роль на эту игру",
                    description=f"Ты играешь за: **{role}**\n\nНикому не рассказывай!",
                    color=discord.Color.red() if "Мафия" in role or "Дон" in role else discord.Color.blue()
                )
                await player.send(embed=embed)
            except discord.Forbidden:
                await interaction.channel.send(f"⚠️ {player.mention}, открой ЛС! Я не смог отправить тебе роль.")

    # --- НОЧНЫЕ КОМАНДЫ (Для игроков) ---

    @app_commands.command(name="mafia_kill", description="[Ночь] Выбрать жертву (только Мафия/Дон)")
    async def action_kill(self, interaction: discord.Interaction, target: discord.Member):
        if self.phase != "night":
            return await interaction.response.send_message("❌ Сейчас не ночь!", ephemeral=True)
        if interaction.user not in self.alive_players:
            return await interaction.response.send_message("❌ Вы мертвы или не в игре.", ephemeral=True)
            
        role = self.roles.get(interaction.user, "")
        if "Мафия" not in role and "Дон" not in role:
            return await interaction.response.send_message("❌ У вас нет прав на убийство!", ephemeral=True)
            
        if target not in self.alive_players:
            return await interaction.response.send_message("❌ Этот игрок уже мертв или не играет.", ephemeral=True)

        self.night_actions["kill"] = target
        await interaction.response.send_message(f"🔫 Вы прицелились в {target.display_name}. Ждите утра.", ephemeral=True)

    @app_commands.command(name="mafia_heal", description="[Ночь] Вылечить игрока (только Доктор)")
    async def action_heal(self, interaction: discord.Interaction, target: discord.Member):
        if self.phase != "night":
            return await interaction.response.send_message("❌ Сейчас не ночь!", ephemeral=True)
            
        role = self.roles.get(interaction.user, "")
        if "Доктор" not in role:
            return await interaction.response.send_message("❌ Вы не Доктор!", ephemeral=True)

        self.night_actions["heal"] = target
        await interaction.response.send_message(f"💉 Вы отправились лечить {target.display_name}.", ephemeral=True)

    @app_commands.command(name="mafia_visit", description="[Ночь] Навестить игрока (только Путана)")
    async def action_visit(self, interaction: discord.Interaction, target: discord.Member):
        if self.phase != "night":
            return await interaction.response.send_message("❌ Сейчас не ночь!", ephemeral=True)
            
        role = self.roles.get(interaction.user, "")
        if "Путана" not in role:
            return await interaction.response.send_message("❌ Эта команда не для вас!", ephemeral=True)

        self.night_actions["block"] = target
        await interaction.response.send_message(f"💋 Вы отправились к {target.display_name}. Сегодня он ничего не сделает.", ephemeral=True)

    # --- УПРАВЛЕНИЕ ФАЗАМИ (Для ведущего) ---

    @app_commands.command(name="mafia_night", description="Ведущий: Объявить наступление ночи")
    async def mafia_night(self, interaction: discord.Interaction):
        if not self.game_started:
            return await interaction.response.send_message("❌ Игра еще не началась.", ephemeral=True)
            
        self.phase = "night"
        # Очищаем действия с прошлой ночи
        self.night_actions = {"kill": None, "heal": None, "block": None}
        
        embed = discord.Embed(
            title="🌙 Город засыпает...",
            description="Просыпается мафия и активные роли.\nИспользуйте команды `/mafia_kill`, `/mafia_heal`, `/mafia_visit` в чате (ответы бота будут скрыты от других).",
            color=discord.Color.dark_blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mafia_day", description="Ведущий: Объявить утро и подвести итоги")
    async def mafia_day(self, interaction: discord.Interaction):
        if self.phase != "night":
            return await interaction.response.send_message("❌ Сейчас не ночь!", ephemeral=True)
            
        self.phase = "day"
        
        # Получаем тех, кто что-то делал
        kill_target = self.night_actions["kill"]
        heal_target = self.night_actions["heal"]
        blocked_target = self.night_actions["block"]

        # Логика ночи
        news = ""
        died_tonight = None

        # Если мафию заблокировала путана, убийство отменяется
        mafia_users = [p for p in self.alive_players if "Мафия" in self.roles[p] or "Дон" in self.roles[p]]
        mafia_blocked = any(m == blocked_target for m in mafia_users)

        if kill_target:
            if mafia_blocked:
                news += "💋 Путана наведалась к Мафии и сорвала их планы на убийство!\n"
            elif kill_target == heal_target:
                news += f"👨‍⚕️ Мафия пыталась убить **{kill_target.display_name}**, но Доктор вовремя спас его!\n"
            else:
                news += f"💀 Этой ночью была жестоко убита жертва Мафии: **{kill_target.display_name}**.\n"
                died_tonight = kill_target

        if not news:
            news = "Этой ночью в городе было на удивление тихо. Никто не пострадал."

        # Обрабатываем смерть
        if died_tonight and died_tonight in self.alive_players:
            self.alive_players.remove(died_tonight)

        embed = discord.Embed(
            title="☀️ Город просыпается!",
            description=f"**Сводка новостей:**\n{news}\n\nЖивых игроков осталось: **{len(self.alive_players)}**.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mafia_stop", description="Принудительно остановить игру")
    async def mafia_stop(self, interaction: discord.Interaction):
        self.players = []
        self.alive_players = []
        self.roles = {}
        self.game_started = False
        await interaction.response.send_message("🛑 Игра в Мафию была остановлена.")

async def setup(bot):
    await bot.add_cog(MafiaGame(bot))