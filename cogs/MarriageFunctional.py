import discord, time
from datetime import datetime, timezone
from discord import app_commands
from discord.ext import commands
from database.db_logic import DB_Manager

from config import BotConfig
from safe_commands import *

# --- КНОПКА ЗАВЕСТИ РЕБЁНКА ---
class ChildView(discord.ui.View):
    def __init__(self, parent_id: int, spouse_id: int, child_id: int, marriage_manager):
        super().__init__(timeout=300)
        self.parent_id = parent_id
        self.spouse_id = spouse_id
        self.child_id = child_id
        self.manager = marriage_manager
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.child_id:
            await safe_send(interaction, "<:deniedemoji:1519737463126360294> Это предложение стать ребёнком не для вас!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👶 Стать ребёнком", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверяем, что родители все ещё в браке
        if not self.manager.is_married(self.parent_id):
            await interaction.response.edit_message(
                content="<:deniedemoji:1519737463126360294> Предложение недействительно: родитель больше не состоит в браке.",
                embed=None,
                view=None
            )
            return

        if self.manager.is_child_in_any_family(self.child_id):
            await interaction.response.edit_message(
                content="<:deniedemoji:1519737463126360294> Вы уже состоите в чьей-то семье!",
                embed=None,
                view=None
            )
            return

        result = self.manager.add_child(self.parent_id, self.child_id)

        if result == "limit_reached":
            await interaction.response.edit_message(
                content="<:deniedemoji:1519737463126360294> В этой семье уже достигнут лимит в `10 детей`!",
                embed=None,
                view=None
            )
        elif result == "already_exists":
            await interaction.response.edit_message(
                content="<:deniedemoji:1519737463126360294> Вы уже являетесь ребёнком в этой семье!",
                embed=None,
                view=None
            )
        elif result == "success":
            embed = discord.Embed(
                title="<:kissemoji:1528331667583012975> ⲡⲟⲡⲟⲗⲏⲉⲏυⲉ ⲃ ⲥⲉⲙьⲉ!",
                description=f"<@{self.child_id}> ᴛᴇᴨᴇᴩь ᴩᴇбᴇноᴋ ʙ ᴄᴇʍьᴇ <@{self.parent_id}> и <@{self.spouse_id}>!",
                color=discord.Color.light_grey(),
                timestamp=discord.utils.utcnow()
            )
            user_avatar = interaction.user.display_avatar.url if interaction.user.display_avatar else None
            embed.set_image(url='https://i.pinimg.com/originals/fc/d4/48/fcd448709cec07713a2db9cb2d40fbb9.gif')
            embed.set_footer(
                text="Семья пополнилась • Взаимное согласие",
                icon_url=user_avatar
            )
            await interaction.response.edit_message(content=None, embed=embed, view=None)
        else:
            await interaction.response.edit_message(
                content="<:deniedemoji:1519737463126360294> Не удалось завести ребёнка. Проверьте данные брака.",
                embed=None,
                view=None
            )

    @discord.ui.button(label="❌ Отказать", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content=f"<:deniedemoji:1519737463126360294> <@{self.child_id}> оᴛᴋᴀзᴀᴧ(ᴀ)ᴄь ᴄᴛᴀᴛь ᴩᴇбᴇнᴋоʍ ʙ ᴄᴇʍьᴇ <@{self.parent_id}>.",
            embed=None,
            view=None)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(
                    content="<:timeemoji:1524124492236980316> ʙᴩᴇʍя ожидᴀния оᴛʙᴇᴛᴀ нᴀ ᴨᴩᴇдᴧожᴇниᴇ ᴄᴛᴀᴛь ᴩᴇбёнᴋоʍ иᴄᴛᴇᴋᴧо.",
                    embed=None,
                    view=None
                )
            except:
                pass

# --- КНОПКА ПОЖЕНИТЬСЯ ---
class MarriageView(discord.ui.View):
    def __init__(self, proposer_id: int, target_id: int, marriage_manager):
        super().__init__(timeout=300)
        self.proposer_id = proposer_id
        self.target_id = target_id
        self.manager = marriage_manager  # Передаем менеджер явно
        self.message = None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target_id:
            await safe_send(interaction, "<:deniedemoji:1519737463126360294> Это предложение не для вас!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="💍 Принять", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверяем актуальность статусов перед заключением брака
        if self.manager.is_married(self.proposer_id) or self.manager.is_married(self.target_id):
            # Если кто-то уже женился, отключаем/удаляем эту форму, чтобы избежать спама
            await interaction.response.edit_message(
                content="<:deniedemoji:1519737463126360294> Предложение более недействительно (один из пользователей уже в браке).", 
                embed=None, 
                view=None # Кнопки исчезнут
            )
            return

        result = self.manager.create_marriage_funbot(self.proposer_id, self.target_id)
        
        if "✅" in result:
            embed = discord.Embed(
                title="<:ringemoji:1523657901569212426> бᴩᴀᴋ зᴀᴋᴧючᴇн!",
                description=f"<@{self.proposer_id}> и <@{self.target_id}> ᴛᴇᴨᴇᴩь ʍуж и жᴇнᴀ! <:giveawayemoji:1515792000279121930>",
                color=discord.Color.pink(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_image(url='https://i.pinimg.com/originals/5a/f9/b5/5af9b5f196e80f530aa19fcffa711e39.gif')
            
            # --- КРАСИВЫЙ СТИЛЬНЫЙ ФУТЕР ---
            # Пытаемся взять аватарку согласившегося пользователя для украшения футера
            user_avatar = interaction.user.display_avatar.url if interaction.user.display_avatar else None
            embed.set_footer(
                text=f"💞 Новая семья создана • Взаимное согласие", 
                icon_url=user_avatar
            )
            
            # Изменяем исходное сообщение: убираем контент, ставим Embed и УДАЛЯЕМ кнопки (view=None)
            await interaction.response.edit_message(content=None, embed=embed, view=None)
            
            # Дополнительное уведомление в чат с пингом
            try:
                if interaction.channel:
                    await interaction.channel.send(
                        f"<:hugemoji:1528331401223606322> <@{self.proposer_id}>, ваш брак успешно заключен с <@{self.target_id}>!"
                    )
            except:
                pass
        else:
            # Если база данных вернула иную ошибку
            await interaction.response.edit_message(view=None) # Убираем кнопки, так как запрос провалился
            await safe_send(interaction, f"<:deniedemoji:1519737463126360294> {result}", ephemeral=True)

    @discord.ui.button(label="❌ Отказать", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Обновляем сообщение, фиксируя отказ, и полностью удаляем кнопки (view=None)
        await interaction.response.edit_message(
            content=f"<:deniedemoji:1519737463126360294> <@{self.target_id}> оᴛᴋᴀзᴀᴧ(ᴀ) ʙ бᴩᴀᴋᴇ ᴄ ᴨоᴧьзоʙᴀᴛᴇᴧᴇʍ <@{self.proposer_id}>.",
            embed=None, 
            view=None
        )
    
    async def on_timeout(self):
        if self.message:
            try:
                # По таймауту также полностью стираем кнопки (view=None)
                await self.message.edit(
                    content="⏳ Время ожидания ответа на предложение истекло.", 
                    embed=None, 
                    view=None
                )
            except:
                pass

# --- КНОПКА ПОДТВЕРЖДЕНИЯ РАЗВОДА ---
class DivorceView(discord.ui.View):
    def __init__(self, user_id: int, spouse_id: int, marriage_manager, bot_client):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.spouse_id = spouse_id
        self.manager = marriage_manager
        self.bot = bot_client
        self.message = None
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await safe_send(interaction, "<:deniedemoji:1519737463126360294> Это не ваш бракоразводный процесс!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="💔 Подтвердить развод", style=discord.ButtonStyle.danger)
    async def confirm_divorce(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Двойная проверка: проверяем, состоит ли пользователь всё ещё в браке перед удалением
        if not self.manager.is_married(self.user_id):
            await interaction.response.edit_message(
                content="<:deniedemoji:1519737463126360294> Данные о браке уже отсутствуют или изменены.", 
                embed=None, 
                view=None
            )
            return

        success, message = self.manager.divorce_simple(self.user_id)
        
        if success:
            embed = discord.Embed(
                title="<:brokenheartemoji:1523753728375656588> бᴩᴀᴋ ᴩᴀᴄᴛоᴩᴦнуᴛ",
                description=f"<@{self.user_id}> ᴩᴀзʙᴇᴧᴄя(ᴀᴄь) ᴄ <@{self.spouse_id}>.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_image(url='https://i.pinimg.com/originals/5c/3f/d0/5c3fd04b1e985a8bddd87ae3c7e58827.gif')
            
            # --- КРАСИВЫЙ СТИЛЬНЫЙ ФУТЕР ---
            user_avatar = interaction.user.display_avatar.url if interaction.user.display_avatar else None
            embed.set_footer(
                text="💔 Свободный статус • Брак расторгнут",
                icon_url=user_avatar
            )
            
            # Редактируем сообщение: ставим Эмбед развода и ПОЛНОСТЬЮ убираем кнопки (view=None)
            await interaction.response.edit_message(content=None, embed=embed, view=None)
            
            # Пингуем бывшего супруга в чате отдельным сообщением
            try:
                spouse = await self.bot.fetch_user(self.spouse_id)
                if interaction.channel:
                    await interaction.channel.send(f"{spouse.mention}, ваш брак был расторгнут. <:brokenheartemoji:1523753728375656588>")
            except:
                pass
        else:
            await interaction.response.edit_message(view=None)
            await safe_send(interaction, f"<:deniedemoji:1519737463126360294> {message}", ephemeral=True)
    
    @discord.ui.button(label="❌ Отмена", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # При отмене полностью убираем эмбед и исчезают кнопки (view=None)
        await interaction.response.edit_message(
            content="<:heartemoji:1516740800518557696> ᴩᴀзʙод оᴛʍᴇнᴇн. ᴄᴇʍья ᴄохᴩᴀнᴇнᴀ!", 
            embed=None, 
            view=None
        )
    
    async def on_timeout(self):
        if self.message:
            try:
                # По истечении времени кнопки также бесследно исчезают (view=None)
                await self.message.edit(
                    content="⏳ Время для подтверждения развода вышло. Действие отменено.", 
                    embed=None, 
                    view=None
                )
            except:
                pass

# --- ГЛАВНЫЙ КЛАСС КОГА ---
class MarriageFunctional(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manager = DB_Manager(BotConfig.DB_PATH)

    @app_commands.command(name="мой_брак", description="Показать информацию о вашем браке.")
    @app_commands.describe(user="Пользователь, информацию о браке которого вы хотите узнать.")
    @app_commands.guild_only()
    async def marriage_info(self, interaction: discord.Interaction, user: discord.Member = None):
        # Если пользователь не указан, берем автора команды
        target_user = user if user else interaction.user
        
        # Использование переданного через контекст менеджера (или глобального manager)
        if not self.manager.is_married(target_user.id):
            msg = "Вы не состоите в браке." if target_user.id == interaction.user.id else f"{target_user.mention} не состоит в браке."
            return await safe_send(interaction, f"<:deniedemoji:1519737463126360294> {msg}", ephemeral=True)
            
        spouse_id = self.manager.get_spouse(target_user.id)
        marriage_data = self.manager.get_information_marry(target_user.id)
        
        if spouse_id is None or marriage_data is None:
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> Не удалось найти данные о браке в базе данных.", ephemeral=True)
            
        # Безопасное получение объекта супруга
        try:
            spouse = await self.bot.fetch_user(spouse_id)
            spouse_name = spouse.mention
            spouse_avatar = spouse.display_avatar.url
        except Exception:
            spouse_name = f"<@{spouse_id}>"
            spouse_avatar = None
            
        created_at = marriage_data['created_at']
        # Корректное преобразование временных меток Discord
        created_dt = discord.utils.format_dt(datetime.fromtimestamp(created_at, tz=timezone.utc), 'f')
        relative_dt = discord.utils.format_dt(datetime.fromtimestamp(created_at, tz=timezone.utc), 'R')
        
        # Вычисляем точную длительность брака
        delta_seconds = int(time.time() - created_at)
        days = delta_seconds // 86400
        hours = (delta_seconds % 86400) // 3600
        minutes = (delta_seconds % 3600) // 60
        
        if days > 0:
            duration = f"{days} дн. {hours} ч. {minutes} мин."
        elif hours > 0:
            duration = f"{hours} ч. {minutes} мин."
        else:
            duration = f"{max(0, minutes)} мин."

        embed = discord.Embed(
            title="<:ringemoji:1523657901569212426> инɸоᴩʍᴀция о бᴩᴀᴋᴇ",
            color=discord.Color.pink(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="<:smilefaceemoji:1524123343370977448> ᴄуᴨᴩуᴦ(ᴀ)",
            value=spouse_name,
            inline=False
        )
        embed.add_field(
            name="<:starsemoji:1519768273925705749> дᴀᴛᴀ зᴀᴋᴧючᴇния",
            value=f"{created_dt}\n({relative_dt})",
            inline=False
        )
        embed.add_field(
            name="<:timeemoji:1524124492236980316> дᴧиᴛᴇᴧьноᴄᴛь",
            value=f"`{duration}`",
            inline=True
        )
        # --- ПОЛУЧЕНИЕ И ФОРМАТИРОВАНИЕ СПИСКА ДЕТЕЙ ---
        children_list = self.manager.get_children(target_user.id)
        if children_list:
            children_mentions = ", ".join([f"<@{child_id}>" for child_id in children_list])
            children_value = f"{children_mentions}\n*(Всего: {len(children_list)}/10)*"
        else:
            children_value = "Детей пока нет"

        embed.add_field(
            name="<:kidemoji:1529537899668967544> дᴇᴛи",
            value=children_value,
            inline=False
        )
        
        if spouse_avatar:
            embed.set_thumbnail(url=spouse_avatar)
            
        embed.set_footer(
            text=f"Запросил: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await safe_send(interaction, embed=embed, ephemeral=False)


    @app_commands.command(name="заключить_брак", description="Предложить брак пользователю.")
    @app_commands.describe(user="Пользователь, которому вы предлагаете брак")
    @app_commands.guild_only()
    async def propose_marriage(self, interaction: discord.Interaction, user: discord.Member):
        # Валидация целей предложения
        if user.id == interaction.user.id:
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> Нельзя жениться на самом себе!", ephemeral=True)
            
        if user.bot:
            return await safe_send(interaction, "🤖 Нельзя жениться на боте!", ephemeral=True)
            
        if self.manager.is_married(interaction.user.id):
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> Вы уже состоите в браке!", ephemeral=True)
            
        if self.manager.is_married(user.id):
            return await safe_send(interaction, f"<:deniedemoji:1519737463126360294> {user.mention} уже состоит в браке!", ephemeral=True)
        
        # Инициализация View с явной передачей менеджера
        view = MarriageView(proposer_id=interaction.user.id, target_id=user.id, marriage_manager=self.manager)
        
        embed = discord.Embed(
            title="<:ringemoji:1523657901569212426> ᴨᴩᴇдᴧожᴇниᴇ бᴩᴀᴋᴀ",
            description=f"{interaction.user.mention} ᴨᴩᴇдᴧᴀᴦᴀᴇᴛ бᴩᴀᴋ {user.mention}!",
            color=discord.Color.pink(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="<:clockemoji:1523658304281116672> ʙᴩᴇʍя нᴀ оᴛʙᴇᴛ",
            value="300 ᴄᴇᴋунд",
            inline=True
        )
        embed.set_image(url='https://i.pinimg.com/originals/f9/ab/3f/f9ab3f93ea21d12d5a0363262a4b8802.gif')
        embed.set_footer(text="Нажмите кнопку для ответа")
        
        # Отправляем сообщение и ОБЯЗАТЕЛЬНО сохраняем его в view.message для таймаутов
        msg = await safe_send(interaction, content=f"{user.mention}, у ʙᴀᴄ ᴇᴄᴛь ᴨᴩᴇдᴧожᴇниᴇ!", embed=embed, view=view)
        if msg:
            view.message = msg\

    @app_commands.command(name="завести_ребенка", description="Завести/усыновить ребёнка в вашу семью.")
    @app_commands.describe(user="Пользователь, которого вы хотите завести в качестве ребёнка")
    @app_commands.guild_only()
    async def adopt_child(self, interaction: discord.Interaction, user: discord.Member):
        # 1. Проверяем, состоит ли автор в браке
        if not self.manager.is_married(interaction.user.id):
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> Вы должны состоять в браке, чтобы завести ребёнка!", ephemeral=True)

        spouse_id = self.manager.get_spouse(interaction.user.id)

        # 2. Проверки на цель
        if user.id == interaction.user.id:
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> Вы не можете стать собственным ребёнком!", ephemeral=True)

        if user.id == spouse_id:
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> Вы не можете завести вашего супруга(у) в качестве ребёнка!", ephemeral=True)

        if self.manager.is_child_in_any_family(user.id):
            return await safe_send(
                interaction, 
                f"<:deniedemoji:1519737463126360294> {user.mention} уже состоит в другой семье!", 
                ephemeral=True
            )

        if user.bot:
            return await safe_send(interaction, "🤖 Нельзя завести бота в качестве ребёнка!", ephemeral=True)

        # 3. Проверка лимита детей
        current_children = self.manager.get_children(interaction.user.id)
        if len(current_children) >= 10:
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> В вашей семье уже достигнут лимит в 10 детей!", ephemeral=True)

        if user.id in current_children:
            return await safe_send(interaction, f"<:deniedemoji:1519737463126360294> {user.mention} уже является ребёнком в вашей семье!", ephemeral=True)

        # Инициализируем UI-view с кнопками для будущего ребёнка
        view = ChildView(
            parent_id=interaction.user.id,
            spouse_id=spouse_id,
            child_id=user.id,
            marriage_manager=self.manager
        )

        embed = discord.Embed(
            title="<:kidemoji:1529537899668967544> ᴨᴩᴇдᴧожᴇниᴇ ᴄᴛᴀᴛь ᴩᴇбᴇнᴋоʍ",
            description=f"{interaction.user.mention} и <@{spouse_id}> хоᴛяᴛ зᴀʙᴇᴄᴛи {user.mention} ʙ ᴋᴀчᴇᴄᴛʙᴇ ᴩᴇбᴇнᴋᴀ!",
            color=discord.Color.light_grey(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="<:clockemoji:1523658304281116672> ʙᴩᴇʍя нᴀ оᴛʙᴇᴛ",
            value="300 ᴄᴇᴋунд",
            inline=True
        )
        embed.set_image(url='https://i.pinimg.com/originals/4a/bb/2b/4abb2bac931994a75c6ac774720f8750.gif')
        embed.set_footer(text="Нажмите кнопку для ответа")

        msg = await safe_send(interaction, content=f"{user.mention}, вам поступило предложение!", embed=embed, view=view)
        if msg:
            view.message = msg

    @app_commands.command(name="развод", description="Расторгнуть брак.")
    @app_commands.guild_only()
    async def divorce_command(self, interaction: discord.Interaction):
        if not self.manager.is_married(interaction.user.id):
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> Вы не состоите в браке!", ephemeral=True)
            
        spouse_id = self.manager.get_spouse(interaction.user.id)
        if spouse_id is None:
            return await safe_send(interaction, "<:deniedemoji:1519737463126360294> Не удалось найти данные о браке.", ephemeral=True)
        
        try:
            spouse = await self.bot.fetch_user(spouse_id)
            spouse_name = spouse.mention
        except Exception:
            spouse_name = f"<@{spouse_id}>"
        
        # Инициализируем View развода с передачей менеджера и клиента бота
        view = DivorceView(user_id=interaction.user.id, spouse_id=spouse_id, marriage_manager=self.manager, bot_client=self.bot)
        
        embed = discord.Embed(
            title="<:brokenheartemoji:1523753728375656588> ᴨодᴛʙᴇᴩждᴇниᴇ ᴩᴀзʙодᴀ",
            description=f"ʙы уʙᴇᴩᴇны, чᴛо хоᴛиᴛᴇ ᴩᴀзʙᴇᴄᴛиᴄь ᴄ {spouse_name}?",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="<:cautionemoji:1520064481357598770> ʙниʍᴀниᴇ",
            value="϶ᴛо дᴇйᴄᴛʙиᴇ нᴇᴧьзя оᴛʍᴇниᴛь!",
            inline=False
        )
        embed.add_field(
            name="<:clockemoji:1523658304281116672> ʙᴩᴇʍя нᴀ оᴛʙᴇᴛ",
            value="30 ᴄᴇᴋунд",
            inline=True
        )
        embed.set_image(url='https://i.pinimg.com/originals/81/cc/04/81cc045c3e66f8b54c71a2a85a64cc9d.gif')
        embed.set_footer(text="Нажмите кнопку для подтверждения")
        
        # Отправляем сообщение и привязываем его к view.message
        msg = await safe_send(interaction, embed=embed, view=view, ephemeral=False)
        if msg:
            view.message = msg


async def setup(bot):
    await bot.add_cog(MarriageFunctional(bot))