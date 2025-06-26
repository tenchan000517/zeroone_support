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
    1: "1386267058307600525",  # 火曜: オンライン講座情報
    2: "1386289811027005511",  # 水曜: 最新情報（ビジネストレンド速報）
    3: None,  # 木曜: メンションなし
    4: None,  # 金曜: メンションなし
    5: "1381201663045668906",  # 土曜: events（地域イベント情報）
    6: None   # 日曜: メンションなし
}

# AIキャラクター会話設定（シンプル版）
AI_CHAT_CONFIG = {
    "enabled": True,
    "target_channel_id": "1236344090086342798",  # AIキャラクター会話専用チャンネル
    "spontaneous_chat_times": [13],  # 自発的会話の時刻（お昼過ぎのみ）
    "user_interaction_enabled": True,  # ユーザーとのインタラクション機能
    "max_responses_per_conversation": 3,  # 1つの会話での最大応答回数
    "conversation_timeout_minutes": 30,  # 会話コンテキストのタイムアウト（分）
    "simple_mode": True,  # シンプルモード有効
    "api_throttle_seconds": 2.0,  # APIリクエスト間隔（秒）
    
    # キャラクターバイパスモード設定
    "character_bypass": {
        "enabled": True,
        "source_channel_id": "1382212340623347794",  # キャラクターバイパス専用チャンネルID
        "default_character_id": "ai_king_dynaka",  # デフォルトキャラクター（キング・ダイナカ）
        "default_target_channel_id": "1236344090086342798"  # デフォルト送信先
    }
}

# Discord メトリクス収集設定
METRICS_CONFIG = {
    # メインロール設定
    "viewable_role_id": 1236344630132473946,  # 閲覧可能ロール「ZERO to ONE」
    "staff_role_id": 1236487195741913119,     # 運営ロール「エグゼクティブマネージャー」
    
    # 集計対象ロール設定
    "tracked_roles": {
        1383347155548504175: "経営幹部",
        1383347231188586628: "学生",
        1383347303347257486: "フリーランス",
        1383347353141907476: "エンジョイ",
        1332242428459221046: "FIND to DO",
        1381201663045668906: "イベント情報", 
        1382167308180394145: "みんなの告知",
        1386289811027005511: "最新情報",
        1386267058307600525: "オンライン講座情報",
        1386366903395815494: "AI・テック情報"
    },
    
    # メトリクス設定
    "collection_schedule": {
        "timezone": "Asia/Tokyo",
        "daily_hour": 0,  # 毎日0:00に実行
        "daily_minute": 0
    },
    
    # エンゲージメントスコア計算設定
    "engagement_weights": {
        "active_ratio_weight": 0.4,    # アクティブユーザー率の重み
        "message_density_weight": 0.6  # メッセージ密度の重み
    },
    
    # リアクション追跡設定
    "reaction_tracking": {
        "enabled": True,
        "track_custom_emojis": True,
        "excluded_channels": [],  # 除外チャンネルID (リスト)
        "max_message_age_days": 30,  # 過去何日分のメッセージを対象とするか
        "top_emojis_limit": 10  # 上位絵文字の表示数
    },
    
    # ダッシュボード連携設定
    "dashboard_integration": {
        "enabled": True,
        "api_url": "https://find-to-do-management-app-tenchan000517-tenchan000517s-projects.vercel.app/api/discord/metrics",
        "timeout_seconds": 10,
        "retry_attempts": 3,
        "fallback_to_db_only": True  # API失敗時はDB保存のみ継続
    }
}

# チャンネル通知設定
CHANNEL_NOTIFICATIONS = {
    "enabled": True,
    "line_webhook_url": "https://find-to-do-management-app.vercel.app/api/webhook/discord-notifications",
    
    "monitored_channels": {
        # WELCOM - 新規参入通知
        "1236341987272032316": {
            "name": "WELCOM",
            "type": "new_member",
            "description": "メンバーが新規参入した時の通知（ボット・運営除外）",
            "exclude_bots": True,
            "notification_message": "🎉 新しいメンバーが WELCOM チャンネルに参加しました！"
        },
        
        # 自己紹介 - 投稿通知
        "1373946891334844416": {
            "name": "自己紹介", 
            "type": "new_post",
            "description": "メンバーが自己紹介をした時の通知（リプライ・ボット・運営除外）",
            "exclude_bots": True,
            "exclude_replies": True,
            "notification_message": "📝 新しい自己紹介が投稿されました！"
        },
        
        # 雑談 - 運営不在監視
        "1236344090086342798": {
            "name": "雑談",
            "type": "staff_absence_monitoring", 
            "description": "メンバー発言後、運営が1時間以上返信しない場合に通知",
            "exclude_bots": True,
            "staff_absence_hours": 1,
            "notification_message": "⚠️ 雑談チャンネルで運営の応答が1時間以上ありません"
        },
        
        # 誰でも告知 - 告知投稿通知
        "1330790111259922513": {
            "name": "誰でも告知",
            "type": "announcement", 
            "description": "メンバーが告知を行った場合に通知（ボット・運営除外）",
            "exclude_bots": True,
            "notification_message": "📢 新しい告知が投稿されました！"
        }
    }
}

# チャンネル紹介通知設定
CHANNEL_INTRO_CONFIG = {
    "enabled": True,
    "target_channel_id": "1236344090086342798",  # 雑談チャンネル
    "mention_role_id": "1332242428459221046",    # FIND to DOロール
    "schedule": {
        "days_of_week": [0, 4],  # 月曜日(0)と金曜日(4)
        "hour": 9,               # 9時
        "minute": 0              # 0分
    },
    "interval_hours": 24  # 24時間間隔での確認
}
