#!/usr/bin/env python3
"""
包括的メトリクス品質診断スクリプト
全データ収集機能の品質問題を特定・分析
"""

import asyncio
import asyncpg
import os
import json
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from collections import defaultdict

# 環境変数読み込み
load_dotenv()

class MetricsQualityAnalyzer:
    def __init__(self):
        self.db_url = os.getenv('NEON_DATABASE_URL')
        self.issues = []
        self.recommendations = []
    
    def add_issue(self, category, severity, description, technical_details=None):
        """問題を記録"""
        self.issues.append({
            'category': category,
            'severity': severity,  # CRITICAL, HIGH, MEDIUM, LOW
            'description': description,
            'technical_details': technical_details or ""
        })
    
    def add_recommendation(self, category, priority, solution, implementation=None):
        """修正提案を記録"""
        self.recommendations.append({
            'category': category,
            'priority': priority,  # URGENT, HIGH, MEDIUM, LOW
            'solution': solution,
            'implementation': implementation or ""
        })
    
    async def analyze_data_integrity(self, conn):
        """データ整合性分析"""
        print("\n🔍 データ整合性分析")
        
        # 1. 日付とタイムスタンプの整合性
        inconsistent_dates = await conn.fetch("""
            SELECT date, created_at, updated_at,
                   EXTRACT(DAY FROM (created_at - (date + INTERVAL '1 day'))) as day_diff
            FROM discord_metrics
            WHERE ABS(EXTRACT(DAY FROM (created_at - (date + INTERVAL '1 day')))) > 1
            ORDER BY date DESC
        """)
        
        if inconsistent_dates:
            print(f"❌ 日付整合性問題: {len(inconsistent_dates)}件")
            for row in inconsistent_dates:
                print(f"   📅 {row['date']}: 作成日時{row['created_at']} (差分: {row['day_diff']:.1f}日)")
            
            self.add_issue(
                "データ整合性", "HIGH",
                f"日付とタイムスタンプが整合しないデータが{len(inconsistent_dates)}件存在",
                "実行時刻と記録日付にずれがある可能性"
            )
        else:
            print("✅ 日付整合性: 正常")
        
        # 2. メッセージ数の論理チェック
        invalid_messages = await conn.fetch("""
            SELECT date, daily_messages, daily_user_messages, daily_staff_messages,
                   (daily_user_messages + daily_staff_messages) as calculated_total
            FROM discord_metrics
            WHERE daily_messages != (daily_user_messages + daily_staff_messages)
            ORDER BY date DESC
        """)
        
        if invalid_messages:
            print(f"❌ メッセージ数計算エラー: {len(invalid_messages)}件")
            for row in invalid_messages:
                print(f"   📅 {row['date']}: 総計{row['daily_messages']} ≠ "
                      f"ユーザー{row['daily_user_messages']} + 運営{row['daily_staff_messages']} "
                      f"= {row['calculated_total']}")
            
            self.add_issue(
                "計算ロジック", "CRITICAL",
                f"メッセージ数の合計計算が間違っている({len(invalid_messages)}件)",
                "daily_messages = daily_user_messages + daily_staff_messages でない"
            )
        else:
            print("✅ メッセージ数計算: 正常")
    
    async def analyze_data_quality(self, conn):
        """データ品質分析"""
        print("\n📊 データ品質分析")
        
        # 1. ゼロメッセージ日の分析
        zero_message_days = await conn.fetch("""
            SELECT date, member_count, daily_messages
            FROM discord_metrics
            WHERE daily_messages = 0
            ORDER BY date DESC
            LIMIT 10
        """)
        
        total_days = await conn.fetchval("SELECT COUNT(*) FROM discord_metrics")
        zero_ratio = len(zero_message_days) / total_days * 100 if total_days > 0 else 0
        
        print(f"📈 ゼロメッセージ日: {len(zero_message_days)}日 ({zero_ratio:.1f}%)")
        if zero_ratio > 50:
            self.add_issue(
                "データ品質", "HIGH",
                f"メッセージが0件の日が{zero_ratio:.1f}%と異常に多い",
                "メッセージカウント機能が正常に動作していない可能性"
            )
        
        # 2. チャンネル統計の品質
        channel_stats_quality = await conn.fetch("""
            SELECT date, 
                   jsonb_array_length(jsonb_object_keys(channel_message_stats)) as channel_count,
                   channel_message_stats
            FROM discord_metrics
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY date DESC
        """)
        
        print("📍 チャンネル統計品質:")
        channel_counts = []
        for row in channel_stats_quality:
            stats = json.loads(row['channel_message_stats'])
            channel_count = len(stats)
            channel_counts.append(channel_count)
            
            total_messages = sum(ch['user_messages'] for ch in stats.values())
            print(f"   📅 {row['date']}: {channel_count}チャンネル, {total_messages}メッセージ")
            
            if channel_count == 0:
                self.add_issue(
                    "チャンネル統計", "MEDIUM",
                    f"{row['date']}: チャンネル統計が空",
                    "チャンネル別メッセージカウントが記録されていない"
                )
        
        # チャンネル数の変動が異常でないかチェック
        if len(channel_counts) > 1:
            avg_channels = sum(channel_counts) / len(channel_counts)
            if any(count < avg_channels * 0.5 for count in channel_counts):
                self.add_issue(
                    "チャンネル統計", "MEDIUM",
                    "チャンネル数が日によって大きく変動している",
                    "全チャンネルを正しく監視できていない可能性"
                )
        
        # 3. ロール統計の品質
        print("\n👥 ロール統計品質:")
        role_stats_quality = await conn.fetch("""
            SELECT date, role_counts
            FROM discord_metrics
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY date DESC
        """)
        
        for row in role_stats_quality:
            role_data = json.loads(row['role_counts'])
            print(f"   📅 {row['date']}: {len(role_data)}ロール")
            
            # ロール統計の詳細チェック
            total_members = 0
            empty_roles = 0
            for role_id, data in role_data.items():
                count = data['count']
                name = data['name']
                total_members += count
                if count == 0:
                    empty_roles += 1
                print(f"      - {name}: {count}人")
            
            if empty_roles > len(role_data) * 0.3:  # 30%以上が0人
                self.add_issue(
                    "ロール統計", "MEDIUM",
                    f"{row['date']}: ロールの{empty_roles}/{len(role_data)}が0人",
                    "ロール取得に問題がある可能性"
                )
    
    async def analyze_collection_patterns(self, conn):
        """収集パターン分析"""
        print("\n⏰ 収集パターン分析")
        
        # 実行時刻パターン
        execution_times = await conn.fetch("""
            SELECT date, 
                   EXTRACT(HOUR FROM created_at) as hour,
                   EXTRACT(MINUTE FROM created_at) as minute,
                   created_at
            FROM discord_metrics
            ORDER BY date DESC
            LIMIT 14
        """)
        
        print("🕐 実行時刻パターン:")
        time_consistency = True
        expected_hour = 0  # 日本時間0:00 = UTC 15:00
        
        for row in execution_times:
            hour = int(row['hour'])
            minute = int(row['minute'])
            print(f"   📅 {row['date']}: {hour:02d}:{minute:02d} UTC ({row['created_at']})")
            
            # 実行時刻が期待値から大きくずれている場合
            if abs(hour - 15) > 2:  # UTC 15:00 ± 2時間
                time_consistency = False
        
        if not time_consistency:
            self.add_issue(
                "実行スケジュール", "MEDIUM",
                "メトリクス収集の実行時刻が不安定",
                "日本時間0:00(UTC15:00)に実行されるべきが異なる時刻で実行されている"
            )
            
            self.add_recommendation(
                "実行スケジュール", "HIGH",
                "タイムゾーン設定を確認し、cronジョブの時刻を修正",
                "metrics_collector.py:528の時刻設定を確認"
            )
    
    async def analyze_message_counting_logic(self, conn):
        """メッセージカウントロジック分析"""
        print("\n💬 メッセージカウントロジック分析")
        
        # 最近のメッセージパターン
        recent_patterns = await conn.fetch("""
            SELECT date, daily_messages, daily_user_messages, daily_staff_messages,
                   member_count, engagement_score
            FROM discord_metrics
            WHERE date >= CURRENT_DATE - INTERVAL '14 days'
            ORDER BY date DESC
        """)
        
        print("📊 最近14日間のメッセージパターン:")
        low_activity_days = 0
        
        for row in recent_patterns:
            total_msg = row['daily_messages']
            user_msg = row['daily_user_messages']
            staff_msg = row['daily_staff_messages']
            members = row['member_count']
            engagement = row['engagement_score']
            
            # メッセージ密度計算
            msg_density = total_msg / members if members > 0 else 0
            
            print(f"   📅 {row['date']}: 総{total_msg}件 (👤{user_msg} + 👮{staff_msg}), "
                  f"密度{msg_density:.3f}, エンゲージ{engagement:.2f}")
            
            if total_msg == 0:
                low_activity_days += 1
        
        if low_activity_days > 7:  # 半数以上が0メッセージ
            self.add_issue(
                "メッセージカウント", "CRITICAL",
                f"14日中{low_activity_days}日でメッセージが0件",
                "on_message イベントハンドラーが正常に動作していない可能性"
            )
            
            self.add_recommendation(
                "メッセージカウント", "URGENT",
                "メッセージ監視機能の完全な見直しが必要",
                """
1. on_message イベントの動作確認
2. チャンネル権限の確認
3. ロール権限の確認
4. メモリ上カウンターのリセットタイミング修正
"""
            )
    
    async def generate_comprehensive_report(self):
        """包括的レポート生成"""
        print("\n" + "="*80)
        print("📋 包括的問題分析レポート")
        print("="*80)
        
        try:
            conn = await asyncpg.connect(self.db_url)
            
            await self.analyze_data_integrity(conn)
            await self.analyze_data_quality(conn)
            await self.analyze_collection_patterns(conn)
            await self.analyze_message_counting_logic(conn)
            
            await conn.close()
            
        except Exception as e:
            print(f"❌ 分析エラー: {e}")
            return
        
        # 問題サマリー
        print("\n" + "="*50)
        print("🚨 発見された問題")
        print("="*50)
        
        if not self.issues:
            print("✅ 重大な問題は発見されませんでした")
        else:
            severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
            for severity in severity_order:
                severity_issues = [i for i in self.issues if i['severity'] == severity]
                if severity_issues:
                    severity_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🔵'}
                    print(f"\n{severity_emoji[severity]} {severity}レベル ({len(severity_issues)}件)")
                    for i, issue in enumerate(severity_issues, 1):
                        print(f"   {i}. [{issue['category']}] {issue['description']}")
                        if issue['technical_details']:
                            print(f"      💡 {issue['technical_details']}")
        
        # 修正提案
        print("\n" + "="*50)
        print("🔧 修正提案")
        print("="*50)
        
        if not self.recommendations:
            print("📝 特に修正提案はありません")
        else:
            priority_order = ['URGENT', 'HIGH', 'MEDIUM', 'LOW']
            for priority in priority_order:
                priority_recs = [r for r in self.recommendations if r['priority'] == priority]
                if priority_recs:
                    priority_emoji = {'URGENT': '🚨', 'HIGH': '⚡', 'MEDIUM': '📝', 'LOW': '💡'}
                    print(f"\n{priority_emoji[priority]} {priority}優先度 ({len(priority_recs)}件)")
                    for i, rec in enumerate(priority_recs, 1):
                        print(f"   {i}. [{rec['category']}] {rec['solution']}")
                        if rec['implementation']:
                            print(f"      🛠️ 実装方法:")
                            for line in rec['implementation'].strip().split('\n'):
                                if line.strip():
                                    print(f"         {line.strip()}")

async def main():
    analyzer = MetricsQualityAnalyzer()
    await analyzer.generate_comprehensive_report()

if __name__ == "__main__":
    asyncio.run(main())