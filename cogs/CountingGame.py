from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands

from config import BotConfig
from safe_commands import safe_delete, safe_send, safe_dm_send


class CountingGame(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Храним данные о последнем успешном сообщении
        # Формат: {"message_id": int, "author": discord.Member/User, "number": int}
        self.last_valid_entry = None
        self.basic_emoji = "<:confirmedemoji:1519738036936638474>"
        self.uncommon_emoji = "<:kissemoji:1528331667583012975>"
        self.rare_emoji = "<:flower:1528326611831750789>"
        self.epic_emoji = "<:danceemoji:1528328548719263834>"

    def cog_load(self):
        """Безопасный запуск восстановления при загрузке кога."""
        # Запускаем фоновую задачу, чтобы не блокировать загрузку когов
        self.bot.loop.create_task(self._initialize_counter())

    async def _initialize_counter(self):
        """Фоновая функция восстановления состояния при старте."""
        # Ждем полной готовности бота
        await self.bot.wait_until_ready()

        channel_id = BotConfig.CHANNELS.get("count")
        if not channel_id:
            print("⚠️ Канал счета не настроен в BotConfig.CHANNELS['count']")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden):
                print(f"⚠️ Не удалось получить канал счета с ID {channel_id}")
                return

        # Ищем последнее сообщение в канале
        try:
            async for message in channel.history(limit=10):
                content = message.content.strip()
                if content.isdigit():
                    number = int(content)
                    # Восстанавливаем следующий порядковый номер
                    BotConfig.next_number_in_count_channel = number + 1

                    # Восстанавливаем информацию о последнем верном сообщении
                    self.last_valid_entry = {
                        "message_id": message.id,
                        "author": message.author,
                        "number": number,
                    }
                    print(
                        f"✅ [CountingGame] Состояние восстановлено! Последнее число: {number}. "
                        f"Следующее число: {BotConfig.next_number_in_count_channel}"
                    )
                    break
        except Exception as e:
            print(f"❌ Ошибка при восстановлении состояния считалочки: {e}")

    async def _safe_add_reaction(self, message: discord.Message, emoji):
        """Безопасная установка реакции без сбоя работы программы."""
        if not emoji:
            return
        try:
            await message.add_reaction(emoji)
        except (discord.HTTPException, discord.InvalidArgument) as e:
            print(f"⚠️ Не удалось поставить реакцию {emoji}: {e}")

    async def remove_role_at_time(
        self, member: discord.Member, role: discord.Role, minutes: int
    ):
        """Вспомогательный асинхронный таск для снятия роли по истечении времени."""
        remove_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        await discord.utils.sleep_until(remove_time)

        if role in member.roles:
            try:
                await member.remove_roles(
                    role, reason="Истекло время наказания в канале счёта"
                )
            except discord.HTTPException:
                pass

    async def _punish_user(self, guild: discord.Guild, author: discord.Member | discord.User, minutes: int = 10):
        """Централизованная функция выдачи наказания и отправки ЛС."""
        role_id = BotConfig.ROLES.get("count_bad")
        if not role_id or not author:
            return

        # Получаем объект Member, если author передан как User
        member = guild.get_member(author.id) if isinstance(author, discord.User) else author

        role = guild.get_role(role_id)
        if role and member and isinstance(member, discord.Member):
            try:
                # 1. Выдаем роль наказания
                await member.add_roles(
                    role,
                    reason="Нарушение правил канала счёта",
                )

                # 2. Формируем Embed для отправки в ЛС
                dm_embed = discord.Embed(
                    title="<:emergencyemoji:1519769135767228576> нᴀᴋᴀзᴀниᴇ ʙ ᴋᴀнᴀᴧᴇ ᴄчёᴛᴀ",
                    description=(
                        f"вы ᴨоᴧучиᴧи ᴩоᴧь **{role.name}** нᴀ ᴄᴇᴩʙᴇᴩᴇ **{guild.name}** "
                        f"из-зᴀ нᴀᴩуɯᴇния ᴨᴩᴀʙиᴧ ʙ ᴋᴀнᴀᴧᴇ ᴄчёᴛᴀ.\n"
                    ),
                    color=discord.Color.brand_red(),
                    timestamp=datetime.now(timezone.utc),
                )
                dm_embed.add_field(name="<:timeemoji:1524124492236980316> дᴧиᴛᴇᴧьноᴄᴛь", value=f"`{minutes} ʍинуᴛ`")
                dm_embed.add_field(
                    name="<:radioemoji:1519767792193110086> ᴋᴀнᴀᴧ",
                    value=f"<#{BotConfig.CHANNELS.get('count')}>",
                    inline=True
                )
                dm_embed.set_thumbnail(url=member.display_avatar.url)

                guild_name = f"cᴇᴩʙᴇᴩ: {guild.name}"
                if guild.icon:
                    dm_embed.set_footer(text=guild_name, icon_url=guild.icon.url)
                else:
                    dm_embed.set_footer(text=guild_name)

                # Отправляем ЛС отдельно, чтобы возможная закрытая личка не ломала выдачу роли
                try:
                    await safe_dm_send(member, embed=dm_embed)
                except Exception as e:
                    print(f"⚠️ Не удалось отправить ЛС пользователю {member.id}: {e}")

                # 3. Запускаем фоновую задачу на снятие роли
                self.bot.loop.create_task(
                    self.remove_role_at_time(member, role, minutes=minutes)
                )

            except discord.HTTPException as e:
                print(f"⚠️ Ошибка при выдаче роли пользователю {author.id}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Проверка канала подсчета
        if message.channel.id != BotConfig.CHANNELS.get("count"):
            return

        # 1. Проверка на соло-счёт (нельзя писать 2 раза подряд)
        # Обратите внимание: проверяем, что предыдущий автор НЕ является ботом
        if (
            self.last_valid_entry
            and self.last_valid_entry["author"].id == message.author.id
            and not self.last_valid_entry["author"].bot
        ):
            await safe_delete(message, delay=1)
            # Наказываем за повторный ввод
            await self._punish_user(message.guild, message.author, minutes=5)

            await safe_send(
                message,
                f"<:deniedemoji:1519737463126360294> {message.author.mention}, пусть другой пользователь напишет следующее число!",
                delete_after=5,
            )
            # ВАЖНО: Прерываем выполнение, чтобы не сработало второе наказание снизу!
            return

        try:
            user_number = int(message.content.strip())
            if user_number != BotConfig.next_number_in_count_channel:
                raise ValueError("Не по порядку")

            # Сохраняем последнее успешно отправленное сообщение
            self.last_valid_entry = {
                "message_id": message.id,
                "author": message.author,
                "number": user_number,
            }

            # Поздравления и реакции на юбилейных числах
            if user_number % 250 == 0:
                await safe_send(
                    message,
                    f"**ⲡⲟⲗьⳅⲟⲃⲁⲧⲉⲗυ, ⲕⲁⲕ ⲿⲉ я ⲃⲁⲙυ ⲅⲟⲣⲿⲩⲥь! <a:animegirl:1523642604124897340>**\n"
                    f"ᴋᴀждый ʙᴀɯ ɯᴀᴦ дᴇᴧᴀᴇᴛ ʍᴇня ᴩᴀдоᴄᴛнᴇᴇ! ᴛᴇᴋущᴇᴇ чиᴄᴧо — {user_number}, нᴇ оᴄᴛᴀнᴀʙᴧиʙᴀйᴛᴇᴄь и нᴇ ᴄдᴀʙᴀйᴛᴇᴄь! <a:akirakogami:1523644045832880218>",
                )
                await self._safe_add_reaction(message, self.epic_emoji)

            elif user_number % 100 == 0:
                await safe_send(
                    message,
                    f"**ⲡⲟⲗьⳅⲟⲃⲁⲧⲉⲗυ, ⲃы ⲇⲟⲥⲧυⲅⲁⲉⲧⲉ ⲃⲉⲣɯυⲏ! ⲅⲟⲣⲿⲩⲥь ⲃⲁⲙυ! <a:yuik:1514940189988880507>**\n"
                    f"ʙы ᴨᴩᴇодоᴧᴇʙᴀᴇᴛᴇ оᴛʍᴇᴛᴋу ʙ {user_number}, нᴇ оᴨуᴄᴋᴀйᴛᴇ ᴩуᴋи нᴀ доᴄᴛиᴦнуᴛоʍ! <a:oshimai:1514940166626742382>",
                )
                await self._safe_add_reaction(message, self.rare_emoji)

            elif user_number % 50 == 0:
                await safe_send(
                    message,
                    f"**ⲡⲟⲗьⳅⲟⲃⲁⲧⲉⲗυ, ⲡⲟⳅⲇⲣⲁⲃⲗяю! <a:makise:1514939694624800818>**\n"
                    f"ʙы доɯᴧи до {user_number}, ᴨᴩодоᴧжᴀйᴛᴇ ʙ ᴛоʍ жᴇ духᴇ! <a:oshimai:1514940166626742382>",
                )
                await self._safe_add_reaction(message, self.uncommon_emoji)

            else:
                await self._safe_add_reaction(message, self.basic_emoji)

            # Увеличиваем счетчик
            BotConfig.next_number_in_count_channel += 1

        except (ValueError, TypeError):
            # Удаляем ошибочное сообщение
            await safe_delete(message, delay=1)

            # Наказываем нарушителя за ошибку в числе
            await self._punish_user(message.guild, message.author)

            await safe_send(
                message,
                f"<:deniedemoji:1519737463126360294> {message.author.mention}, балбес, соблюдай порядок чисел!",
                delete_after=5,
            )

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Отслеживание удаления верного числа."""
        if message.channel.id != BotConfig.CHANNELS.get("count"):
            return

        if message.author == self.bot.user:
            return

        if (
            self.last_valid_entry
            and message.id == self.last_valid_entry["message_id"]
        ):
            author = self.last_valid_entry["author"]
            number = self.last_valid_entry["number"]

            # Очищаем запись, чтобы избежать дублирования
            self.last_valid_entry = None

            # Выдаем роль за удаление
            await self._punish_user(message.guild, author, minutes=30)

            # Оповещаем в канал о восстанавливаемой цифре и обновляем last_valid_entry на новое сообщение бота
            sent_msg = await safe_send(message.channel, content=str(number))
            if sent_msg:
                self.last_valid_entry = {
                    "message_id": sent_msg.id,
                    "author": sent_msg.author,
                    "number": number,
                }

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(
        self, payload: discord.RawBulkMessageDeleteEvent
    ):
        """Защита при массовой очистке чата (Bulk Delete / Purge)."""
        if payload.channel_id != BotConfig.CHANNELS.get("count"):
            return

        # Если среди массово удаленных сообщений было последнее правильное число
        if (
            self.last_valid_entry
            and self.last_valid_entry["message_id"] in payload.message_ids
        ):
            number = self.last_valid_entry["number"]

            # Сбрасываем запись ДО выполнения действий, чтобы on_message_delete не сработал параллельно
            self.last_valid_entry = None

            channel = self.bot.get_channel(payload.channel_id)
            if channel:
                # Восстанавливаем число БЕЗ наказания пользователей
                sent_msg = await safe_send(
                    channel,
                    content=f"<:cautionemoji:1520064481357598770> Пᴩоизоɯᴧᴀ очиᴄᴛᴋᴀ ᴄообщᴇний. ʙоᴄᴄᴛᴀноʙᴧᴇно чиᴄᴧо: **{number}**",
                )
                if sent_msg:
                    self.last_valid_entry = {
                        "message_id": sent_msg.id,
                        "author": sent_msg.author,
                        "number": number,
                    }

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ):
        """Отслеживание изменения верного числа."""
        if before.channel.id != BotConfig.CHANNELS.get("count"):
            return

        # Если отредактировали именно последнее засчитанное число
        if (
            self.last_valid_entry
            and before.id == self.last_valid_entry["message_id"]
        ):
            # Если текст фактически изменился
            if before.content != after.content:
                author = self.last_valid_entry["author"]
                number = self.last_valid_entry["number"]

                # Сбрасываем кэш ДО удаления, чтобы on_message_delete не сработал повторно!
                self.last_valid_entry = None

                # Удаляем отредактированное сообщение
                await safe_delete(after)

                # Выдаем роль за редактирование
                await self._punish_user(after.guild, author, minutes=30)

                # Оповещаем в канал восстановленным числом
                sent_msg = await safe_send(after.channel, content=str(number))
                if sent_msg:
                    self.last_valid_entry = {
                        "message_id": sent_msg.id,
                        "author": sent_msg.author,
                        "number": number,
                    }


async def setup(bot):
    await bot.add_cog(CountingGame(bot))