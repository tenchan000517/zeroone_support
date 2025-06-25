#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import datetime

def analyze_schedule():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))  # JST
    current_weekday = now.weekday()
    
    print(f"現在時刻: {now.strftime('%Y-%m-%d %H:%M:%S')} JST")
    print(f"現在の曜日番号: {current_weekday}")
    
    weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
    print(f"現在の曜日: {weekday_names[current_weekday]}曜日")
    
    print("\n=== デフォルト設定分析 ===")
    
    # デフォルト設定
    default_settings = {
        "quotes": {
            "enabled": True,
            "hour": 9,
            "minute": 0,
            "days": "毎日"
        },
        "tips": {
            "enabled": True,
            "hour": 18,
            "minute": 0,
            "days": "毎日"
        },
        "challenge": {
            "enabled": True,
            "hour": 10,
            "minute": 0,
            "days": "毎日"
        },
        "trends": {
            "enabled": True,
            "hour": 8,
            "minute": 0,
            "days": "1,4",  # 火曜日と金曜日
            "days_text": "火曜日, 金曜日"
        }
    }
    
    print("コンテンツタイプごとの設定:")
    for content_type, settings in default_settings.items():
        print(f"\n{content_type.upper()}:")
        print(f"  有効: {settings['enabled']}")
        print(f"  時刻: {settings['hour']:02d}:{settings['minute']:02d}")
        if content_type == "trends":
            print(f"  送信曜日: {settings['days_text']} (番号: {settings['days']})")
        else:
            print(f"  送信曜日: {settings['days']}")
    
    print("\n=== 今日の送信予定分析 ===")
    
    # トレンドの曜日チェック
    trend_days = [int(d.strip()) for d in "1,4".split(',')]
    print(f"トレンド送信曜日設定: {trend_days} (火曜=1, 金曜=4)")
    print(f"今日はトレンド送信対象: {'YES' if current_weekday in trend_days else 'NO'}")
    
    if current_weekday not in trend_days:
        print(f"理由: 今日は{weekday_names[current_weekday]}曜日（番号{current_weekday}）で、トレンド送信対象の曜日ではありません")
    
    print(f"\n今日送信される予定のコンテンツ:")
    today_schedule = []
    
    # 各コンテンツタイプをチェック
    for content_type, settings in default_settings.items():
        if settings['enabled']:
            if content_type == "trends":
                if current_weekday in trend_days:
                    today_schedule.append(f"  {settings['hour']:02d}:{settings['minute']:02d} - {content_type.upper()}")
            else:
                today_schedule.append(f"  {settings['hour']:02d}:{settings['minute']:02d} - {content_type.upper()}")
    
    if today_schedule:
        for item in sorted(today_schedule):
            print(item)
    else:
        print("  送信予定なし")

if __name__ == "__main__":
    analyze_schedule()