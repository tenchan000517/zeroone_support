# -*- coding:utf-8 -*-
from datetime import datetime, timedelta
from models.database import SessionLocal, User, PointHistory, ServerSettings
import os
from dotenv import load_dotenv

load_dotenv()

class PointManager:
    def __init__(self):
        self.default_point_name = os.getenv('POINT_NAME', 'ポイント')
        self.default_daily_bonus = int(os.getenv('DAILY_BONUS_AMOUNT', 100))
    
    def get_or_create_user(self, user_id: str) -> User:
        """ユーザーを取得または作成"""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            if not user:
                user = User(user_id=str(user_id), points=0)
                session.add(user)
                session.commit()
            return user
        finally:
            session.close()
    
    def get_server_settings(self, server_id: str) -> ServerSettings:
        """サーバー設定を取得または作成"""
        session = SessionLocal()
        try:
            settings = session.query(ServerSettings).filter_by(server_id=str(server_id)).first()
            if not settings:
                settings = ServerSettings(
                    server_id=str(server_id),
                    point_name=self.default_point_name,
                    daily_bonus_amount=self.default_daily_bonus
                )
                session.add(settings)
                session.commit()
            return settings
        finally:
            session.close()
    
    def get_points(self, user_id: str) -> int:
        """ユーザーのポイントを取得"""
        user = self.get_or_create_user(user_id)
        return user.points
    
    def add_points(self, user_id: str, amount: int, reason: str) -> bool:
        """ポイントを追加"""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            if not user:
                user = User(user_id=str(user_id), points=0)
                session.add(user)
            
            user.points += amount
            
            # 履歴を記録
            history = PointHistory(
                user_id=str(user_id),
                amount=amount,
                reason=reason
            )
            session.add(history)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"ポイント追加エラー: {e}")
            return False
        finally:
            session.close()
    
    def remove_points(self, user_id: str, amount: int, reason: str) -> bool:
        """ポイントを減らす"""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            if not user or user.points < amount:
                return False
            
            user.points -= amount
            
            # 履歴を記録
            history = PointHistory(
                user_id=str(user_id),
                amount=-amount,
                reason=reason
            )
            session.add(history)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"ポイント削除エラー: {e}")
            return False
        finally:
            session.close()
    
    def claim_daily_bonus(self, user_id: str, server_id: str) -> tuple[bool, str]:
        """デイリーボーナスを請求"""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            if not user:
                user = User(user_id=str(user_id), points=0)
                session.add(user)
            
            settings = self.get_server_settings(server_id)
            
            if not settings.daily_bonus_enabled:
                return False, "デイリーボーナスは無効化されています"
            
            # 最後のボーナス取得から24時間経過しているか確認
            now = datetime.utcnow()
            if user.last_daily_bonus:
                time_diff = now - user.last_daily_bonus
                if time_diff < timedelta(hours=24):
                    remaining = timedelta(hours=24) - time_diff
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    return False, f"次のデイリーボーナスまで {hours}時間{minutes}分 です"
            
            # ボーナス付与
            user.points += settings.daily_bonus_amount
            user.last_daily_bonus = now
            
            # 履歴を記録
            history = PointHistory(
                user_id=str(user_id),
                amount=settings.daily_bonus_amount,
                reason="デイリーボーナス"
            )
            session.add(history)
            session.commit()
            
            return True, f"{settings.daily_bonus_amount}{settings.point_name}を獲得しました！"
        except Exception as e:
            session.rollback()
            print(f"デイリーボーナスエラー: {e}")
            return False, "エラーが発生しました"
        finally:
            session.close()
    
    def get_leaderboard(self, limit: int = 10) -> list:
        """ポイントランキングを取得"""
        session = SessionLocal()
        try:
            users = session.query(User).order_by(User.points.desc()).limit(limit).all()
            return [(user.user_id, user.points) for user in users]
        finally:
            session.close()
    
    def set_points(self, user_id: str, amount: int) -> bool:
        """ポイントを直接設定（管理者用）"""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            if not user:
                user = User(user_id=str(user_id), points=amount)
                session.add(user)
            else:
                user.points = amount
            
            # 履歴を記録
            history = PointHistory(
                user_id=str(user_id),
                amount=amount,
                reason="管理者による設定"
            )
            session.add(history)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"ポイント設定エラー: {e}")
            return False
        finally:
            session.close()