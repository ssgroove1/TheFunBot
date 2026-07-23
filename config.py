import os
from pathlib import Path
from discord import app_commands

BASE_DIR = Path(__file__).parent

class BotConfig:
    # =============== CHANNELS ===============
    CHANNELS = {
        'commands': 1468672520717865053,
        'mod_commands': 1526631623876022332,
        'radio': 1519803349711454298,
        'welcome': 1417900621155274762,
        'count': 1513576705896222861,
        'mod_logs': 1526548916084936831,
        'mod_logs_commands': 1526548916084936830,
        'warning_logs': 1526553007028830349,
        'tech_logs': 1526888079946944574,
        'emergency_logs': 1526607520519684096,
        'trigger_voice': 1513626188080353442,
        'rules': 1417897315452059689,
        'chat': 1522690703220805814,
        'help': 1513905501191147732,
        'feedback': 1526548916084936828,
    }

    # Для прямой совместимости с когом подсчета
    COUNT_CHANNEL_ID = CHANNELS['count']

    # =============== ROLES ===============
    ROLES = {
        'muted': 1512893252141973558,
        'count_bad': 1513493354208301166,
        'first_warn': 1512794784216121344,
        'second_warn': 1512794946556530930,
        'third_warn': 1512794981138563072,
        'warnings_category': 1512794679219978270,
        'quarantine': 1526282672261959855,
    }

    # =============== DB PATH ===============
    DB_PATH = str(BASE_DIR / "database" / "fg_db.db")
    
    # =============== VARIABLES ===============
    GUILD_ID = 1417892629152010281
    DEVELOPER_ID = 777122004376879115  # ⚠️ Проверьте, точно ли это ваш ID аккаунта!
    COMMAND_PREFIX = '/'

    next_number_in_count_channel = 1

    # =============== RADIO ===============
    RADIO_CONFIG = {
        "public": {"name": "общий", "emoji": "📻", "range": 100},
        "emergency": {"name": "϶ᴋᴄᴛᴩᴇнный", "emoji": "🚨", "range": 50},
        "umbrella": {"name": "ᴜᴍʙʀᴇʟʟᴀ", "emoji": "🩸", "range": 30},
        "stars": {"name": "s.ᴛ.ᴀ.ʀ.s.", "emoji": "🌟", "range": 75},
        "bsaa": {"name": "ʙsᴀᴀ", "emoji": "🧪", "range": 80}
    }
    RADIO_SOUNDS = ["պⲉⲗɥⲟⲕ.", "ⲏⲁⲥⲧⲣⲟύⲕⲁ.", "ⲥυⲅⲏⲁⲗ ⲡⲣυⲏяⲧ.", "ⲡⲉⲣⲉⲇⲁю...", "ⲡⲣυⲉⲙ..."]
    RADIO_NOISES = ["шшш...", "треск...", "шум ветра...", "помехи...", "потеря сигнала..."]
    CIPHER = {'а':'α','б':'β','в':'ν','г':'γ','д':'δ','е':'ε','ё':'ε','ж':'ζ','з':'ζ','и':'ι',
            'й':'ι','κ':'κ','л':'λ','м':'μ','н':'ν','о':'ο','п':'π','р':'ρ','с':'σ','т':'τ',
            'у':'υ','ф':'φ','х':'χ','ц':'ψ','ч':'ω','ш':'ω','щ':'ω','ъ':'ʏ','ы':'ʏ','ь':'ʏ',
            'э':'ε','ю':'υ','я':'α'}
            
    CHANNELS_CHOICE = [app_commands.Choice(name=f"{v['emoji']} {v['name']}", value=k) for k,v in RADIO_CONFIG.items()]
    ENCRYPTS = [app_commands.Choice(name=n, value=str(i)) for i,n in enumerate(["❌ Нет", "🔒 Базовое", "🔐 Полное"])]
    NOISES = [app_commands.Choice(name=n, value=str(i)) for i,n in enumerate(["📡 Без помех", "📡 Легкие", "📡 Средние", "📡 Сильные"])]