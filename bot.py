import discord, sys, os, asyncio
from dotenv import load_dotenv
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import BotConfig
from safe_commands import *

BASE_DIR = Path(__file__).parent
env_path = BASE_DIR / "shared.env"
load_dotenv(env_path)
VERIFICATION_MESSAGES = {}
XP_COOLDOWNS = {}

# Настройки бота
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.moderation = True
bot = commands.Bot(command_prefix=BotConfig.COMMAND_PREFIX, intents=intents, max_messages=1000)

init_safe(bot) # safe_send, safe_reply...

# ========== ЗАПУСК БОТА ==========

@bot.event
async def on_ready():
    print("=========================================")
    print(f"Бот успешно запущен как: {bot.user.name} (ID: {bot.user.id})")
    
    # 1. Проверяем, какие коги (модули) реально загружены в бота
    loaded_cogs = list(bot.cogs.keys())
    print(f"Загруженные коги/модули ({len(loaded_cogs)} шт): {loaded_cogs}")
    if not loaded_cogs:
        print("⚠️ ВНИМАНИЕ: Ни один ког/модуль не загружен! Проверьте пути к папке cogs.")
    
    print("\nПроверка каналов из config.py:")
    for channel_name, channel_id in BotConfig.CHANNELS.items():
        channel = bot.get_channel(channel_id)
        if channel:
            print(f"✅ Канал [{channel_name}] (ID: {channel_id}) успешно найден на сервере: '{channel.guild.name}'")
        else:
            print(f"❌ Канал [{channel_name}] (ID: {channel_id}) НЕ найден! Бот не сможет отправить туда логи.")
            
    # 3. Проверяем статус интентов (Intents)
    print("\nСтатус Интентов:")
    print(f"• Message Content (Текст сообщений): {bot.intents.message_content}")
    print(f"• Members (Участники сервера): {bot.intents.members}")
    print("=========================================")
    await bot.change_presence(activity=discord.CustomActivity(name="Отвечаю за актив 🍀"))

async def load_extensions():
    # Проходим по всем файлам в папке cogs
    cogs_dir = BASE_DIR / "cogs"
    for filename in os.listdir(cogs_dir):
        # Загружаем только файлы с расширением .py
        if filename.endswith('.py'):
            cog_name = f'cogs.{filename[:-3]}'
            try:
                await bot.load_extension(cog_name)
                print(f"✅ Модуль {cog_name} успешно загружен.")
            except Exception as e:
                print(f"❌ Ошибка загрузки модуля {cog_name}: {e}")

    if BotConfig.GUILD_ID:
        guild = discord.Object(id=BotConfig.GUILD_ID)
        
        # Копируем наши глобальные команды из Когов в дерево этого сервера
        bot.tree.copy_global_to(guild=guild)
        
        # Синхронизируем дерево конкретного сервера
        synced = await bot.tree.sync(guild=guild)
        print(f"⚙️ [Локальная синхронизация] Успешно загружено {len(synced)} команд на сервер {guild.id}.")
    else:
        # Глобальная синхронизация (для продакшена, команды обновляются до 1 часа)
        synced = await bot.tree.sync()
        print(f"⚙️ [Глобальная синхронизация] Успешно загружено {len(synced)} глобальных команд.")

# Запуск бота (с учетом асинхронности в d.py 2.0+)
async def main():
    async with bot:
        await load_extensions()
        token = os.getenv("BOT_TOKEN")
        if not token:
            print("❌ Ошибка: Переменная среды BOT_TOKEN не установлена!")
            return
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())