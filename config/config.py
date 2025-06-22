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
CONNPASS_API_KEY = os.getenv('CONNPASS_API_KEY')

# RSS監視設定
RSS_CONFIG = {
    "enabled": True,
    "url": "https://find-to-do.com/rss.xml",
    "check_interval": 600,  # 秒（10分間隔）
    "data_dir": "data",
    "last_check_file": "data/rss_last_check.json",
    "target_channel_id": "1236319713013792811",  # 投稿先チャンネルID
    "mention_role_id": "1386267058307600525"     # メンション対象ロールID
}

# 週間コンテンツ曜日別メンションロールID設定
WEEKLY_MENTION_ROLES = {
    0: None,  # 月曜: メンションなし
    1: "1386289811027005511",  # 火曜: connpass（オンライン講座情報）
    2: "1386267058307600525",  # 水曜: trends（ビジネストレンド速報）
    3: None,  # 木曜: メンションなし
    4: None,  # 金曜: メンションなし
    5: "1381201663045668906",  # 土曜: events（地域イベント情報）
    6: None   # 日曜: メンションなし
}

# AIキャラクター会話設定
AI_CHAT_CONFIG = {
    "enabled": True,
    "target_channel_id": "1236344090086342798",  # AIキャラクター会話専用チャンネル
    "spontaneous_chat_times": [8, 13, 20],  # 自発的会話の時刻（朝昼晩）
    "user_interaction_enabled": True,  # ユーザーとのインタラクション機能
    "max_responses_per_conversation": 3,  # 1つの会話での最大応答回数
    "conversation_timeout_minutes": 30  # 会話コンテキストのタイムアウト（分）
}
