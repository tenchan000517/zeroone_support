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
import aiohttp
import json
import asyncio
from typing import Optional, Dict, List
from collections import defaultdict

# 設定インポート
from config.config import METRICS_CONFIG

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector(commands.Cog):
    """Discord KPI メトリクス収集クラス"""
    
    def __init__(self, bot):
        self.bot = bot
        # 環境変数から改行文字を削除
        db_url_raw = os.getenv('NEON_DATABASE_URL')
        self.db_url = db_url_raw.replace('\n', '').replace(' ', '') if db_url_raw else None
        
        # コンフィグからロール設定を読み込み
        self.VIEWABLE_ROLE_ID = METRICS_CONFIG["viewable_role_id"]
        self.STAFF_ROLE_ID = METRICS_CONFIG["staff_role_id"]
        self.TRACKED_ROLE_IDS = list(METRICS_CONFIG["tracked_roles"].keys())
        self.ROLE_NAMES = METRICS_CONFIG["tracked_roles"]
        
        # エンゲージメント計算の重み設定
        self.ENGAGEMENT_WEIGHTS = METRICS_CONFIG["engagement_weights"]
        
        # リアクション追跡設定
        self.REACTION_CONFIG = METRICS_CONFIG["reaction_tracking"]
        
        # ダッシュボード連携設定
        self.DASHBOARD_CONFIG = METRICS_CONFIG["dashboard_integration"]
        
        # ガントチャート収集設定
        self.GANTT_CONFIG = METRICS_CONFIG["gantt_chart_collection"]
        
        # メッセージカウント用の辞書（メモリ上で管理）
        self.message_counts = defaultdict(lambda: defaultdict(int))  # {channel_id: {user_id: count}}
        self.staff_message_counts = defaultdict(lambda: defaultdict(int))  # {channel_id: {user_id: count}}
        
        # リアクションカウント用の辞書（メモリ上で管理）
        self.reaction_counts = defaultdict(lambda: defaultdict(int))  # {channel_id: {emoji: count}}
        self.user_reaction_counts = defaultdict(int)  # {user_id: count} - ユーザー別リアクション数
        
        # 時間別ガントチャートデータを蓄積するためのメモリストレージ
        self.hourly_gantt_data = {}  # {hour: gantt_data} 形式で24時間分保持
        
        # 定期収集タスク開始
        if not self.daily_metrics_task.is_running():
            self.daily_metrics_task.start()
        
        # 1時間ごとのガントチャートデータ収集タスク開始
        if not self.hourly_gantt_collection_task.is_running():
            self.hourly_gantt_collection_task.start()
        
        logger.info("📊 MetricsCollector初期化完了")
    
    def cog_unload(self):
        """Cog終了時の処理"""
        self.daily_metrics_task.cancel()
        if hasattr(self, 'hourly_gantt_collection_task'):
            self.hourly_gantt_collection_task.cancel()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージ送信時にカウント（低負荷実装）"""
        # BOTメッセージは除外
        if message.author.bot:
            return
        
        print(f"🔍 [METRICS] メッセージ受信: {message.author.name} in {message.channel.name}")
        
        # チャンネルが閲覧可能ロールで見えるかチェック
        guild = message.guild
        if not guild:
            print(f"❌ [METRICS] ギルドなし: {message.id}")
            return
            
        print(f"🔍 [METRICS] ギルド: {guild.name} (ID: {guild.id})")
        
        viewable_role = guild.get_role(self.VIEWABLE_ROLE_ID)
        if not viewable_role:
            print(f"❌ [METRICS] 閲覧可能ロール {self.VIEWABLE_ROLE_ID} が見つかりません")
            print(f"🔍 [METRICS] 利用可能なロール一覧:")
            for role in guild.roles:
                print(f"  - {role.name} (ID: {role.id})")
            return
            
        print(f"✅ [METRICS] 閲覧可能ロール見つかりました: {viewable_role.name}")
        
        # チャンネルの権限をチェック
        channel_perms = message.channel.permissions_for(viewable_role)
        print(f"🔍 [METRICS] チャンネル権限 view_channel: {channel_perms.view_channel}")
        if not channel_perms.view_channel:
            print(f"❌ [METRICS] チャンネル {message.channel.name} は閲覧可能ロールで見えません")
            return
        
        # 運営ロールかどうかチェック
        staff_role = guild.get_role(self.STAFF_ROLE_ID)
        is_staff = staff_role in message.author.roles if staff_role else False
        print(f"🔍 [METRICS] 運営ロール: {staff_role.name if staff_role else 'なし'}, is_staff: {is_staff}")
        
        # メッセージカウント
        if is_staff:
            self.staff_message_counts[message.channel.id][message.author.id] += 1
            print(f"📊 [METRICS] 運営メッセージカウント +1: {message.author.name}")
        else:
            self.message_counts[message.channel.id][message.author.id] += 1
            print(f"📊 [METRICS] ユーザーメッセージカウント +1: {message.author.name}")
        
        # 現在のカウント状況を表示
        total_user = sum(sum(users.values()) for users in self.message_counts.values())
        total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
        
        # チャンネル別の詳細も表示
        channel_details = []
        for channel_id, users in self.message_counts.items():
            channel = guild.get_channel(channel_id)
            channel_name = channel.name if channel else f"ID:{channel_id}"
            user_count = sum(users.values())
            if user_count > 0:
                channel_details.append(f"{channel_name}({user_count}件)")
        
        staff_channel_details = []
        for channel_id, users in self.staff_message_counts.items():
            channel = guild.get_channel(channel_id)
            channel_name = channel.name if channel else f"ID:{channel_id}"
            staff_count = sum(users.values())
            if staff_count > 0:
                staff_channel_details.append(f"{channel_name}({staff_count}件)")
        
        print(f"📊 [METRICS] 現在の合計 - ユーザー: {total_user}件, 運営: {total_staff}件")
        if channel_details:
            print(f"📍 [METRICS] ユーザーチャンネル別: {', '.join(channel_details)}")
        if staff_channel_details:
            print(f"👮 [METRICS] 運営チャンネル別: {', '.join(staff_channel_details)}")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """リアクション追加時の処理"""
        # BOTの場合は除外
        if user.bot:
            return
        
        # リアクション追跡が無効の場合は処理しない
        if not self.REACTION_CONFIG["enabled"]:
            return
        
        # チャンネルが除外対象の場合は処理しない
        if reaction.message.channel.id in self.REACTION_CONFIG["excluded_channels"]:
            return
        
        print(f"👍 [REACTIONS] リアクション追加: {reaction.emoji} by {user.name} in {reaction.message.channel.name}")
        
        # チャンネルの権限チェック（既存のメッセージ処理と同様）
        guild = reaction.message.guild
        if not guild:
            return
        
        viewable_role = guild.get_role(self.VIEWABLE_ROLE_ID)
        if not viewable_role:
            return
        
        channel_perms = reaction.message.channel.permissions_for(viewable_role)
        if not channel_perms.view_channel:
            return
        
        # 絵文字文字列を取得
        emoji_str = self._get_emoji_string(reaction.emoji)
        
        # リアクションカウント
        self.reaction_counts[reaction.message.channel.id][emoji_str] += 1
        self.user_reaction_counts[user.id] += 1
        
        print(f"📊 [REACTIONS] リアクションカウント +1: {emoji_str} (チャンネル: {reaction.message.channel.name})")
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """リアクション削除時の処理"""
        # BOTの場合は除外
        if user.bot:
            return
        
        # リアクション追跡が無効の場合は処理しない
        if not self.REACTION_CONFIG["enabled"]:
            return
        
        # チャンネルが除外対象の場合は処理しない
        if reaction.message.channel.id in self.REACTION_CONFIG["excluded_channels"]:
            return
        
        print(f"👎 [REACTIONS] リアクション削除: {reaction.emoji} by {user.name} in {reaction.message.channel.name}")
        
        # チャンネルの権限チェック（既存のメッセージ処理と同様）
        guild = reaction.message.guild
        if not guild:
            return
        
        viewable_role = guild.get_role(self.VIEWABLE_ROLE_ID)
        if not viewable_role:
            return
        
        channel_perms = reaction.message.channel.permissions_for(viewable_role)
        if not channel_perms.view_channel:
            return
        
        # 絵文字文字列を取得
        emoji_str = self._get_emoji_string(reaction.emoji)
        
        # リアクションカウント減算（0以下にならないよう制限）
        if self.reaction_counts[reaction.message.channel.id][emoji_str] > 0:
            self.reaction_counts[reaction.message.channel.id][emoji_str] -= 1
        
        if self.user_reaction_counts[user.id] > 0:
            self.user_reaction_counts[user.id] -= 1
        
        print(f"📊 [REACTIONS] リアクションカウント -1: {emoji_str} (チャンネル: {reaction.message.channel.name})")
    
    def _get_emoji_string(self, emoji) -> str:
        """絵文字から文字列を取得"""
        if isinstance(emoji, str):
            # 標準絵文字
            return emoji
        else:
            # カスタム絵文字
            if self.REACTION_CONFIG["track_custom_emojis"]:
                return f"<:{emoji.name}:{emoji.id}>"
            else:
                return emoji.name
    
    async def collect_online_users_data(self, guild: discord.Guild) -> dict:
        """オンラインユーザーデータを収集"""
        try:
            online_users = []
            status_counts = {'online': 0, 'idle': 0, 'dnd': 0, 'offline': 0}
            activity_counts = {}
            
            for member in guild.members:
                # ステータスカウント
                status_counts[str(member.status)] += 1
                
                # オンラインのユーザーのみ詳細記録
                if member.status != discord.Status.offline:
                    user_data = {
                        'user_id': str(member.id),
                        'username': member.name,
                        'display_name': member.display_name,
                        'status': str(member.status),
                        'is_bot': member.bot
                    }
                    
                    # アクティビティ情報
                    if member.activity:
                        activity_type = str(member.activity.type).split('.')[-1].lower()
                        user_data['activity_type'] = activity_type
                        user_data['activity_name'] = member.activity.name
                        
                        # アクティビティ種別カウント
                        activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
                    
                    online_users.append(user_data)
            
            # 統計情報
            online_stats = {
                'total_online': len(online_users),
                'status_breakdown': status_counts,
                'activity_breakdown': activity_counts,
                'online_users_count': len([u for u in online_users if not u['is_bot']]),
                'online_bots_count': len([u for u in online_users if u['is_bot']]),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"📊 オンラインユーザー収集完了: {online_stats['total_online']}人")
            return {
                'stats': online_stats,
                'users': online_users
            }
            
        except Exception as e:
            logger.error(f"❌ オンラインユーザー収集エラー: {e}")
            return {'stats': {}, 'users': []}
    
    async def collect_gantt_chart_data(self, guild: discord.Guild) -> dict:
        """フロントエンド用ガントチャートデータを収集（指定ロールのユーザーのみ）"""
        try:
            logger.info(f"🔍 [DEBUG] ガントチャート収集開始 - Guild: {guild.name} (ID: {guild.id})")
            
            # ガントチャート収集が無効の場合は空データを返す
            if not self.GANTT_CONFIG["enabled"]:
                logger.warning(f"⚠️  [DEBUG] ガントチャート収集が無効です: {self.GANTT_CONFIG['enabled']}")
                return {}
            
            current_time = datetime.now(timezone.utc)
            target_role_ids = self.GANTT_CONFIG["target_roles"]
            logger.info(f"🔍 [DEBUG] 対象ロールID: {target_role_ids}")
            
            # 対象ロールがない場合は空データを返す
            if not target_role_ids:
                logger.warning("ガントチャート収集対象ロールが設定されていません")
                return {}
            
            # 対象ロールが実際に存在するかチェック
            target_roles = []
            for role_id in target_role_ids:
                role = guild.get_role(role_id)
                if role:
                    target_roles.append(role)
                    logger.info(f"✅ [DEBUG] 対象ロール見つかりました: {role.name} (ID: {role_id}, メンバー数: {len(role.members)})")
                else:
                    logger.warning(f"❌ [DEBUG] 対象ロールが見つかりません: {role_id}")
            
            if not target_roles:
                logger.warning("❌ [DEBUG] 有効な対象ロールがありません")
                return {}
            
            # 現在オンライン中の対象ロールユーザー情報を収集
            online_users = []
            total_members_checked = 0
            online_members_found = 0
            target_role_members_found = 0
            
            logger.info(f"🔍 [DEBUG] 全メンバー数: {len(guild.members)}")
            
            for member in guild.members:
                total_members_checked += 1
                
                # BOTは除外
                if member.bot:
                    continue
                
                # オンライン状態チェック
                if member.status != discord.Status.offline:
                    online_members_found += 1
                    
                    # ユーザーのロール情報を取得
                    member_role_ids = [role.id for role in member.roles if role.id != guild.default_role.id]
                    
                    # 対象ロールを持っているかチェック
                    has_target_role = any(role_id in target_role_ids for role_id in member_role_ids)
                    
                    if has_target_role:
                        target_role_members_found += 1
                        logger.info(f"✅ [DEBUG] 対象ユーザー発見: {member.display_name} (Status: {member.status})")
                        
                        # 対象ロールを持つユーザーのみ収集
                        role_ids_str = [str(role_id) for role_id in member_role_ids]
                        role_names = [role.name for role in member.roles if role.id != guild.default_role.id]
                        
                        user_data = {
                            'user_id': str(member.id),
                            'username': member.name,
                            'display_name': member.display_name,
                            'status': str(member.status),
                            'role_ids': role_ids_str,
                            'role_names': role_names,
                            'activity_type': None,
                            'activity_name': None,
                            'timestamp': current_time.isoformat()
                        }
                        
                        # アクティビティ情報
                        if member.activity:
                            activity_type = str(member.activity.type).split('.')[-1].lower()
                            user_data['activity_type'] = activity_type
                            user_data['activity_name'] = member.activity.name
                        
                        online_users.append(user_data)
            
            logger.info(f"📊 [DEBUG] 収集結果:")
            logger.info(f"  - 全メンバー数: {total_members_checked}")
            logger.info(f"  - オンラインメンバー数: {online_members_found}")
            logger.info(f"  - 対象ロール保持オンラインメンバー数: {target_role_members_found}")
            logger.info(f"  - 収集データ数: {len(online_users)}")
            
            for member in guild.members:
                if member.status != discord.Status.offline and not member.bot:
                    # ユーザーのロール情報を取得
                    member_role_ids = [role.id for role in member.roles if role.id != guild.default_role.id]
                    
                    # 対象ロールを持っているかチェック
                    has_target_role = any(role_id in target_role_ids for role_id in member_role_ids)
                    
                    if has_target_role:
                        # 対象ロールを持つユーザーのみ収集
                        role_ids_str = [str(role_id) for role_id in member_role_ids]
                        role_names = [role.name for role in member.roles if role.id != guild.default_role.id]
                        
                        user_data = {
                            'user_id': str(member.id),
                            'username': member.name,
                            'display_name': member.display_name,
                            'status': str(member.status),
                            'role_ids': role_ids_str,
                            'role_names': role_names,
                            'activity_type': None,
                            'activity_name': None,
                            'timestamp': current_time.isoformat()
                        }
                        
                        # アクティビティ情報
                        if member.activity:
                            activity_type = str(member.activity.type).split('.')[-1].lower()
                            user_data['activity_type'] = activity_type
                            user_data['activity_name'] = member.activity.name
                        
                        online_users.append(user_data)
            
            # 統計情報の計算
            total_online = len(online_users)
            
            # 対象ロール別オンライン数の集計（指定されたロールのみ）
            role_online_counts = {}
            for role_id in target_role_ids:
                role = guild.get_role(role_id)
                if role:
                    # 対象ロールを持つオンラインユーザーの数をカウント
                    role_online_count = len([
                        user for user in online_users 
                        if str(role_id) in user['role_ids']
                    ])
                    
                    # そのロールを持つ全メンバー数（BOT除外）
                    total_role_members = len([m for m in role.members if not m.bot])
                    
                    role_online_counts[str(role_id)] = {
                        'role_name': role.name,
                        'online_count': role_online_count,
                        'total_members': total_role_members,
                        'online_rate': round((role_online_count / total_role_members) * 100, 2) if total_role_members > 0 else 0
                    }
            
            # ステータス別集計
            status_counts = {'online': 0, 'idle': 0, 'dnd': 0}
            for user in online_users:
                status_counts[user['status']] = status_counts.get(user['status'], 0) + 1
            
            # アクティビティ別集計
            activity_counts = {}
            for user in online_users:
                if user['activity_type']:
                    activity_counts[user['activity_type']] = activity_counts.get(user['activity_type'], 0) + 1
            
            # 時間別データ（現在の時刻のスナップショット）
            current_hour = current_time.hour
            hourly_data = {
                str(current_hour): {
                    'total_online': total_online,
                    'status_breakdown': status_counts,
                    'activity_breakdown': activity_counts,
                    'role_breakdown': role_online_counts
                }
            }
            
            gantt_data = {
                'date': current_time.date().isoformat(),
                'timestamp': current_time.isoformat(),
                'total_online_users': total_online,
                'status_breakdown': status_counts,
                'activity_breakdown': activity_counts,
                'role_breakdown': role_online_counts,
                'hourly_snapshot': hourly_data,
                'online_users': online_users,
                'top_active_roles': [
                    {'role_name': data['role_name'], 'online_count': data['online_count'], 'online_rate': data['online_rate']}
                    for data in sorted(role_online_counts.values(), key=lambda x: x['online_rate'], reverse=True)[:10]
                    if data['online_count'] > 0
                ]
            }
            
            # 対象ロール名をログに出力
            target_role_names = []
            for role_id in target_role_ids:
                role = guild.get_role(role_id)
                if role:
                    target_role_names.append(role.name)
            
            logger.info(f"📊 ガントチャートデータ収集完了: {total_online}人オンライン（対象ロール: {', '.join(target_role_names)}）")
            return gantt_data
            
        except Exception as e:
            logger.error(f"❌ ガントチャートデータ収集エラー: {e}")
            return {}
    
    async def compile_daily_gantt_data(self, guild: discord.Guild) -> dict:
        """24時間分の時間別ガントチャートデータを統合"""
        try:
            current_time = datetime.now(timezone.utc)
            today_str = current_time.date().isoformat()
            
            # 現在の時刻のデータも含めて最新情報にする
            current_gantt_data = await self.collect_gantt_chart_data(guild)
            current_hour = current_time.hour
            
            # 現在の時刻のデータを更新
            if current_gantt_data:
                self.hourly_gantt_data[current_hour] = current_gantt_data
            
            # 24時間分のデータを統合
            hourly_timeline = {}
            total_unique_users = set()
            role_activity_summary = {}
            
            # 0-23時の各時間のデータを整理
            for hour in range(24):
                if hour in self.hourly_gantt_data:
                    hourly_data = self.hourly_gantt_data[hour]
                    hourly_timeline[f"{hour:02d}:00"] = {
                        'total_online': hourly_data.get('total_online_users', 0),
                        'status_breakdown': hourly_data.get('status_breakdown', {}),
                        'timestamp': hourly_data.get('timestamp', ''),
                        'online_users': hourly_data.get('online_users', [])
                    }
                    
                    # ユニークユーザー集計
                    for user in hourly_data.get('online_users', []):
                        total_unique_users.add(user['user_id'])
                        
                        # ロール別活動集計
                        for role_id in user.get('role_ids', []):
                            if role_id not in role_activity_summary:
                                role_activity_summary[role_id] = {
                                    'user_set': set(),
                                    'total_appearances': 0
                                }
                            role_activity_summary[role_id]['user_set'].add(user['user_id'])
                            role_activity_summary[role_id]['total_appearances'] += 1
                else:
                    # データがない時間帯
                    hourly_timeline[f"{hour:02d}:00"] = {
                        'total_online': 0,
                        'status_breakdown': {},
                        'timestamp': '',
                        'online_users': []
                    }
            
            # ロール別サマリーの作成
            role_summary = {}
            for role_id, data in role_activity_summary.items():
                role = guild.get_role(int(role_id)) if role_id.isdigit() else None
                if role:
                    unique_users = len(data['user_set'])
                    total_members = len(role.members)
                    role_summary[role_id] = {
                        'role_name': role.name,
                        'unique_active_users': unique_users,
                        'total_members': total_members,
                        'activity_rate': round((unique_users / total_members) * 100, 2) if total_members > 0 else 0,
                        'total_appearances': data['total_appearances'],
                        'avg_online_per_hour': round(data['total_appearances'] / 24, 2)
                    }
            
            # 最も活発な時間帯の特定
            peak_hour_data = max(
                [(hour, data) for hour, data in hourly_timeline.items() if data['total_online'] > 0],
                key=lambda x: x[1]['total_online'],
                default=(None, {'total_online': 0})
            )
            
            daily_gantt_summary = {
                'date': today_str,
                'summary_timestamp': current_time.isoformat(),
                'total_unique_users_today': len(total_unique_users),
                'peak_hour': peak_hour_data[0],
                'peak_online_count': peak_hour_data[1]['total_online'],
                'hourly_timeline': hourly_timeline,
                'role_daily_summary': role_summary,
                'data_coverage': len([h for h in hourly_timeline.values() if h['total_online'] > 0])
            }
            
            logger.info(f"📊 日次ガントチャートデータ統合完了: {len(total_unique_users)}人のユニークユーザー")
            return daily_gantt_summary
            
        except Exception as e:
            logger.error(f"❌ 日次ガントチャートデータ統合エラー: {e}")
            return {}
    
    @tasks.loop(hours=1)
    async def hourly_gantt_collection_task(self):
        """1時間ごとにガントチャートデータを収集"""
        try:
            current_time = datetime.now(timezone.utc)
            current_hour = current_time.hour
            
            logger.info(f"⏰ 時間別ガントチャートデータ収集開始: {current_hour}:00")
            
            guild = await self.get_main_guild()
            if not guild:
                logger.warning("❌ メインギルドが見つかりません")
                return
            
            # 現在のオンライン状況を収集
            gantt_data = await self.collect_gantt_chart_data(guild)
            
            if gantt_data:
                # 時間別データとして保存
                self.hourly_gantt_data[current_hour] = gantt_data
                
                # メモリ最適化：設定された保持時間を超えるデータは削除
                retention_hours = self.GANTT_CONFIG.get("data_retention_hours", 25)
                hours_to_remove = []
                for stored_hour in self.hourly_gantt_data.keys():
                    hour_diff = (current_hour - stored_hour) % 24
                    if hour_diff >= retention_hours:  # 設定時間より古い
                        hours_to_remove.append(stored_hour)
                
                for hour in hours_to_remove:
                    del self.hourly_gantt_data[hour]
                
                online_count = gantt_data.get('total_online_users', 0)
                logger.info(f"✅ 時間別データ収集完了: {current_hour}:00 - {online_count}人オンライン")
                
                # デバッグ用：現在の蓄積状況
                stored_hours = sorted(self.hourly_gantt_data.keys())
                logger.info(f"📋 蓄積中の時間データ: {stored_hours}")
            else:
                logger.warning(f"❌ {current_hour}:00のデータ収集に失敗")
                
        except Exception as e:
            logger.error(f"❌ 時間別ガントチャートデータ収集エラー: {e}")
    
    @hourly_gantt_collection_task.before_loop
    async def before_hourly_gantt_collection(self):
        """時間別収集タスク開始前の待機"""
        await self.bot.wait_until_ready()
        
        # 初回実行時に現在の時刻のデータを即座に収集
        try:
            guild = await self.get_main_guild()
            if guild:
                current_hour = datetime.now(timezone.utc).hour
                gantt_data = await self.collect_gantt_chart_data(guild)
                if gantt_data:
                    self.hourly_gantt_data[current_hour] = gantt_data
                    logger.info(f"🚀 初期時間別データ収集完了: {current_hour}:00")
        except Exception as e:
            logger.error(f"❌ 初期時間別データ収集エラー: {e}")
        
        logger.info("⏰ 時間別ガントチャートデータ収集タスクを開始しました")
    
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
    
    def get_daily_reaction_stats(self) -> Dict[str, any]:
        """日次リアクション統計を取得"""
        if not self.REACTION_CONFIG["enabled"]:
            return {}
        
        total_reactions = sum(sum(emojis.values()) for emojis in self.reaction_counts.values())
        total_unique_emojis = len(set(emoji for emojis in self.reaction_counts.values() for emoji in emojis.keys()))
        total_reaction_users = len([count for count in self.user_reaction_counts.values() if count > 0])
        
        # チャンネル別リアクション統計
        channel_reactions = {}
        for channel_id, emojis in self.reaction_counts.items():
            channel_total = sum(emojis.values())
            if channel_total > 0:
                channel_reactions[str(channel_id)] = {
                    'total_reactions': channel_total,
                    'unique_emojis': len(emojis),
                    'emoji_breakdown': dict(emojis)
                }
        
        # 人気絵文字トップN
        all_emoji_counts = defaultdict(int)
        for emojis in self.reaction_counts.values():
            for emoji, count in emojis.items():
                all_emoji_counts[emoji] += count
        
        top_emojis = sorted(all_emoji_counts.items(), key=lambda x: x[1], reverse=True)[:self.REACTION_CONFIG["top_emojis_limit"]]
        
        return {
            'total_reactions': total_reactions,
            'unique_emojis': total_unique_emojis,
            'reaction_users': total_reaction_users,
            'channel_reactions': channel_reactions,
            'top_emojis': [{'emoji': emoji, 'count': count} for emoji, count in top_emojis]
        }
    
    async def send_to_dashboard(self, metrics: dict) -> bool:
        """ダッシュボードAPIにメトリクスを送信"""
        if not self.DASHBOARD_CONFIG["enabled"]:
            logger.info("📊 ダッシュボード連携が無効のため、スキップします")
            return True
        
        try:
            # フィールド名をキャメルケースに変換
            dashboard_metrics = {
                'date': metrics['date'].isoformat(),
                'memberCount': metrics['member_count'],
                'onlineCount': metrics['online_count'],
                'dailyMessages': metrics['daily_messages'],
                'dailyUserMessages': metrics['daily_user_messages'],
                'dailyStaffMessages': metrics['daily_staff_messages'],
                'activeUsers': metrics['active_users'],
                'engagementScore': metrics['engagement_score'],
                'channelMessageStats': metrics['channel_message_stats'],
                'staffChannelStats': metrics['staff_channel_stats'],
                'roleCounts': metrics['role_counts'],
                'reactionStats': metrics.get('reaction_stats', {}),  # 新機能
                'ganttChartData': metrics.get('gantt_chart_data', {})  # ガントチャート用データ
            }
            
            timeout = aiohttp.ClientTimeout(total=self.DASHBOARD_CONFIG["timeout_seconds"])
            
            for attempt in range(self.DASHBOARD_CONFIG["retry_attempts"]):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        # 認証ヘッダーの準備
                        headers = {'Content-Type': 'application/json'}
                        discord_api_token = os.getenv('DISCORD_API_TOKEN')
                        if discord_api_token:
                            headers['Authorization'] = f'Bearer {discord_api_token}'
                        
                        async with session.post(
                            self.DASHBOARD_CONFIG["api_url"],
                            json=dashboard_metrics,
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                logger.info(f"✅ ダッシュボードへの送信成功: {result}")
                                return True
                            else:
                                response_text = await response.text()
                                logger.error(f"❌ ダッシュボードAPIエラー({response.status}): {response_text}")
                                
                except aiohttp.ClientError as e:
                    logger.warning(f"⚠️ ダッシュボード送信試行 {attempt + 1}/{self.DASHBOARD_CONFIG['retry_attempts']}: {e}")
                    if attempt == self.DASHBOARD_CONFIG["retry_attempts"] - 1:
                        raise
                    await asyncio.sleep(2)  # 2秒待機してリトライ
                    
        except Exception as e:
            logger.error(f"❌ ダッシュボード送信エラー: {type(e).__name__}: {e}")
            if self.DASHBOARD_CONFIG["fallback_to_db_only"]:
                logger.info("📊 フォールバック: データベースのみに保存を継続")
                return True
            return False
        
        return False
    
    def reset_daily_counts(self):
        """日次カウントをリセット"""
        total_user = sum(sum(users.values()) for users in self.message_counts.values())
        total_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
        total_reactions = sum(sum(emojis.values()) for emojis in self.reaction_counts.values())
        total_reaction_users = len([count for count in self.user_reaction_counts.values() if count > 0])
        
        print(f"🔄 [METRICS] カウントリセット前 - ユーザー: {total_user}件, 運営: {total_staff}件, リアクション: {total_reactions}件 ({total_reaction_users}人)")
        
        self.message_counts.clear()
        self.staff_message_counts.clear()
        self.reaction_counts.clear()
        self.user_reaction_counts.clear()
        
        print(f"✅ [METRICS] メッセージ・リアクションカウントをリセットしました")
        logger.info("📝 メッセージ・リアクションカウントをリセットしました")
    
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
    
    async def calculate_engagement_score(self, member_count: int, active_users: int, daily_messages: int) -> float:
        """エンゲージメントスコアを計算"""
        try:
            if member_count == 0:
                return 0.0
            
            # エンゲージメントスコア = (アクティブユーザー率 * 重み1) + (メッセージ密度 * 重み2)
            active_ratio = (active_users / member_count) * 100
            message_density = daily_messages / member_count if member_count > 0 else 0
            
            # 設定から重みを取得
            active_weight = self.ENGAGEMENT_WEIGHTS["active_ratio_weight"]
            message_weight = self.ENGAGEMENT_WEIGHTS["message_density_weight"]
            
            engagement_score = (active_ratio * active_weight) + (message_density * message_weight)
            
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
            
            # リアクション統計を取得
            reaction_stats = self.get_daily_reaction_stats()
            
            # ロールメンバー数を取得
            role_counts = await self.count_role_members(guild)
            
            # 基本メトリクス収集
            member_count = guild.member_count
            online_count = len([m for m in guild.members if m.status != discord.Status.offline])
            active_users = await self.count_active_users(guild)
            
            # 24時間分の時間別ガントチャートデータを統合
            gantt_chart_data = await self.compile_daily_gantt_data(guild)
            
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
                'role_counts': role_counts,
                'reaction_stats': reaction_stats,
                'gantt_chart_data': gantt_chart_data
            }
            
            logger.info(f"✅ メトリクス収集完了: {metrics['date']}")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ メトリクス収集エラー: {e}")
            return None
    
    async def save_metrics_to_db(self, metrics: dict) -> bool:
        """メトリクスをデータベースとダッシュボードに保存"""
        # 1. ダッシュボードAPI送信
        dashboard_success = await self.send_to_dashboard(metrics)
        
        # 2. データベース保存
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
                reaction_stats_json = json.dumps(metrics['reaction_stats'])
                
                # テーブルにreaction_statsカラムが存在するかチェック
                column_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'discord_metrics' 
                        AND column_name = 'reaction_stats'
                    )
                """)
                
                if column_exists:
                    # reaction_statsカラムが存在する場合
                    result = await conn.execute("""
                        INSERT INTO discord_metrics 
                        (id, date, member_count, online_count, daily_messages, active_users, 
                         engagement_score, daily_user_messages, daily_staff_messages,
                         channel_message_stats, staff_channel_stats, role_counts, reaction_stats,
                         created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
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
                        reaction_stats = $13,
                        updated_at = NOW()
                    """, cuid, metrics['date'], metrics['member_count'], 
                        metrics['online_count'], metrics['daily_messages'], 
                        metrics['active_users'], metrics['engagement_score'],
                        metrics['daily_user_messages'], metrics['daily_staff_messages'],
                        channel_stats_json, staff_stats_json, role_counts_json, reaction_stats_json)
                else:
                    # reaction_statsカラムが存在しない場合（従来の形式で保存）
                    logger.warning("⚠️ reaction_statsカラムが存在しません。リアクション統計はスキップされます。")
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
                
                # 結果判定
                if dashboard_success:
                    logger.info("✅ ダッシュボード・データベース両方に保存成功")
                    return True
                else:
                    logger.warning("⚠️ データベース保存成功、ダッシュボード送信失敗")
                    return True  # データベース保存は成功しているため True を返す
                    
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ データベース保存エラー: {e}")
            if dashboard_success:
                logger.warning("⚠️ ダッシュボード送信成功、データベース保存失敗")
            return False
    
    async def get_recent_metrics(self, days: int = 7) -> list:
        """最近のメトリクスデータを取得"""
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                # 過去N日間のデータを取得
                rows = await conn.fetch("""
                    SELECT * FROM discord_metrics 
                    WHERE date >= CURRENT_DATE - INTERVAL %s
                    ORDER BY date DESC
                """ % f"'{days} days'")
                
                print(f"🔍 [METRICS] データ取得: {len(rows)}件 (過去{days}日間)")
                for row in rows:
                    print(f"  📅 {row['date']}: メンバー{row['member_count']}人, メッセージ{row['daily_messages']}件")
                
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
            # 手動実行時はリセットしない（定期実行時のみリセット）
            
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
            
            # リアクション統計
            if metrics['reaction_stats'] and self.REACTION_CONFIG["enabled"]:
                reaction_stats = metrics['reaction_stats']
                embed.add_field(
                    name="👍 リアクション総数", 
                    value=f"{reaction_stats.get('total_reactions', 0):,}", 
                    inline=True
                )
                embed.add_field(
                    name="😊 使用絵文字数", 
                    value=f"{reaction_stats.get('unique_emojis', 0):,}", 
                    inline=True
                )
                embed.add_field(
                    name="🙋 リアクションユーザー", 
                    value=f"{reaction_stats.get('reaction_users', 0):,}人", 
                    inline=True
                )
                
                # 人気絵文字トップ5
                if reaction_stats.get('top_emojis'):
                    top_emojis_text = "\n".join([f"{data['emoji']}: {data['count']}回" 
                                               for data in reaction_stats['top_emojis'][:5]])
                    embed.add_field(name="🔥 人気絵文字トップ5", value=top_emojis_text, inline=False)
            
            # ガントチャートデータ（24時間分の統合データ）
            if metrics['gantt_chart_data']:
                gantt_data = metrics['gantt_chart_data']
                embed.add_field(
                    name="👥 本日のユニークユーザー", 
                    value=f"{gantt_data.get('total_unique_users_today', 0)}人", 
                    inline=True
                )
                
                # ピーク時間帯
                peak_hour = gantt_data.get('peak_hour')
                peak_count = gantt_data.get('peak_online_count', 0)
                if peak_hour:
                    embed.add_field(
                        name="📈 ピーク時間帯",
                        value=f"{peak_hour} ({peak_count}人)",
                        inline=True
                    )
                
                # データ収集カバレッジ
                coverage = gantt_data.get('data_coverage', 0)
                embed.add_field(
                    name="📊 データ収集状況",
                    value=f"{coverage}/24時間",
                    inline=True
                )
                
                # ロール別日次サマリー
                role_summary = gantt_data.get('role_daily_summary', {})
                if role_summary:
                    top_active_roles = sorted(
                        [(role_id, data) for role_id, data in role_summary.items()],
                        key=lambda x: x[1]['activity_rate'],
                        reverse=True
                    )[:5]
                    
                    role_text = "\n".join([
                        f"{data['role_name']}: {data['unique_active_users']}人 ({data['activity_rate']:.1f}%)"
                        for role_id, data in top_active_roles
                        if data['unique_active_users'] > 0
                    ])
                    
                    if role_text:
                        embed.add_field(
                            name="🏷️ ロール別日次アクティブ率",
                            value=role_text,
                            inline=False
                        )
            
            # 現在のカウント状況（リセットしていないため継続中）
            current_user = sum(sum(users.values()) for users in self.message_counts.values())
            current_staff = sum(sum(users.values()) for users in self.staff_message_counts.values())
            current_reactions = sum(sum(emojis.values()) for emojis in self.reaction_counts.values())
            embed.add_field(
                name="📊 現在の累計カウント",
                value=f"ユーザー: {current_user}件\n運営: {current_staff}件\nリアクション: {current_reactions}件\n（次回0:00にリセット）",
                inline=False
            )
            
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
            print(f"🔗 DB接続テスト開始...")
            print(f"🔗 self.db_url: {repr(self.db_url)}")
            print(f"🔗 URL長さ: {len(self.db_url) if self.db_url else 0}")
            print(f"🔗 URLの最初50文字: {self.db_url[:50] if self.db_url else 'None'}")
            
            # 環境変数を直接確認
            import os
            direct_url = os.getenv('NEON_DATABASE_URL')
            print(f"🔗 直接環境変数: {repr(direct_url)}")
            print(f"🔗 直接環境変数長さ: {len(direct_url) if direct_url else 0}")
            
            if not self.db_url:
                await interaction.followup.send("❌ NEON_DATABASE_URL 環境変数が設定されていません")
                return
                
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
            print(f"❌ DB接続エラー詳細: {type(e).__name__}: {str(e)}")
            print(f"❌ エラー引数: {e.args}")
            print(f"❌ エラー詳細情報: {repr(e)}")
            await interaction.followup.send(f"❌ DB接続エラー: {str(e)}\n詳細: {type(e).__name__}")
    
    @tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone(timedelta(hours=9))))  # 日本時間0:00に実行
    async def daily_metrics_task(self):
        """定期的にメトリクスを収集（日本時間0:00）"""
        print(f"⏰ [METRICS] 定期メトリクス収集開始（日本時間0:00）...")
        logger.info("⏰ 定期メトリクス収集開始（日本時間0:00）...")
        
        metrics = await self.collect_daily_metrics()
        if metrics:
            print(f"📊 [METRICS] メトリクス収集完了: ユーザー{metrics['daily_user_messages']}件, 運営{metrics['daily_staff_messages']}件")
            success = await self.save_metrics_to_db(metrics)
            if success:
                print(f"✅ [METRICS] データベース保存成功")
                # 日次カウントをリセット
                self.reset_daily_counts()
                logger.info("✅ 定期メトリクス収集・保存完了")
            else:
                print(f"❌ [METRICS] データベース保存失敗")
                logger.error("❌ 定期メトリクス保存失敗")
        else:
            print(f"❌ [METRICS] メトリクス収集失敗")
    
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
        
        # リアクション統計
        reaction_total = sum(sum(emojis.values()) for emojis in self.reaction_counts.values())
        reaction_users = len([count for count in self.user_reaction_counts.values() if count > 0])
        unique_emojis = len(set(emoji for emojis in self.reaction_counts.values() for emoji in emojis.keys()))
        
        # 基本統計
        embed.add_field(
            name="📈 メッセージ統計",
            value=f"ユーザー: {user_total}件\n運営: {staff_total}件\n合計: {user_total + staff_total}件",
            inline=True
        )
        
        if self.REACTION_CONFIG["enabled"]:
            embed.add_field(
                name="👍 リアクション統計",
                value=f"総数: {reaction_total}件\nユーザー: {reaction_users}人\n絵文字: {unique_emojis}種類",
                inline=True
            )
        
        embed.add_field(
            name="👥 アクティブ",
            value=f"ユーザー: {active_users}人\nチャンネル: {len(self.message_counts) + len(self.staff_message_counts)}",
            inline=True
        )
        
        # チャンネル別詳細
        if user_details:
            embed.add_field(
                name="📍 ユーザーメッセージ詳細",
                value="\n".join(user_details[:5]),
                inline=False
            )
        
        if staff_details:
            embed.add_field(
                name="👮 運営メッセージ詳細",
                value="\n".join(staff_details[:5]),
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @discord.app_commands.command(name="metrics_config", description="メトリクス設定を表示")
    @discord.app_commands.default_permissions(administrator=True)
    async def show_metrics_config(self, interaction: discord.Interaction):
        """現在のメトリクス設定を表示"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="⚙️ メトリクス設定",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        # メインロール設定
        viewable_role = interaction.guild.get_role(self.VIEWABLE_ROLE_ID)
        staff_role = interaction.guild.get_role(self.STAFF_ROLE_ID)
        
        embed.add_field(
            name="🔧 メインロール設定",
            value=f"閲覧可能ロール: {viewable_role.name if viewable_role else 'Unknown'} (ID: {self.VIEWABLE_ROLE_ID})\n"
                  f"運営ロール: {staff_role.name if staff_role else 'Unknown'} (ID: {self.STAFF_ROLE_ID})",
            inline=False
        )
        
        # 集計対象ロール
        tracked_roles_text = []
        for role_id, role_name in self.ROLE_NAMES.items():
            role = interaction.guild.get_role(role_id)
            actual_name = role.name if role else "Not Found"
            member_count = len(role.members) if role else 0
            tracked_roles_text.append(f"• {role_name}: {member_count}人 ({actual_name})")
        
        embed.add_field(
            name="📊 集計対象ロール",
            value="\n".join(tracked_roles_text[:10]),  # 最大10件表示
            inline=False
        )
        
        # エンゲージメント設定
        embed.add_field(
            name="📈 エンゲージメント計算設定",
            value=f"アクティブ率重み: {self.ENGAGEMENT_WEIGHTS['active_ratio_weight']}\n"
                  f"メッセージ密度重み: {self.ENGAGEMENT_WEIGHTS['message_density_weight']}",
            inline=True
        )
        
        # 収集スケジュール
        schedule = METRICS_CONFIG["collection_schedule"]
        embed.add_field(
            name="⏰ 収集スケジュール",
            value=f"タイムゾーン: {schedule['timezone']}\n"
                  f"実行時刻: 毎日 {schedule['daily_hour']:02d}:{schedule['daily_minute']:02d}",
            inline=True
        )
        
        # リアクション追跡設定
        reaction_config = METRICS_CONFIG["reaction_tracking"]
        embed.add_field(
            name="👍 リアクション追跡設定",
            value=f"機能: {'有効' if reaction_config['enabled'] else '無効'}\n"
                  f"カスタム絵文字: {'追跡' if reaction_config['track_custom_emojis'] else '除外'}\n"
                  f"除外チャンネル: {len(reaction_config['excluded_channels'])}件\n"
                  f"メッセージ対象期間: {reaction_config['max_message_age_days']}日\n"
                  f"トップ絵文字表示数: {reaction_config['top_emojis_limit']}件",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)
    
    @discord.app_commands.command(name="metrics_reactions", description="リアクション統計を詳細表示")
    @discord.app_commands.default_permissions(administrator=True)
    async def show_reaction_metrics(self, interaction: discord.Interaction):
        """リアクション統計を詳細表示"""
        await interaction.response.defer()
        
        if not self.REACTION_CONFIG["enabled"]:
            await interaction.followup.send("❌ リアクション追跡機能が無効になっています")
            return
        
        embed = discord.Embed(
            title="👍 リアクション統計詳細",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        # 全体統計
        total_reactions = sum(sum(emojis.values()) for emojis in self.reaction_counts.values())
        total_reaction_users = len([count for count in self.user_reaction_counts.values() if count > 0])
        unique_emojis = len(set(emoji for emojis in self.reaction_counts.values() for emoji in emojis.keys()))
        
        embed.add_field(
            name="📊 全体統計",
            value=f"総リアクション数: {total_reactions:,}件\nリアクションユーザー: {total_reaction_users:,}人\n使用絵文字数: {unique_emojis:,}種類",
            inline=False
        )
        
        # チャンネル別リアクション統計
        channel_details = []
        for channel_id, emojis in self.reaction_counts.items():
            channel = interaction.guild.get_channel(int(channel_id))
            channel_name = channel.name if channel else f"Unknown({channel_id})"
            channel_total = sum(emojis.values())
            channel_unique = len(emojis)
            if channel_total > 0:
                channel_details.append(f"{channel_name}: {channel_total}件 ({channel_unique}種類)")
        
        if channel_details:
            embed.add_field(
                name="📍 チャンネル別リアクション",
                value="\n".join(channel_details[:10]),  # 最大10チャンネル表示
                inline=False
            )
        
        # 人気絵文字ランキング
        all_emoji_counts = defaultdict(int)
        for emojis in self.reaction_counts.values():
            for emoji, count in emojis.items():
                all_emoji_counts[emoji] += count
        
        if all_emoji_counts:
            top_emojis = sorted(all_emoji_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            emoji_ranking = "\n".join([f"{i+1}. {emoji}: {count}回" 
                                     for i, (emoji, count) in enumerate(top_emojis)])
            embed.add_field(
                name="🏆 人気絵文字ランキング",
                value=emoji_ranking,
                inline=False
            )
        
        # 設定情報
        embed.add_field(
            name="⚙️ 設定",
            value=f"カスタム絵文字追跡: {'有効' if self.REACTION_CONFIG['track_custom_emojis'] else '無効'}\n"
                  f"除外チャンネル: {len(self.REACTION_CONFIG['excluded_channels'])}件\n"
                  f"メッセージ対象期間: {self.REACTION_CONFIG['max_message_age_days']}日",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)
    
    @discord.app_commands.command(name="online_gantt_test", description="現在のオンライン状況をガントチャート用データとして表示（テスト）")
    @discord.app_commands.default_permissions(administrator=True)
    async def online_gantt_test(self, interaction: discord.Interaction):
        """現在のオンライン状況をガントチャート用データとして表示（テスト用）"""
        await interaction.response.defer()
        
        try:
            guild = interaction.guild
            gantt_data = await self.collect_gantt_chart_data(guild)
            
            if not gantt_data:
                await interaction.followup.send("❌ データの取得に失敗しました")
                return
            
            # メイン統計表示
            embed = discord.Embed(
                title="🕐 現在のオンライン状況（ガントチャート用データ）",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # 基本統計
            embed.add_field(
                name="📊 基本統計",
                value=f"オンライン総数: {gantt_data['total_online_users']}人\n"
                      f"データ取得時刻: {gantt_data['timestamp'][:19]}Z",
                inline=False
            )
            
            # ステータス別
            status_breakdown = gantt_data.get('status_breakdown', {})
            if status_breakdown:
                status_text = "\n".join([
                    f"{status.capitalize()}: {count}人"
                    for status, count in status_breakdown.items()
                    if count > 0
                ])
                embed.add_field(name="🟢 ステータス別", value=status_text, inline=True)
            
            # アクティビティ別
            activity_breakdown = gantt_data.get('activity_breakdown', {})
            if activity_breakdown:
                activity_text = "\n".join([
                    f"{activity.capitalize()}: {count}人"
                    for activity, count in sorted(activity_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
                ])
                embed.add_field(name="🎮 アクティビティ別", value=activity_text, inline=True)
            
            # ロール別オンライン率トップ5
            top_roles = gantt_data.get('top_active_roles', [])
            if top_roles:
                role_text = "\n".join([
                    f"**{role['role_name']}**\n{role['online_count']}人 ({role['online_rate']:.1f}%)"
                    for role in top_roles[:5]
                ])
                embed.add_field(name="🏷️ アクティブロールトップ5", value=role_text, inline=False)
            
            await interaction.followup.send(embed=embed)
            
            # オンラインユーザー詳細を別メッセージで送信
            online_users = gantt_data.get('online_users', [])
            if online_users:
                # ロール1332242428459221046を持つユーザーを特別表示
                target_role_id = "1332242428459221046"
                target_role_users = [
                    user for user in online_users 
                    if target_role_id in user['role_ids']
                ]
                
                detail_embed = discord.Embed(
                    title="👥 オンラインユーザー詳細",
                    color=discord.Color.blue()
                )
                
                # 全ユーザー（最初の10人）
                all_users_text = "\n".join([
                    f"**{user['display_name']}** ({user['status']})"
                    + (f" - {user['activity_name']}" if user['activity_name'] else "")
                    for user in online_users[:10]
                ])
                detail_embed.add_field(
                    name=f"🌐 全オンラインユーザー（最初の10人）",
                    value=all_users_text or "なし",
                    inline=False
                )
                
                # 特定ロールのユーザー
                if target_role_users:
                    target_role = guild.get_role(int(target_role_id))
                    role_name = target_role.name if target_role else f"ロールID: {target_role_id}"
                    
                    target_users_text = "\n".join([
                        f"**{user['display_name']}** ({user['status']})"
                        + (f" - {user['activity_name']}" if user['activity_name'] else "")
                        + f" | ロール: {', '.join(user['role_names'][:2])}"
                        for user in target_role_users[:10]
                    ])
                    detail_embed.add_field(
                        name=f"🎯 {role_name} のオンラインユーザー（{len(target_role_users)}人）",
                        value=target_users_text,
                        inline=False
                    )
                
                # JSON形式のサンプル
                sample_user = online_users[0] if online_users else {}
                json_sample = {
                    'user_id': sample_user.get('user_id', 'sample_id'),
                    'display_name': sample_user.get('display_name', 'Sample User'),
                    'status': sample_user.get('status', 'online'),
                    'role_ids': sample_user.get('role_ids', []),
                    'timestamp': sample_user.get('timestamp', '')
                }
                
                detail_embed.add_field(
                    name="📋 データ形式サンプル",
                    value=f"```json\n{json.dumps(json_sample, indent=2, ensure_ascii=False)[:500]}```",
                    inline=False
                )
                
                await interaction.followup.send(embed=detail_embed)
            
        except Exception as e:
            logger.error(f"❌ ガントチャートテスト表示エラー: {e}")
            await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}")
    
    @discord.app_commands.command(name="role_filter_test", description="特定ロールのオンライン状況をテスト表示")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(role="フィルタリングするロール")
    async def role_filter_test(self, interaction: discord.Interaction, role: discord.Role):
        """特定ロールのオンライン状況をテスト表示"""
        await interaction.response.defer()
        
        try:
            gantt_data = await self.collect_gantt_chart_data(interaction.guild)
            
            if not gantt_data:
                await interaction.followup.send("❌ データの取得に失敗しました")
                return
            
            # 指定ロールのユーザーをフィルタリング
            online_users = gantt_data.get('online_users', [])
            role_users = [
                user for user in online_users 
                if str(role.id) in user['role_ids']
            ]
            
            embed = discord.Embed(
                title=f"🏷️ ロール「{role.name}」のオンライン状況",
                color=role.color or discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # 基本統計
            total_role_members = len(role.members)
            online_role_members = len(role_users)
            online_rate = (online_role_members / total_role_members * 100) if total_role_members > 0 else 0
            
            embed.add_field(
                name="📊 統計",
                value=f"総メンバー数: {total_role_members}人\n"
                      f"オンライン: {online_role_members}人\n"
                      f"オンライン率: {online_rate:.1f}%",
                inline=True
            )
            
            # ステータス別集計
            if role_users:
                status_counts = {}
                activity_counts = {}
                
                for user in role_users:
                    status = user['status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    if user['activity_type']:
                        activity = user['activity_type']
                        activity_counts[activity] = activity_counts.get(activity, 0) + 1
                
                status_text = "\n".join([
                    f"{status.capitalize()}: {count}人"
                    for status, count in status_counts.items()
                ])
                embed.add_field(name="🟢 ステータス別", value=status_text, inline=True)
                
                if activity_counts:
                    activity_text = "\n".join([
                        f"{activity.capitalize()}: {count}人"
                        for activity, count in sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                    ])
                    embed.add_field(name="🎮 アクティビティ", value=activity_text, inline=True)
                
                # オンラインユーザー一覧
                users_text = "\n".join([
                    f"**{user['display_name']}** ({user['status']})"
                    + (f" - {user['activity_name']}" if user['activity_name'] else "")
                    for user in role_users[:15]
                ])
                
                if len(role_users) > 15:
                    users_text += f"\n... 他 {len(role_users) - 15}人"
                
                embed.add_field(
                    name=f"👥 オンラインメンバー ({len(role_users)}人)",
                    value=users_text or "なし",
                    inline=False
                )
            else:
                embed.add_field(
                    name="結果",
                    value="このロールのオンラインメンバーはいません",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"❌ ロールフィルターテスト表示エラー: {e}")
            await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}")
    
    @discord.app_commands.command(name="hourly_gantt_status", description="時間別ガントチャートデータの蓄積状況を確認")
    @discord.app_commands.default_permissions(administrator=True)
    async def hourly_gantt_status(self, interaction: discord.Interaction):
        """時間別ガントチャートデータの蓄積状況を確認"""
        await interaction.response.defer()
        
        try:
            current_time = datetime.now(timezone.utc)
            current_hour = current_time.hour
            
            embed = discord.Embed(
                title="⏰ 時間別ガントチャートデータ蓄積状況",
                color=discord.Color.blue(),
                timestamp=current_time
            )
            
            # 基本情報
            stored_hours = sorted(self.hourly_gantt_data.keys())
            
            # 対象ロール情報
            target_role_names = []
            for role_id in self.GANTT_CONFIG["target_roles"]:
                role = interaction.guild.get_role(role_id)
                if role:
                    target_role_names.append(f"{role.name}({len([m for m in role.members if not m.bot])}人)")
            
            embed.add_field(
                name="📊 蓄積状況",
                value=f"現在時刻: {current_hour}:00\n"
                      f"蓄積時間数: {len(stored_hours)}/24時間\n"
                      f"対象ロール: {', '.join(target_role_names) if target_role_names else 'なし'}\n"
                      f"蓄積データ: {stored_hours}",
                inline=False
            )
            
            # 各時間のデータ詳細
            if self.hourly_gantt_data:
                hourly_details = []
                for hour in range(24):
                    if hour in self.hourly_gantt_data:
                        data = self.hourly_gantt_data[hour]
                        online_count = data.get('total_online_users', 0)
                        timestamp = data.get('timestamp', '')[:16] if data.get('timestamp') else ''
                        hourly_details.append(f"{hour:02d}:00 - {online_count}人 ({timestamp})")
                    else:
                        hourly_details.append(f"{hour:02d}:00 - データなし")
                
                # 12時間ずつ分けて表示
                embed.add_field(
                    name="🌅 午前（0-11時）",
                    value="\n".join(hourly_details[:12]),
                    inline=True
                )
                embed.add_field(
                    name="🌆 午後（12-23時）",
                    value="\n".join(hourly_details[12:]),
                    inline=True
                )
            else:
                embed.add_field(
                    name="⚠️ 状況",
                    value="時間別データが蓄積されていません",
                    inline=False
                )
            
            # タスク状況
            task_status = "実行中" if self.hourly_gantt_collection_task.is_running() else "停止中"
            next_run = self.hourly_gantt_collection_task.next_iteration
            next_run_str = next_run.strftime('%H:%M:%S') if next_run else "不明"
            
            embed.add_field(
                name="🔧 タスク状況",
                value=f"収集タスク: {task_status}\n"
                      f"次回実行: {next_run_str}",
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"❌ 時間別状況確認エラー: {e}")
            await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}")

async def setup(bot):
    """Cogのセットアップ"""
    await bot.add_cog(MetricsCollector(bot))