"""
メトリクス収集機能の修正版
特定された問題を解決する具体的な修正コード
"""

# =====================================
# 修正1: メッセージカウント機能の改善
# =====================================

# 問題: on_messageイベントが正常に動作していない
# 原因: 
# 1. 権限チェックが複雑すぎて多くのメッセージを除外
# 2. printデバッグは機能するがloggerが機能していない可能性
# 3. メモリカウンターのリセットタイミング

FIXED_ON_MESSAGE = '''
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
        # デバッグ用（printとlogger両方使用）
        channel_name = getattr(message.channel, 'name', 'Unknown')
        print(f"[METRICS] メッセージ受信: {message.author.name} in {channel_name}")
        logger.info(f"[METRICS] メッセージ受信: {message.author.name} in {channel_name}")
        
        # シンプルな権限チェック（問題の原因を特定するため一時的に簡略化）
        # 閲覧可能ロールのチェックを一時的にスキップ
        
        # 運営ロールかどうかチェック
        staff_role = message.guild.get_role(self.STAFF_ROLE_ID)
        is_staff = staff_role and (staff_role in message.author.roles)
        
        # メッセージカウント
        channel_id = str(message.channel.id)  # 文字列に変換（JSONシリアライズのため）
        user_id = str(message.author.id)
        
        if is_staff:
            if channel_id not in self.staff_message_counts:
                self.staff_message_counts[channel_id] = {}
            if user_id not in self.staff_message_counts[channel_id]:
                self.staff_message_counts[channel_id][user_id] = 0
            self.staff_message_counts[channel_id][user_id] += 1
            print(f"[METRICS] 運営メッセージカウント +1: {message.author.name} (累計: {self.staff_message_counts[channel_id][user_id]})")
        else:
            if channel_id not in self.message_counts:
                self.message_counts[channel_id] = {}
            if user_id not in self.message_counts[channel_id]:
                self.message_counts[channel_id][user_id] = 0
            self.message_counts[channel_id][user_id] += 1
            print(f"[METRICS] ユーザーメッセージカウント +1: {message.author.name} (累計: {self.message_counts[channel_id][user_id]})")
        
        # 定期的な統計ログ（10メッセージごと）
        total_messages = sum(sum(users.values()) for users in self.message_counts.values())
        total_messages += sum(sum(users.values()) for users in self.staff_message_counts.values())
        
        if total_messages % 10 == 0:
            total_user = sum(sum(users.values()) for users in self.message_counts.values())
            total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
            print(f"[METRICS] 📊 現在の累計 - ユーザー: {total_user}件, 運営: {total_staff}件")
            logger.info(f"[METRICS] 現在の累計 - ユーザー: {total_user}件, 運営: {total_staff}件")
            
    except Exception as e:
        print(f"[METRICS] ❌ on_message処理エラー: {type(e).__name__}: {e}")
        logger.error(f"[METRICS] on_message処理エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
'''

# =====================================
# 修正2: デイリーメッセージ統計の改善
# =====================================

FIXED_GET_DAILY_MESSAGE_STATS = '''
def get_daily_message_stats(self) -> Dict[str, any]:
    """改善された日次メッセージ統計取得"""
    print("[METRICS] 日次メッセージ統計を集計中...")
    
    # ユーザーメッセージ集計
    total_user_messages = 0
    user_channel_stats = {}
    
    for channel_id, users in self.message_counts.items():
        user_count = len(users)
        message_count = sum(users.values())
        total_user_messages += message_count
        
        if message_count > 0:
            user_channel_stats[str(channel_id)] = {
                'user_messages': message_count,
                'user_count': user_count
            }
            print(f"[METRICS] チャンネル{channel_id}: {message_count}件 ({user_count}人)")
    
    # 運営メッセージ集計
    total_staff_messages = 0
    staff_channel_stats = {}
    
    for channel_id, users in self.staff_message_counts.items():
        staff_count = len(users)
        message_count = sum(users.values())
        total_staff_messages += message_count
        
        if message_count > 0:
            staff_channel_stats[str(channel_id)] = {
                'staff_messages': message_count,
                'staff_count': staff_count
            }
            print(f"[METRICS] 運営チャンネル{channel_id}: {message_count}件 ({staff_count}人)")
    
    # 全チャンネル統計をマージ
    all_channel_stats = {}
    all_channel_ids = set(user_channel_stats.keys()) | set(staff_channel_stats.keys())
    
    for channel_id in all_channel_ids:
        all_channel_stats[channel_id] = {
            'user_messages': user_channel_stats.get(channel_id, {}).get('user_messages', 0),
            'user_count': user_channel_stats.get(channel_id, {}).get('user_count', 0),
            'staff_messages': staff_channel_stats.get(channel_id, {}).get('staff_messages', 0),
            'staff_count': staff_channel_stats.get(channel_id, {}).get('staff_count', 0)
        }
    
    result = {
        'total_user_messages': total_user_messages,
        'total_staff_messages': total_staff_messages,
        'total_messages': total_user_messages + total_staff_messages,
        'channel_stats': user_channel_stats,  # ユーザーメッセージのチャンネル統計
        'staff_channel_stats': staff_channel_stats,  # 運営メッセージのチャンネル統計
        'all_channel_stats': all_channel_stats  # 統合統計（追加）
    }
    
    print(f"[METRICS] 統計集計完了: 総計{result['total_messages']}件 "
          f"(ユーザー{total_user_messages} + 運営{total_staff_messages})")
    
    return result
'''

# =====================================
# 修正3: アクティブユーザー数の修正
# =====================================

FIXED_COUNT_ACTIVE_USERS = '''
async def count_active_users(self, guild: discord.Guild) -> int:
    """改善されたアクティブユーザー数カウント"""
    try:
        # アクティブユーザー = 今日メッセージを送信したユーザー
        active_user_ids = set()
        
        # ユーザーメッセージから
        for channel_users in self.message_counts.values():
            active_user_ids.update(channel_users.keys())
        
        # 運営は除外（運営ロールを持つユーザーを除外）
        staff_role = guild.get_role(self.STAFF_ROLE_ID)
        if staff_role:
            active_non_staff_users = 0
            for user_id_str in active_user_ids:
                try:
                    user_id = int(user_id_str)
                    member = guild.get_member(user_id)
                    if member and staff_role not in member.roles:
                        active_non_staff_users += 1
                except:
                    pass
            
            print(f"[METRICS] アクティブユーザー数: {active_non_staff_users}人 (運営除く)")
            logger.info(f"[METRICS] アクティブユーザー数: {active_non_staff_users}人")
            return active_non_staff_users
        else:
            # 運営ロールが見つからない場合は全アクティブユーザー数を返す
            active_count = len(active_user_ids)
            print(f"[METRICS] アクティブユーザー数: {active_count}人")
            logger.info(f"[METRICS] アクティブユーザー数: {active_count}人")
            return active_count
            
    except Exception as e:
        print(f"[METRICS] ❌ アクティブユーザー数取得エラー: {e}")
        logger.error(f"[METRICS] アクティブユーザー数取得エラー: {e}")
        return 0
'''

# =====================================
# 修正4: スケジュール実行の改善
# =====================================

FIXED_DAILY_METRICS_TASK = '''
@tasks.loop(time=time(hour=15, minute=0, tzinfo=timezone.utc))  # UTC 15:00 = JST 0:00
async def daily_metrics_task(self):
    """改善された定期メトリクス収集"""
    try:
        # 実行時刻をログに記録（JST）
        utc_now = datetime.now(timezone.utc)
        jst_now = utc_now.astimezone(timezone(timedelta(hours=9)))
        
        print(f"⏰ [METRICS] 定期実行開始 - UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}, JST: {jst_now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏰ 定期メトリクス収集開始 - JST: {jst_now}")
        
        # 現在のカウント状況を表示
        total_user = sum(sum(users.values()) for users in self.message_counts.values())
        total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
        print(f"[METRICS] 収集前のカウント - ユーザー: {total_user}件, 運営: {total_staff}件")
        
        metrics = await self.collect_daily_metrics()
        if metrics:
            # 日付を明示的に設定（JST基準の前日）
            # 0:00に実行されるので、前日のデータとして保存
            metrics['date'] = (jst_now - timedelta(days=1)).date()
            print(f"[METRICS] 保存日付: {metrics['date']}")
            
            success = await self.save_metrics_to_db(metrics)
            if success:
                print(f"✅ [METRICS] 定期メトリクス収集・保存完了")
                logger.info("✅ 定期メトリクス収集・保存完了")
                # 成功後にカウントリセット
                self.reset_daily_counts()
            else:
                print(f"❌ [METRICS] 定期メトリクス保存失敗")
                logger.error("❌ 定期メトリクス保存失敗")
        else:
            print(f"❌ [METRICS] 定期メトリクス収集失敗")
            logger.error("❌ 定期メトリクス収集失敗")
            
    except Exception as e:
        print(f"❌ [METRICS] 定期メトリクス処理エラー: {type(e).__name__}: {e}")
        logger.error(f"❌ 定期メトリクス処理エラー: {e}")
        import traceback
        traceback.print_exc()
'''

# =====================================
# 修正5: デバッグコマンドの追加
# =====================================

DEBUG_COMMANDS = '''
@discord.app_commands.command(name="metrics_debug", description="メトリクス収集のデバッグ情報を表示")
@discord.app_commands.default_permissions(administrator=True)
async def debug_metrics(self, interaction: discord.Interaction):
    """メトリクス収集のデバッグ情報"""
    await interaction.response.defer()
    
    # 現在のカウント状況
    total_user = sum(sum(users.values()) for users in self.message_counts.values())
    total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
    
    # チャンネル別詳細
    channel_details = []
    for channel_id, users in self.message_counts.items():
        count = sum(users.values())
        if count > 0:
            channel = interaction.guild.get_channel(int(channel_id))
            channel_name = channel.name if channel else f"ID:{channel_id}"
            channel_details.append(f"{channel_name}: {count}件")
    
    embed = discord.Embed(
        title="🔍 メトリクスデバッグ情報",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="📊 現在のカウント",
        value=f"ユーザー: {total_user}件\\n運営: {total_staff}件\\n合計: {total_user + total_staff}件",
        inline=True
    )
    
    embed.add_field(
        name="📍 チャンネル数",
        value=f"ユーザー: {len(self.message_counts)}ch\\n運営: {len(self.staff_message_counts)}ch",
        inline=True
    )
    
    embed.add_field(
        name="🔧 設定",
        value=f"閲覧可能ロール: {self.VIEWABLE_ROLE_ID}\\n運営ロール: {self.STAFF_ROLE_ID}",
        inline=True
    )
    
    if channel_details:
        embed.add_field(
            name="📝 チャンネル別詳細",
            value="\\n".join(channel_details[:5]),  # 最大5件
            inline=False
        )
    
    # 最後のリセット時刻
    if hasattr(self, '_last_reset_time'):
        embed.add_field(
            name="🔄 最後のリセット",
            value=self._last_reset_time.strftime('%Y-%m-%d %H:%M:%S'),
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@discord.app_commands.command(name="metrics_test_count", description="テスト用メッセージカウント")
@discord.app_commands.default_permissions(administrator=True)
async def test_message_count(self, interaction: discord.Interaction):
    """テスト用にメッセージをカウント"""
    await interaction.response.defer()
    
    # テストメッセージを擬似的にカウント
    test_channel_id = str(interaction.channel_id)
    test_user_id = str(interaction.user.id)
    
    if test_channel_id not in self.message_counts:
        self.message_counts[test_channel_id] = {}
    if test_user_id not in self.message_counts[test_channel_id]:
        self.message_counts[test_channel_id][test_user_id] = 0
    
    self.message_counts[test_channel_id][test_user_id] += 1
    
    count = self.message_counts[test_channel_id][test_user_id]
    total = sum(sum(users.values()) for users in self.message_counts.values())
    
    await interaction.followup.send(
        f"✅ テストカウント追加\\n"
        f"このチャンネルでのあなたのカウント: {count}\\n"
        f"全体の総カウント: {total}"
    )
'''

# =====================================
# 実装手順
# =====================================

IMPLEMENTATION_STEPS = """
📋 実装手順:

1. **バックアップ作成**
   ```bash
   cp cogs/metrics_collector.py cogs/metrics_collector.py.backup
   ```

2. **段階的な修正適用**
   
   Phase 1: メッセージカウント機能の修正
   - on_message メソッドを置き換え
   - get_daily_message_stats メソッドを置き換え
   - count_active_users メソッドを置き換え
   
   Phase 2: スケジュール実行の修正
   - daily_metrics_task メソッドを置き換え
   
   Phase 3: デバッグ機能の追加
   - metrics_debug コマンドを追加
   - metrics_test_count コマンドを追加

3. **テスト手順**
   - Botを再起動
   - /metrics_test_count でカウントテスト
   - /metrics_debug でカウント状況確認
   - 実際にメッセージを送信してカウント確認
   - /metrics で手動収集テスト

4. **監視**
   - bot.log でエラー確認
   - printデバッグ出力の確認
"""

if __name__ == "__main__":
    print("🔧 メトリクス収集機能修正コード")
    print("=" * 50)
    print("\n以下のコードをcogs/metrics_collector.pyに適用してください。")
    print("\n各修正は段階的に適用し、動作確認を行ってください。")
    print(IMPLEMENTATION_STEPS)