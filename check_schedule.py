#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import sqlite3

def check_schedule():
    conn = sqlite3.connect('weekly_content.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM weekly_content_settings')
    rows = cursor.fetchall()

    print('現在の週間スケジュール設定:')
    print('=' * 60)

    default_schedule = ['quotes', 'connpass', 'trends', 'tech', 'challenge', 'events', 'mindset']
    weekday_names = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']

    for row in rows:
        print(f'Guild ID: {row[0]}')
        print()
        
        issues_found = False
        
        for i in range(7):
            content_idx = 5 + i * 4
            hour_idx = 6 + i * 4
            minute_idx = 7 + i * 4
            
            current_content = row[content_idx]
            current_hour = row[hour_idx]
            current_minute = row[minute_idx]
            expected_content = default_schedule[i]
            
            if current_content == expected_content:
                print(f'✓ {weekday_names[i]}: {current_content} ({current_hour:02d}:{current_minute:02d})')
            else:
                print(f'⚠️  {weekday_names[i]}: {current_content} ({current_hour:02d}:{current_minute:02d})')
                print(f'   期待値: {expected_content}')
                issues_found = True
        
        if not issues_found:
            print('\n✅ すべての設定が期待値と一致しています')
        else:
            print('\n❌ 期待値と異なる設定が見つかりました')
        
        print('=' * 60)

    conn.close()

if __name__ == "__main__":
    check_schedule()