-- 新しいカラムを追加するSQL（SQLiteコマンドラインで実行）
-- 使用方法: sqlite3 bot_data.db < quick_fix.sql

-- interval_hours カラムの追加
ALTER TABLE channel_intro_settings ADD COLUMN interval_hours INTEGER DEFAULT 168;

-- scheduled_hour カラムの追加  
ALTER TABLE channel_intro_settings ADD COLUMN scheduled_hour INTEGER;

-- scheduled_minute カラムの追加
ALTER TABLE channel_intro_settings ADD COLUMN scheduled_minute INTEGER;

-- 既存データの移行（interval_daysがある場合）
UPDATE channel_intro_settings 
SET interval_hours = COALESCE(interval_days * 24, 168)
WHERE interval_hours IS NULL OR interval_hours = 168;

-- 結果確認
.schema channel_intro_settings
SELECT * FROM channel_intro_settings;