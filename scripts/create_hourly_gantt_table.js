const { Client } = require('pg');
require('dotenv').config();

async function createHourlyGanttTable() {
    const client = new Client({
        connectionString: process.env.NEON_DATABASE_URL,
        ssl: { rejectUnauthorized: false }
    });

    try {
        console.log('🔌 データベースに接続中...');
        await client.connect();
        
        console.log('📊 hourly_gantt_data テーブルを作成中...');
        
        const createTableSQL = `
            -- 時間別ガントチャートデータ保存用テーブル
            CREATE TABLE IF NOT EXISTS hourly_gantt_data (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
                data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- 日付と時間の組み合わせでユニーク制約
                UNIQUE(date, hour)
            );
        `;
        
        await client.query(createTableSQL);
        console.log('✅ テーブル作成完了');
        
        console.log('🔍 インデックスを作成中...');
        
        const createIndexesSQL = `
            -- インデックス作成（クエリパフォーマンス向上）
            CREATE INDEX IF NOT EXISTS idx_hourly_gantt_date_hour ON hourly_gantt_data(date, hour);
            CREATE INDEX IF NOT EXISTS idx_hourly_gantt_created_at ON hourly_gantt_data(created_at);
        `;
        
        await client.query(createIndexesSQL);
        console.log('✅ インデックス作成完了');
        
        console.log('💬 コメント追加中...');
        
        const commentsSQL = `
            -- コメント追加
            COMMENT ON TABLE hourly_gantt_data IS '時間別オンラインユーザーガントチャートデータ';
            COMMENT ON COLUMN hourly_gantt_data.date IS '収集日付';
            COMMENT ON COLUMN hourly_gantt_data.hour IS '時間（0-23）';
            COMMENT ON COLUMN hourly_gantt_data.data IS 'ガントチャートJSON データ';
            COMMENT ON COLUMN hourly_gantt_data.created_at IS '作成日時';
            COMMENT ON COLUMN hourly_gantt_data.updated_at IS '更新日時';
        `;
        
        await client.query(commentsSQL);
        console.log('✅ コメント追加完了');
        
        // テーブル確認
        const checkResult = await client.query(`
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'hourly_gantt_data'
            ORDER BY ordinal_position;
        `);
        
        console.log('\n📋 作成されたテーブル構造:');
        checkResult.rows.forEach(row => {
            console.log(`  ${row.column_name}: ${row.data_type}`);
        });
        
        console.log('\n🎉 hourly_gantt_data テーブルの作成が完了しました！');
        
    } catch (error) {
        console.error('❌ エラー:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

// 実行
createHourlyGanttTable();