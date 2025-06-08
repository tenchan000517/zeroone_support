import os
from dotenv import load_dotenv

# .envファイルの内容を読み込む
load_dotenv()

# 環境変数から設定を読み込む
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
MAIN_CHAT_CHANNEL = os.getenv('MAIN_CHAT_CHANNEL')
BOT_SALON_CHANNEL = os.getenv('BOT_SALON_CHANNEL')
BACK_MODE_CHANNEL = os.getenv('BACK_MODE_CHANNEL')
GRAVE_CHANNEL = os.getenv('GRAVE_CHANNEL')
STORM_CHANNEL = os.getenv('STORM_CHANNEL')
DEV_CHANNEL = os.getenv('DEV_CHANNEL')
POKEMON_CHANNEL = os.getenv('POKEMON_CHANNEL')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DOORKEEPER_API_TOKEN = os.getenv('DOORKEEPER_API_TOKEN')
