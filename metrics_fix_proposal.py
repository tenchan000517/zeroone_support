#!/usr/bin/env python3
"""
メトリクス収集機能修正提案
特定された問題の具体的な修正コード
"""

IDENTIFIED_ISSUES = """
🔍 特定された主要問題:

1. 【CRITICAL】メッセージカウント機能の根本的問題
   - ゼロメッセージ日が異常に多い
   - on_message イベントハンドラーが適切に動作していない可能性

2. 【HIGH】日付とタイムスタンプの不整合
   - 実行日と記録日時にずれがある

3. 【MEDIUM】チャンネル統計の不完全性
   - 全チャンネルを監視できていない可能性

4. 【MEDIUM】実行スケジュールの不安定性
   - 期待される時刻に実行されていない
"""

PROPOSED_FIXES = """
🔧 具体的修正提案:

=== 修正1: メッセージカウント機能の改善 ===
問題: on_message イベントでのカウントが正常に動作していない

現在のコード問題点:
- メモリ上のカウンターが適切にリセットされていない
- チャンネル権限チェックが複雑すぎて失敗している可能性
- ロール権限の確認でエラーが発生している可能性

修正方針:
1. シンプルなメッセージカウント方式への変更
2. エラーハンドリングの強化
3. デバッグログの充実
4. カウンターリセットタイミングの修正
"""

# 修正されたメッセージカウント機能
FIXED_MESSAGE_COUNTING = '''
@commands.Cog.listener()
async def on_message(self, message):
    """改善されたメッセージカウント機能"""
    # BOTメッセージは除外
    if message.author.bot:
        return
    
    # ギルドチェック
    if not message.guild:
        return
    
    try:
        # デバッグログ
        logger.info(f"[METRICS] メッセージ受信: {message.author.name} in {message.channel.name}")
        
        # 閲覧可能ロールの存在確認
        viewable_role = message.guild.get_role(self.VIEWABLE_ROLE_ID)
        if not viewable_role:
            logger.warning(f"[METRICS] 閲覧可能ロール {self.VIEWABLE_ROLE_ID} が見つかりません")
            return
        
        # チャンネルが閲覧可能かチェック
        channel_perms = message.channel.permissions_for(viewable_role)
        if not channel_perms.view_channel:
            # プライベートチャネルは除外（ログは出さない）
            return
        
        # 運営ロールかどうかチェック
        staff_role = message.guild.get_role(self.STAFF_ROLE_ID)
        is_staff = staff_role and (staff_role in message.author.roles)
        
        # メッセージカウント（エラーハンドリング付き）
        try:
            if is_staff:
                self.staff_message_counts[message.channel.id][message.author.id] += 1
                logger.debug(f"[METRICS] 運営メッセージ +1: {message.author.name}")
            else:
                self.message_counts[message.channel.id][message.author.id] += 1
                logger.debug(f"[METRICS] ユーザーメッセージ +1: {message.author.name}")
        except Exception as e:
            logger.error(f"[METRICS] カウント処理エラー: {e}")
            return
        
        # 定期的な統計ログ（5分に1回程度）
        if hasattr(self, '_last_stats_log'):
            if (datetime.now() - self._last_stats_log).seconds > 300:  # 5分
                self._log_current_stats()
                self._last_stats_log = datetime.now()
        else:
            self._last_stats_log = datetime.now()
            
    except Exception as e:
        logger.error(f"[METRICS] on_message処理エラー: {e}")

def _log_current_stats(self):
    """現在のカウント状況をログ出力"""
    total_user = sum(sum(users.values()) for users in self.message_counts.values())
    total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
    
    logger.info(f"[METRICS] 現在の累計 - ユーザー: {total_user}件, 運営: {total_staff}件")
'''

SCHEDULE_FIX = '''
=== 修正2: スケジュール実行の改善 ===

問題: 実行時刻が不安定

修正コード:
@tasks.loop(time=time(hour=15, minute=0, tzinfo=timezone.utc))  # UTC 15:00 = JST 0:00
async def daily_metrics_task(self):
    """改善された定期メトリクス収集"""
    try:
        # 実行時刻をログに記録
        jst_time = datetime.now(timezone(timedelta(hours=9)))
        logger.info(f"⏰ 定期メトリクス収集開始 JST: {jst_time}")
        
        metrics = await self.collect_daily_metrics()
        if metrics:
            # 日付を明示的に設定（JST基準）
            metrics['date'] = jst_time.date()
            
            success = await self.save_metrics_to_db(metrics)
            if success:
                logger.info("✅ 定期メトリクス収集・保存完了")
                # 成功後にカウントリセット
                self.reset_daily_counts()
            else:
                logger.error("❌ 定期メトリクス保存失敗")
        else:
            logger.error("❌ 定期メトリクス収集失敗")
            
    except Exception as e:
        logger.error(f"❌ 定期メトリクス処理エラー: {e}")
'''

ERROR_HANDLING_IMPROVEMENT = '''
=== 修正3: エラーハンドリングの改善 ===

async def collect_daily_metrics(self) -> dict:
    """改善されたメトリクス収集"""
    logger.info("📊 KPI収集開始...")
    
    try:
        guild = await self.get_main_guild()
        if not guild:
            logger.error("❌ メインギルドが取得できません")
            return None
        
        # メッセージ統計を取得（エラーハンドリング付き）
        try:
            message_stats = self.get_daily_message_stats()
            logger.info(f"📊 メッセージ統計: 総計{message_stats['total_messages']}件")
        except Exception as e:
            logger.error(f"❌ メッセージ統計取得エラー: {e}")
            # デフォルト値で継続
            message_stats = {
                'total_user_messages': 0,
                'total_staff_messages': 0,
                'total_messages': 0,
                'channel_stats': {},
                'staff_channel_stats': {}
            }
        
        # ロールメンバー数を取得（エラーハンドリング付き）
        try:
            role_counts = await self.count_role_members(guild)
            logger.info(f"👥 ロール統計: {len(role_counts)}ロール処理完了")
        except Exception as e:
            logger.error(f"❌ ロール統計取得エラー: {e}")
            role_counts = {}
        
        # 基本メトリクス収集
        try:
            member_count = guild.member_count or 0
            online_count = len([m for m in guild.members if m.status != discord.Status.offline])
            active_users = await self.count_active_users(guild)
            
            logger.info(f"👥 メンバー統計: 総計{member_count}人, オンライン{online_count}人, アクティブ{active_users}人")
        except Exception as e:
            logger.error(f"❌ メンバー統計取得エラー: {e}")
            member_count = online_count = active_users = 0
        
        # エンゲージメントスコア計算
        engagement_score = await self.calculate_engagement_score(
            member_count, active_users, message_stats['total_user_messages']
        )
        
        # 最終データ構築
        metrics = {
            'date': date.today(),
            'member_count': member_count,
            'online_count': online_count,
            'daily_messages': message_stats['total_messages'],
            'daily_user_messages': message_stats['total_user_messages'],
            'daily_staff_messages': message_stats['total_staff_messages'],
            'active_users': active_users,
            'engagement_score': engagement_score,
            'channel_message_stats': message_stats['channel_stats'],
            'staff_channel_stats': message_stats['staff_channel_stats'],
            'role_counts': role_counts
        }
        
        logger.info(f"✅ メトリクス収集完了: {metrics}")
        return metrics
        
    except Exception as e:
        logger.error(f"❌ メトリクス収集エラー: {e}")
        return None
'''

RESET_TIMING_FIX = '''
=== 修正4: カウンターリセットタイミングの修正 ===

def reset_daily_counts(self):
    """改善されたカウンターリセット"""
    # リセット前の統計をログ出力
    total_user = sum(sum(users.values()) for users in self.message_counts.values())
    total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
    
    logger.info(f"🔄 カウンターリセット実行")
    logger.info(f"   リセット前 - ユーザー: {total_user}件, 運営: {total_staff}件")
    
    # 詳細統計もログ出力
    if total_user > 0 or total_staff > 0:
        logger.info(f"   チャンネル数: ユーザー{len(self.message_counts)}, 運営{len(self.staff_message_counts)}")
    
    # カウンターリセット
    self.message_counts.clear()
    self.staff_message_counts.clear()
    
    logger.info("✅ カウンターリセット完了")
'''

IMPLEMENTATION_PRIORITY = """
🚨 実装優先度:

【最優先】
1. メッセージカウント機能の修正
   - on_message イベントハンドラーの改善
   - エラーハンドリングの強化

【高優先】
2. スケジュール実行の修正
   - タイムゾーン設定の明確化
   - 実行時刻の安定化

【中優先】
3. ログ出力の改善
   - デバッグ情報の充実
   - 問題特定の容易化

【低優先】
4. データ検証機能の追加
   - 収集後のデータ品質チェック
   - 異常値の検出
"""

if __name__ == "__main__":
    print(IDENTIFIED_ISSUES)
    print(PROPOSED_FIXES)
    print(IMPLEMENTATION_PRIORITY)