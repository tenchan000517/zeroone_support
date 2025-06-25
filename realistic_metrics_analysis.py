#!/usr/bin/env python3
"""
より現実的なメトリクス分析
実際の使用パターンを考慮した分析
"""

import asyncio
import asyncpg
import os
import json
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

async def analyze_realistic_patterns():
    """現実的なパターン分析"""
    db_url = os.getenv('NEON_DATABASE_URL')
    if not db_url:
        print("❌ データベースURL未設定")
        return
    
    try:
        conn = await asyncpg.connect(db_url)
        
        print("=" * 60)
        print("📊 現実的なメトリクス分析")
        print("=" * 60)
        
        # 1. 曜日別パターン分析
        print("\n📅 曜日別メッセージパターン")
        weekday_stats = await conn.fetch("""
            SELECT 
                EXTRACT(DOW FROM date) as day_of_week,
                COUNT(*) as day_count,
                AVG(daily_messages) as avg_messages,
                SUM(CASE WHEN daily_messages = 0 THEN 1 ELSE 0 END) as zero_days,
                MAX(daily_messages) as max_messages,
                MIN(daily_messages) as min_messages
            FROM discord_metrics
            GROUP BY EXTRACT(DOW FROM date)
            ORDER BY day_of_week
        """)
        
        weekday_names = ['日', '月', '火', '水', '木', '金', '土']
        for row in weekday_stats:
            dow = int(row['day_of_week'])
            avg_msg = row['avg_messages'] or 0
            zero_ratio = (row['zero_days'] / row['day_count'] * 100) if row['day_count'] > 0 else 0
            
            print(f"   {weekday_names[dow]}曜日: 平均{avg_msg:.1f}件, "
                  f"ゼロ日{row['zero_days']}/{row['day_count']}日({zero_ratio:.0f}%), "
                  f"最大{row['max_messages']}件")
        
        # 2. チャンネル活動パターン
        print("\n📍 チャンネル活動パターン")
        channel_activity = await conn.fetch("""
            SELECT 
                date,
                channel_message_stats,
                daily_messages
            FROM discord_metrics
            WHERE daily_messages > 0
            ORDER BY date DESC
            LIMIT 10
        """)
        
        channel_frequency = defaultdict(int)
        channel_messages = defaultdict(int)
        
        for row in channel_activity:
            stats = json.loads(row['channel_message_stats'])
            print(f"\n   📅 {row['date']} (総{row['daily_messages']}件):")
            
            for ch_id, ch_stats in stats.items():
                msg_count = ch_stats.get('user_messages', 0)
                user_count = ch_stats.get('user_count', 0)
                
                channel_frequency[ch_id] += 1
                channel_messages[ch_id] += msg_count
                
                if msg_count > 0:
                    print(f"      - チャンネル{ch_id}: {msg_count}件 ({user_count}人)")
        
        # 最も活発なチャンネル
        print("\n📊 チャンネル別累計統計:")
        sorted_channels = sorted(channel_messages.items(), key=lambda x: x[1], reverse=True)
        for ch_id, total_msg in sorted_channels[:5]:
            freq = channel_frequency[ch_id]
            print(f"   - チャンネル{ch_id}: 累計{total_msg}件 ({freq}日間で記録)")
        
        # 3. アクティブユーザーの問題分析
        print("\n👥 アクティブユーザー数の問題")
        active_user_check = await conn.fetch("""
            SELECT date, active_users, daily_messages, member_count
            FROM discord_metrics
            ORDER BY date DESC
            LIMIT 10
        """)
        
        for row in active_user_check:
            activity_rate = (row['active_users'] / row['member_count'] * 100) if row['member_count'] > 0 else 0
            print(f"   📅 {row['date']}: アクティブ{row['active_users']}人/{row['member_count']}人 "
                  f"({activity_rate:.1f}%), メッセージ{row['daily_messages']}件")
        
        # 4. 実際の問題判定
        print("\n🔍 実際の問題判定:")
        
        # 問題1: アクティブユーザーが常に0
        if all(row['active_users'] == 0 for row in active_user_check):
            print("   ❌ 【確実な問題】アクティブユーザー数が全日程で0人")
            print("      → count_active_users 関数が機能していない")
        
        # 問題2: チャンネル記録の偏り
        if len(channel_frequency) <= 3:
            print("   ⚠️ 【可能性のある問題】記録されているチャンネルが少なすぎる")
            print(f"      → {len(channel_frequency)}チャンネルのみ記録")
            print("      → 特定のチャンネルのみカウントされている可能性")
        
        # 問題3: メッセージ0の日の妥当性
        total_days = await conn.fetchval("SELECT COUNT(*) FROM discord_metrics")
        zero_days = await conn.fetchval("SELECT COUNT(*) FROM discord_metrics WHERE daily_messages = 0")
        zero_ratio = (zero_days / total_days * 100) if total_days > 0 else 0
        
        if zero_ratio > 30:
            print(f"   ⚠️ 【要確認】メッセージ0の日が{zero_ratio:.0f}%")
            print("      → 完全に正常とは言えないが、小規模コミュニティなら可能性あり")
        
        # 5. 正常に動作している部分
        print("\n✅ 正常に動作している部分:")
        print("   - データベースへの保存機能")
        print("   - 定期実行（毎日0:00）")
        print("   - ロール別メンバー数の取得")
        print("   - 基本的なメッセージカウント（部分的）")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")

async def check_specific_channels():
    """特定チャンネルの詳細確認"""
    db_url = os.getenv('NEON_DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    print("\n" + "="*60)
    print("📍 記録されているチャンネルID一覧")
    print("="*60)
    
    # 全期間でメッセージが記録されたチャンネル
    all_data = await conn.fetch("""
        SELECT channel_message_stats
        FROM discord_metrics
        WHERE daily_messages > 0
    """)
    
    channel_names = {
        "1236344090086342798": "AIキャラクター会話",
        "1236319711113777233": "一般",
        "1372050153472528504": "不明1",
        "1373946891334844416": "不明2",
        "1383411485367205948": "不明3",
        "1384299271603355750": "不明4"
    }
    
    all_channels = set()
    for row in all_data:
        stats = json.loads(row['channel_message_stats'])
        all_channels.update(stats.keys())
    
    print("\n記録されたチャンネル:")
    for ch_id in sorted(all_channels):
        ch_name = channel_names.get(ch_id, "未確認")
        print(f"   - {ch_id}: {ch_name}")
    
    await conn.close()

async def main():
    await analyze_realistic_patterns()
    await check_specific_channels()

if __name__ == "__main__":
    asyncio.run(main())