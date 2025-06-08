# -*- coding:utf-8 -*-
from models.daily_settings import DailyContentSettings, get_session
import discord
from typing import Optional

class DailySettingsManager:
    def __init__(self):
        pass
    
    def get_guild_settings(self, guild_id: str) -> DailyContentSettings:
        """ギルドの設定を取得（存在しない場合はデフォルト設定で作成）"""
        session = get_session()
        try:
            settings = session.query(DailyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings:
                # デフォルト設定で新規作成
                settings = DailyContentSettings(guild_id=guild_id)
                session.add(settings)
                session.commit()
            return settings
        finally:
            session.close()
    
    def update_channel_settings(self, guild_id: str, channel_id: str = None, mention_target: str = None) -> bool:
        """チャンネルとメンション設定を更新"""
        session = get_session()
        try:
            settings = session.query(DailyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings:
                settings = DailyContentSettings(guild_id=guild_id)
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
    
    def update_content_schedule(self, guild_id: str, content_type: str, enabled: bool = None, 
                              hour: int = None, minute: int = None, days: str = None) -> bool:
        """コンテンツのスケジュール設定を更新"""
        session = get_session()
        try:
            settings = session.query(DailyContentSettings).filter_by(guild_id=guild_id).first()
            if not settings:
                settings = DailyContentSettings(guild_id=guild_id)
                session.add(settings)
            
            if content_type == "quotes":
                if enabled is not None:
                    settings.quotes_enabled = enabled
                if hour is not None:
                    settings.quotes_hour = hour
                if minute is not None:
                    settings.quotes_minute = minute
            elif content_type == "tips":
                if enabled is not None:
                    settings.tips_enabled = enabled
                if hour is not None:
                    settings.tips_hour = hour
                if minute is not None:
                    settings.tips_minute = minute
            elif content_type == "challenge":
                if enabled is not None:
                    settings.challenge_enabled = enabled
                if hour is not None:
                    settings.challenge_hour = hour
                if minute is not None:
                    settings.challenge_minute = minute
            elif content_type == "trends":
                if enabled is not None:
                    settings.trends_enabled = enabled
                if hour is not None:
                    settings.trends_hour = hour
                if minute is not None:
                    settings.trends_minute = minute
                if days is not None:
                    settings.trends_days = days
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating schedule settings: {e}")
            return False
        finally:
            session.close()
    
    def get_target_channel(self, guild: discord.Guild, settings: DailyContentSettings) -> Optional[discord.TextChannel]:
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
    
    def get_mention_text(self, guild: discord.Guild, settings: DailyContentSettings) -> str:
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
    
    def validate_time(self, hour: int, minute: int) -> bool:
        """時刻の妥当性をチェック"""
        return 0 <= hour <= 23 and 0 <= minute <= 59
    
    def validate_weekdays(self, days_str: str) -> bool:
        """曜日設定の妥当性をチェック"""
        try:
            days = [int(d.strip()) for d in days_str.split(',')]
            return all(0 <= day <= 6 for day in days)
        except:
            return False
    
    def format_schedule_info(self, settings: DailyContentSettings) -> str:
        """スケジュール情報を整形して返す"""
        info = []
        
        if settings.quotes_enabled:
            info.append(f"📝 起業家格言: {settings.quotes_hour:02d}:{settings.quotes_minute:02d}")
        else:
            info.append("📝 起業家格言: 無効")
        
        if settings.tips_enabled:
            info.append(f"🛠️ スキルTips: {settings.tips_hour:02d}:{settings.tips_minute:02d}")
        else:
            info.append("🛠️ スキルTips: 無効")
        
        if settings.challenge_enabled:
            info.append(f"🎯 今日のチャレンジ: {settings.challenge_hour:02d}:{settings.challenge_minute:02d}")
        else:
            info.append("🎯 今日のチャレンジ: 無効")
        
        if settings.trends_enabled:
            days_map = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}
            days = [days_map[int(d)] for d in settings.trends_days.split(',')]
            info.append(f"📊 ビジネストレンド: {settings.trends_hour:02d}:{settings.trends_minute:02d} ({','.join(days)}曜日)")
        else:
            info.append("📊 ビジネストレンド: 無効")
        
        return "\n".join(info)