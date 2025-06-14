"""
Discord Bot - Task Management Database 接続テスト
"""
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

async def test_database_connection():
    """データベース接続テスト"""
    print("🔍 タスク管理データベース接続テストを開始...")
    
    try:
        # 環境変数から接続情報取得
        db_url = os.getenv('NEON_DATABASE_URL')
        
        if not db_url:
            print("❌ NEON_DATABASE_URL が設定されていません")
            print("   .env ファイルに以下を追加してください:")
            print("   NEON_DATABASE_URL=postgresql://username:password@host/database")
            return False
            
        print(f"📡 接続先: {db_url.split('@')[1] if '@' in db_url else 'URL設定済み'}")
        
        async with asyncpg.connect(db_url) as conn:
            # 基本接続テスト
            result = await conn.fetchval('SELECT 1 as test')
            print(f"✅ 基本接続: 成功 (結果: {result})")
            
            # データベース情報取得
            db_info = await conn.fetchrow("SELECT version() as version")
            print(f"📊 DB情報: {db_info['version'][:50]}...")
            
            # 既存テーブル確認
            tables = await conn.fetch("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            print(f"📋 利用可能テーブル ({len(tables)}個):")
            for table in tables:
                print(f"   - {table['table_name']} ({table['table_type']})")
            
            # ユーザーテーブル読み取りテスト
            if any(t['table_name'] == 'users' for t in tables):
                users = await conn.fetch("SELECT id, name, email FROM users LIMIT 5")
                print(f"👥 ユーザーデータ取得: {len(users)}件")
                for user in users:
                    print(f"   - {user['name']} ({user['id'][:8]}...)")
            else:
                print("⚠️  usersテーブルが見つかりません")
            
            # タスクテーブル読み取りテスト
            if any(t['table_name'] == 'tasks' for t in tables):
                tasks = await conn.fetch("""
                    SELECT id, title, status, priority 
                    FROM tasks 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                print(f"📝 タスクデータ取得: {len(tasks)}件")
                for task in tasks:
                    print(f"   - {task['title'][:30]}... ({task['status']}, {task['priority']})")
            else:
                print("⚠️  tasksテーブルが見つかりません")
            
            # プロジェクトテーブル読み取りテスト
            if any(t['table_name'] == 'projects' for t in tables):
                projects = await conn.fetch("""
                    SELECT id, name, status, progress 
                    FROM projects 
                    LIMIT 5
                """)
                print(f"🏗️  プロジェクトデータ取得: {len(projects)}件")
                for project in projects:
                    print(f"   - {project['name']} ({project['status']}, {project['progress']}%)")
            else:
                print("⚠️  projectsテーブルが見つかりません")
            
            print("\n🎉 データベース接続テスト完了！すべて正常に動作しています。")
            return True
            
    except asyncpg.exceptions.InvalidCatalogNameError:
        print("❌ データベースが存在しません")
        print("   データベース名を確認してください")
        return False
        
    except asyncpg.exceptions.InvalidPasswordError:
        print("❌ 認証エラー: パスワードが間違っています")
        return False
        
    except asyncpg.exceptions.ConnectionDoesNotExistError:
        print("❌ 接続エラー: ホストに接続できません")
        print("   ネットワーク接続とホスト名を確認してください")
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        return False

async def test_write_permission():
    """書き込み権限テスト"""
    print("\n🔍 書き込み権限テストを開始...")
    
    try:
        db_url = os.getenv('NEON_DATABASE_URL')
        
        async with asyncpg.connect(db_url) as conn:
            # テスト用テーブル作成（存在しない場合）
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS discord_bot_test (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ テストテーブル作成: 成功")
            
            # データ挿入テスト
            test_id = await conn.fetchval("""
                INSERT INTO discord_bot_test (test_data) 
                VALUES ($1) 
                RETURNING id
            """, f"Discord Bot Test - {asyncio.get_event_loop().time()}")
            print(f"✅ データ挿入: 成功 (ID: {test_id})")
            
            # データ読み取りテスト
            test_record = await conn.fetchrow("""
                SELECT * FROM discord_bot_test WHERE id = $1
            """, test_id)
            print(f"✅ データ読み取り: 成功 ({test_record['test_data']})")
            
            # データ削除テスト
            await conn.execute("""
                DELETE FROM discord_bot_test WHERE id = $1
            """, test_id)
            print("✅ データ削除: 成功")
            
            # テストテーブル削除
            await conn.execute("DROP TABLE IF EXISTS discord_bot_test")
            print("✅ テストテーブル削除: 成功")
            
            print("\n🎉 書き込み権限テスト完了！データベース操作が可能です。")
            return True
            
    except Exception as e:
        print(f"❌ 書き込み権限テストエラー: {e}")
        return False

async def main():
    """メインテスト実行"""
    print("=" * 60)
    print("🤖 Discord Bot - Database Connection Test")
    print("=" * 60)
    
    # 基本接続テスト
    connection_ok = await test_database_connection()
    
    if connection_ok:
        # 書き込み権限テスト
        write_ok = await test_write_permission()
        
        if write_ok:
            print("\n🚀 すべてのテストが成功しました！")
            print("   Discord Bot からタスク管理データベースへの接続準備完了です。")
        else:
            print("\n⚠️  接続は可能ですが、書き込み権限に問題があります。")
    else:
        print("\n❌ データベース接続に失敗しました。")
        print("   設定を確認してから再実行してください。")

if __name__ == "__main__":
    asyncio.run(main())