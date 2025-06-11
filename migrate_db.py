#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database migration script for channel intro settings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import migrate_interval_column, engine

if __name__ == "__main__":
    print("Starting database migration...")
    
    try:
        # Check current schema
        with engine.connect() as conn:
            result = conn.execute("PRAGMA table_info(channel_intro_settings)")
            columns = [row[1] for row in result.fetchall()]
            print(f"Current columns: {columns}")
            
            # Check if there's any existing data
            if 'channel_intro_settings' in [table[0] for table in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                result = conn.execute("SELECT COUNT(*) FROM channel_intro_settings")
                count = result.fetchone()[0]
                print(f"Existing records: {count}")
                
                if count > 0:
                    result = conn.execute("SELECT guild_id, enabled, channel_id, interval_days FROM channel_intro_settings")
                    print("Current data:")
                    for row in result.fetchall():
                        print(f"  Guild: {row[0]}, Enabled: {row[1]}, Channel: {row[2]}, Days: {row[3]}")
        
        # Run migration
        migrate_interval_column()
        
        # Verify migration
        with engine.connect() as conn:
            result = conn.execute("PRAGMA table_info(channel_intro_settings)")
            columns = [row[1] for row in result.fetchall()]
            print(f"Updated columns: {columns}")
            
            if 'interval_hours' in columns:
                result = conn.execute("SELECT guild_id, enabled, channel_id, interval_hours FROM channel_intro_settings")
                print("Migrated data:")
                for row in result.fetchall():
                    print(f"  Guild: {row[0]}, Enabled: {row[1]}, Channel: {row[2]}, Hours: {row[3]}")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()