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

-- インデックス作成（クエリパフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_hourly_gantt_date_hour ON hourly_gantt_data(date, hour);
CREATE INDEX IF NOT EXISTS idx_hourly_gantt_created_at ON hourly_gantt_data(created_at);

-- コメント追加
COMMENT ON TABLE hourly_gantt_data IS '時間別オンラインユーザーガントチャートデータ';
COMMENT ON COLUMN hourly_gantt_data.date IS '収集日付';
COMMENT ON COLUMN hourly_gantt_data.hour IS '時間（0-23）';
COMMENT ON COLUMN hourly_gantt_data.data IS 'ガントチャートJSON データ';
COMMENT ON COLUMN hourly_gantt_data.created_at IS '作成日時';
COMMENT ON COLUMN hourly_gantt_data.updated_at IS '更新日時';