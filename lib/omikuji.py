import random

# ZERO to ONEおみくじの結果とメッセージ
OMIKUJI_RESULTS = {
    "大吉": {
        "emoji": "🚀",
        "message": "ユニコーン企業への道が開かれた！今日は革新的なアイデアが湧き出る日です！",
        "advice": "起業家精神で新しいビジネスにチャレンジしてみてください✨"
    },
    "吉": {
        "emoji": "💼", 
        "message": "スタートアップの成長期！ビジネスが順調に発展していきます！",
        "advice": "チームとのコミュニケーションを大切にしてください♪"
    },
    "中吉": {
        "emoji": "💡",
        "message": "MVP開発に適した日。小さな改善が大きなインパクトを生みます",
        "advice": "ユーザーフィードバックに耳を傾けてみましょう"
    },
    "小吉": {
        "emoji": "🤝",
        "message": "ネットワーキングの日。新しいパートナーやメンターとの出会いがありそう",
        "advice": "人とのつながりを大切にしてください"
    },
    "末吉": {
        "emoji": "📈",
        "message": "ピボットのタイミングかも？最後に大きなブレイクスルーが待っています",
        "advice": "諦めずに実験と改善を続けましょう"
    },
    "凶": {
        "emoji": "📚",
        "message": "今日は学習と研究の日。知識への投資が明日の成功を生みます",
        "advice": "スキルアップや業界研究に時間を使いましょう！"
    },
    "大凶": {
        "emoji": "🔄",
        "message": "リセットのタイミング。今日は戦略を再考して新しいアプローチを検討しましょう",
        "advice": "休息も戦略の一部。リフレッシュして新たな視点を得ましょう🛁"
    }
}

# DJアイズインキュベーターのスタートアップおみくじ（リニューアル版）
def dj_omikuji():
    # より現実的な確率設定
    weighted_results = [
        ("大吉", 5),    # 5%
        ("吉", 20),     # 20%
        ("中吉", 25),   # 25%
        ("小吉", 25),   # 25%
        ("末吉", 15),   # 15%
        ("凶", 8),      # 8%
        ("大凶", 2)     # 2%
    ]
    
    # 重み付きランダム選択
    results = []
    weights = []
    for result, weight in weighted_results:
        results.append(result)
        weights.append(weight)
    
    chosen_result = random.choices(results, weights=weights)[0]
    result_data = OMIKUJI_RESULTS[chosen_result]
    
    # ランダムな演出
    sound_effects = [
        "ガラガラガラ... 🎲",
        "カランコロン... 🔔", 
        "シャラシャラ... ✨",
        "リンリンリン... 🛎️"
    ]
    
    lucky_items = [
        "Slack", "Notion", "Figma", "コーヒー", "ホワイトボード", "ブレストストーミング", 
        "MVPマインド", "リーンスタートアップ", "ユーザーインタビュー", "ピッチデッキ"
    ]
    
    sound = random.choice(sound_effects)
    lucky_item = random.choice(lucky_items)
    
    response_string = f"""🏢 **DJアイズのおみくじ** 🏢

{sound}
　　　　カランッ！

✨━━━━━━━━━━━━━━━━✨
　　　　　**{chosen_result}** {result_data['emoji']}
✨━━━━━━━━━━━━━━━━✨

💭 **インキュベーターからのメッセージ**
{result_data['message']}

🌟 **今日のアドバイス**
{result_data['advice']}

🍀 **今日のビジネスツール:** {lucky_item}

🏢 明日もZERO to ONE精神で頑張りましょう 🏢"""

    return response_string

# 旧関数（互換性維持）
def omikuji():
    return dj_omikuji()