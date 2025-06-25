#!/usr/bin/env python3
"""
包括的メトリクス品質診断スクリプト（修正版）
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
        all_days = await conn.fetch("""
            SELECT date, member_count, daily_messages, daily_user_messages, daily_staff_messages
            FROM discord_metrics
            ORDER BY date DESC
        """)
        
        zero_message_days = [row for row in all_days if row['daily_messages'] == 0]
        total_days = len(all_days)
        zero_ratio = len(zero_message_days) / total_days * 100 if total_days > 0 else 0
        
        print(f"📈 総日数: {total_days}日")
        print(f"📈 ゼロメッセージ日: {len(zero_message_days)}日 ({zero_ratio:.1f}%)")
        
        # 最近10日間の詳細
        print("\n📊 最近10日間の詳細:")
        for row in all_days[:10]:
            print(f"   📅 {row['date']}: 総{row['daily_messages']}件 "
                  f"(👤{row['daily_user_messages']} + 👮{row['daily_staff_messages']}), "
                  f"メンバー{row['member_count']}人")
        
        if zero_ratio > 50:
            self.add_issue(
                "データ品質", "CRITICAL",
                f"メッセージが0件の日が{zero_ratio:.1f}%と異常に多い",
                "メッセージカウント機能が正常に動作していない可能性"
            )
            
            self.add_recommendation(
                "メッセージカウント", "URGENT",
                "on_message イベントハンドラーの完全な見直し",
                """
1. ロール権限チェックのシンプル化
2. チャンネル権限チェックの最適化
3. エラーハンドリングの強化
4. デバッグログの充実
"""
            )
        
        # 2. チャンネル統計の品質
        print("\n📍 チャンネル統計品質:")
        channel_stats_quality = await conn.fetch("""
            SELECT date, channel_message_stats
            FROM discord_metrics
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY date DESC
        """)
        
        for row in channel_stats_quality:
            try:
                stats = json.loads(row['channel_message_stats'])
                channel_count = len(stats)
                total_messages = sum(ch.get('user_messages', 0) for ch in stats.values())
                
                print(f"   📅 {row['date']}: {channel_count}チャンネル, {total_messages}メッセージ")
                
                # チャンネル詳細（最大3つ）
                for i, (ch_id, ch_stats) in enumerate(list(stats.items())[:3]):
                    msg_count = ch_stats.get('user_messages', 0)
                    user_count = ch_stats.get('user_count', 0)
                    if msg_count > 0:
                        print(f"      - チャンネル{ch_id}: {msg_count}件 ({user_count}人)")
                
                if channel_count == 0:
                    self.add_issue(
                        "チャンネル統計", "HIGH",
                        f"{row['date']}: チャンネル統計が空",
                        "チャンネル別メッセージカウントが記録されていない"
                    )
                elif channel_count == 1:
                    self.add_issue(
                        "チャンネル統計", "MEDIUM",
                        f"{row['date']}: 1チャンネルのみ記録",
                        "複数チャンネルを監視できていない可能性"
                    )
                    
            except Exception as e:
                print(f"      ❌ JSONパースエラー: {e}")
        
        # 3. ロール統計の品質
        print("\n👥 ロール統計品質:")
        role_stats_quality = await conn.fetch("""
            SELECT date, role_counts
            FROM discord_metrics
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY date DESC
        """)
        
        expected_roles = 7  # 設定されているロール数
        
        for row in role_stats_quality:
            try:
                role_data = json.loads(row['role_counts'])
                print(f"   📅 {row['date']}: {len(role_data)}ロール")
                
                # ロール統計の詳細チェック
                empty_roles = 0
                for role_id, data in role_data.items():
                    count = data.get('count', 0)
                    name = data.get('name', 'Unknown')
                    if count == 0:
                        empty_roles += 1
                        print(f"      ⚠️ {name}: 0人")
                    else:
                        print(f"      ✅ {name}: {count}人")
                
                if len(role_data) < expected_roles:
                    self.add_issue(
                        "ロール統計", "MEDIUM",
                        f"{row['date']}: {expected_roles}ロール中{len(role_data)}ロールのみ取得",
                        "一部のロールIDが見つからない可能性"
                    )
                    
                if empty_roles > len(role_data) * 0.3:
                    self.add_issue(
                        "ロール統計", "LOW",
                        f"{row['date']}: {empty_roles}/{len(role_data)}ロールが0人",
                        "ロールメンバー取得に問題がある可能性"
                    )
                    
            except Exception as e:
                print(f"      ❌ JSONパースエラー: {e}")
    
    async def analyze_collection_patterns(self, conn):
        """収集パターン分析"""
        print("\n⏰ 収集パターン分析")
        
        # 実行時刻パターン
        execution_times = await conn.fetch("""
            SELECT date, 
                   EXTRACT(HOUR FROM created_at) as hour,
                   EXTRACT(MINUTE FROM created_at) as minute,
                   created_at,
                   updated_at
            FROM discord_metrics
            ORDER BY date DESC
            LIMIT 14
        """)
        
        print("🕐 実行時刻パターン (created_at):")
        time_consistency = True
        expected_hour = 15  # UTC 15:00 = JST 0:00
        
        for row in execution_times:
            hour = int(row['hour'])
            minute = int(row['minute'])
            jst_hour = (hour + 9) % 24  # UTCからJSTへ変換
            
            print(f"   📅 {row['date']}: UTC {hour:02d}:{minute:02d} (JST {jst_hour:02d}:{minute:02d})")
            
            # updated_atとの差分も確認
            if row['created_at'] != row['updated_at']:
                print(f"      ⚠️ 更新あり: {row['updated_at']}")
            
            # 実行時刻が期待値から大きくずれている場合
            if abs(hour - expected_hour) > 2:
                time_consistency = False
        
        if not time_consistency:
            self.add_issue(
                "実行スケジュール", "HIGH",
                "メトリクス収集の実行時刻が不安定",
                "日本時間0:00(UTC15:00)に実行されるべきが異なる時刻で実行されている"
            )
            
            self.add_recommendation(
                "実行スケジュール", "HIGH",
                "タイムゾーン設定を確認し、スケジュール設定を修正",
                """
1. metrics_collector.py:528の時刻設定を確認
2. タイムゾーンをUTCで明示的に指定
3. ログにJST時刻も記録
"""
            )
    
    async def analyze_message_counting_logic(self, conn):
        """メッセージカウントロジック分析"""
        print("\n💬 メッセージカウントロジック分析")
        
        # 最近のメッセージパターン
        recent_patterns = await conn.fetch("""
            SELECT date, daily_messages, daily_user_messages, daily_staff_messages,
                   member_count, engagement_score, active_users
            FROM discord_metrics
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY date DESC
        """)
        
        print("📊 最近30日間のメッセージパターン分析:")
        
        # 統計情報
        zero_days = sum(1 for row in recent_patterns if row['daily_messages'] == 0)
        low_days = sum(1 for row in recent_patterns if 0 < row['daily_messages'] < 10)
        normal_days = sum(1 for row in recent_patterns if row['daily_messages'] >= 10)
        
        print(f"   📊 統計サマリー:")
        print(f"      - 0メッセージ日: {zero_days}日 ({zero_days/len(recent_patterns)*100:.1f}%)")
        print(f"      - 低活動日(1-9件): {low_days}日 ({low_days/len(recent_patterns)*100:.1f}%)")
        print(f"      - 通常活動日(10件以上): {normal_days}日 ({normal_days/len(recent_patterns)*100:.1f}%)")
        
        # メッセージ密度の分析
        print("\n   📈 メッセージ密度分析:")
        densities = []
        for row in recent_patterns[:7]:  # 最近7日
            total_msg = row['daily_messages']
            members = row['member_count']
            active = row['active_users']
            density = total_msg / members if members > 0 else 0
            active_ratio = active / members * 100 if members > 0 else 0
            
            densities.append(density)
            
            print(f"      📅 {row['date']}: 密度{density:.3f} "
                  f"(メッセージ{total_msg}/メンバー{members}), "
                  f"アクティブ率{active_ratio:.1f}%")
        
        avg_density = sum(densities) / len(densities) if densities else 0
        
        if avg_density < 0.05:  # 平均密度が0.05未満
            self.add_issue(
                "メッセージ密度", "CRITICAL",
                f"平均メッセージ密度が{avg_density:.3f}と極めて低い",
                "メッセージカウント機能が正常に動作していない"
            )
            
            self.add_recommendation(
                "メッセージカウント修正", "URGENT",
                "メッセージカウント機能の根本的な修正が必要",
                """
1. on_message イベントの動作確認
2. 権限チェックロジックのシンプル化
3. メモリカウンターの管理改善
4. リセットタイミングの修正
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
        
        # 最終サマリー
        print("\n" + "="*50)
        print("📌 対応優先度サマリー")
        print("="*50)
        print("""
1. 【最優先】メッセージカウント機能の修正
   - 現状: ほとんどの日でメッセージが0件
   - 影響: エンゲージメント分析が無意味になっている
   
2. 【高優先】実行スケジュールの安定化
   - 現状: 実行時刻が不安定
   - 影響: データの日付整合性に問題
   
3. 【中優先】チャンネル統計の改善
   - 現状: 1チャンネルしか記録されていない
   - 影響: チャンネル別分析ができない
""")

async def main():
    analyzer = MetricsQualityAnalyzer()
    await analyzer.generate_comprehensive_report()

if __name__ == "__main__":
    asyncio.run(main())