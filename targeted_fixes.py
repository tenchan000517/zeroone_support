"""
ターゲットを絞った修正提案
実際の問題に対する具体的な修正
"""

# =====================================
# 修正1: アクティブユーザー数の修正（最優先）
# =====================================

PRIORITY_1_ACTIVE_USERS_FIX = '''
async def count_active_users(self, guild: discord.Guild) -> int:
    """修正版：アクティブユーザー数カウント"""
    try:
        # デバッグログ
        print(f"[METRICS] アクティブユーザー数カウント開始")
        
        # 今日メッセージを送信したユーザーIDを収集
        active_user_ids = set()
        
        # ユーザーメッセージから収集
        for channel_id, users in self.message_counts.items():
            for user_id in users.keys():
                active_user_ids.add(user_id)
                print(f"[METRICS] アクティブユーザー追加: {user_id}")
        
        # 運営メッセージからも収集（運営は除外するため別途カウント）
        staff_user_ids = set()
        for channel_id, users in self.staff_message_counts.items():
            for user_id in users.keys():
                staff_user_ids.add(user_id)
        
        print(f"[METRICS] 収集完了 - ユーザー: {len(active_user_ids)}人, 運営: {len(staff_user_ids)}人")
        
        # 運営ロールを持つユーザーを除外
        staff_role = guild.get_role(self.STAFF_ROLE_ID)
        active_non_staff_count = 0
        
        if staff_role:
            for user_id_str in active_user_ids:
                try:
                    user_id = int(user_id_str)
                    member = guild.get_member(user_id)
                    if member and staff_role not in member.roles:
                        active_non_staff_count += 1
                except Exception as e:
                    print(f"[METRICS] ユーザー{user_id_str}の確認エラー: {e}")
                    # エラーでもカウントは継続
                    active_non_staff_count += 1
        else:
            # 運営ロールが見つからない場合は全員をカウント
            active_non_staff_count = len(active_user_ids)
            print(f"[METRICS] 運営ロールが見つからないため全員をカウント")
        
        print(f"[METRICS] アクティブユーザー数（運営除く）: {active_non_staff_count}人")
        logger.info(f"👥 アクティブユーザー数（運営除く）: {active_non_staff_count}")
        
        return active_non_staff_count
        
    except Exception as e:
        print(f"[METRICS] ❌ アクティブユーザー数取得エラー: {type(e).__name__}: {e}")
        logger.error(f"❌ アクティブユーザー数取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return 0
'''

# =====================================
# 修正2: メッセージカウント初期化の修正
# =====================================

PRIORITY_2_INIT_FIX = '''
def __init__(self, bot):
    self.bot = bot
    # 環境変数から改行文字を削除
    db_url_raw = os.getenv('NEON_DATABASE_URL')
    self.db_url = db_url_raw.replace('\\n', '').replace(' ', '') if db_url_raw else None
    
    # ロールIDの定義（既存のまま）
    self.VIEWABLE_ROLE_ID = 1236344630132473946
    self.STAFF_ROLE_ID = 1236487195741913119
    self.TRACKED_ROLE_IDS = [
        1381201663045668906,
        1382167308180394145,
        1332242428459221046,
        1383347155548504175,
        1383347231188586628,
        1383347303347257486,
        1383347353141907476
    ]
    
    # ロール名のマッピング（既存のまま）
    self.ROLE_NAMES = {
        1332242428459221046: "FIND to DO",
        1381201663045668906: "イベント情報",
        1382167308180394145: "みんなの告知",
        1383347155548504175: "経営幹部",
        1383347231188586628: "学生",
        1383347303347257486: "フリーランス",
        1383347353141907476: "エンジョイ"
    }
    
    # メッセージカウント用の辞書を正しく初期化
    # defaultdictの使い方を修正
    self.message_counts = {}  # {channel_id: {user_id: count}}
    self.staff_message_counts = {}  # {channel_id: {user_id: count}}
    
    # 定期収集タスク開始
    if not self.daily_metrics_task.is_running():
        self.daily_metrics_task.start()
    
    logger.info("📊 MetricsCollector初期化完了")
    print("[METRICS] MetricsCollector初期化完了")
'''

# =====================================
# 修正3: on_messageの軽微な修正
# =====================================

PRIORITY_3_ON_MESSAGE_FIX = '''
@commands.Cog.listener()
async def on_message(self, message):
    """軽微な修正版：メッセージカウント"""
    # BOTメッセージは除外
    if message.author.bot:
        return
    
    # ギルドチェック
    if not message.guild:
        return
    
    try:
        # チャンネルIDとユーザーIDを文字列で管理（JSON互換性のため）
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        
        # 閲覧可能ロールの存在確認
        viewable_role = message.guild.get_role(self.VIEWABLE_ROLE_ID)
        if not viewable_role:
            # ロールが見つからない場合もカウントは続行
            pass
        else:
            # チャンネルが閲覧可能かチェック
            channel_perms = message.channel.permissions_for(viewable_role)
            if not channel_perms.view_channel:
                # プライベートチャンネルは除外
                return
        
        # 運営ロールかどうかチェック
        staff_role = message.guild.get_role(self.STAFF_ROLE_ID)
        is_staff = staff_role and (staff_role in message.author.roles)
        
        # メッセージカウント（辞書の初期化を含む）
        if is_staff:
            if channel_id not in self.staff_message_counts:
                self.staff_message_counts[channel_id] = {}
            if user_id not in self.staff_message_counts[channel_id]:
                self.staff_message_counts[channel_id][user_id] = 0
            self.staff_message_counts[channel_id][user_id] += 1
        else:
            if channel_id not in self.message_counts:
                self.message_counts[channel_id] = {}
            if user_id not in self.message_counts[channel_id]:
                self.message_counts[channel_id][user_id] = 0
            self.message_counts[channel_id][user_id] += 1
        
    except Exception as e:
        print(f"[METRICS] ❌ on_message処理エラー: {type(e).__name__}: {e}")
        logger.error(f"[METRICS] on_message処理エラー: {e}")
'''

# =====================================
# 修正4: デバッグコマンドの追加（問題特定用）
# =====================================

DEBUG_COMMAND = '''
@discord.app_commands.command(name="metrics_live", description="現在のライブカウント状況を表示")
@discord.app_commands.default_permissions(administrator=True)
async def show_live_metrics(self, interaction: discord.Interaction):
    """現在のメッセージカウント状況を詳細表示"""
    await interaction.response.defer()
    
    # 現在のカウント詳細
    embed = discord.Embed(
        title="📊 ライブメトリクス状況",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # ユーザーメッセージ詳細
    user_total = 0
    user_details = []
    for channel_id, users in self.message_counts.items():
        channel = interaction.guild.get_channel(int(channel_id))
        channel_name = channel.name if channel else f"Unknown({channel_id})"
        channel_total = sum(users.values())
        user_count = len(users)
        user_total += channel_total
        if channel_total > 0:
            user_details.append(f"{channel_name}: {channel_total}件 ({user_count}人)")
    
    # 運営メッセージ詳細
    staff_total = 0
    staff_details = []
    for channel_id, users in self.staff_message_counts.items():
        channel = interaction.guild.get_channel(int(channel_id))
        channel_name = channel.name if channel else f"Unknown({channel_id})"
        channel_total = sum(users.values())
        staff_count = len(users)
        staff_total += channel_total
        if channel_total > 0:
            staff_details.append(f"{channel_name}: {channel_total}件 ({staff_count}人)")
    
    # アクティブユーザー数を計算
    active_users = await self.count_active_users(interaction.guild)
    
    # 基本統計
    embed.add_field(
        name="📈 総計",
        value=f"ユーザー: {user_total}件\\n運営: {staff_total}件\\n合計: {user_total + staff_total}件",
        inline=True
    )
    
    embed.add_field(
        name="👥 アクティブ",
        value=f"ユーザー: {active_users}人\\nチャンネル: {len(self.message_counts) + len(self.staff_message_counts)}",
        inline=True
    )
    
    # チャンネル別詳細
    if user_details:
        embed.add_field(
            name="📍 ユーザーメッセージ詳細",
            value="\\n".join(user_details[:5]),
            inline=False
        )
    
    if staff_details:
        embed.add_field(
            name="👮 運営メッセージ詳細",
            value="\\n".join(staff_details[:5]),
            inline=False
        )
    
    await interaction.followup.send(embed=embed)
'''

# =====================================
# 実装手順（優先順位付き）
# =====================================

IMPLEMENTATION_PLAN = """
📋 段階的実装計画

【Phase 1: 最優先修正】
1. count_active_users メソッドの置き換え
   - これが最も重要な修正
   - アクティブユーザー0人問題を解決

2. __init__ メソッドの修正
   - defaultdictの問題を解決
   - 辞書の初期化を適切に

【Phase 2: 動作確認】
3. metrics_live コマンドの追加
   - 現在の状況をリアルタイムで確認
   - 問題の特定に使用

【Phase 3: 最適化】
4. on_message の軽微な修正
   - エラーハンドリングの改善
   - 辞書初期化の明示的な処理

【テスト手順】
1. Botを再起動
2. /metrics_live でカウント確認
3. メッセージを送信してカウントアップ確認
4. /metrics で手動収集実行
5. アクティブユーザー数が0以外になることを確認

【期待される改善】
✅ アクティブユーザー数が正しくカウントされる
✅ ユーザー別のカウントが正確になる
✅ エラーログで問題を特定しやすくなる
"""

print(IMPLEMENTATION_PLAN)