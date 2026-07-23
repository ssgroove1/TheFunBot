import discord, asyncio, random, re
from datetime import datetime, timezone, timedelta
from discord import app_commands
from discord.ext import commands

from safe_commands import *

# --- КНОПКА УЧАСТИЯ (Для публичного сообщения) ---
class PublicGiveawayView(discord.ui.View):
    def __init__(self, manager):
        super().__init__(timeout=None)
        self.manager = manager
        self.lock = asyncio.Lock()  # Блокировка от одновременных нажатий (Race Condition)

    @discord.ui.button(label="учᴀᴄᴛʙоʙᴀᴛь (0)", style=discord.ButtonStyle.green, custom_id="public_join")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.manager.is_ended or self.manager.is_cancelled:
            return await safe_send(interaction, "Розыгрыш уже завершен или отменен.", ephemeral=True)
        
        user_id = interaction.user.id
        
        async with self.lock:  # Гарантирует атомарность изменения списка участников
            if user_id in self.manager.participants:
                self.manager.participants.remove(user_id)
                msg = "Вы вышли из розыгрыша."
            else:
                self.manager.participants.add(user_id)
                msg = "Вы успешно зарегистрировались в розыгрыше!"
            
            button.label = f"учᴀᴄᴛʙоʙᴀᴛь ({len(self.manager.participants)})"
            
            # Правильное обновление сообщения через response, чтобы Discord не выдавал ошибку таймаута
            await interaction.response.edit_message(view=self)
            
        # Отправляем сообщение подтверждения после успешного обновления кнопки
        await safe_send(interaction, msg, ephemeral=True)


# --- КНОПКИ УПРАВЛЕНИЯ (Для скрытого сообщения) ---
class AdminControlView(discord.ui.View):
    def __init__(self, manager):
        super().__init__(timeout=None)
        self.manager = manager

    @discord.ui.button(label="оᴛʍᴇниᴛь ᴩозыᴦᴩыɯ", style=discord.ButtonStyle.red, custom_id="admin_cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Исправлено: Добавлен await для safe_send
        if not interaction.user.guild_permissions.administrator:
            return await safe_send(interaction, "У вас нет прав для отмены этого розыгрыша.", ephemeral=True)
            
        if self.manager.is_ended or self.manager.is_cancelled:
            return await safe_send(interaction, "Этот розыгрыш уже нельзя отменить.", ephemeral=True)
            
        self.manager.is_cancelled = True
        self.manager.event.set() 
        
        # Отключаем кнопки управления админа
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
                
        # Отключаем кнопки участников на публичном сообщении
        if self.manager.public_view:
            for child in self.manager.public_view.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
                    
        # Модифицируем эмбед
        if self.manager.public_embed:
            self.manager.public_embed.description = (
                f"{self.manager.description}\n\n"
                f"<:forbiddenemoji:1515790567555203123> **ᴩозыᴦᴩыɯ быᴧ оᴛʍᴇнᴇн ᴀдʍиниᴄᴛᴩᴀᴛоᴩоʍ.**"
            )
            self.manager.public_embed.color = discord.Color.red()
            
        # Обновляем публичное сообщение
        if self.manager.public_message and self.manager.public_view:
            await self.manager.public_message.edit(embed=self.manager.public_embed, view=self.manager.public_view)
            
        # Подтверждаем действие админа
        await interaction.response.edit_message(view=self)
        await safe_send(interaction, "Вы успешно отменили розыгрыш.", ephemeral=True)

    @discord.ui.button(label="зᴀʙᴇᴩɯиᴛь доᴄᴩочно", style=discord.ButtonStyle.blurple, custom_id="admin_end_fast")
    async def end_fast_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await safe_send(interaction, "У вас нет прав для досрочного завершения.", ephemeral=True)
            
        if self.manager.is_ended or self.manager.is_cancelled:
            return await safe_send(interaction, "Розыгрыш нельзя завершить.", ephemeral=True)
            
        self.manager.is_ended = True
        self.manager.event.set()  # Пробуждаем главный цикл розыгрыша для подведения итогов
        
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
                
        await interaction.response.edit_message(view=self)
        await safe_send(interaction, "Розыгрыш завершается досрочно...", ephemeral=True)


# --- ГЛАВНЫЙ КОНТРОЛЛЕР РОЗЫГРЫША ---
class GiveawayManager:
    def __init__(self, description: str, prize_text_after: str, mention_role: discord.Role = None):
        self.description = description
        self.prize_text_after = prize_text_after
        self.mention_role = mention_role
        
        self.participants = set()
        self.is_cancelled = False
        self.is_ended = False
        self.event = asyncio.Event()
        
        self.public_message = None
        self.public_embed = None
        self.public_view = None

# --- ГЛАВНЫЙ КЛАСС КОГА ---
class GiveawayFunctional(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def parse_duration(self, duration_str: str) -> int:
        # Убираем пробелы по краям и приводим к нижнему регистру
        duration_str = duration_str.strip().lower()
        
        # Регулярное выражение с поддержкой возможных пробелов между числом и буквой (\s*)
        if not (match := re.match(r"^(\d+)\s*([smhd])$", duration_str)):
            return 0
            
        amount = int(match.group(1))
        unit = match.group(2)
        
        # Защита от переполнения/слишком больших чисел
        if amount > 1000000:
            return 0
            
        units = {
            "s": 1,          # секунды
            "m": 60,         # минуты
            "h": 3600,       # часы
            "d": 86400       # дни
        }
        
        seconds = amount * units[unit]
        
        # Ограничение: розыгрыш не может идти дольше 1 года (31,536,000 секунд)
        if seconds > 31536000:
            return 0
            
        return seconds

    @app_commands.command(name="giveaway", description="Запустить новый розыгрыш")
    @app_commands.describe(
        описание="Текст самого розыгрыша (что происходит)",
        приз_после_выигрыша="Текст, который пишется при победе",
        время="Через сколько итоги? (Пример: 10m, 2h, 1d)",
        количество_победителей="Сколько человек должно выиграть?",
        роль_для_упоминания="Какую роль пингануть при победе (необязательно)",
        канал="Канал, куда отправить розыгрыш (необязательно)"
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_events=True)
    async def giveaway(self,
        interaction: discord.Interaction,
        описание: str,
        приз_после_выигрыша: str,
        время: str,
        количество_победителей: int,
        роль_для_упоминания: discord.Role = None,
        канал: discord.TextChannel = None
    ):
        # 1. Валидация входных данных
        if количество_победителей <= 0:
            return await safe_send(interaction, "❌ Количество победителей должно быть больше 0!", ephemeral=True)
            
        seconds = self.parse_duration(время)
        if seconds <= 0:
            return await safe_send(interaction, "❌ Неверный формат времени! Используйте, например: 30s, 15m, 2h, 1d.", ephemeral=True)

        # Выбор целевого канала
        target_channel = канал if канал else interaction.channel
        
        # 2. Расчет времени завершения
        end_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        timestamp = int(end_time.timestamp())

        # 3. Инициализация менеджера
        manager = GiveawayManager(описание, приз_после_выигрыша, роль_для_упоминания)

        # Настройка публичного эмбеда
        manager.public_embed = discord.Embed(
            title="<:giveawayemoji:1515792000279121930> ⲏⲟⲃыύ ⲣⲟⳅыⲅⲣыɯ! <:giveawayemoji:1515792000279121930>",
            description=f"{описание}\n\n<:luckyemoji:1515790408922173450> **ᴨобᴇдиᴛᴇᴧᴇй:** {количество_победителей}\n<:timeemoji:1524124492236980316> **зᴀʙᴇᴩɯиᴛᴄя:** <t:{timestamp}:R>",
            color=discord.Color.gold(),
        )
        manager.public_embed.set_footer(text="нᴀжʍиᴛᴇ нᴀ ᴋноᴨᴋу нижᴇ, чᴛобы ᴨᴩиняᴛь учᴀᴄᴛиᴇ!")
        manager.public_view = PublicGiveawayView(manager)

        # Исправлено: Публичное сообщение в канал отправляем через стандартный .send(), 
        # чтобы не ломать логику safe_send, завязанную на interaction.
        manager.public_message = await target_channel.send(embed=manager.public_embed, view=manager.public_view)
        
        # Отправка скрытой панели управления администратору
        admin_view = AdminControlView(manager)
        await safe_send(
            interaction, 
            f"<:confirmedemoji:1519738036936638474> Розыгрыш успешно запущен в канале {target_channel.mention}!\nПанель управления доступна только вам ниже:", 
            view=admin_view,
            ephemeral=True
        )
        
        # 4. Ожидание завершения таймера или нажатия админ-кнопок
        try:
            await asyncio.wait_for(manager.event.wait(), timeout=float(seconds))
        except asyncio.TimeoutError:
            pass

        # Если розыгрыш был отменен — прерываем выполнение (эмбед уже обновлен внутри AdminControlView)
        if manager.is_cancelled:
            return

        # 5. Блокировка кнопок участия
        if manager.public_view:
            for child in manager.public_view.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
        
        # Красивое изменение описания в зависимости от того, как завершился розыгрыш
        if manager.is_ended:
            # Если завершили досрочно кнопкой
            status_text = "<:forbiddenemoji:1515790567555203123> **ᴩозыᴦᴩыɯ зᴀʙᴇᴩɯᴇн доᴄᴩочно!**"
            manager.public_embed.color = discord.Color.blurple()
        else:
            # Если завершился сам по таймеру
            status_text = "<:forbiddenemoji:1515790567555203123> **ᴩозыᴦᴩыɯ зᴀʙᴇᴩɯᴇн!**"
            manager.public_embed.color = discord.Color.dark_grey()

        manager.public_embed.description = f"{описание}\n\n<:luckyemoji:1515790408922173450> **ᴨобᴇдиᴛᴇᴧᴇй:** {количество_победителей}\n{status_text}"
        await manager.public_message.edit(embed=manager.public_embed, view=manager.public_view)

        # 6. Подведение итогов и выбор победителей
        if not manager.participants:
            no_participants_embed = discord.Embed(
                description=f"ʙ ᴩозыᴦᴩыɯᴇ **'{описание}'** ниᴋᴛо нᴇ ᴨᴩиняᴧ учᴀᴄᴛиᴇ. ᴨобᴇдиᴛᴇᴧи нᴇ ʙыбᴩᴀны. <:forbiddenemoji:1515790567555203123>",
                color=discord.Color.red()
            )
            await target_channel.send(embed=no_participants_embed)
        else:
            participants_list = list(manager.participants)
            actual_winners_count = min(количество_победителей, len(participants_list))
            winners_ids = random.sample(participants_list, k=actual_winners_count)
            
            # Создаем упоминания
            winners_mentions = [f"<@{w_id}>" for w_id in winners_ids]
            winners_text = ", ".join(winners_mentions)
            
            # Формируем строку пинга роли (если она задана)
            mention_str = f"\n🔔 Уведомление для роли: {manager.mention_role.mention}" if manager.mention_role else ""
            
            # Определяем корректный заголовок
            title_text = (
                "<:giveawayemoji:1515792000279121930> ⲣⲉⳅⲩⲗьⲧⲁⲧы ⲣⲟⳅыⲅⲣыɯⲁ! <:giveawayemoji:1515792000279121930>" 
                if actual_winners_count > 1 else 
                "<:giveawayemoji:1515792000279121930> ⲣⲉⳅⲩⲗьⲧⲁⲧ ⲣⲟⳅыⲅⲣыɯⲁ! <:giveawayemoji:1515792000279121930>"
            )

            success_embed = discord.Embed(
                title=title_text,
                description=f"ʙ ᴩозыᴦᴩыɯᴇ **'{описание}'**\n<:luckyemoji:1515790408922173450> ᴨобᴇждᴀюᴛ: {winners_text}!\n\n**<:treasureemoji:1515794261839188199> Ваш выигрыш:** {manager.prize_text_after}{mention_str}",
                color=discord.Color.green(),
            )
            
            # Отправляем текстовый пинг вместе с красивым Эмбедом, чтобы победители получили уведомление
            await target_channel.send(content=winners_text, embed=success_embed)
    

async def setup(bot):
    await bot.add_cog(GiveawayFunctional(bot))