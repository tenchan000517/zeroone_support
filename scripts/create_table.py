#!/usr/bin/env python3
"""
時間別ガントチャートテーブル作成スクリプト
"""

import asyncpg
import asyncio
import os
from dotenv import load_dotenv

async def create_hourly_gantt_table():
    """hourly_gantt_data テーブルを作成"""
    
    # 環境変数読み込み
    load_dotenv()
    db_url = os.getenv('NEON_DATABASE_URL')
    
    if not db_url:
        print("❌ NEON_DATABASE_URL 環境変数が設定されていません")
        return False
    
    try:
        print("🔌 データベースに接続中...")
        # DB接続（改行文字を削除）
        clean_db_url = db_url.replace('\n', '').replace(' ', '')
        conn = await asyncpg.connect(clean_db_url)
        
        print("✅ データベース接続成功")
        
        # PostgreSQL バージョン確認
        version_result = await conn.fetchrow("SELECT version()")
        print(f"📊 PostgreSQL: {version_result['version'].split(' ')[0]}")
        
        # 既存テーブル確認
        tables_result = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"\n📋 既存テーブル数: {len(tables_result)}個")
        for table in tables_result:
            print(f"  - {table['table_name']}")
        
        # hourly_gantt_data テーブル作成
        print(f"\n📊 hourly_gantt_data テーブルを作成中...")
        
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS hourly_gantt_data (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
                data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(date, hour)
            );
        """
        
        await conn.execute(create_table_sql)
        print("✅ テーブル作成完了")
        
        # インデックス作成
        print("🔍 インデックス作成中...")
        
        create_indexes_sql = """
            CREATE INDEX IF NOT EXISTS idx_hourly_gantt_date_hour ON hourly_gantt_data(date, hour);
            CREATE INDEX IF NOT EXISTS idx_hourly_gantt_created_at ON hourly_gantt_data(created_at);
        """
        
        await conn.execute(create_indexes_sql)
        print("✅ インデックス作成完了")
        
        # コメント追加
        print("💬 コメント追加中...")
        
        comments_sql = """
            COMMENT ON TABLE hourly_gantt_data IS '時間別オンラインユーザーガントチャートデータ';
            COMMENT ON COLUMN hourly_gantt_data.date IS '収集日付';
            COMMENT ON COLUMN hourly_gantt_data.hour IS '時間（0-23）';
            COMMENT ON COLUMN hourly_gantt_data.data IS 'ガントチャートJSON データ';
            COMMENT ON COLUMN hourly_gantt_data.created_at IS '作成日時';
            COMMENT ON COLUMN hourly_gantt_data.updated_at IS '更新日時';
        """
        
        await conn.execute(comments_sql)
        print("✅ コメント追加完了")
        
        # テーブル確認
        table_info = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'hourly_gantt_data'
            ORDER BY ordinal_position
        """)
        
        print(f"\n📋 作成されたテーブル構造:")
        for col in table_info:
            nullable = "NULL可" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  {col['column_name']}: {col['data_type']} ({nullable}){default}")
        
        # インデックス確認
        indexes = await conn.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes 
            WHERE tablename = 'hourly_gantt_data'
        """)
        
        print(f"\n🔍 作成されたインデックス:")
        for idx in indexes:
            print(f"  - {idx['indexname']}")
        
        await conn.close()
        
        print(f"\n🎉 hourly_gantt_data テーブルの作成が完了しました！")
        print(f"📊 これで時間別ガントチャートデータの永続保存が可能になります。")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_hourly_gantt_table())
    if not success:
        exit(1)