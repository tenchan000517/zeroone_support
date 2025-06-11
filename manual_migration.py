#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動データベースマイグレーション実行スクリプト
"""

import sqlite3
import os

def run_migration():
    db_path = 'bot_data.db'
    
    if not os.path.exists(db_path):
        print(f"❌ データベースファイル {db_path} が見つかりません")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 現在のテーブル構造を確認中...")
        cursor.execute("PRAGMA table_info(channel_intro_settings)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"現在のカラム: {columns}")
        
        # interval_hours カラムの追加
        if 'interval_hours' not in columns:
            print("➕ interval_hours カラムを追加中...")
            cursor.execute("ALTER TABLE channel_intro_settings ADD COLUMN interval_hours INTEGER DEFAULT 168")
            
            # 既存のinterval_daysデータがあれば移行
            if 'interval_days' in columns:
                print("🔄 interval_days データを移行中...")
                cursor.execute("""
                    UPDATE channel_intro_settings 
                    SET interval_hours = COALESCE(interval_days * 24, 168)
                    WHERE interval_hours IS NULL OR interval_hours = 168
                """)
            print("✅ interval_hours カラム追加完了")
        
        # scheduled_hour カラムの追加
        if 'scheduled_hour' not in columns:
            print("➕ scheduled_hour カラムを追加中...")
            cursor.execute("ALTER TABLE channel_intro_settings ADD COLUMN scheduled_hour INTEGER")
            print("✅ scheduled_hour カラム追加完了")
        
        # scheduled_minute カラムの追加
        if 'scheduled_minute' not in columns:
            print("➕ scheduled_minute カラムを追加中...")
            cursor.execute("ALTER TABLE channel_intro_settings ADD COLUMN scheduled_minute INTEGER")
            print("✅ scheduled_minute カラム追加完了")
        
        conn.commit()
        
        # 更新後のテーブル構造を確認
        print("\n🔍 更新後のテーブル構造:")
        cursor.execute("PRAGMA table_info(channel_intro_settings)")
        for row in cursor.fetchall():
            print(f"  {row[1]} ({row[2]})")
        
        # データ確認
        cursor.execute("SELECT COUNT(*) FROM channel_intro_settings")
        count = cursor.fetchone()[0]
        print(f"\n📊 レコード数: {count}")
        
        if count > 0:
            cursor.execute("SELECT guild_id, enabled, channel_id, interval_hours, scheduled_hour, scheduled_minute FROM channel_intro_settings")
            print("\n📋 現在のデータ:")
            for row in cursor.fetchall():
                print(f"  Guild: {row[0]}, Enabled: {row[1]}, Channel: {row[2]}, Hours: {row[3]}, Hour: {row[4]}, Minute: {row[5]}")
        
        conn.close()
        print("\n✅ マイグレーション完了!")
        
    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 手動データベースマイグレーション開始")
    run_migration()