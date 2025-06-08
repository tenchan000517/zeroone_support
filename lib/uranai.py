import requests
import datetime
import random

# 星座名の定義
ZODIAC_SIGNS = [
    "♈ 牡羊座", "♉ 牡牛座", "♊ 双子座", "♋ 蟹座",
    "♌ 獅子座", "♍ 乙女座", "♎ 天秤座", "♏ 蠍座",
    "♐ 射手座", "♑ 山羊座", "♒ 水瓶座", "♓ 魚座"
]

# ZERO to ONE運勢メッセージのバリエーション
FORTUNE_INTRO = [
    "起業家精神があなたを導いています！",
    "イノベーションの星座からのメッセージです✨",
    "今日のあなたのビジネス運命が開かれました！",
    "DJアイズのスタートアップ占いの結果は...",
    "シリコンバレーから届く成功のエネルギー！"
]

# ZERO to ONEラッキーメッセージ
LUCKY_MESSAGES = {
    "high": [
        "今日は革新的なアイデアが生まれる日！新しいビジネスを始めるチャンスです🚀",
        "あなたの起業家精神が最高潮に！今日こそZERO to ONEを実現する時✨",
        "投資家があなたのプレゼンに注目する日。ピッチの準備はできていますか？🌟",
        "今日のあなたは次世代のイノベーターです！世界を変える第一歩を踏み出しましょう"
    ],
    "medium": [
        "スタートアップの基盤を固める良い日。チーム作りやマーケット調査に最適です💼",
        "MVP開発やユーザーテストに適した日。小さな改善が大きな成果につながります♪",
        "ネットワーキングに最適な日。新しい出会いがビジネスチャンスを生みそう🤝",
        "データ分析や戦略見直しの日。現状を整理して次のステップを計画しましょう🍀"
    ],
    "low": [
        "今日は学習と準備の日。スキルアップやマーケット研究に時間を使いましょう📚",
        "リスクマネジメントを見直す好機。慎重な判断が将来の成功につながります⚖️",
        "今日の課題は明日のイノベーション。失敗を恐れず挑戦し続けましょう💪",
        "ピボットのタイミングかも？新しい角度からビジネスを見直してみて🔄"
    ]
}

# DJアイズ占い（リニューアル版）
def dj_eyes_fortune(user_name):
    response_string = ''
    date = datetime.datetime.today().strftime("%Y/%m/%d")

    try:
        res = requests.get(url='http://api.jugemkey.jp/api/horoscope/free/'+ date)
        seiza_index = random.randint(0, 11)  # 星座をランダム選択
        seiza_name = ZODIAC_SIGNS[seiza_index]
        txt = res.json()["horoscope"][date][seiza_index]
        
        # 数値を絵文字とパーセンテージに変換
        job_score = int(txt["job"])
        money_score = int(txt["money"])
        love_score = int(txt["love"])
        total_score = int(txt["total"])
        
        job_emoji = create_star_rating(job_score)
        money_emoji = create_star_rating(money_score)
        love_emoji = create_star_rating(love_score)
        total_emoji = create_star_rating(total_score)
        
        # ランキングをパーセンテージに変換（より魅力的な計算）
        rank = int(txt["rank"])
        base_percentage = (13 - rank) * 8  # より幅のある計算
        random_boost = random.randint(-3, 7)  # ランダム要素
        final_percentage = max(15, min(98, base_percentage + random_boost))
        
        # 運勢レベル判定
        if final_percentage >= 80:
            fortune_level = "high"
        elif final_percentage >= 50:
            fortune_level = "medium"
        else:
            fortune_level = "low"
        
        intro_msg = random.choice(FORTUNE_INTRO)
        lucky_msg = random.choice(LUCKY_MESSAGES[fortune_level])
        
        response_string = f"""🚀 **DJアイズのZERO to ONE占い** 🚀

{intro_msg}

⭐ **{user_name}**さんは今日、**{seiza_name}**の起業家として輝きます ⭐
✨ **ビジネス成功率: {final_percentage}%** ✨

{txt["content"]}

💡 **今日のスタートアップアドバイス**
{lucky_msg}

🍀 **ラッキーツール:** {txt["item"]}
🌈 **ラッキーブランドカラー:** {txt["color"]}

📊 **起業家運勢詳細**
💼 ビジネス運: {job_emoji} ({job_score}/5)
💰 資金調達運: {money_emoji} ({money_score}/5) 
💕 チームワーク運: {love_emoji} ({love_score}/5)
🌟 イノベーション運: {total_emoji} ({total_score}/5)

✨ 今日もZERO to ONEの精神で挑戦しましょう！ ✨"""
        
    except Exception as e:
        print(f"占いAPIエラー: {e}")
        response_string = """🚀 **DJアイズのZERO to ONE占い** 🚀

申し訳ございません...
今、イノベーションの星座が再起動中です 💻

少し時間をおいてから、
もう一度「**今日の運勢**」と話しかけてくださいね！

✨ きっと素晴らしいビジネスチャンスが待っています ✨"""

    return response_string

# 星評価システム
def create_star_rating(score):
    full_stars = score
    empty_stars = 5 - score
    return "⭐" * full_stars + "☆" * empty_stars

# 旧関数（互換性維持）
def uranai(user_name):
    return dj_eyes_fortune(user_name)

# 旧関数（互換性維持）
def emoji(number, category):
    res = ''
    for i in range(number):
        if category == 'job':
            res += '💼 '
        elif category == 'money':
            res += '💰 '
        elif category == 'love':
            res += '❤️ '
        elif category == 'total':
            res += '⭐ '
    return res