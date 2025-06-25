#!/usr/bin/env python3
"""
Discord メトリクス データベースバックアップスクリプト
既存の discord_metrics テーブルのデータをJSON形式でバックアップ

使用方法:
python backup_database.py

出力: discord_metrics_backup_YYYYMMDD_HHMMSS.json
"""

import asyncio
import asyncpg
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

async def backup_discord_metrics():
    """discord_metrics テーブルのデータをバックアップ"""
    
    # データベース接続URL取得
    db_url_raw = os.getenv('NEON_DATABASE_URL')
    if not db_url_raw:
        print("❌ NEON_DATABASE_URL 環境変数が設定されていません")
        return False
    
    db_url = db_url_raw.replace('\n', '').replace(' ', '')
    
    try:
        print("🔗 データベースに接続中...")
        conn = await asyncpg.connect(db_url)
        
        try:
            # テーブル存在確認
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'discord_metrics'
                )
            """)
            
            if not table_exists:
                print("❌ discord_metrics テーブルが存在しません")
                return False
            
            print("✅ discord_metrics テーブルを確認")
            
            # データ取得
            print("📊 データを取得中...")
            rows = await conn.fetch("SELECT * FROM discord_metrics ORDER BY date DESC")
            
            if not rows:
                print("ℹ️ バックアップするデータがありません")
                return True
            
            print(f"📄 {len(rows)}件のレコードを取得")
            
            # JSON変換用のデータ準備
            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "table_name": "discord_metrics",
                "record_count": len(rows),
                "data": []
            }
            
            for row in rows:
                # Row型から辞書型に変換し、日付をISO形式に変換
                row_dict = dict(row)
                if 'date' in row_dict and row_dict['date']:
                    row_dict['date'] = row_dict['date'].isoformat()
                if 'created_at' in row_dict and row_dict['created_at']:
                    row_dict['created_at'] = row_dict['created_at'].isoformat()
                if 'updated_at' in row_dict and row_dict['updated_at']:
                    row_dict['updated_at'] = row_dict['updated_at'].isoformat()
                
                backup_data["data"].append(row_dict)
            
            # ファイル名生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"discord_metrics_backup_{timestamp}.json"
            
            # ファイル保存
            print(f"💾 バックアップファイルを作成中: {backup_filename}")
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ バックアップが完了しました: {backup_filename}")
            print(f"📈 バックアップサイズ: {os.path.getsize(backup_filename) / 1024:.1f} KB")
            
            # 最新のデータ概要を表示
            if backup_data["data"]:
                latest = backup_data["data"][0]
                print(f"📅 最新データ: {latest.get('date', 'N/A')}")
                print(f"👥 メンバー数: {latest.get('member_count', 'N/A'):,}")
                print(f"💬 メッセージ数: {latest.get('daily_messages', 'N/A'):,}")
            
            return True
            
        finally:
            await conn.close()
            print("🔌 データベース接続を閉じました")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {type(e).__name__}: {e}")
        return False

async def main():
    """メイン処理"""
    print("💾 Discord メトリクス データベースバックアップ開始")
    print("=" * 60)
    
    success = await backup_discord_metrics()
    
    print()
    print("=" * 60)
    if success:
        print("✅ バックアップが正常に完了しました")
        print("🔒 このバックアップファイルは安全な場所に保管してください")
    else:
        print("❌ バックアップに失敗しました")
        print("🔍 エラーログを確認してください")

if __name__ == "__main__":
    asyncio.run(main())