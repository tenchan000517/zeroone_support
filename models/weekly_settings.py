# -*- coding:utf-8 -*-
from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class WeeklyContentSettings(Base):
    __tablename__ = 'weekly_content_settings'
    
    guild_id = Column(String, primary_key=True)
    
    # チャンネル設定
    channel_id = Column(String, nullable=True)  # 送信先チャンネルID
    mention_target = Column(String, nullable=True)  # メンション対象（role_id, @everyone, None）
    
    # 地域設定（イベント情報用）
    regions = Column(String, default="愛知県")  # カンマ区切りで複数地域
    
    # 曜日別コンテンツ設定（デフォルト7:00）
    # 月曜: 起業家格言
    monday_enabled = Column(Boolean, default=True)
    monday_content = Column(String, default="quotes")
    monday_hour = Column(Integer, default=7)
    monday_minute = Column(Integer, default=0)
    
    # 火曜: ビジネストレンド
    tuesday_enabled = Column(Boolean, default=True)
    tuesday_content = Column(String, default="trends")
    tuesday_hour = Column(Integer, default=7)
    tuesday_minute = Column(Integer, default=0)
    
    # 水曜: スキルアップTips
    wednesday_enabled = Column(Boolean, default=True)
    wednesday_content = Column(String, default="tips")
    wednesday_hour = Column(Integer, default=7)
    wednesday_minute = Column(Integer, default=0)
    
    # 木曜: テック・イノベーション
    thursday_enabled = Column(Boolean, default=True)
    thursday_content = Column(String, default="tech")
    thursday_hour = Column(Integer, default=7)
    thursday_minute = Column(Integer, default=0)
    
    # 金曜: 今日のチャレンジ
    friday_enabled = Column(Boolean, default=True)
    friday_content = Column(String, default="challenge")
    friday_hour = Column(Integer, default=7)
    friday_minute = Column(Integer, default=0)
    
    # 土曜: 地域イベント情報
    saturday_enabled = Column(Boolean, default=True)
    saturday_content = Column(String, default="events")
    saturday_hour = Column(Integer, default=7)
    saturday_minute = Column(Integer, default=0)
    
    # 日曜: 成功マインドセット
    sunday_enabled = Column(Boolean, default=True)
    sunday_content = Column(String, default="mindset")
    sunday_hour = Column(Integer, default=7)
    sunday_minute = Column(Integer, default=0)

# データベース設定
engine = create_engine('sqlite:///weekly_content.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()