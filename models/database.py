# -*- coding:utf-8 -*-
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String, primary_key=True)
    points = Column(Integer, default=0)
    last_daily_bonus = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PointHistory(Base):
    __tablename__ = 'point_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ServerSettings(Base):
    __tablename__ = 'server_settings'
    
    server_id = Column(String, primary_key=True)
    point_name = Column(String, default='ポイント')
    daily_bonus_amount = Column(Integer, default=100)
    daily_bonus_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# データベース接続設定
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_data.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """データベースを初期化"""
    Base.metadata.create_all(bind=engine)