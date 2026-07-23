import discord, random
from pathlib import Path
from discord import app_commands
from discord.ext import commands

from safe_commands import *

# --- НАСТРОЙКА ПУТЕЙ И ЧТЕНИЕ ФАЙЛОВ С ГИФКАМИ ---
BASE_DIR = Path(__file__).parent.resolve()
gifs_dir = BASE_DIR / "gifs"

print(f"🔍 Бот ищет папку с гифками по пути: {gifs_dir}")

# Словарь для хранения списков гифок
gifs_data = {}
gif_files = ["hug", "kiss", "hello", "flower", "pat", "slap", "bite", "cry", "dance", "ice_cream", "smile", "pokemon"]

for name in gif_files:
    file_path = gifs_dir / f"{name}_gifs.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Читаем строки, очищаем от пробелов и убираем пустые строки
            lines = [line.strip() for line in f.readlines() if line.strip()]
            gifs_data[f"{name}_gifs"] = lines
            # Выводим в консоль успешный статус, чтобы вы видели, что файлы прочитались
            print(f"✅ Успешно загружен файл: {name}_gifs.txt (Найдено гифок: {len(lines)})")
    except FileNotFoundError:
        print(f"⚠️ Файл НЕ НАЙДЕН по пути: {file_path}. Инициализирован пустой список.")
        gifs_data[f"{name}_gifs"] = []

# --- ИНТЕРАКТИВНАЯ КНОПКА ПОЛУЧЕНИЯ ЦВЕТОВ ---
class GetFlowerView(discord.ui.View):
    def __init__(self, user: discord.Member, target: discord.Member, text: str):
        super().__init__(timeout=300)
        self.user = user
        self.target = target
        self.text = text
        self.message = None
    
    @discord.ui.button(label="получить цветы", style=discord.ButtonStyle.primary, emoji="💐")
    async def get_flower_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверяем, не пытается ли отправитель забрать свои же цветы
        if interaction.user.id == self.user.id:
            await safe_send(interaction, "🤗 Вы не можете забрать свои же цветы!", ephemeral=True)
            return
        # Проверяем, для того ли человека предназначены цветы
        elif interaction.user.id != self.target.id:
            await safe_send(interaction, "😡 Цветы предназначены не для вас!", ephemeral=True)
            return
        
        # Обновляем состояние кнопки
        button.disabled = True
        button.label = "цветы получены"
        button.style = discord.ButtonStyle.secondary
        button.emoji = "🌹"
        
        try:
            await interaction.response.edit_message(view=self)
        except Exception:
            try:
                await interaction.edit_original_response(view=self)
            except Exception:
                pass
        
        # Отправляем теплое подтверждение в чат
        await safe_send(
            interaction, 
            f"<:drinkemoji:1528327054364381296> {self.target.mention} успешно получает цветы от {self.user.mention}!\n<:pinkletter:1528326773987737610> С пожеланиями: **{self.text}**", 
            ephemeral=True
        )
    
    async def on_timeout(self):
        # Отключаем все кнопки при таймауте
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
                child.emoji = "🥀"
                child.label = "цветы сгнили"
                child.style = discord.ButtonStyle.secondary
                
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

# --- ГЛАВНЫЙ КЛАСС КОГА ---
class RoleplayFunctional(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ========== КОМАНДЫ РАЗВЛЕЧЕНИЯ ==========

    # Вспомогательный метод для выполнения ролевых действий
    async def _execute_action(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member, 
        gifs_key: str, 
        embed_title: str, 
        action_verb: str, 
        color: discord.Color, 
        self_error: str
    ):
        if not gifs_key.endswith("_gifs"):
            pure_name = gifs_key
            gifs_key = f"{pure_name}_gifs"
        else:
            pure_name = gifs_key.replace("_gifs", "")

        # Получение списка гифок из глобального словаря gifs_data
        gifs_list = gifs_data.get(gifs_key, [])
        
        # Если список пуст или ключа нет
        if not gifs_list:
            # Выведет красивое и точное имя файла, который бот не смог найти
            await safe_send(
                interaction, 
                f"<:deniedemoji:1519737463126360294> Нет доступных гифок! Проверьте файл {pure_name}_gifs.txt", 
                ephemeral=True
            )
            return

        # 3. Валидация
        if member.bot:
            await safe_send(interaction, "🤖 Нельзя использовать интерактивные действия на ботах!", ephemeral=True)
            return

        if member.id == interaction.user.id:
            await safe_send(interaction, self_error, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        # 4. Сборка и отправка
        random_gif = random.choice(gifs_list)
        embed = discord.Embed(
            title=embed_title,
            description=f"{interaction.user.mention} {action_verb} {member.mention}!",
            color=color
        )
        embed.set_image(url=random_gif)
        embed.set_footer(
            text=f"Вызвал(а): {interaction.user.display_name}", 
            icon_url=interaction.user.display_avatar.url
        )
        await safe_send(interaction, embed=embed, ephemeral=False)

    # Вспомогательный метод для выполнения ОДИНОЧНЫХ ролевых действий
    async def _execute_solo_action(
        self, 
        interaction: discord.Interaction, 
        gifs_key: str, 
        embed_title: str, 
        description_text: str, 
        footer_verb: str,
        color: discord.Color
    ):

        if not gifs_key.endswith("_gifs"):
            pure_name = gifs_key
            gifs_key = f"{pure_name}_gifs"
        else:
            pure_name = gifs_key.replace("_gifs", "")

        # Получение списка гифок из глобального словаря gifs_data
        gifs_list = gifs_data.get(gifs_key, [])
        
        # Если список пуст или ключа нет
        if not gifs_list:
            # Выведет красивое и точное имя файла, который бот не смог найти
            await safe_send(
                interaction, 
                f"<:deniedemoji:1519737463126360294> Нет доступных гифок! Проверьте файл {pure_name}_gifs.txt", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=False)

        # 3. Выбор гифки и сборка Embed
        random_gif = random.choice(gifs_list)
        embed = discord.Embed(
            title=embed_title,
            description=f"{interaction.user.mention} {description_text}",
            color=color,
            timestamp=interaction.created_at
        )
        embed.set_footer(
            text=f"{footer_verb}: {interaction.user.display_name}", 
            icon_url=interaction.user.display_avatar.url
        )
        embed.set_image(url=random_gif)

        # 4. Отправка
        await safe_send(interaction, embed=embed, ephemeral=False)


    # 🫂 1. Команда: Обнять
    @app_commands.command(name='обнять', description='Обнимите дорогого вам человека!')
    @app_commands.describe(member="Кого вы хотите обнять")
    @app_commands.guild_only()
    async def hug_command(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="hug_gifs",
            embed_title="<:hugemoji:1528331401223606322> Обнимашки!",
            action_verb="обнимает",
            color=discord.Color.pink(),
            self_error="😥 Простите, вы не можете обнять самого себя!"
        )

    # 💋 2. Команда: Поцеловать
    @app_commands.command(name='поцеловать', description='Поцелуйте дорогого вам человека!')
    @app_commands.describe(member="Кого вы хотите поцеловать")
    @app_commands.guild_only()
    async def kiss_command(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="kiss_gifs",
            embed_title="<:kissemoji:1528331667583012975> Поцелуйчики!",
            action_verb="поцеловал(а)",
            color=discord.Color.brand_red(),
            self_error="😥 Простите, вы не можете поцеловать самого себя!"
        )

    # 👋 3. Команда: Поздороваться
    @app_commands.command(name='поздароваться', description='Поздоровайтесь с пользователем!')
    @app_commands.describe(member="С кем поздароваться")
    @app_commands.guild_only()
    async def hello_command(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="hello_gifs",
            embed_title="<:smilefaceemoji:1524123343370977448> Приветствие!",
            action_verb="поздоровался(лась) с",
            color=discord.Color.gold(),
            self_error="😥 Простите, вы не можете поздороваться с собой!"
        )

    # 🐱 4. Команда: Погладить
    @app_commands.command(name='погладить', description='Погладить пользователя!')
    @app_commands.describe(member="Кого погладить")
    @app_commands.guild_only()
    async def pat_command(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="pat_gifs",
            embed_title="<:patemoji:1528331054694268938> Прижимашки!",
            action_verb="погладил(а)",
            color=discord.Color.purple(),
            self_error="😥 Простите, вы не можете погладить себя!"
        )

    # 💥 5. Команда: Ударить (Лещ)
    @app_commands.command(name='ударить', description='Дать леща пользователю!')
    @app_commands.describe(member="Кому дать леща")
    @app_commands.guild_only()
    async def slap_command(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="slap_gifs",
            embed_title="<:emergencyemoji:1519769135767228576> Рукоприкладство!",
            action_verb="дал(а) леща",
            color=discord.Color.darker_grey(),
            self_error="😏 Вы не можете ударить себя самого!"
        )

    # 🦷 6. Команда: Укусить
    @app_commands.command(name='укусить', description='Укусить пользователя!')
    @app_commands.describe(member="Кого укусить")
    @app_commands.guild_only()
    async def bite_command(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="bite_gifs",
            embed_title="<:biteemoji:1528329875981734019> Укусики!",
            action_verb="кусает",
            color=discord.Color.darker_grey(),
            self_error="<:bitingemoji:1528330124422811749> Вы не можете кусать себя самого!"
        )

    # 😭 Команда: Заплакать (Одиночная)
    @app_commands.command(name="заплакать", description="Заплакать в чате.")
    @app_commands.guild_only()
    async def cry_solo_command(self, interaction: discord.Interaction):
        await self._execute_solo_action(
            interaction=interaction,
            gifs_key="cry_gifs",
            embed_title="<:cryemoji2:1529763501642350702> Слезки!",
            description_text="плачет. <:cryingemoji2:1529763168874664047>",
            footer_verb="Грустит",
            color=discord.Color.blue())
        
    # 😁 Команда: Улыбка (Одиночная)
    @app_commands.command(name="улыбнуться", description="Показать улыбку чату.")
    @app_commands.guild_only()
    async def smile_solo_command(self, interaction: discord.Interaction):
        await self._execute_solo_action(
            interaction=interaction,
            gifs_key="smile",  # Теперь проверяется правильный файл!
            embed_title="<:smilefaceemoji:1524123343370977448> Улыбочка!",
            description_text="улыбается! <:smilingemoji:1528328892207599779>",
            footer_verb="Показать улыбку",
            color=discord.Color.from_str("#ffd900"))

    # 💃 Команда: Танцевать (Одиночная)
    @app_commands.command(name="танцевать", description="Зажечь в одиночном танце!")
    @app_commands.guild_only()
    async def dance_solo_command(self, interaction: discord.Interaction):
        await self._execute_solo_action(
            interaction=interaction,
            gifs_key="dance_gifs",  # Теперь проверяется правильный файл!
            embed_title="<:danceemoji:1528328548719263834> Танцульки!",
            description_text="устроил(а) зажигательный танец! <:musicemoji:1528328280023896266>",
            footer_verb="Танцует",
            color=discord.Color.magenta())
        
    # 🍦 Команда: Мороженое (Одиночная)
    @app_commands.command(name="мороженое", description="Покушать мороженое.")
    @app_commands.guild_only()
    async def ice_cream_solo_command(self, interaction: discord.Interaction):
        await self._execute_solo_action(
            interaction=interaction,
            gifs_key="ice_cream",  # Теперь проверяется правильный файл!
            embed_title="<:ice_cream:1528327548558118952> Вкусняшка!",
            description_text="кушает вкусное мороженое! <:ice_cream2:1528327698861002783>",
            footer_verb="Вкусное мороженое",
            color=discord.Color.from_str("#f3efef"))
        
    # ❤️ Команда: Покемон (Одиночная)
    @app_commands.command(name="покемон", description="Поймать покемона.")
    @app_commands.guild_only()
    async def pokemon_solo_command(self, interaction: discord.Interaction):
        await self._execute_solo_action(
            interaction=interaction,
            gifs_key="pokemon",  # Теперь проверяется правильный файл!
            embed_title="<:pokemon:1528322643055607939> Покемончики!",
            description_text="бросает шар с покемоном! <:pokemonball:1528323153233711135>",
            footer_verb="Покемон игрока",
            color=discord.Color.from_str("#ff0000"))

    @app_commands.command(
        name="цветы", 
        description="Подарить пользователю записку с цветами!"
    )
    @app_commands.describe(
        member="Кому вы хотите подарить цветы",
        text="Текст вашего пожелания или записки"
    )
    @app_commands.guild_only()
    async def gift_user(self, interaction: discord.Interaction, member: discord.Member, text: str = "Всего самого наилучшего! 🤗"):
        # Проверка наличия гифок
        if not gifs_data.get('flower_gifs'):
            await safe_send(interaction, "<:deniedemoji:1519737463126360294> Нет доступных гифок! Проверьте файл flower_gifs.txt", ephemeral=True)
            return

        # Валидация участников
        if member == interaction.user:
            await safe_send(interaction, "😥 Простите, вы не можете подарить цветы себе!", ephemeral=True)
            return

        if member.bot:
            await safe_send(interaction, "🤖 Нельзя подарить цветы боту!", ephemeral=True)
            return

        if len(text) > 150:
            await safe_send(interaction, "<:deniedemoji:1519737463126360294> Пожелание не может быть длиннее 150 символов!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        # Выбираем случайную гифку
        random_gif = random.choice(gifs_data['flower_gifs'])
        
        # Сборка Embed
        embed = discord.Embed(
            title="<:flower:1528326611831750789> Цветочки, подарочки!",
            description=f"{interaction.user.mention} подарил(а) {member.mention} цветы! <:pinkletter:1528326773987737610>\n\n**Нажмите на кнопку ниже, чтобы получить подарок!**",
            color=discord.Color.brand_red()
        )
        embed.set_image(url=random_gif)
        embed.set_footer(
            text=f"Исполнитель: {interaction.user.display_name}", 
            icon_url=interaction.user.display_avatar.url
        )

        # Создаем интерактивную панель с кнопкой и отправляем в канал
        view = GetFlowerView(user=interaction.user, target=member, text=text)
        sent_message = await safe_send(interaction, embed=embed, view=view, ephemeral=False)
        
        # Передаем ссылку на сообщение во View для корректной работы таймаута
        view.message = sent_message
    
    # ========== КОНТЕКСТНЫЕ МЕНЮ (ПКМ ПО ПОЛЬЗОВАТЕЛЮ) ==========

    @app_commands.context_menu(name="Обнять")
    @app_commands.guild_only()
    async def show_hug_user(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="hug_gifs",
            embed_title="<:hugemoji:1528331401223606322> Обнимашки!",
            action_verb="обнимает",
            color=discord.Color.pink(),
            self_error="😥 Простите, вы не можете обнять самого себя!"
        )

    @app_commands.context_menu(name="Поцеловать")
    @app_commands.guild_only()
    async def show_kiss_user(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="kiss_gifs",
            embed_title="<:kissemoji:1528331667583012975> Поцелуйчики!",
            action_verb="поцеловал(а)",
            color=discord.Color.brand_red(),
            self_error="😥 Простите, вы не можете поцеловать самого себя!"
        )

    @app_commands.context_menu(name="Поздороваться")
    @app_commands.guild_only()
    async def show_welcome_user(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="hello_gifs",
            embed_title="<:smilefaceemoji:1524123343370977448> Приветствие!",
            action_verb="поздоровался(лась) с",
            color=discord.Color.gold(),
            self_error="😥 Простите, вы не можете поздороваться с собой!"
        )

    @app_commands.context_menu(name="Погладить")
    @app_commands.guild_only()
    async def show_pat_user(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="pat_gifs",
            embed_title="<:patemoji:1528331054694268938> Прижимашки!",
            action_verb="погладил(а)",
            color=discord.Color.purple(),
            self_error="😥 Простите, вы не можете погладить себя!"
        )

    @app_commands.context_menu(name="Ударить")
    @app_commands.guild_only()
    async def show_slap_user(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="slap_gifs",
            embed_title="<:emergencyemoji:1519769135767228576> Рукоприкладство!",
            action_verb="дал(а) леща",
            color=discord.Color.darker_grey(),
            self_error="😏 Вы не можете ударить себя самого!"
        )

    @app_commands.context_menu(name="Укусить")
    @app_commands.guild_only()
    async def show_bite_user(self, interaction: discord.Interaction, member: discord.Member):
        await self._execute_action(
            interaction=interaction,
            member=member,
            gifs_key="bite_gifs",
            embed_title="<:biteemoji:1528329875981734019> Укусики!",
            action_verb="кусает",
            color=discord.Color.darker_grey(),
            self_error="<:bitingemoji:1528330124422811749> Вы не можете кусать себя самого!"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleplayFunctional(bot))