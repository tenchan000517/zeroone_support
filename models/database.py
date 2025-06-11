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

class ChannelIntroSettings(Base):
    __tablename__ = 'channel_intro_settings'
    
    guild_id = Column(String, primary_key=True)
    enabled = Column(Boolean, default=False)
    channel_id = Column(String, nullable=True)
    interval_hours = Column(Integer, default=168)  # デフォルト7日 = 168時間
    scheduled_hour = Column(Integer, nullable=True)  # 指定送信時刻（時）
    scheduled_minute = Column(Integer, nullable=True)  # 指定送信時刻（分）
    target_role_id = Column(String, nullable=True)  # 対象ロールID（デフォルト：@everyone）
    last_sent = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# データベース接続設定
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_data.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """データベースを初期化"""
    Base.metadata.create_all(bind=engine)
    migrate_interval_column()

def migrate_interval_column():
    """interval_days を interval_hours に移行"""
    try:
        # SQLite では ALTER TABLE ADD COLUMN のみサポート
        with engine.connect() as conn:
            # SQLAlchemy 2.0 compatibility
            from sqlalchemy import text
            
            # interval_hours カラムが存在するかチェック
            result = conn.execute(text("PRAGMA table_info(channel_intro_settings)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'interval_hours' not in columns:
                print("Migrating channel_intro_settings: adding interval_hours column...")
                
                # interval_hours カラムを追加
                conn.execute(text("ALTER TABLE channel_intro_settings ADD COLUMN interval_hours INTEGER DEFAULT 168"))
                
                # interval_days が存在する場合、データを移行
                if 'interval_days' in columns:
                    print("Migrating data from interval_days to interval_hours...")
                    # interval_days の値を24倍して interval_hours に設定
                    conn.execute(text("""
                        UPDATE channel_intro_settings 
                        SET interval_hours = COALESCE(interval_days * 24, 168)
                        WHERE interval_hours IS NULL OR interval_hours = 168
                    """))
                    conn.commit()
                    print("Migration completed successfully")
                else:
                    conn.commit()
                    print("interval_hours column added with default value")
            
            # 時刻指定フィールドを追加
            columns_updated = False
            if 'scheduled_hour' not in columns:
                print("Adding scheduled_hour column...")
                conn.execute(text("ALTER TABLE channel_intro_settings ADD COLUMN scheduled_hour INTEGER"))
                columns_updated = True
                
            if 'scheduled_minute' not in columns:
                print("Adding scheduled_minute column...")
                conn.execute(text("ALTER TABLE channel_intro_settings ADD COLUMN scheduled_minute INTEGER"))
                columns_updated = True
                
            if 'target_role_id' not in columns:
                print("Adding target_role_id column...")
                conn.execute(text("ALTER TABLE channel_intro_settings ADD COLUMN target_role_id STRING"))
                columns_updated = True
                
            if columns_updated:
                conn.commit()
                print("New columns added successfully")
                    
    except Exception as e:
        print(f"Migration error (might be safe to ignore if column already exists): {e}")