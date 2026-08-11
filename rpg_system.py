import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import random
import time
from database import DB_PATH, get_user, update_user

# ==========================================
# 📜 БАЗА ИЗ 30 УНИКАЛЬНЫХ ЗАДАНИЙ
# ==========================================
QUESTS = {
    # 💬 АКТИВНОСТЬ В ЧАТЕ (6 заданий)
    "msg_10": {"name": "Связист I", "desc": "Написать 10 сообщений в чатах", "type": "msg", "target": 10, "coins": 100, "xp": 15},
    "msg_50": {"name": "Связист II", "desc": "Написать 50 сообщений в чатах", "type": "msg", "target": 50, "coins": 250, "xp": 30},
    "msg_100": {"name": "Связист III", "desc": "Написать 100 сообщений в чатах", "type": "msg", "target": 100, "coins": 500, "xp": 60},
    "msg_250": {"name": "Душа компании", "desc": "Написать 250 сообщений в чатах", "type": "msg", "target": 250, "coins": 1000, "xp": 120},
    "msg_500": {"name": "Мастер коммуникаций", "desc": "Написать 500 сообщений в чатах", "type": "msg", "target": 500, "coins": 2000, "xp": 250},
    "msg_1000": {"name": "Голос сервера", "desc": "Написать 1,000 сообщений в чатах", "type": "msg", "target": 1000, "coins": 5000, "xp": 500},
    
    # 🎧 АКТИВНОСТЬ В VOICE (6 заданий)
    "voice_15": {"name": "Радиообмен I", "desc": "Провести в голосовых каналах 15 минут", "type": "voice", "target": 15, "coins": 150, "xp": 20},
    "voice_60": {"name": "Радиообмен II", "desc": "Провести в голосовых каналах 1 час (60 мин)", "type": "voice", "target": 60, "coins": 400, "xp": 50},
    "voice_120": {"name": "Собрание синдиката", "desc": "Провести в голосовых каналах 2 часа (120 мин)", "type": "voice", "target": 120, "coins": 1000, "xp": 100},
    "voice_300": {"name": "Долгая смена", "desc": "Провести в голосовых каналах 5 часов (300 мин)", "type": "voice", "target": 300, "coins": 2500, "xp": 300},
    "voice_600": {"name": "Жизнь на орбите", "desc": "Провести в голосовых каналах 10 часов (600 мин)", "type": "voice", "target": 600, "coins": 5000, "xp": 600},
    "voice_1200": {"name": "Сон в капсуле", "desc": "Провести в голосовых каналах 20 часов", "type": "voice", "target": 1200, "coins": 12000, "xp": 1000},

    # 💰 ЭКОНОМИКА: НАЛИЧНЫЕ (3 задания)
    "bal_1k": {"name": "Накопления I", "desc": "Иметь на руках 1,000 наличных монет", "type": "balance", "target": 1000, "coins": 200, "xp": 25},
    "bal_5k": {"name": "Накопления II", "desc": "Иметь на руках 5,000 наличных монет", "type": "balance", "target": 5000, "coins": 750, "xp": 75},
    "bal_25k": {"name": "Капиталист", "desc": "Иметь на руках 25,000 наличных монет", "type": "balance", "target": 25000, "coins": 3000, "xp": 200},
    
    # 🏦 ЭКОНОМИКА: БАНК (3 задания)
    "bank_5k": {"name": "Вкладчик I", "desc": "Иметь на счету в банке 5,000 монет", "type": "bank", "target": 5000, "coins": 500, "xp": 50},
    "bank_50k": {"name": "Вкладчик II", "desc": "Иметь на счету в банке 50,000 монет", "type": "bank", "target": 50000, "coins": 4000, "xp": 300},
    "bank_100k": {"name": "Инвестор", "desc": "Иметь на счету в банке 100,000 монет", "type": "bank", "target": 100000, "coins": 10000, "xp": 500},

    # 🏆 УРОВНИ И RPG (4 задания)
    "lvl_3": {"name": "Первые шаги", "desc": "Достичь 3 уровня активности", "type": "level", "target": 3, "coins": 300, "xp": 0},
    "lvl_10": {"name": "Освоившийся", "desc": "Достичь 10 уровня активности", "type": "level", "target": 10, "coins": 1500, "xp": 0},
    "lvl_25": {"name": "Ветеран станции", "desc": "Достичь 25 уровня активности", "type": "level", "target": 25, "coins": 5000, "xp": 0},
    "lvl_50": {"name": "Легенда космоса", "desc": "Достичь 50 уровня активности", "type": "level", "target": 50, "coins": 15000, "xp": 0},

    # 💖 РЕПУТАЦИЯ (3 задания)
    "rep_1": {"name": "Доброе дело", "desc": "Иметь 1 очко репутации (от других)", "type": "rep", "target": 1, "coins": 250, "xp": 50},
    "rep_5": {"name": "Хороший парень", "desc": "Иметь 5 очков репутации", "type": "rep", "target": 5, "coins": 1000, "xp": 150},
    "rep_15": {"name": "Авторитет", "desc": "Иметь 15 очков репутации", "type": "rep", "target": 15, "coins": 4000, "xp": 400},

    # 💼 ПРОФЕССИИ (3 задания)
    "job_miner": {"name": "Тяжелый труд", "desc": "Устроиться на работу «Шахтер»", "type": "job", "target": "Шахтер", "coins": 200, "xp": 20},
    "job_biz": {"name": "Белый воротничок", "desc": "Устроиться на работу «Бизнесмен»", "type": "job", "target": "Бизнесмен", "coins": 200, "xp": 20},
    "job_hacker": {"name": "Взлом системы", "desc": "Устроиться на работу «Хакер»", "type": "job", "target": "Хакер", "coins": 200, "xp": 20},

    # 🤝 СОЦИАЛЬНЫЕ (2 задания)
    "social_clan": {"name": "Братство", "desc": "Состоять в любом клане", "type": "clan", "target": 1, "coins": 1000, "xp": 100},
    "social_marry": {"name": "Вторая половинка", "desc": "Найти партнера (заключить брак)", "type": "partner", "target": 1, "coins": 1500, "xp": 150}
}

# ==========================================
# ВНУТРЕННИЕ ФУНКЦИИ ДЛЯ РАБОТЫ С БД КВЕСТОВ
# ==========================================
async def get_quest_data(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Авто-создание колонок, если их еще нет в базе
        try:
            await db.execute("ALTER TABLE users ADD COLUMN active_quest TEXT DEFAULT ''")
            await db.execute("ALTER TABLE users ADD COLUMN quest_progress INTEGER DEFAULT 0")
            await db.execute("ALTER TABLE users ADD COLUMN completed_quests TEXT DEFAULT ''")
            await db.commit()
        except:
            pass
        
        async with db.execute("SELECT active_quest, quest_progress, completed_quests FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row: return row[0] or "", row[1] or 0, row[2] or ""
            return "", 0, ""

async def update_quest_data(user_id: int, quest_id: str, progress: int, completed: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        if completed is not None:
            await db.execute("UPDATE users SET active_quest = ?, quest_progress = ?, completed_quests = ? WHERE user_id = ?", (quest_id, progress, completed, user_id))
        else:
            await db.execute("UPDATE users SET active_quest = ?, quest_progress = ? WHERE user_id = ?", (quest_id, progress, user_id))
        await db.commit()

# ==========================================
# ОСНОВНОЙ КЛАСС КОГОВ
# ==========================================
class RPGSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_joins = {} # Словарь для отслеживания времени входа в войс

    # 1. ТРЕКЕР СООБЩЕНИЙ
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        quest_id, progress, _ = await get_quest_data(message.author.id)
        if quest_id and QUESTS.get(quest_id) and QUESTS[quest_id]["type"] == "msg":
            await update_quest_data(message.author.id, quest_id, progress + 1)

    # 2. ТРЕКЕР ГОЛОСОВЫХ КАНАЛОВ (В МИНУТАХ)
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot: return
        
        # Пользователь зашел в любой войс
        if before.channel is None and after.channel is not None:
            self.voice_joins[member.id] = time.time()
            
        # Пользователь полностью вышел из войса
        elif before.channel is not None and after.channel is None:
            join_time = self.voice_joins.pop(member.id, None)
            if join_time:
                minutes_spent = int((time.time() - join_time) / 60)
                if minutes_spent > 0:
                    quest_id, progress, _ = await get_quest_data(member.id)
                    if quest_id and QUESTS.get(quest_id) and QUESTS[quest_id]["type"] == "voice":
                        await update_quest_data(member.id, quest_id, progress + minutes_spent)

    # ==========================================
    # БЛОК СОЦИАЛЬНЫХ КОМАНД (ПРОФИЛЬ, ИНВЕНТАРЬ)
    # ==========================================
    @app_commands.command(name="profile", description="Посмотреть свой или чужой профиль")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user_data = await get_user(target.id)
        
        if not user_data:
            return await interaction.response.send_message(f"❌ Профиль {target.display_name} еще не создан в базе.", ephemeral=True)
        
        balance = user_data[2] if user_data[2] is not None else 0
        xp = user_data[4] if user_data[4] is not None else 0
        level = user_data[5] if user_data[5] is not None else 0
        partner = user_data[7] if user_data[7] is not None else 0
        rep = user_data[9] if user_data[9] is not None else 0
        bank = user_data[10] if user_data[10] is not None else 0
        job = user_data[12] if user_data[12] is not None else "Безработный"
        
        embed = discord.Embed(title=f"📜 Профиль: {target.display_name}", color=target.color or 0x2b2d31)
        if target.avatar: embed.set_thumbnail(url=target.avatar.url)
        
        embed.add_field(name="Уровень", value=f"**{level}** ({xp} XP)", inline=True)
        embed.add_field(name="Репутация", value=f"💖 **{rep}**", inline=True)
        embed.add_field(name="Профессия", value=f"💼 **{job}**", inline=True)
        embed.add_field(name="Наличные", value=f"🪙 **{balance}**", inline=True)
        embed.add_field(name="В банке", value=f"🏦 **{bank}**", inline=True)
        
        partner_text = f"<@{partner}>" if partner != 0 else "Одинок(а)"
        embed.add_field(name="Брак", value=f"💍 {partner_text}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rep", description="Выдать репутацию пользователю (+1 карма)")
    @app_commands.checks.cooldown(1, 43200, key=lambda i: i.user.id)
    async def rep(self, interaction: discord.Interaction, member: discord.Member):
        if member == interaction.user or member.bot:
            return await interaction.response.send_message("❌ Нельзя выдать репутацию себе или боту.", ephemeral=True)
            
        target_data = await get_user(member.id)
        if not target_data:
            return await interaction.response.send_message("❌ Этот игрок еще не зарегистрирован в базе.", ephemeral=True)

        current_rep = target_data[9] if target_data[9] is not None else 0
        await update_user(member.id, "rep", current_rep + 1)
        await interaction.response.send_message(f"💖 Вы выразили уважение {member.mention}! Теперь его репутация: **{current_rep + 1}**.")

    @app_commands.command(name="inventory", description="Посмотреть свой инвентарь")
    async def inventory(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT item_name, amount FROM inventory WHERE user_id = ?", (interaction.user.id,)) as cursor:
                items = await cursor.fetchall()
                
        if not items: return await interaction.response.send_message("🎒 Ваш инвентарь пуст.", ephemeral=True)
            
        desc = "\n".join([f"🔹 **{item[0]}** — {item[1]} шт." for item in items])
        embed = discord.Embed(title=f"🎒 Инвентарь {interaction.user.display_name}", description=desc, color=0x2b2d31)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="top", description="Топ богачей сервера")
    async def top(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            query = "SELECT user_id, COALESCE(balance, 0) + COALESCE(bank, 0) AS total FROM users ORDER BY total DESC LIMIT 10"
            async with db.execute(query) as cursor:
                top_users = await cursor.fetchall()
                
        if not top_users: return await interaction.response.send_message("❌ В базе данных пока нет богачей.", ephemeral=True)

        desc = ""
        for i, (uid, total) in enumerate(top_users, 1): desc += f"**{i}.** <@{uid}> — **{total}** 🪙\n"
        embed = discord.Embed(title="🏆 Топ богачей", description=desc, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # НОВАЯ СИСТЕМА ЗАДАНИЙ (ГРУППА /quest)
    # ==========================================
    quest = app_commands.Group(name="quest", description="Система продвинутых заданий и квестов")

    @quest.command(name="info", description="Посмотреть текущее активное задание")
    async def quest_info(self, interaction: discord.Interaction):
        quest_id, progress, _ = await get_quest_data(interaction.user.id)
        if not quest_id or quest_id not in QUESTS:
            return await interaction.response.send_message("У вас нет активного задания! Напишите `/quest start`, чтобы взять новое.", ephemeral=True)
            
        q = QUESTS[quest_id]
        embed = discord.Embed(title=f"🎯 Текущее задание: {q['name']}", description=q['desc'], color=0x3498db)
        
        if q["type"] in ["msg", "voice"]:
            progress_bar = f"**{progress}** / {q['target']}"
            embed.add_field(name="Прогресс", value=progress_bar, inline=False)
        else:
            embed.add_field(name="Статус", value="Выполните условия и нажмите `/quest claim`", inline=False)
            
        embed.add_field(name="Награда", value=f"🪙 **{q['coins']}** монет | 🔮 **{q['xp']}** XP", inline=False)
        await interaction.response.send_message(embed=embed)

    @quest.command(name="start", description="Взять новое случайное задание из пула")
    async def quest_start(self, interaction: discord.Interaction):
        quest_id, progress, completed_str = await get_quest_data(interaction.user.id)
        if quest_id:
            return await interaction.response.send_message("❌ У вас уже есть активное задание! Сначала завершите его (`/quest claim`) или отмените (`/quest cancel`).", ephemeral=True)
            
        completed = completed_str.split(",") if completed_str else []
        available = [k for k in QUESTS.keys() if k not in completed]
        
        if not available:
            return await interaction.response.send_message("🎉 Вы выполнили **все 30 заданий** на сервере! Настоящая Легенда.", ephemeral=True)
            
        new_quest_id = random.choice(available)
        await update_quest_data(interaction.user.id, new_quest_id, 0)
        
        q = QUESTS[new_quest_id]
        embed = discord.Embed(title="📜 Получено новое задание!", description=f"**{q['name']}**\n{q['desc']}", color=0xe67e22)
        await interaction.response.send_message(embed=embed)

    @quest.command(name="cancel", description="Отказаться от текущего задания")
    async def quest_cancel(self, interaction: discord.Interaction):
        quest_id, _, _ = await get_quest_data(interaction.user.id)
        if not quest_id:
            return await interaction.response.send_message("У вас и так нет активного задания.", ephemeral=True)
            
        await update_quest_data(interaction.user.id, "", 0)
        await interaction.response.send_message("🗑️ Вы успешно отказались от задания. Теперь можно взять новое через `/quest start`.", ephemeral=True)

    @quest.command(name="claim", description="Получить награду за выполненное задание")
    async def quest_claim(self, interaction: discord.Interaction):
        quest_id, progress, completed_str = await get_quest_data(interaction.user.id)
        if not quest_id or quest_id not in QUESTS:
            return await interaction.response.send_message("❌ У вас нет активного задания.", ephemeral=True)
            
        q = QUESTS[quest_id]
        is_completed = False
        user = await get_user(interaction.user.id)
        
        # Проверка условий выполнения
        if q["type"] in ["msg", "voice"]:
            if progress >= q["target"]: is_completed = True
        elif user:
            if q["type"] == "balance" and (user[2] or 0) >= q["target"]: is_completed = True
            elif q["type"] == "bank" and (user[10] or 0) >= q["target"]: is_completed = True
            elif q["type"] == "level" and (user[5] or 0) >= q["target"]: is_completed = True
            elif q["type"] == "rep" and (user[9] or 0) >= q["target"]: is_completed = True
            elif q["type"] == "job" and user[12] == q["target"]: is_completed = True
            elif q["type"] == "clan" and (user[8] or 0) != 0: is_completed = True
            elif q["type"] == "partner" and (user[7] or 0) != 0: is_completed = True
            
        if is_completed:
            await update_user(interaction.user.id, "balance", (user[2] or 0) + q["coins"])
            await update_user(interaction.user.id, "xp", (user[4] or 0) + q["xp"])
            
            # Заносим квест в список выполненных
            completed = completed_str.split(",") if completed_str else []
            completed.append(quest_id)
            await update_quest_data(interaction.user.id, "", 0, ",".join(completed))
            
            embed = discord.Embed(title="📜 Задание выполнено!", description=f"Вы успешно завершили **«{q['name']}»**!", color=0x2ecc71)
            embed.add_field(name="Награда", value=f"**+{q['coins']}** 🪙\n**+{q['xp']}** XP", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            prog_text = f"Прогресс: {progress} / {q['target']}" if q["type"] in ["msg", "voice"] else "Условие еще не выполнено. Проверьте свой профиль!"
            await interaction.response.send_message(f"❌ Задание **«{q['name']}»** еще не завершено.\n{prog_text}", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            minutes, seconds = divmod(int(error.retry_after), 60)
            hours, minutes = divmod(minutes, 60)
            time_str = f"**{hours} ч {minutes} мин**" if hours > 0 else f"**{minutes} мин {seconds} сек**"
            await interaction.response.send_message(f"⏳ Команда пока недоступна. Подождите {time_str}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RPGSystem(bot))