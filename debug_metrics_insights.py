#!/usr/bin/env python3
"""
インサイト保存機能診断スクリプト
Discord Bot メトリクス収集機能の詳細診断
"""

import asyncio
import asyncpg
import os
import json
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

async def main():
    print("=" * 60)
    print("📊 Discord Bot インサイト保存機能診断")
    print("=" * 60)
    
    # 1. 環境変数チェック
    print("\n1️⃣ 環境変数チェック")
    db_url = os.getenv('NEON_DATABASE_URL')
    if db_url:
        print(f"✅ NEON_DATABASE_URL: 設定済み (長さ: {len(db_url)}文字)")
        print(f"   プレフィックス: {db_url[:20]}...")
    else:
        print("❌ NEON_DATABASE_URL: 未設定")
        return
    
    try:
        # 2. データベース接続テスト
        print("\n2️⃣ データベース接続テスト")
        conn = await asyncpg.connect(db_url)
        print("✅ データベース接続成功")
        
        try:
            # 3. テーブル存在確認
            print("\n3️⃣ テーブル構造確認")
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'discord_metrics'
                )
            """)
            
            if table_exists:
                print("✅ discord_metricsテーブル: 存在")
                
                # テーブルスキーマ情報取得
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'discord_metrics'
                    ORDER BY ordinal_position
                """)
                
                print("   📋 テーブルスキーマ:")
                for col in columns:
                    nullable = "NULL可" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"      - {col['column_name']}: {col['data_type']} ({nullable})")
                
            else:
                print("❌ discord_metricsテーブル: 存在しない")
                return
            
            # 4. データ確認
            print("\n4️⃣ 保存データ確認")
            
            # 最新5件のデータを取得
            recent_data = await conn.fetch("""
                SELECT date, member_count, daily_messages, engagement_score, created_at
                FROM discord_metrics
                ORDER BY date DESC
                LIMIT 5
            """)
            
            if recent_data:
                print(f"✅ データ件数: {len(recent_data)}件（最新5件表示）")
                for row in recent_data:
                    print(f"   📅 {row['date']}: メンバー{row['member_count']}人, "
                          f"メッセージ{row['daily_messages']}件, "
                          f"エンゲージメント{row['engagement_score']:.2f}, "
                          f"保存日時{row['created_at']}")
            else:
                print("⚠️ 保存されたデータが見つかりません")
            
            # 5. 今日のデータ確認
            print("\n5️⃣ 本日のデータ確認")
            today_data = await conn.fetchrow("""
                SELECT * FROM discord_metrics
                WHERE date = CURRENT_DATE
            """)
            
            if today_data:
                print("✅ 本日のデータ: 存在")
                print(f"   📊 メンバー数: {today_data['member_count']}")
                print(f"   💬 メッセージ数: {today_data['daily_messages']}")
                print(f"   👤 ユーザーメッセージ: {today_data['daily_user_messages']}")
                print(f"   👮 運営メッセージ: {today_data['daily_staff_messages']}")
                print(f"   📈 エンゲージメント: {today_data['engagement_score']}")
                print(f"   🕐 更新時刻: {today_data['updated_at']}")
                
                # JSONデータの詳細確認
                if today_data['channel_message_stats']:
                    channel_stats = json.loads(today_data['channel_message_stats'])
                    print(f"   📍 チャンネル別統計: {len(channel_stats)}チャンネル")
                    for ch_id, stats in list(channel_stats.items())[:3]:
                        print(f"      チャンネル{ch_id}: {stats['user_messages']}件")
                
                if today_data['role_counts']:
                    role_counts = json.loads(today_data['role_counts'])
                    print(f"   👥 ロール統計: {len(role_counts)}ロール")
                    for role_id, data in list(role_counts.items())[:3]:
                        print(f"      {data['name']}: {data['count']}人")
            else:
                print("⚠️ 本日のデータが見つかりません")
            
            # 6. データの整合性確認
            print("\n6️⃣ データ整合性確認")
            
            # 過去7日間のデータ推移
            trend_data = await conn.fetch("""
                SELECT date, daily_messages, member_count
                FROM discord_metrics
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY date DESC
            """)
            
            if len(trend_data) > 1:
                print("✅ データトレンド分析:")
                for i, row in enumerate(trend_data):
                    if i == 0:
                        print(f"   📅 {row['date']} (今日): メッセージ{row['daily_messages']}件, メンバー{row['member_count']}人")
                    else:
                        prev_msg = trend_data[i-1]['daily_messages']
                        msg_change = row['daily_messages'] - prev_msg if prev_msg else 0
                        change_icon = "📈" if msg_change > 0 else "📉" if msg_change < 0 else "➡️"
                        print(f"   📅 {row['date']}: メッセージ{row['daily_messages']}件 {change_icon}, メンバー{row['member_count']}人")
            
            # 7. 自動保存設định確認
            print("\n7️⃣ 自動保存設定確認")
            print("   ⏰ 定期実行時刻: 毎日 日本時間 0:00")
            print("   🔄 手動実行コマンド: /metrics")
            print("   📊 履歴確認コマンド: /metrics_history")
            print("   🧪 テスト実行コマンド: /metrics_test")
            
        finally:
            await conn.close()
            print("\n✅ データベース接続終了")
    
    except Exception as e:
        print(f"\n❌ エラー発生: {type(e).__name__}: {str(e)}")
        print(f"   詳細: {repr(e)}")
    
    print("\n" + "=" * 60)
    print("🔍 診断完了")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())