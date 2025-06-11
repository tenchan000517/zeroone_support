-- Migration script to add interval_hours column to channel_intro_settings
-- Run this manually if needed: sqlite3 bot_data.db < migration.sql

-- Add the new interval_hours column
ALTER TABLE channel_intro_settings ADD COLUMN interval_hours INTEGER DEFAULT 168;

-- Migrate existing data from interval_days to interval_hours (if interval_days exists)
UPDATE channel_intro_settings 
SET interval_hours = COALESCE(interval_days * 24, 168)
WHERE interval_hours IS NULL OR interval_hours = 168;

-- Show final table structure
.schema channel_intro_settings

-- Show migrated data
SELECT guild_id, enabled, channel_id, interval_hours FROM channel_intro_settings;