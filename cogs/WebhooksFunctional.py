from datetime import datetime, timezone, timedelta
import random, discord
from discord import app_commands
from discord.ext import commands, tasks

from config import BotConfig
from safe_commands import safe_send

# Конфигурация доступных персонажей
CHARACTERS = {
    "scp035": {
        "name": "SCP-035",
        "nick_prefix": "[𝙎𝘾𝙋 035]",
        "avatar_url": "https://i.pinimg.com/736x/28/03/14/28031446cf8e18d55c11ee90588fb0bf.jpg",
        "avatar_url_after": "https://i.pinimg.com/1200x/dd/bb/e8/ddbbe8338846172fd52739ee99a12436.jpg",
        "embed_title": "<:SCP035emoji:1520063257325473913> 𝙎𝙤𝙢𝙚𝙗𝙤𝙙𝙮 𝙪𝙨𝙚𝙙 𝙖 𝙢𝙖𝙨𝙠!",
        "embed_desc": "<:emergencyemoji:1519769135767228576> {} ᴄᴛᴀᴧ одᴇᴩжиʍ sᴄᴩ 035",
        "embed_img": "https://i.pinimg.com/1200x/ed/6d/a0/ed6da036c1394a0333c4a0470d87ba50.jpg",
        "death_msg": "<:SCP035_2emoji:1520066884920410311> {} ᴨоᴦибᴀᴇᴛ оᴛ ʍᴀᴄᴋи одᴇᴩжиʍоᴄᴛи!",
        "phrases_before_10m": [
            "*ʍᴀᴄᴋᴀ ᴦоʙоᴩиᴛ:* {}", "{}*... ᴨоʍоᴦиᴛᴇ...*", "*я чуʙᴄᴛʙую ᴄᴛᴩᴀнноᴇ...* {}"
        ],
        "phrases_after_10m": [
            "*ʍᴀᴄᴋᴀ ᴦоʙоᴩиᴛ:* {}", "{} *- ᴄниʍиᴛᴇ ʍᴇня!*", "*я ʙᴀᴄ ʙижу...* {}",
            "*ʍᴀᴄᴋᴀ ɯᴇᴨчᴇᴛ:* {}", "{} *- ᴛы ужᴇ ʍой!*", "*ᴄᴧиɯᴋоʍ ᴨоздно...* {}"
        ],
        "default_before": "*...чᴛо-ᴛо нᴇ ᴛᴀᴋ...*",
        "default_after": "*ʍᴀᴄᴋᴀ поглощает разум...*"
    },
    "ghoul": {
        "name": "Токийский гуль",
        "nick_prefix": "[𝙂𝙝𝙤𝙪𝙡]",
        "avatar_url": "https://i.pinimg.com/736x/b4/45/c1/b445c141f541ce0ced9584d2ca6ea831.jpg",
        "avatar_url_after": "https://i.pinimg.com/736x/d3/d9/dd/d3d9dd019db561d711c40a616af9d5c5.jpg",
        "embed_title": "<:redemoji:1529165891718086777> 𝑺𝒐𝒎𝒆𝒐𝒏𝒆'𝒔 𝒈𝒐𝒏𝒆 𝒄𝒓𝒂𝒛𝒚!",
        "embed_desc": "<:eyeemoji:1529166420590723212> {} ᴨоᴦᴩузиᴧᴄя ʙ ᴦоᴧод и ᴨᴩобудиᴧ ᴋᴀгунᴇ...",
        "embed_img": "https://i.ytimg.com/vi/IJcQrvdvwJw/maxresdefault.jpg",
        "death_msg": "<:skullemoji:1529166895717028000> {} ᴨоᴛᴇᴩяᴧ ᴋонᴛᴩоᴧь нᴀд ᴋᴀкуджᴀ и быᴧ нᴇйᴛᴩᴀᴧизоʙᴀн!",
        "phrases_before_10m": [
            "*ᴦоᴧод уᴄиᴧиʙᴀᴇᴛᴄя...* {}", "{}*... ᴦᴧᴀзᴀ ᴄᴛᴀноʙяᴛᴄя ᴋᴩᴀᴄныʍи...*",
            "*ᴋᴀᴦуны ᴨуᴧьᴄиᴩуюᴛ:* {}", "{}*... я нᴇ хочу ᴇᴄᴛь ᴧюдᴇй...*", "*иᴄᴛᴇᴩичᴇᴄᴋий ᴄʍᴇх... {}*"
        ],
        "phrases_after_10m": [
            "{} *- ᴄᴋоᴧьᴋо будᴇᴛ 1000-7?*", "*я гуᴧь...* {}",
            "{} *- ᴛы думаᴇɯь, ʍнᴇ боᴧьно?*", "*ᴋᴀᴋуджᴀ ᴨоᴦᴧощᴀᴇᴛ ʍᴇня:* {}",
            "{} *- я ᴨᴩиняᴧ ᴄʙою ᴄущноᴄᴛь...*", "*ᴄᴀᴩᴀᴋᴀноɯᴋи ʙ уɯᴀх...* {}*"
        ],
        "default_before": "*...хᴩуᴄᴛ ᴨᴀᴧьцᴇʍ...*",
        "default_after": "*истерический смех... 1000-7...*"
    },
    "bakugo": {
        "name": "Кацуки Бакуго",
        "nick_prefix": "[𝘿𝙮𝙣𝙖𝙢𝙞𝙜𝙝𝙩]",
        "avatar_url": "https://i.pinimg.com/1200x/8b/1b/9c/8b1b9cce4be14432a3985e8c1f39be50.jpg",
        "avatar_url_after": "https://i.pinimg.com/736x/22/50/10/225010f5e2c3efdbd872d3f79d1cd661.jpg",
        "embed_title": "<:explosiveemoji:1529190661104861465> 𝑲𝒊𝒏𝒈 𝑬𝒙𝒑𝒍𝒐-𝑲𝒊𝒍𝒍 𝑫𝒚𝒏𝒂𝒎𝒊𝒈𝒉𝒕!",
        "embed_desc": "<:fireemoji:1529191805306798183> {} ᴨоᴦᴩузиᴧᴄя ʙ яᴩоᴄᴛь и ʙзᴩыʙᴀᴇᴛ ʙᴄё ʙоᴋᴩуᴦ...",
        "embed_img": "https://i.pinimg.com/736x/24/85/6e/24856e82ac3124413adbd62955457d15.jpg",
        "death_msg": "<:smokeemoji:1529191179428560898> {} ʙыдохᴄя и ᴨᴇᴩᴇᴦᴩᴇᴧ ᴄʙои ʙзᴩыʙныᴇ жᴇᴧᴇзы!",
        "phrases_before_10m": [
            "*иᴄᴋᴩы нᴀ ᴧᴀдонях...* {}", "{}*... Чᴇʍоᴅᴀн бᴇз ᴩучᴋи, ᴄъᴇбни ᴄ доᴩоᴦи!*",
            "*бᴀᴋуᴦо ᴦᴩоʍᴋо ᴩычиᴛ:* {}", "{}*... Я ᴄᴛᴀну ноʍᴇᴩоʍ один!*",
            "*оᴦнᴇнный ʙзᴩыʙ:* {}"
        ],
        "phrases_after_10m": [
            "{} *- издохни! (sʜɪɴᴇᴇ!)*", "*оᴦнᴇнный удᴀᴩ!* {}",
            "{} *- я ᴛᴇбя убью!*", "*ᴦᴩᴀунд зᴇᴩо!* {}",
            "{} *- зᴀᴛᴋниᴄь и ᴄʍоᴛᴩи, ᴋᴀᴋ я ʙыиᴦᴩыʙᴀю!*", "*ʙзᴩыʙнᴀя ʙоᴧнᴀ ᴄноᴄиᴛ ʙᴄё ʙоᴋᴩуᴦ...* {}"
        ],
        "default_before": "*...треск искр на ладонях...*",
        "default_after": "*ИЗДОХНИ-И-И! <:explosiveemoji:1529190661104861465>*"
    }
}


class WebhooksFunctional(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Раздельное хранение данных для каждого персонажа
        self.active_users = {
            "scp035": None,
            "ghoul": None,
            "bakugo": None
        }
        self.webhooks_times = {
            "scp035": None,
            "ghoul": None,
            "bakugo": None
        }
        self.cooldowns = {
            "scp035": None,
            "ghoul": None,
            "bakugo": None
        }

        self._webhook_cache = {}

    def cog_unload(self):
        self.mask_check_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.mask_check_loop.is_running():
            self.mask_check_loop.start()
            print("🔁 Фоновый цикл проверки персонажей успешно запущен!")

    async def get_or_create_webhook(self, channel: discord.TextChannel) -> discord.Webhook | None:
        if channel.id in self._webhook_cache:
            return self._webhook_cache[channel.id]

        try:
            webhooks = await channel.webhooks()
            for wh in webhooks:
                if wh.user == self.bot.user:
                    self._webhook_cache[channel.id] = wh
                    return wh

            new_wh = await channel.create_webhook(name="FunBotWebhookSystem")
            self._webhook_cache[channel.id] = new_wh
            return new_wh
        except (discord.Forbidden, discord.HTTPException):
            return None

    async def remove_role_at_time(self, member: discord.Member, role: discord.Role, minutes: int):
        await discord.utils.sleep_until(
            datetime.now(timezone.utc) + timedelta(minutes=minutes)
        )
        if role in member.roles:
            try:
                await member.remove_roles(role, reason="Автоматическое снятие роли")
            except discord.HTTPException:
                pass

    @tasks.loop(seconds=60)
    async def mask_check_loop(self):
        now_ts = datetime.now(timezone.utc).timestamp()

        for mode in ["scp035", "ghoul"]:
            user_id = self.active_users[mode]
            mask_time = self.webhooks_times[mode]

            if user_id is None or mask_time is None:
                continue

            # 1800 секунд = 30 минут
            if now_ts - mask_time >= 1800:
                char_data = CHARACTERS[mode]

                # Сбрасываем персонажа
                self.active_users[mode] = None
                self.webhooks_times[mode] = None
                self.cooldowns[mode] = now_ts + 3600

                user = self.bot.get_user(user_id)
                if not user:
                    continue

                for guild in self.bot.guilds:
                    member = guild.get_member(user_id)
                    if not member:
                        continue

                    prefix = char_data["nick_prefix"]
                    if prefix in member.display_name:
                        try:
                            await member.edit(nick=member.display_name.replace(f"{prefix} ", ""))
                        except discord.HTTPException:
                            pass

                    channel = guild.get_channel(BotConfig.CHANNELS.get("chat"))
                    if channel:
                        try:
                            await channel.send(char_data["death_msg"].format(user.mention))
                        except discord.HTTPException:
                            pass

    @mask_check_loop.before_loop
    async def before_mask_check_loop(self):
        await self.bot.wait_until_ready()

    async def _activate_mode(self, inter: discord.Interaction, mode: str):
        if inter.channel_id != BotConfig.CHANNELS.get("commands"):
            return await safe_send(
                inter,
                f"<:accessdeniedemoji:1517986918573408318> Эта команда работает только в канале <#{BotConfig.CHANNELS.get('commands')}>!",
                ephemeral=True,
            )

        user_id = inter.user.id
        now_ts = datetime.now(timezone.utc).timestamp()

        # 1. ПРОВЕРКА: Если пользователь УЖЕ носит любого из персонажей
        if user_id in self.active_users.values():
            return await safe_send(
                inter,
                "<:deniedemoji:1519737463126360294> Вы не можете использовать двух персонажей одновременно!",
                ephemeral=True,
            )

        # 2. ПРОВЕРКА: Занят ли запрашиваемый персонаж кем-то другим
        if self.active_users[mode] is not None:
            return await safe_send(
                inter,
                f"<:deniedemoji:1519737463126360294> Этот персонаж уже занят пользователем <@{self.active_users[mode]}>!",
                ephemeral=True,
            )

        # 3. ПРОВЕРКА: Кулдаун персонажа
        cooldown = self.cooldowns[mode]
        if cooldown is not None and now_ts < cooldown:
            remain_min = int((cooldown - now_ts) // 60)
            return await safe_send(
                inter,
                f"<:deniedemoji:1519737463126360294> Силы персонажа восстанавливаются. Ждите {remain_min if remain_min > 0 else 1} мин.",
                ephemeral=True,
            )

        # Активация
        char_data = CHARACTERS[mode]
        self.active_users[mode] = user_id
        self.webhooks_times[mode] = now_ts
        self.cooldowns[mode] = None

        embed = discord.Embed(
            title=char_data["embed_title"],
            description=char_data["embed_desc"].format(inter.user.mention),
            color=discord.Color.brand_red() if mode == "ghoul" else discord.Color.light_grey(),
        )
        embed.add_field(
            name="<:cautionemoji:1520064481357598770> 𝑾𝒂𝒓𝒏𝒊𝒏𝒈:",
            value="Через 10 минут начинается безумие! Через 30 минут — гибель.",
        )
        embed.set_image(url=char_data["embed_img"])

        await safe_send(inter, embed=embed, ephemeral=False)

        # Смена никнейма
        try:
            await inter.user.edit(nick=f"{char_data['nick_prefix']} {inter.user.display_name}")
        except discord.HTTPException:
            pass

    @app_commands.command(name="надеть_маску", description="Стать одержимым маской.")
    @app_commands.guild_only()
    async def mask_scp(self, inter: discord.Interaction):
        await self._activate_mode(inter, "scp035")

    @app_commands.command(name="съесть_сараконошку", description="Пробудить силы токийского гуля.")
    @app_commands.guild_only()
    async def mask_ghoul(self, inter: discord.Interaction):
        await self._activate_mode(inter, "ghoul")

    @app_commands.command(name="взрывные_железы", description="Активировать режим Кацуки Бакуго")
    @app_commands.guild_only()
    async def mask_bakugo(self, inter: discord.Interaction):
        await self._activate_mode(inter, "bakugo")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.webhook_id or not message.guild:
            return

        if message.channel.id == BotConfig.CHANNELS.get('count'):
            return

        # Определяем, является ли автор сообщения одним из активных персонажей
        active_mode = None
        for mode, uid in self.active_users.items():
            if uid == message.author.id:
                active_mode = mode
                break

        if active_mode is None:
            return

        mask_time = self.webhooks_times[active_mode]
        if mask_time is None:
            return

        char_data = CHARACTERS[active_mode]
        now_ts = datetime.now(timezone.utc).timestamp()
        seconds_passed = now_ts - mask_time

        # 1. СКАЧИВАЕМ ВЛОЖЕНИЯ
        files = []
        if message.attachments:
            for attachment in message.attachments:
                try:
                    file = await attachment.to_file()
                    file.fp.seek(0)
                    files.append(file)
                except Exception as e:
                    print(f"[Ошибка скачивания файла]: {e}")

        # 2. ПОДГОТАВЛИВАЕМ ТЕКСТ
        raw_text = message.content.strip() if message.content else ""

        # Проверяем, является ли текст сообщения ТОЛЬКО ссылкой на гифку или медиа
        is_only_gif_url = any(
            domain in raw_text.lower() 
            for domain in ["tenor.com", "giphy.com", ".gif"]
        ) and " " not in raw_text

        # Сообщение считается "чистым текстом", только если это НЕ файл и НЕ ссылка на гифку
        has_custom_text = bool(raw_text) and not files and not is_only_gif_url

        if seconds_passed >= 600: # 10 минут
            if has_custom_text:
                new_text = random.choice(char_data["phrases_after_10m"]).format(raw_text)
            else:
                # Если отправлена только гифка или файл — ставим дефолтную фразу
                default_phrase = char_data["default_after"]
                new_text = f"{default_phrase}\n{raw_text}".strip() if is_only_gif_url else default_phrase
            current_avatar = char_data.get("avatar_url_after", char_data["avatar_url"])
        else:
            # Шанс пропуска сообщений работает только для чисто текстовых сообщений
            if random.random() <= 0.3 and not files and not is_only_gif_url:
                return

            if has_custom_text:
                new_text = random.choice(char_data["phrases_before_10m"]).format(raw_text)
            else:
                # Если отправлена только гифка или файл — ставим дефолтную фразу
                default_phrase = char_data["default_before"]
                new_text = f"{default_phrase}\n{raw_text}".strip() if is_only_gif_url else default_phrase
            current_avatar = char_data["avatar_url"]

        # 3. ОТПРАВЛЯЕМ ВЕБХУК
        webhook = await self.get_or_create_webhook(message.channel)

        if webhook:
            try:
                kwargs = {
                    "content": new_text,
                    "username": message.author.display_name,
                    "avatar_url": current_avatar,
                    "files": files
                }
                if isinstance(message.channel, discord.Thread):
                    kwargs["thread"] = message.channel

                await webhook.send(**kwargs)
            except discord.HTTPException as e:
                print(f"[Ошибка отправки вебхука]: {e}")
                self._webhook_cache.pop(message.channel.id, None)

        # 4. УДАЛЯЕМ ИСХОДНОЕ СООБЩЕНИЕ
        try:
            await message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        for mode, uid in list(self.active_users.items()):
            if uid is not None and member.id == uid:
                now_ts = datetime.now(timezone.utc).timestamp()
                char_data = CHARACTERS[mode]

                self.active_users[mode] = None
                self.webhooks_times[mode] = None
                self.cooldowns[mode] = now_ts + 3600

                channel_id = BotConfig.CHANNELS.get('chat')
                if channel_id:
                    channel = member.guild.get_channel(channel_id)
                    if channel:
                        try:
                            await channel.send(
                                f"<:skullemoji:1529166895717028000> {member.mention} нᴇ ᴄᴨᴩᴀʙиᴧᴄя ᴄ ᴋонᴛᴩоᴧᴇʍ, ᴄиндᴩоʍ {char_data['name']} быᴧ нᴇйᴛᴩᴀᴧизоʙᴀн!"
                            )
                        except discord.HTTPException:
                            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(WebhooksFunctional(bot))