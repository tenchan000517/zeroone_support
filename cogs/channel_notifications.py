"""
Discord Bot - チャンネル通知機能
特定チャンネルでの活動を監視し、LINEボットにリマインド通知を送信
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import logging
from typing import Optional, Dict
from collections import defaultdict

# 設定インポート
from config.config import CHANNEL_NOTIFICATIONS, METRICS_CONFIG

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChannelNotifications(commands.Cog):
    """チャンネル通知機能クラス"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = CHANNEL_NOTIFICATIONS
        
        # 運営ロールID
        self.STAFF_ROLE_ID = METRICS_CONFIG["staff_role_id"]
        
        # 監視データ（メモリ上で管理）
        self.last_user_message = {}  # {channel_id: datetime} - 最後のユーザーメッセージ時刻
        self.last_staff_message = {}  # {channel_id: datetime} - 最後の運営メッセージ時刻
        
        # 監視タスク開始
        if self.config["enabled"] and not self.staff_absence_monitor.is_running():
            self.staff_absence_monitor.start()
        
        logger.info("📢 ChannelNotifications初期化完了")
    
    def cog_unload(self):
        """Cog終了時の処理"""
        self.staff_absence_monitor.cancel()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージ送信時の監視処理"""
        # BOTメッセージは除外
        if message.author.bot:
            return
        
        # 監視機能が無効の場合は処理しない
        if not self.config["enabled"]:
            return
        
        channel_id = str(message.channel.id)
        
        # 監視対象チャンネルかチェック
        if channel_id not in self.config["monitored_channels"]:
            return
        
        channel_config = self.config["monitored_channels"][channel_id]
        guild = message.guild
        
        # 運営ロールチェック
        staff_role = guild.get_role(self.STAFF_ROLE_ID) if guild else None
        is_staff = staff_role in message.author.roles if staff_role else False
        
        print(f"📢 [NOTIFICATIONS] メッセージ検知: {message.author.name} in {channel_config['name']} (運営: {is_staff})")
        
        # チャンネルタイプ別の処理
        await self._process_channel_message(message, channel_config, is_staff)
    
    async def _process_channel_message(self, message, channel_config, is_staff):
        """チャンネルタイプ別のメッセージ処理"""
        channel_type = channel_config["type"]
        channel_id = str(message.channel.id)
        
        if channel_type == "new_member":
            # WELCOM チャンネル - 新規参入通知（運営除外）
            if not is_staff:
                await self._handle_welcome_message(message, channel_config)
            else:
                print(f"👮 [NOTIFICATIONS] 運営発言のため通知スキップ: {message.author.display_name} in {channel_config['name']}")
            
        elif channel_type == "new_post":
            # 自己紹介チャンネル - 新規投稿通知（リプライ・運営除外）
            if not message.reference and not is_staff:  # リプライでない かつ 運営でない場合
                await self._handle_introduction_message(message, channel_config)
            elif is_staff:
                print(f"👮 [NOTIFICATIONS] 運営発言のため通知スキップ: {message.author.display_name} in {channel_config['name']}")
                
        elif channel_type == "staff_absence_monitoring":
            # 雑談チャンネル - 運営不在監視
            await self._handle_chat_monitoring(message, channel_config, is_staff)
            
        elif channel_type == "announcement":
            # 誰でも告知チャンネル - 告知投稿通知（運営除外）
            if not is_staff:
                await self._handle_announcement_message(message, channel_config)
            else:
                print(f"👮 [NOTIFICATIONS] 運営発言のため通知スキップ: {message.author.display_name} in {channel_config['name']}")
    
    async def _handle_welcome_message(self, message, channel_config):
        """WELCOM チャンネルの新規参入通知"""
        notification_data = {
            "type": "new_member",
            "channel": channel_config["name"],
            "user": {
                "name": message.author.display_name,
                "id": str(message.author.id),
                "avatar": str(message.author.avatar) if message.author.avatar else None
            },
            "message": {
                "content": message.content[:200],  # 最大200文字
                "timestamp": message.created_at.isoformat(),
                "jump_url": message.jump_url
            },
            "notification_message": channel_config["notification_message"]
        }
        
        await self._send_notification(notification_data)
        print(f"🎉 [NOTIFICATIONS] 新規参入通知送信: {message.author.display_name}")
    
    async def _handle_introduction_message(self, message, channel_config):
        """自己紹介チャンネルの新規投稿通知"""
        notification_data = {
            "type": "introduction",
            "channel": channel_config["name"],
            "user": {
                "name": message.author.display_name,
                "id": str(message.author.id),
                "avatar": str(message.author.avatar) if message.author.avatar else None
            },
            "message": {
                "content": message.content[:200],  # 最大200文字
                "timestamp": message.created_at.isoformat(),
                "jump_url": message.jump_url
            },
            "notification_message": channel_config["notification_message"]
        }
        
        await self._send_notification(notification_data)
        print(f"📝 [NOTIFICATIONS] 自己紹介通知送信: {message.author.display_name}")
    
    async def _handle_chat_monitoring(self, message, channel_config, is_staff):
        """雑談チャンネルの運営不在監視"""
        channel_id = str(message.channel.id)
        now = datetime.now()
        
        if is_staff:
            # 運営メッセージの場合、運営最終発言時刻を更新
            self.last_staff_message[channel_id] = now
            print(f"👮 [NOTIFICATIONS] 運営発言記録: {message.author.display_name}")
        else:
            # ユーザーメッセージの場合、ユーザー最終発言時刻を更新
            self.last_user_message[channel_id] = now
            print(f"👤 [NOTIFICATIONS] ユーザー発言記録: {message.author.display_name}")
    
    async def _handle_announcement_message(self, message, channel_config):
        """誰でも告知チャンネルの告知投稿通知"""
        notification_data = {
            "type": "announcement",
            "channel": channel_config["name"],
            "user": {
                "name": message.author.display_name,
                "id": str(message.author.id),
                "avatar": str(message.author.avatar) if message.author.avatar else None
            },
            "message": {
                "content": message.content[:300],  # 告知は少し長めに
                "timestamp": message.created_at.isoformat(),
                "jump_url": message.jump_url
            },
            "notification_message": channel_config["notification_message"]
        }
        
        await self._send_notification(notification_data)
        print(f"📢 [NOTIFICATIONS] 告知通知送信: {message.author.display_name}")
    
    @tasks.loop(minutes=10)  # 10分間隔で監視
    async def staff_absence_monitor(self):
        """運営不在監視タスク"""
        if not self.config["enabled"]:
            return
        
        # 雑談チャンネル設定取得
        chat_channel_id = "1236344090086342798"
        chat_config = self.config["monitored_channels"].get(chat_channel_id)
        
        if not chat_config or chat_config["type"] != "staff_absence_monitoring":
            return
        
        now = datetime.now()
        absence_threshold = timedelta(hours=chat_config["staff_absence_hours"])
        
        # 最後のユーザーメッセージから運営不在時間をチェック
        if chat_channel_id in self.last_user_message:
            last_user_time = self.last_user_message[chat_channel_id]
            last_staff_time = self.last_staff_message.get(chat_channel_id, datetime.min)
            
            # ユーザーメッセージ後に運営の応答があるかチェック
            if last_user_time > last_staff_time:
                absence_duration = now - last_user_time
                
                if absence_duration >= absence_threshold:
                    # 運営不在アラート送信
                    await self._send_staff_absence_alert(chat_config, absence_duration)
                    
                    # アラート送信後は運営発言時刻をリセット（重複送信防止）
                    self.last_staff_message[chat_channel_id] = now
    
    async def _send_staff_absence_alert(self, channel_config, absence_duration):
        """運営不在アラート送信"""
        hours = int(absence_duration.total_seconds() // 3600)
        minutes = int((absence_duration.total_seconds() % 3600) // 60)
        
        notification_data = {
            "type": "staff_absence",
            "channel": channel_config["name"],
            "absence_duration": {
                "hours": hours,
                "minutes": minutes,
                "total_minutes": int(absence_duration.total_seconds() // 60)
            },
            "notification_message": f"{channel_config['notification_message']} ({hours}時間{minutes}分経過)"
        }
        
        await self._send_notification(notification_data)
        print(f"⚠️ [NOTIFICATIONS] 運営不在アラート送信: {hours}時間{minutes}分")
    
    @staff_absence_monitor.before_loop
    async def before_staff_absence_monitor(self):
        """タスク開始前の待機"""
        await self.bot.wait_until_ready()
    
    async def _send_notification(self, notification_data):
        """LINE ボットに通知を送信"""
        if not self.config["line_webhook_url"]:
            print("⚠️ [NOTIFICATIONS] LINE Webhook URLが設定されていません")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["line_webhook_url"],
                    json=notification_data,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ LINE通知送信成功: {notification_data['type']}")
                    else:
                        response_text = await response.text()
                        logger.error(f"❌ LINE通知送信失敗({response.status}): {response_text}")
                        
        except Exception as e:
            logger.error(f"❌ LINE通知送信エラー: {type(e).__name__}: {e}")
    
    @discord.app_commands.command(name="notifications_status", description="チャンネル通知機能の状態確認")
    @discord.app_commands.default_permissions(administrator=True)
    async def show_notifications_status(self, interaction: discord.Interaction):
        """通知機能の状態を表示"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="📢 チャンネル通知機能ステータス",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # 基本設定
        embed.add_field(
            name="⚙️ 基本設定",
            value=f"機能: {'有効' if self.config['enabled'] else '無効'}\n"
                  f"LINE連携: {'設定済み' if self.config['line_webhook_url'] else '未設定'}\n"
                  f"監視タスク: {'実行中' if self.staff_absence_monitor.is_running() else '停止中'}",
            inline=False
        )
        
        # 監視チャンネル
        channel_status = []
        for channel_id, config in self.config["monitored_channels"].items():
            channel = interaction.guild.get_channel(int(channel_id))
            channel_name = channel.name if channel else f"Unknown({channel_id})"
            channel_status.append(f"• {config['name']}: {channel_name} ({config['type']})")
        
        embed.add_field(
            name="📍 監視チャンネル",
            value="\n".join(channel_status[:10]) if channel_status else "なし",
            inline=False
        )
        
        # 最新活動
        if self.last_user_message or self.last_staff_message:
            activity_status = []
            for channel_id in set(self.last_user_message.keys()) | set(self.last_staff_message.keys()):
                config = self.config["monitored_channels"].get(channel_id, {})
                channel_name = config.get("name", f"ID:{channel_id}")
                
                last_user = self.last_user_message.get(channel_id)
                last_staff = self.last_staff_message.get(channel_id)
                
                if last_user:
                    activity_status.append(f"👤 {channel_name}: ユーザー {last_user.strftime('%H:%M')}")
                if last_staff:
                    activity_status.append(f"👮 {channel_name}: 運営 {last_staff.strftime('%H:%M')}")
            
            embed.add_field(
                name="🕐 最新活動",
                value="\n".join(activity_status[:8]) if activity_status else "なし",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @discord.app_commands.command(name="notifications_test", description="通知機能のテスト送信")
    @discord.app_commands.default_permissions(administrator=True)
    async def test_notification(self, interaction: discord.Interaction):
        """テスト通知を送信"""
        await interaction.response.defer()
        
        test_data = {
            "type": "test",
            "channel": "テストチャンネル",
            "user": {
                "name": interaction.user.display_name,
                "id": str(interaction.user.id),
                "avatar": str(interaction.user.avatar) if interaction.user.avatar else None
            },
            "message": {
                "content": "これはテスト通知です",
                "timestamp": datetime.now().isoformat(),
                "jump_url": "https://discord.com/channels/test"
            },
            "notification_message": "🧪 テスト通知が送信されました"
        }
        
        await self._send_notification(test_data)
        
        embed = discord.Embed(
            title="🧪 テスト通知送信",
            description="LINE通知のテスト送信を実行しました",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        if self.config["line_webhook_url"]:
            embed.add_field(name="送信先", value="LINE Bot", inline=True)
            embed.add_field(name="状態", value="送信完了", inline=True)
        else:
            embed.add_field(name="⚠️ 警告", value="LINE Webhook URLが未設定", inline=False)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    """Cogのセットアップ"""
    await bot.add_cog(ChannelNotifications(bot))