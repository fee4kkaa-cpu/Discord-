import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# ================= НАСТРОЙКИ МАГАЗИНА =================
DB_PATH = "nebula.db"
PRIVATE_ROOMS_CATEGORY_ID = "1527080134530699276" # ВПИШИ СЮДА СВОЙ ID КАТЕГОРИИ ДЛЯ КОМНАТ!
# ======================================================

def init_shop_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Создаем таблицу, если ее вообще нет
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, bank INTEGER DEFAULT 0, 
        xp INTEGER DEFAULT 0, voice_time INTEGER DEFAULT 0, messages INTEGER DEFAULT 0,
        bio TEXT DEFAULT 'Я играю на NEBULA!', profile_color TEXT DEFAULT '2f3136'
    )""")
    
    # АВТО-ПОЧИНКА: Добавляем колонки, если их забыл создать другой ког
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    needed_columns = {
        'balance': 'INTEGER DEFAULT 0', 'bank': 'INTEGER DEFAULT 0',
        'xp': 'INTEGER DEFAULT 0', 'voice_time': 'INTEGER DEFAULT 0', 'messages': 'INTEGER DEFAULT 0',
        'bio': "TEXT DEFAULT 'Я играю на NEBULA!'", 'profile_color': "TEXT DEFAULT '2f3136'"
    }
    for col, dtype in needed_columns.items():
        if col not in columns:
            try: cur.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
            except: pass

    cur.execute("""CREATE TABLE IF NOT EXISTS user_rooms (
        user_id INTEGER PRIMARY KEY, room_name TEXT, channel_id INTEGER
    )""")
    conn.commit()
    conn.close()

# Умный поиск имени колонки (user_id или id)
def get_id_col():
    conn = sqlite3.connect(DB_PATH)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    conn.close()
    return "user_id" if "user_id" in cols else "id"

def get_balance(uid):
    id_col = get_id_col()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT balance FROM users WHERE {id_col} = ?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute(f"INSERT INTO users ({id_col}) VALUES (?)", (uid,))
        conn.commit()
        row = (0,)
    conn.close()
    return row[0]

def update_balance(uid, amount):
    id_col = get_id_col()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET balance = balance + ? WHERE {id_col} = ?", (amount, uid))
    conn.commit()
    conn.close()

# --- 1. МОДАЛЬНЫЕ ОКНА ---
class RoomNameModal(discord.ui.Modal):
    def __init__(self, action: str, price: int):
        super().__init__(title="Настройка приватной комнаты")
        self.action = action 
        self.price = price
        self.room_name = discord.ui.TextInput(
            label="Введите название комнаты", placeholder="Например: Nebula Lounge", min_length=2, max_length=30, required=True
        )
        self.add_item(self.room_name)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        
        update_balance(user_id, -self.price)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        if self.action == "create":
            category = interaction.guild.get_channel(PRIVATE_ROOMS_CATEGORY_ID)
            if not category:
                return await interaction.followup.send("❌ Категория комнат не настроена. Сообщите администратору.")
            
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
                interaction.user: discord.PermissionOverwrite(manage_channels=True, connect=True, speak=True)
            }
            channel = await interaction.guild.create_voice_channel(
                name=self.room_name.value, category=category, overwrites=overwrites, reason="Покупка личной комнаты"
            )
            cur.execute("INSERT OR REPLACE INTO user_rooms (user_id, room_name, channel_id) VALUES (?, ?, ?)", 
                        (user_id, self.room_name.value, channel.id))
            await interaction.followup.send(f"✅ Комната {channel.mention} успешно создана! Списано: **{self.price}** 🪙")

        elif self.action == "rename":
            cur.execute("SELECT channel_id FROM user_rooms WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if row:
                channel = interaction.guild.get_channel(row[0])
                if channel: await channel.edit(name=self.room_name.value)
                cur.execute("UPDATE user_rooms SET room_name = ? WHERE user_id = ?", (self.room_name.value, user_id))
                await interaction.followup.send(f"✅ Название изменено на **{self.room_name.value}**! Списано: **{self.price}** 🪙")
            else:
                update_balance(user_id, self.price)
                await interaction.followup.send("❌ У вас нет комнаты для переименования!")

        conn.commit(); conn.close()


class CustomizationModal(discord.ui.Modal):
    def __init__(self, target: str, price: int):
        super().__init__(title="Смена БИО" if target == "bio" else "Смена цвета профиля")
        self.target, self.price = target, price

        if target == "bio":
            self.val = discord.ui.TextInput(label="Новое БИО", placeholder="Я крутой игрок сервера Nebula!", max_length=100)
        else:
            self.val = discord.ui.TextInput(label="HEX-Код цвета (без #)", placeholder="ff0000 (Красный)", min_length=6, max_length=6)
        self.add_item(self.val)

    async def on_submit(self, interaction: discord.Interaction):
        update_balance(interaction.user.id, -self.price)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        id_col = get_id_col()
        
        if self.target == "bio":
            cur.execute(f"UPDATE users SET bio = ? WHERE {id_col} = ?", (self.val.value, interaction.user.id))
            msg = "✅ Ваше БИО успешно обновлено!"
        else:
            cur.execute(f"UPDATE users SET profile_color = ? WHERE {id_col} = ?", (self.val.value, interaction.user.id))
            msg = "✅ Цвет профиля успешно обновлен!"
            
        conn.commit(); conn.close()
        await interaction.response.send_message(f"{msg} Списано: **{self.price}** 🪙", ephemeral=True)


# --- 2. ИНТЕРФЕЙС МАГАЗИНА ---
class ShopDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Приватные комнаты", description="Создание и настройка своих войсов", emoji="🏠", value="rooms"),
            discord.SelectOption(label="Кастомизация", description="Настройка профиля, био и цвета", emoji="🎨", value="custom")
        ]
        super().__init__(placeholder="Выберите категорию товаров...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        balance = get_balance(interaction.user.id)
        embed = discord.Embed(title="🛒 Магазин NEBULA", color=0x9b59b6)
        embed.set_footer(text=f"Ваш баланс: {balance} монет")

        view = discord.ui.View(timeout=None)
        
        if self.values[0] == "rooms":
            embed.description = "**🏠 Приватные комнаты**\nВаш личный уголок на сервере."
            view.add_item(discord.ui.Button(label="Купить комнату (5000 🪙)", style=discord.ButtonStyle.success, custom_id="shop_buy_room"))
            view.add_item(discord.ui.Button(label="Изменить название (500 🪙)", style=discord.ButtonStyle.secondary, custom_id="shop_rename_room"))

        elif self.values[0] == "custom":
            embed.description = "**🎨 Кастомизация профиля**\nСделайте свой профиль уникальным!"
            view.add_item(discord.ui.Button(label="Сменить БИО (300 🪙)", style=discord.ButtonStyle.primary, custom_id="shop_bio"))
            view.add_item(discord.ui.Button(label="Цвет профиля (1000 🪙)", style=discord.ButtonStyle.primary, custom_id="shop_color"))

        view.add_item(ShopDropdown())
        await interaction.response.edit_message(embed=embed, view=view)


class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ShopDropdown())


# --- 3. ОСНОВНОЙ КОГ ---
class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_shop_db()

    @app_commands.command(name="shop", description="Открыть магазин NEBULA")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🛍️ Магазин NEBULA", description="Добро пожаловать в магазин! Выберите категорию товаров в меню ниже.", color=0x9b59b6)
        if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed, view=ShopView())

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component: return
        custom_id = interaction.data.get("custom_id", "")
        user_id = interaction.user.id

        if custom_id == "shop_buy_room":
            if get_balance(user_id) < 5000: return await interaction.response.send_message("❌ Недостаточно средств! Нужно 5000 🪙.", ephemeral=True)
            conn = sqlite3.connect(DB_PATH)
            if conn.execute("SELECT * FROM user_rooms WHERE user_id = ?", (user_id,)).fetchone():
                conn.close()
                return await interaction.response.send_message("❌ У вас уже есть приватная комната!", ephemeral=True)
            conn.close()
            await interaction.response.send_modal(RoomNameModal("create", 5000))

        elif custom_id == "shop_rename_room":
            if get_balance(user_id) < 500: return await interaction.response.send_message("❌ Нужно 500 🪙.", ephemeral=True)
            await interaction.response.send_modal(RoomNameModal("rename", 500))

        elif custom_id == "shop_bio":
            if get_balance(user_id) < 300: return await interaction.response.send_message("❌ Нужно 300 🪙.", ephemeral=True)
            await interaction.response.send_modal(CustomizationModal("bio", 300))

        elif custom_id == "shop_color":
            if get_balance(user_id) < 1000: return await interaction.response.send_message("❌ Нужно 1000 🪙.", ephemeral=True)
            await interaction.response.send_modal(CustomizationModal("color", 1000))

async def setup(bot):
    await bot.add_cog(ShopCog(bot))

