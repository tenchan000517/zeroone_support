# -*- coding:utf-8 -*-
from models.weekly_settings import WeeklyContentSettings, get_session
import discord
from typing import Optional, List

class WeeklySettingsManager:
    def __init__(self):
        self.weekdays = {
            0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
            4: "friday", 5: "saturday", 6: "sunday"
        }
        self.weekday_names = {
            0: "月曜日", 1: "火曜日", 2: "水曜日", 3: "木曜日",
            4: "金曜日", 5: "土曜日", 6: "日曜日"
        }
        self.content_types = {
            "quotes": "💎 起業家格言",
            "trends": "📊 ビジネストレンド", 
            "tips": "🛠️ スキルアップTips",
            "tech": "🌐 テック・イノベーション",
            "challenge": "🎯 今日のチャレンジ",
            "events": "🎪 地域イベント情報",
            "connpass": "💻 オンライン講座情報",
            "mindset": "🚀 成功マインドセット"
        }
    
    def get_guild_settings(self, guild_id: str) -> WeeklyContentSettings:
        """ギルドの設定を取得（存在しない場合はデフォルト設定で作成）"""
        session = get_session()
        try:
            settings = session.query(WeeklyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings:
                # デフォルト設定で新規作成
                settings = WeeklyContentSettings(guild_id=guild_id)
                session.add(settings)
                session.commit()
            return settings
        finally:
            session.close()
    
    def get_today_content_info(self, guild_id: str, weekday: int) -> dict:
        """今日のコンテンツ情報を取得"""
        session = get_session()
        try:
            settings = session.query(WeeklyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings:
                # デフォルト設定で新規作成
                settings = WeeklyContentSettings(guild_id=guild_id)
                session.add(settings)
                session.commit()
                session.refresh(settings)  # 最新データを取得
            
            weekday_prefix = self.weekdays[weekday]
            
            enabled = getattr(settings, f"{weekday_prefix}_enabled")
            content_type = getattr(settings, f"{weekday_prefix}_content")
            hour = getattr(settings, f"{weekday_prefix}_hour")
            minute = getattr(settings, f"{weekday_prefix}_minute")
            
            return {
                "enabled": enabled,
                "content_type": content_type,
                "hour": hour,
                "minute": minute,
                "weekday_name": self.weekday_names[weekday]
            }
        finally:
            session.close()
    
    def update_channel_settings(self, guild_id: str, channel_id: str = None, mention_target: str = None) -> bool:
        """チャンネルとメンション設定を更新"""
        session = get_session()
        try:
            settings = session.query(WeeklyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings:
                settings = WeeklyContentSettings(guild_id=guild_id)
                session.add(settings)
            
            if channel_id is not None:
                settings.channel_id = channel_id
            if mention_target is not None:
                settings.mention_target = mention_target
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating channel settings: {e}")
            return False
        finally:
            session.close()
    
    def update_regions(self, guild_id: str, regions: List[str]) -> bool:
        """地域設定を更新"""
        session = get_session()
        try:
            settings = session.query(WeeklyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings:
                settings = WeeklyContentSettings(guild_id=guild_id)
                session.add(settings)
            
            settings.regions = ",".join(regions)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating regions: {e}")
            return False
        finally:
            session.close()
    
    def update_weekday_schedule(self, guild_id: str, weekday: int, enabled: bool = None, 
                               content_type: str = None, hour: int = None, minute: int = None) -> bool:
        """特定曜日のスケジュール設定を更新"""
        session = get_session()
        try:
            settings = session.query(WeeklyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings:
                settings = WeeklyContentSettings(guild_id=guild_id)
                session.add(settings)
            
            weekday_prefix = self.weekdays[weekday]
            
            if enabled is not None:
                setattr(settings, f"{weekday_prefix}_enabled", enabled)
            if content_type is not None:
                setattr(settings, f"{weekday_prefix}_content", content_type)
            if hour is not None:
                setattr(settings, f"{weekday_prefix}_hour", hour)
            if minute is not None:
                setattr(settings, f"{weekday_prefix}_minute", minute)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating weekday schedule: {e}")
            return False
        finally:
            session.close()
    
    def get_target_channel(self, guild: discord.Guild, settings: WeeklyContentSettings) -> Optional[discord.TextChannel]:
        """設定に基づいて送信先チャンネルを取得"""
        if settings.channel_id:
            # 指定されたチャンネルIDを使用
            channel = guild.get_channel(int(settings.channel_id))
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        
        # フォールバック: 従来の優先順位
        # 1. システムチャンネル
        if guild.system_channel:
            return guild.system_channel
        
        # 2. general系チャンネル
        for channel in guild.text_channels:
            if any(word in channel.name.lower() for word in ['general', '一般', 'メイン', 'main']):
                return channel
        
        # 3. 最初のテキストチャンネル
        if guild.text_channels:
            return guild.text_channels[0]
        
        return None
    
    def get_mention_text(self, guild: discord.Guild, settings: WeeklyContentSettings) -> str:
        """設定に基づいてメンションテキストを生成"""
        if not settings.mention_target:
            return ""
        
        if settings.mention_target == "@everyone":
            return "@everyone "
        elif settings.mention_target == "@here":
            return "@here "
        else:
            # ロールIDとして処理
            try:
                role = guild.get_role(int(settings.mention_target))
                if role:
                    return f"{role.mention} "
            except ValueError:
                pass
        
        return ""
    
    def get_regions_list(self, guild_id: str) -> List[str]:
        """地域設定をリストで取得"""
        session = get_session()
        try:
            settings = session.query(WeeklyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings or not settings.regions:
                return ["愛知県"]
            return [region.strip() for region in settings.regions.split(",")]
        finally:
            session.close()
    
    def validate_time(self, hour: int, minute: int) -> bool:
        """時刻の妥当性をチェック"""
        return 0 <= hour <= 23 and 0 <= minute <= 59
    
    def format_schedule_info(self, settings: WeeklyContentSettings) -> str:
        """スケジュール情報を整形して返す"""
        info = []
        
        for weekday in range(7):
            weekday_prefix = self.weekdays[weekday]
            weekday_name = self.weekday_names[weekday]
            
            enabled = getattr(settings, f"{weekday_prefix}_enabled")
            content_type = getattr(settings, f"{weekday_prefix}_content")
            hour = getattr(settings, f"{weekday_prefix}_hour")
            minute = getattr(settings, f"{weekday_prefix}_minute")
            
            content_name = self.content_types.get(content_type, content_type)
            
            if enabled:
                info.append(f"{weekday_name}: {content_name} ({hour:02d}:{minute:02d})")
            else:
                info.append(f"{weekday_name}: 無効")
        
        return "\n".join(info)