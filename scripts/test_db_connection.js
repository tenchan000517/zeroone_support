const { Client } = require('pg');
require('dotenv').config();

async function testDatabaseConnection() {
    console.log('🔌 データベース接続テスト開始...');
    
    if (!process.env.NEON_DATABASE_URL) {
        console.error('❌ NEON_DATABASE_URL 環境変数が設定されていません');
        return;
    }
    
    console.log('📍 接続先:', process.env.NEON_DATABASE_URL.replace(/:[^:@]*@/, ':***@'));
    
    const client = new Client({
        connectionString: process.env.NEON_DATABASE_URL,
        ssl: { rejectUnauthorized: false }
    });

    try {
        await client.connect();
        console.log('✅ データベース接続成功');
        
        // 基本情報取得
        const versionResult = await client.query('SELECT version()');
        console.log('📊 PostgreSQL バージョン:', versionResult.rows[0].version.split(' ')[0]);
        
        // 現在のデータベース名
        const dbResult = await client.query('SELECT current_database()');
        console.log('🗄️  現在のデータベース:', dbResult.rows[0].current_database);
        
        // 既存テーブル一覧
        const tablesResult = await client.query(`
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        `);
        
        console.log('\n📋 既存テーブル一覧:');
        if (tablesResult.rows.length === 0) {
            console.log('  (テーブルなし)');
        } else {
            tablesResult.rows.forEach(row => {
                console.log(`  - ${row.table_name} (${row.table_type})`);
            });
        }
        
        // discord_metrics テーブルの詳細確認
        const discordMetricsCheck = await client.query(`
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'discord_metrics'
            ORDER BY ordinal_position;
        `);
        
        if (discordMetricsCheck.rows.length > 0) {
            console.log('\n📊 discord_metrics テーブル構造:');
            discordMetricsCheck.rows.forEach(row => {
                console.log(`  ${row.column_name}: ${row.data_type} ${row.is_nullable === 'YES' ? '(NULL可)' : '(NOT NULL)'}`);
            });
            
            // レコード数確認
            const countResult = await client.query('SELECT COUNT(*) FROM discord_metrics');
            console.log(`📈 discord_metrics レコード数: ${countResult.rows[0].count}件`);
        } else {
            console.log('\n❌ discord_metrics テーブルが見つかりません');
        }
        
        console.log('\n🎉 データベーステスト完了');
        
    } catch (error) {
        console.error('❌ データベース接続エラー:', error.message);
        console.error('💡 考えられる原因:');
        console.error('  1. NEON_DATABASE_URL の設定が間違っている');
        console.error('  2. データベースサーバーがダウンしている');
        console.error('  3. ネットワーク接続の問題');
        console.error('  4. SSL設定の問題');
    } finally {
        await client.end();
    }
}

// 実行
testDatabaseConnection();