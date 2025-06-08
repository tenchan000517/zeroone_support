# -*- coding:utf-8 -*-
from sqlalchemy import Column, String, Integer, Boolean, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

class DailyContentSettings(Base):
    __tablename__ = 'daily_content_settings'
    
    guild_id = Column(String, primary_key=True)
    
    # チャンネル設定
    channel_id = Column(String, nullable=True)  # 送信先チャンネルID
    mention_target = Column(String, nullable=True)  # メンション対象（role_id, @everyone, None）
    
    # 起業家格言の設定
    quotes_enabled = Column(Boolean, default=True)
    quotes_hour = Column(Integer, default=9)
    quotes_minute = Column(Integer, default=0)
    
    # スキルアップTipsの設定
    tips_enabled = Column(Boolean, default=True)
    tips_hour = Column(Integer, default=18)
    tips_minute = Column(Integer, default=0)
    
    # 今日のチャレンジの設定
    challenge_enabled = Column(Boolean, default=True)
    challenge_hour = Column(Integer, default=10)
    challenge_minute = Column(Integer, default=0)
    
    # ビジネストレンドの設定
    trends_enabled = Column(Boolean, default=True)
    trends_hour = Column(Integer, default=8)
    trends_minute = Column(Integer, default=0)
    trends_days = Column(String, default="1,4")  # 曜日（月曜=0, 火曜=1...）

# データベース設定
engine = create_engine('sqlite:///daily_content.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()