"""
Discord Bot - KPI メトリクス収集機能
タスク管理アプリのデータベースにKPIデータを保存
"""

import asyncpg
import discord
from discord.ext import commands, tasks
from datetime import datetime, date, time, timezone, timedelta
import os
import logging
from typing import Optional, Dict, List
from collections import defaultdict

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector(commands.Cog):
    """Discord KPI メトリクス収集クラス"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_url = os.getenv('NEON_DATABASE_URL')
        
        # ロールIDの定義
        self.VIEWABLE_ROLE_ID = 1236344630132473946  # 閲覧可能ロール
        self.STAFF_ROLE_ID = 1236487195741913119     # 運営ロール
        self.TRACKED_ROLE_IDS = [
            1381201663045668906,
            1382167308180394145,
            1332242428459221046,
            1383347155548504175,
            1383347231188586628,
            1383347303347257486,
            1383347353141907476
        ]
        
        # ロール名のマッピング（自動取得できない場合のバックアップ）
        self.ROLE_NAMES = {
            1332242428459221046: "FIND to DO",
            1381201663045668906: "イベント情報",
            1382167308180394145: "みんなの告知",
            1383347155548504175: "経営幹部",
            1383347231188586628: "学生",
            1383347303347257486: "フリーランス",
            1383347353141907476: "エンジョイ"
        }
        
        # メッセージカウント用の辞書（メモリ上で管理）
        self.message_counts = defaultdict(lambda: defaultdict(int))  # {channel_id: {user_id: count}}
        self.staff_message_counts = defaultdict(lambda: defaultdict(int))  # {channel_id: {user_id: count}}
        
        # 定期収集タスク開始
        if not self.daily_metrics_task.is_running():
            self.daily_metrics_task.start()
        
        logger.info("📊 MetricsCollector初期化完了")
    
    def cog_unload(self):
        """Cog終了時の処理"""
        self.daily_metrics_task.cancel()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージ送信時にカウント（低負荷実装）"""
        # BOTメッセージは除外
        if message.author.bot:
            return
        
        # チャンネルが閲覧可能ロールで見えるかチェック
        guild = message.guild
        if not guild:
            return
            
        viewable_role = guild.get_role(self.VIEWABLE_ROLE_ID)
        if not viewable_role:
            return
            
        # チャンネルの権限をチェック
        channel_perms = message.channel.permissions_for(viewable_role)
        if not channel_perms.view_channel:
            return
        
        # 運営ロールかどうかチェック
        staff_role = guild.get_role(self.STAFF_ROLE_ID)
        is_staff = staff_role in message.author.roles if staff_role else False
        
        # メッセージカウント
        if is_staff:
            self.staff_message_counts[message.channel.id][message.author.id] += 1
        else:
            self.message_counts[message.channel.id][message.author.id] += 1
    
    async def get_main_guild(self) -> Optional[discord.Guild]:
        """メインサーバーを取得"""
        if not self.bot.guilds:
            logger.error("❌ サーバーが見つかりません")
            return None
        
        # 最初のサーバーをメインとして使用
        guild = self.bot.guilds[0]
        logger.info(f"📍 対象サーバー: {guild.name} (ID: {guild.id})")
        return guild
    
    def get_daily_message_stats(self) -> Dict[str, any]:
        """日次メッセージ統計を取得"""
        total_user_messages = sum(sum(users.values()) for users in self.message_counts.values())
        total_staff_messages = sum(sum(users.values()) for users in self.staff_message_counts.values())
        
        # チャンネル別統計
        channel_stats = {}
        for channel_id, users in self.message_counts.items():
            channel_stats[str(channel_id)] = {
                'user_messages': sum(users.values()),
                'user_count': len(users)
            }
        
        staff_channel_stats = {}
        for channel_id, users in self.staff_message_counts.items():
            staff_channel_stats[str(channel_id)] = {
                'staff_messages': sum(users.values()),
                'staff_count': len(users)
            }
        
        return {
            'total_user_messages': total_user_messages,
            'total_staff_messages': total_staff_messages,
            'total_messages': total_user_messages + total_staff_messages,
            'channel_stats': channel_stats,
            'staff_channel_stats': staff_channel_stats
        }
    
    def reset_daily_counts(self):
        """日次カウントをリセット"""
        self.message_counts.clear()
        self.staff_message_counts.clear()
        logger.info("📝 メッセージカウントをリセットしました")
    
    async def count_role_members(self, guild: discord.Guild) -> Dict[str, any]:
        """特定ロールのメンバー数をカウント"""
        role_counts = {}
        
        for role_id in self.TRACKED_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                role_name = role.name
                member_count = len(role.members)
                role_counts[str(role_id)] = {
                    'name': role_name,
                    'count': member_count
                }
                logger.info(f"👥 ロール {role_name}: {member_count}人")
            else:
                # バックアップ名を使用
                backup_name = self.ROLE_NAMES.get(role_id, f"Unknown Role {role_id}")
                role_counts[str(role_id)] = {
                    'name': backup_name,
                    'count': 0
                }
                logger.warning(f"⚠️ ロールID {role_id} ({backup_name}) が見つかりません")
        
        return role_counts
    
    async def count_active_users(self, guild: discord.Guild) -> int:
        """アクティブユーザー数をカウント（運営※エグゼクティブマネージャーなどを除く）"""
        try:
            staff_role = guild.get_role(self.STAFF_ROLE_ID)
            
            # オンライン状態のユーザー（BOTと運営を除く）
            active_users = len([
                m for m in guild.members 
                if not m.bot 
                and m.status != discord.Status.offline
                and (not staff_role or staff_role not in m.roles)
            ])
            
            logger.info(f"👥 アクティブユーザー数（運営除く）: {active_users}")
            return active_users
            
        except Exception as e:
            logger.error(f"❌ アクティブユーザー数取得エラー: {e}")
            return 0
    
    async def calculate_engagement_score(self, member_count: int, active_users: int, daily_messages: int) -> float:
        """エンゲージメントスコアを計算"""
        try:
            if member_count == 0:
                return 0.0
            
            # エンゲージメントスコア = (アクティブユーザー率 * 0.4) + (メッセージ密度 * 0.6)
            active_ratio = (active_users / member_count) * 100
            message_density = daily_messages / member_count if member_count > 0 else 0
            
            engagement_score = (active_ratio * 0.4) + (message_density * 0.6)
            
            logger.info(f"📈 エンゲージメントスコア: {engagement_score:.2f}")
            return round(engagement_score, 2)
            
        except Exception as e:
            logger.error(f"❌ エンゲージメントスコア計算エラー: {e}")
            return 0.0
    
    async def collect_daily_metrics(self) -> dict:
        """日次メトリクスを収集"""
        logger.info("📊 KPI収集開始...")
        
        try:
            guild = await self.get_main_guild()
            if not guild:
                return None
            
            # メッセージ統計を取得
            message_stats = self.get_daily_message_stats()
            
            # ロールメンバー数を取得
            role_counts = await self.count_role_members(guild)
            
            # 基本メトリクス収集
            member_count = guild.member_count
            online_count = len([m for m in guild.members if m.status != discord.Status.offline])
            active_users = await self.count_active_users(guild)
            
            # エンゲージメントスコア計算
            engagement_score = await self.calculate_engagement_score(
                member_count, active_users, message_stats['total_user_messages']
            )
            
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
            
            logger.info(f"✅ メトリクス収集完了: {metrics['date']}")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ メトリクス収集エラー: {e}")
            return None
    
    async def save_metrics_to_db(self, metrics: dict) -> bool:
        """メトリクスをデータベースに保存"""
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                logger.info("📊 DB接続成功")
                
                # テーブル存在確認
                table_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'discord_metrics'
                    )
                """)
                
                if not table_exists:
                    logger.error("❌ discord_metricsテーブルが存在しません")
                    return False
                
                # UPSERT（存在する場合は更新、しない場合は挿入）
                logger.info("SQL実行開始...")
                # cuid生成のためのUUID
                import uuid
                cuid = f"c{str(uuid.uuid4()).replace('-', '')[:24]}"
                
                # JSONデータの準備
                import json
                channel_stats_json = json.dumps(metrics['channel_message_stats'])
                staff_stats_json = json.dumps(metrics['staff_channel_stats'])
                role_counts_json = json.dumps(metrics['role_counts'])
                
                result = await conn.execute("""
                    INSERT INTO discord_metrics 
                    (id, date, member_count, online_count, daily_messages, active_users, 
                     engagement_score, daily_user_messages, daily_staff_messages,
                     channel_message_stats, staff_channel_stats, role_counts, 
                     created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
                    ON CONFLICT (date) DO UPDATE SET
                    member_count = $3, 
                    online_count = $4, 
                    daily_messages = $5,
                    active_users = $6, 
                    engagement_score = $7,
                    daily_user_messages = $8,
                    daily_staff_messages = $9,
                    channel_message_stats = $10,
                    staff_channel_stats = $11,
                    role_counts = $12,
                    updated_at = NOW()
                """, cuid, metrics['date'], metrics['member_count'], 
                    metrics['online_count'], metrics['daily_messages'], 
                    metrics['active_users'], metrics['engagement_score'],
                    metrics['daily_user_messages'], metrics['daily_staff_messages'],
                    channel_stats_json, staff_stats_json, role_counts_json)
                
                logger.info(f"✅ データベース保存成功: {result}")
                return True
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ データベース保存エラー: {e}")
            return False
    
    async def get_recent_metrics(self, days: int = 7) -> list:
        """最近のメトリクスデータを取得"""
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                # 過去N日間のデータを取得
                rows = await conn.fetch("""
                    SELECT * FROM discord_metrics 
                    WHERE date >= CURRENT_DATE - INTERVAL '$1 days'
                    ORDER BY date DESC
                """, days)
                
                return [dict(row) for row in rows]
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ データ取得エラー: {e}")
            return []
    
    @discord.app_commands.command(name="metrics", description="Discord KPIを収集・保存")
    @discord.app_commands.default_permissions(administrator=True)
    async def collect_metrics(self, interaction: discord.Interaction):
        """KPIメトリクスを手動で収集"""
        await interaction.response.defer()
        
        # メトリクス収集
        metrics = await self.collect_daily_metrics()
        if not metrics:
            await interaction.followup.send("❌ メトリクス収集に失敗しました")
            return
        
        # データベース保存
        success = await self.save_metrics_to_db(metrics)
        
        if success:
            # 日次カウントをリセット
            self.reset_daily_counts()
            
            embed = discord.Embed(
                title="📊 Discord KPI収集完了",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="📅 日付", value=str(metrics['date']), inline=True)
            embed.add_field(name="👥 総メンバー", value=f"{metrics['member_count']:,}", inline=True)
            embed.add_field(name="🟢 オンライン", value=f"{metrics['online_count']:,}", inline=True)
            embed.add_field(name="💬 総メッセージ", value=f"{metrics['daily_messages']:,}", inline=True)
            embed.add_field(name="👤 ユーザーメッセージ", value=f"{metrics['daily_user_messages']:,}", inline=True)
            embed.add_field(name="👮 運営メッセージ", value=f"{metrics['daily_staff_messages']:,}", inline=True)
            embed.add_field(name="🏃 アクティブユーザー", value=f"{metrics['active_users']:,}", inline=True)
            embed.add_field(name="📈 エンゲージメント", value=f"{metrics['engagement_score']:.2f}", inline=True)
            
            # ロール別メンバー数
            role_text = "\n".join([f"{data['name']}: {data['count']}人" 
                                 for role_id, data in metrics['role_counts'].items()])
            embed.add_field(name="👥 ロール別メンバー", value=role_text or "なし", inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ データベース保存に失敗しました")
    
    @discord.app_commands.command(name="metrics_history", description="KPI履歴を表示")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(days="表示する日数（最大30日）")
    async def show_metrics_history(self, interaction: discord.Interaction, days: int = 7):
        """過去のKPIメトリクスを表示"""
        await interaction.response.defer()
        
        # 日数制限
        days = min(days, 30)
        
        # データ取得
        metrics_list = await self.get_recent_metrics(days)
        
        if not metrics_list:
            await interaction.followup.send(f"📊 過去{days}日間のデータが見つかりません")
            return
        
        embed = discord.Embed(
            title=f"📊 Discord KPI履歴（過去{days}日間）",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for metrics in metrics_list[:10]:  # 最大10件表示
            date_str = metrics['date'].strftime('%Y-%m-%d')
            embed.add_field(
                name=f"📅 {date_str}",
                value=(
                    f"👥 メンバー: {metrics['member_count']:,}\n"
                    f"💬 メッセージ: {metrics['daily_messages']:,}\n"
                    f"📈 エンゲージメント: {metrics['engagement_score']:.2f}"
                ),
                inline=True
            )
        
        await interaction.followup.send(embed=embed)
    
    @discord.app_commands.command(name="metrics_test", description="DB接続テスト")
    @discord.app_commands.default_permissions(administrator=True)
    async def test_db_connection(self, interaction: discord.Interaction):
        """データベース接続をテスト"""
        await interaction.response.defer()
        
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                # バージョン確認
                version = await conn.fetchval("SELECT version()")
                
                # テーブル確認
                table_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'discord_metrics'
                    )
                """)
                
                embed = discord.Embed(
                    title="🔌 DB接続テスト結果",
                    color=discord.Color.green() if table_exists else discord.Color.yellow()
                )
                embed.add_field(name="接続状態", value="✅ 成功", inline=True)
                embed.add_field(name="discord_metricsテーブル", 
                              value="✅ 存在" if table_exists else "❌ 存在しない", 
                              inline=True)
                embed.add_field(name="PostgreSQLバージョン", 
                              value=version.split('\n')[0], 
                              inline=False)
                
                await interaction.followup.send(embed=embed)
            finally:
                await conn.close()
                
        except Exception as e:
            await interaction.followup.send(f"❌ DB接続エラー: {str(e)}")
    
    @tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone(timedelta(hours=9))))  # 日本時間0:00に実行
    async def daily_metrics_task(self):
        """定期的にメトリクスを収集（日本時間0:00）"""
        logger.info("⏰ 定期メトリクス収集開始（日本時間0:00）...")
        
        metrics = await self.collect_daily_metrics()
        if metrics:
            success = await self.save_metrics_to_db(metrics)
            if success:
                # 日次カウントをリセット
                self.reset_daily_counts()
                logger.info("✅ 定期メトリクス収集・保存完了")
            else:
                logger.error("❌ 定期メトリクス保存失敗")
    
    @daily_metrics_task.before_loop
    async def before_daily_metrics(self):
        """タスク開始前の待機"""
        await self.bot.wait_until_ready()
    
    @tasks.loop(minutes=2)  # テスト用: 2分間隔
    async def test_auto_save(self):
        """自動保存テスト用（短時間間隔）"""
        logger.info("🧪 テスト用自動メトリクス収集開始...")
        
        metrics = await self.collect_daily_metrics()
        if metrics:
            success = await self.save_metrics_to_db(metrics)
            if success:
                logger.info("✅ テスト用自動保存成功")
            else:
                logger.error("❌ テスト用自動保存失敗")
    
    @test_auto_save.before_loop
    async def before_test_auto_save(self):
        """テストタスク開始前の待機"""
        await self.bot.wait_until_ready()
    
    @discord.app_commands.command(name="metrics_auto_test", description="自動保存テスト開始/停止")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(action="start: テスト開始, stop: テスト停止")
    async def toggle_auto_test(self, interaction: discord.Interaction, action: str):
        """自動保存テストの開始/停止"""
        if action == "start":
            if not self.test_auto_save.is_running():
                self.test_auto_save.start()
                await interaction.response.send_message("🧪 自動保存テスト開始（2分間隔で実行中）")
            else:
                await interaction.response.send_message("⚠️ テストは既に実行中です")
        elif action == "stop":
            if self.test_auto_save.is_running():
                self.test_auto_save.cancel()
                await interaction.response.send_message("⏹️ 自動保存テスト停止")
            else:
                await interaction.response.send_message("⚠️ テストは実行されていません")
        else:
            await interaction.response.send_message("❌ action は 'start' または 'stop' を指定してください")
    
    @discord.app_commands.command(name="metrics_schedule", description="自動収集スケジュール確認")
    @discord.app_commands.default_permissions(administrator=True)
    async def check_schedule(self, interaction: discord.Interaction):
        """自動収集スケジュールを確認"""
        embed = discord.Embed(
            title="📅 メトリクス自動収集スケジュール",
            color=discord.Color.blue()
        )
        
        # 24時間定期収集
        if self.daily_metrics_task.is_running():
            next_run = self.daily_metrics_task.next_iteration
            if next_run:
                next_run_jst = next_run.astimezone(timezone(timedelta(hours=9)))
                embed.add_field(
                    name="🕛 日次収集（本番）",
                    value=f"**毎日 日本時間 0:00**\n次回実行: {next_run_jst.strftime('%Y-%m-%d %H:%M:%S JST')}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🕛 日次収集（本番）",
                    value="**毎日 日本時間 0:00**\n状態: 実行中",
                    inline=False
                )
        else:
            embed.add_field(
                name="🕛 日次収集（本番）",
                value="**停止中**",
                inline=False
            )
        
        # テスト用収集
        if self.test_auto_save.is_running():
            next_test = self.test_auto_save.next_iteration
            if next_test:
                next_test_jst = next_test.astimezone(timezone(timedelta(hours=9)))
                embed.add_field(
                    name="🧪 テスト収集（2分間隔）",
                    value=f"次回実行: {next_test_jst.strftime('%H:%M:%S JST')}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🧪 テスト収集（2分間隔）",
                    value="実行中",
                    inline=False
                )
        else:
            embed.add_field(
                name="🧪 テスト収集（2分間隔）",
                value="**停止中**",
                inline=False
            )
        
        # 現在時刻
        now_jst = datetime.now(timezone(timedelta(hours=9)))
        embed.add_field(
            name="🕐 現在時刻",
            value=f"{now_jst.strftime('%Y-%m-%d %H:%M:%S JST')}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Cogのセットアップ"""
    await bot.add_cog(MetricsCollector(bot))