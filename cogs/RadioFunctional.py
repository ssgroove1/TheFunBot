import discord, random, re
from discord import app_commands
from datetime import datetime
from discord.ext import commands

from config import BotConfig
from safe_commands import *

# --- РАДИО КОНТРОЛЛЕР ---
class RadioManager:
    def __init__(self): 
        self.active = {}
        
    def encrypt(self, text, level=1):
        if not level: 
            return text
        cipher_dict = getattr(BotConfig, "CIPHER", {}) # Безопасно берет словарь или оставляет пустым
        enc = ''.join(cipher_dict.get(c, c) for c in text.lower())
        return ''.join(c + random.choice('*&#@!?') if random.random() > .7 and level == 2 else c for c in enc)
        
    def decrypt(self, text):
        rev = {v:k for k, v in BotConfig.CIPHER.items()}
        return ''.join(rev.get(c, c) for c in re.sub(r'[*&#@!?]', '', text))
        
    def add_noise(self, text, level):
        if not level: 
            return text
        words = text.split()
        if level >= 1:
            for _ in range(random.randint(0, len(words)//4)):
                i = random.randint(0, len(words)-1)
                words[i] = words[i] + '...' if random.random()>.5 else '...' + words[i]
        if level >= 2:
            for _ in range(random.randint(len(words)//3, len(words)//2)):
                i = random.randint(0, len(words)-1)
                words[i] = f"[{random.choice(BotConfig.RADIO_NOISES)}] {words[i]}"
        if level >= 3:
            for _ in range(random.randint(len(words)//2, len(words))):
                i = random.randint(0, len(words)-1)
                w = list(words[i])
                if len(w) > 1:
                    for j in range(random.randint(1, len(w)//2)):
                        if random.random()>.5: 
                            w[j] = random.choice('*?!')
                    words[i] = ''.join(w)
        return ' '.join(words)
    
class RadioView(discord.ui.View):
    def __init__(self, recipient, sender, channel, msg, enc):
        super().__init__(timeout=300)
        self.recipient, self.sender, self.channel, self.msg, self.enc = recipient, sender, channel, msg, enc
    
    @discord.ui.button(label="📨 Ответить", style=discord.ButtonStyle.primary)
    async def reply(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user.id != self.recipient.id:
            return await safe_send(inter, "<:deniedemoji:1519737463126360294> Не для вас!", ephemeral=True)
        await inter.response.send_modal(RadioModal(self.sender, self.recipient, self.channel, self.msg, self.enc))
        
    @discord.ui.button(label="🔊 Повтор", style=discord.ButtonStyle.secondary)
    async def repeat(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user.id not in [self.recipient.id, self.sender.id]:
            return await safe_send(inter, "<:deniedemoji:1519737463126360294> Нет доступа!", ephemeral=True)
        await safe_send(inter, f"```\n{self.msg}\n```", ephemeral=True)

    async def on_timeout(self):
        # Если ссылка на сообщение не была сохранена, ничего не делаем
        if not self.message:
            return

        # Проходим по всем кнопкам внутри View и выключаем их
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

        # Пытаемся отредактировать сообщение, удалив активные компоненты
        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            # Игнорируем ошибки, если сообщение было удалено пользователем/модератором до таймаута
            pass


class RadioModal(discord.ui.Modal, title="Ответ"):
    reply = discord.ui.TextInput(label="Сообщение", style=discord.TextStyle.paragraph, max_length=200)
    
    def __init__(self, sender, recipient, channel, orig, enc):
        super().__init__()
        self.sender, self.recipient, self.channel, self.orig, self.enc = sender, recipient, channel, orig, enc
        self.radio_mgr = RadioManager()
    
    async def on_submit(self, inter):
        msg = self.reply.value
        if self.enc: 
            msg = self.radio_mgr.encrypt(msg, self.enc)
        embed = discord.Embed(
            title="<:radioemoji:1519767792193110086> оᴛʙᴇᴛ",
            description=f"📡 {inter.user.mention} → {self.sender.mention}",
            color=discord.Color.gold()
        )
        embed.add_field(name="<:messageemoji:1519990110882496705> ᴄообщᴇниᴇ", value=f"```\n{msg}\n```", inline=False)
        try:
            if self.channel == "public" or self.channel == "emergency":
                await safe_send(inter, embed=embed)
            else:
                await safe_send(self.sender, embed=embed)
            await safe_send(inter, "<:confirmedemoji:1519738036936638474> Отправлено!", ephemeral=True)
        except discord.Forbidden:
            await safe_send(inter, f"<:deniedemoji:1519737463126360294> Не могу отправить ЛС {self.sender.mention} — пользователь закрыл ЛС", ephemeral=True)
        except Exception as e:
            await safe_send(inter, f"<:deniedemoji:1519737463126360294> Ошибка: {e}", ephemeral=True)

class RadioFunctional(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.radio_mgr = RadioManager()

    @app_commands.command(name="радио", description="Отправить сообщение по рации.")
    @app_commands.describe(user="Кому", message="Сообщение (текст)", channel="Канал", encrypt="Шифрование", noise="Помехи")
    @app_commands.choices(
        channel=BotConfig.CHANNELS_CHOICE,
        encrypt=BotConfig.ENCRYPTS,
        noise=BotConfig.NOISES)
    @app_commands.guild_only()
    async def radio(self, interaction: discord.Interaction, user: discord.Member, message: str,
                    channel: app_commands.Choice[str] = None, encrypt: app_commands.Choice[str] = None,
                    noise: app_commands.Choice[str] = None):
        
        # 1. Защита от таймаута — сразу переводим в режим ожидания
        await interaction.response.defer(ephemeral=True)

        try:
            # 2. Безопасное получение списка разрешенных каналов (проверка типов на случай если CHANNELS это list или dict)
            config_channels = getattr(BotConfig, 'CHANNELS', {})
            if isinstance(config_channels, dict):
                allowed_channels = [config_channels.get('radio'), config_channels.get('commands')]
            elif isinstance(config_channels, list):
                allowed_channels = config_channels
            else:
                allowed_channels = []

            # Исключаем None значения из списка каналов
            allowed_channels = [c for c in allowed_channels if c is not None]

            if interaction.channel.id not in allowed_channels:
                radio_channel_mention = f"<#{config_channels.get('radio')}>" if isinstance(config_channels, dict) and config_channels.get('radio') else "специальном канале"
                await interaction.followup.send(
                    content=f"<:deniedemoji:1519737463126360294> Эта команда работает только в {radio_channel_mention}!", 
                    ephemeral=True)
                return

            # 3. Валидация входных данных
            if len(message) > 200:
                await interaction.followup.send(content="<:deniedemoji:1519737463126360294> Сообщение должно быть меньше 200 символов!", ephemeral=True)
                return
            if user.bot:
                await interaction.followup.send(content="<:deniedemoji:1519737463126360294> Нельзя отправлять сообщение боту!", ephemeral=True)
                return
            if user.id == interaction.user.id:
                await interaction.followup.send(content="<:deniedemoji:1519737463126360294> Нельзя отправить сообщение самому себе!", ephemeral=True)
                return
            
            ch = channel.value if channel else "public"
            enc = int(encrypt.value) if encrypt else 0
            ns = int(noise.value) if noise else 0

            if enc and ch == "emergency":
                await interaction.followup.send(content="<:deniedemoji:1519737463126360294> Шифрование не может быть использовано в **экстренном канале**!", ephemeral=True)
                return
            
            # 4. Обработка текста сообщения через радио менеджер
            info = BotConfig.RADIO_CONFIG[ch]
            msg = message
            if enc: 
                msg = self.radio_mgr.encrypt(msg, enc)
            if ns: 
                msg = self.radio_mgr.add_noise(msg, ns)
            
            # 5. Сборка Embed сообщения
            embed = discord.Embed(
                title=f"{info['emoji']} {info['name']}",
                description=f"**{random.choice(BotConfig.RADIO_SOUNDS)}**\n📡 {interaction.user.mention} → {user.mention}",
                color=discord.Color.darker_grey() if ch != "umbrella" else discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="ᴄообщᴇниᴇ", value=f"```\n{msg}\n```", inline=False)
            
            if ns: 
                noise_labels = ["", "<:goodconnectionemoji:1519985770750808134> Легкие", "<:mediumconnectionemoji:1519986766499811428> Средние", "<:badconnectionemoji:1519985656305291325> Сильные"]
                embed.add_field(name="ᴨоʍᴇхи", value=noise_labels[ns], inline=True)
                
            if enc: 
                encrypt_labels = ["", "<:lockemoji:1519992045152899072> Базовое", "<:fulllockemoji:1519992041986064506> Полное"]
                embed.add_field(name="ɯиɸᴩоʙᴀниᴇ", value=encrypt_labels[enc], inline=True)
                
            status_icon = '<:excelentconnectionemoji:1519985715977523350>' if random.random() > .2 else '<:goodconnectionemoji:1519985770750808134>'
            status_text = 'Стабильна' if random.random() > .2 else 'Нестабильна'
            embed.add_field(name="ᴄᴛᴀᴛуᴄ", value=f"{status_icon} {status_text}", inline=True)
            embed.add_field(name="ᴩᴀдиуᴄ", value=f"<:radiowavesemoji:1519988737579286659> {info['range']} км", inline=True)
            
            # 6. Отправка сообщения
            view = RadioView(user, interaction.user, ch, msg, enc)
            if ch in ["public", "emergency"]:
                # Публичные каналы идут в текстовый канал сервера
                await interaction.channel.send(embed=embed, view=view)
            else:
                # Закрытые каналы отправляются только в личные сообщения получателя
                await user.send(embed=embed, view=view)
                
            # Завершаем взаимодействие успешным ответом
            await interaction.followup.send(content=f"<:confirmedemoji:1519738036936638474> Отправлено {user.mention}", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send(content=f"<:deniedemoji:1519737463126360294> Не могу отправить ЛС {user.mention} — пользователь закрыл доступ к ЛС.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(content=f"<:deniedemoji:1519737463126360294> Ошибка при отправке радиосообщения: `{e}`", ephemeral=True)

    @app_commands.command(name="расшифровать", description="Расшифровать зашифрованное сообщение с радио.")
    @app_commands.describe(message="Зашифрованный текст сообщения")
    @app_commands.guild_only()
    async def decrypt(self, interaction: discord.Interaction, message: str):
        # 1. Защищаем команду от таймаута в 3 секунды (делаем ответ скрытым)
        await interaction.response.defer(ephemeral=True)

        # 2. Быстрая проверка на пустое сообщение
        clean_message = message.strip()
        if not clean_message:
            await interaction.followup.send(
                content="<:deniedemoji:1519737463126360294> Сообщение не может быть пустым!", 
                ephemeral=True
            )
            return

        try:
            # 3. Дешифровка через ваш менеджер радио
            decrypted_text = self.radio_mgr.decrypt(clean_message)

            if not decrypted_text:
                decrypted_text = "[Не удалось расшифровать данные / неверный формат]"

            # 4. Сборка красивого Embed с результатами расшифровки
            embed = discord.Embed(
                title="<:keysemoji:1519980356260860066> ᴩᴀᴄɯиɸᴩоʙᴋᴀ", 
                color=discord.Color.purple()
            )

            embed.add_field(
                name="<:messageemoji:1519990110882496705> оᴩиᴦинᴀᴧ", 
                value=decrypted_text)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            # Безопасный перехват любых непредвиденных ошибок при работе radio_mgr
            await interaction.followup.send(
                content=f"<:deniedemoji:1519737463126360294> Произошла ошибка при дешифровке: `{e}`", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(RadioFunctional(bot))