from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    language = Column(String, default='ru')
    level = Column(String, default='A2')
    daily_words = Column(Integer, default=10)
    streak = Column(Integer, default=0)
    last_active = Column(DateTime, default=datetime.utcnow)
    notification_time = Column(String, default='09:00')
    notification_enabled = Column(Boolean, default=True)
    audio_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default={})
    
    progress = relationship("UserWordProgress", back_populates="user", cascade="all, delete-orphan")
    stats = relationship("UserStats", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Word(Base):
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    transcription = Column(String)
    example = Column(String)
    example_translation = Column(String)
    level = Column(String)
    part_of_speech = Column(String)
    topic = Column(String)
    frequency = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    progress = relationship("UserWordProgress", back_populates="word", cascade="all, delete-orphan")

class UserWordProgress(Base):
    __tablename__ = 'user_word_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'))
    stage = Column(Integer, default=0)
    next_review = Column(DateTime, default=datetime.utcnow)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime)
    first_seen = Column(DateTime, default=datetime.utcnow)
    mastered_at = Column(DateTime)
    
    user = relationship("User", back_populates="progress")
    word = relationship("Word", back_populates="progress")

class UserStats(Base):
    __tablename__ = 'user_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    total_reviews = Column(Integer, default=0)
    correct_reviews = Column(Integer, default=0)
    total_words_learned = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_time_spent = Column(Integer, default=0)
    last_week_activity = Column(JSON, default=lambda: [0] * 7)
    achievements = Column(JSON, default=list)
    
    user = relationship("User", back_populates="stats")