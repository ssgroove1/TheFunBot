import discord
from discord import app_commands
from discord.ext import commands

from config import BotConfig
from safe_commands import *

# --- ГЛАВНЫЙ КЛАСС КОГА ---
class TechicalCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ========== КОМАНДА ДЛЯ РЕГУЛИРОВКИ ==========

    @app_commands.command(name='sync', description='Синхронизировать команды только для этого сервера.')
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def sync_command(self, interaction: discord.Interaction):
        if interaction.user.id != BotConfig.DEVELOPER_ID:
            # Для взаимодействия (Slash-команд) лучше использовать interaction.response.send_message
            # Если ваша функция safe_send адаптирована под interaction, оставляйте её
            await safe_send(interaction, "<:deniedemoji:1519737463126360294> У тебя нет прав для этой команды.", ephemeral=True)
            return

        # Отправляем предварительное сообщение, так как синхронизация может занять пару секунд
        await interaction.response.defer(ephemeral=True)

        try:
            current_guild = interaction.guild

            # 1. Очищаем глобальные команды, чтобы они не разлетались по всему Discord
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync(guild=None)

            # 2. Копируем глобальные команды бота в дерево текущего сервера
            self.bot.tree.copy_global_to(guild=current_guild)

            # 3. Синхронизируем команды конкретно для этого сервера (происходит мгновенно)
            await self.bot.tree.sync(guild=current_guild)

            # Отвечаем об успешном завершении
            await interaction.followup.send(
                f"<:confirmedemoji:1519738036936638474> Команды успешно синхронизированы для сервера **{current_guild.name}**.",
                ephemeral=False
            )

        except Exception as e:
            await interaction.followup.send(f"❌ Произошла ошибка при синхронизации: {e}", ephemeral=True)

    @app_commands.command(name='status', description='Статус бота.')
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def status_of_bot(self, interaction: discord.Interaction):
        # 1. Сразу сообщаем Discord, что мы приняли команду и думаем (избегаем таймаута в 3 секунды)
        await interaction.response.defer(ephemeral=True)

        # 2. Проверка разработчика
        if interaction.user.id != BotConfig.DEVELOPER_ID:
            await safe_send(
                interaction, 
                "<:forbiddenemoji:1515780232404144279> У тебя нет прав для этой команды.", 
                ephemeral=True
            )
            return

        # 3. Отправляем ответ с использованием safe_send
        # Важно: ephemeral=True здесь обязателен, так как defer() был сделан скрытым
        await safe_send(
            interaction, 
            f"{interaction.user.mention}, бот ещё жив! <:grantedemoji:1520173483299049623>",
            ephemeral=True
        )

    @app_commands.command(name='set', description='[Разработчик] Установить текущее число для канала подсчёта.')
    @app_commands.describe(last_count="Последнее верно названное число в канале (по умолчанию 0)")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def set_count(self, interaction: discord.Interaction, last_count: int = 0):
        # 1. Жесткая проверка на ID разработчика
        if interaction.user.id != BotConfig.DEVELOPER_ID:
            return await safe_send(
                interaction, 
                "<:deniedemoji:1519737463126360294> Эта команда доступна только главному разработчику бота.", 
                ephemeral=True)
            
        # 2. Валидация значения (счётчик обычно не может быть меньше 0)
        if last_count < 0:
            return await safe_send(
                interaction, 
                "❌ Число не может быть отрицательным!", 
                ephemeral=True
            )

        # 3. Присвоение значения (убраны лишние int(), так как тип уже гарантирован discord.py)
        BotConfig.next_number_in_count_channel = last_count + 1
        
        # 4. Отправка подтверждения
        await safe_send(
            interaction, 
            f"<:confirmedemoji:1519738036936638474> Счётчик успешно перезаписан!\n"
            f"• Последнее число: `{last_count}`\n"
            f"• Ожидаемое следующее число: `{BotConfig.next_number_in_count_channel}`", 
            ephemeral=True)

async def setup(bot):
    await bot.add_cog(TechicalCommands(bot))