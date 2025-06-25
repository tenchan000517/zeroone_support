#!/usr/bin/env python3
"""
Discord メトリクス テーブル拡張スクリプト
reaction_stats カラムを既存の discord_metrics テーブルに追加

使用方法:
1. 事前にデータベースのバックアップを取る
2. このスクリプトを実行してカラムを追加
3. 動作確認後、本番運用開始

注意: 本スクリプトは既存データを変更します。実行前に必ずバックアップを取ってください。
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

async def add_reaction_stats_column():
    """discord_metrics テーブルに reaction_stats カラムを追加"""
    
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
            # 既存テーブルの確認
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
            
            # reaction_stats カラムの存在確認
            column_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'discord_metrics' 
                    AND column_name = 'reaction_stats'
                )
            """)
            
            if column_exists:
                print("ℹ️ reaction_stats カラムは既に存在します")
                return True
            
            # カラム追加実行
            print("🔧 reaction_stats カラムを追加中...")
            await conn.execute("""
                ALTER TABLE discord_metrics 
                ADD COLUMN reaction_stats JSONB DEFAULT '{}'::jsonb
            """)
            
            print("✅ reaction_stats カラムを正常に追加しました")
            
            # 追加確認
            verify_column = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'discord_metrics' 
                    AND column_name = 'reaction_stats'
                )
            """)
            
            if verify_column:
                print("✅ カラム追加の確認が完了しました")
                
                # テーブル構造の表示
                print("\n📋 更新後のテーブル構造:")
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'discord_metrics'
                    ORDER BY ordinal_position
                """)
                
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
                
                return True
            else:
                print("❌ カラム追加の確認に失敗しました")
                return False
            
        finally:
            await conn.close()
            print("🔌 データベース接続を閉じました")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {type(e).__name__}: {e}")
        return False

async def main():
    """メイン処理"""
    print("🚀 Discord メトリクス テーブル拡張スクリプト開始")
    print("=" * 60)
    
    # 注意喚起
    print("⚠️  重要: このスクリプトはデータベーステーブルを変更します")
    print("⚠️  実行前に必ずデータベースのバックアップを取ってください")
    print()
    
    # 確認プロンプト
    confirm = input("続行しますか？ (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("🛑 処理を中止しました")
        return
    
    print()
    success = await add_reaction_stats_column()
    
    print()
    print("=" * 60)
    if success:
        print("✅ テーブル拡張が正常に完了しました")
        print("📊 リアクション統計機能を使用できます")
    else:
        print("❌ テーブル拡張に失敗しました")
        print("🔍 エラーログを確認し、必要に応じて手動でカラムを追加してください")
        print("🔧 手動追加SQL: ALTER TABLE discord_metrics ADD COLUMN reaction_stats JSONB DEFAULT '{}'::jsonb;")

if __name__ == "__main__":
    asyncio.run(main())