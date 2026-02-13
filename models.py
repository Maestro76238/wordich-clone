from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    language = Column(String, default='ru')
    level = Column(String, default='A2')  # A1, A2, B1, B2
    daily_words = Column(Integer, default=10)
    streak = Column(Integer, default=0)
    last_active = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    progress = relationship("UserWordProgress", back_populates="user")

class Word(Base):
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    transcription = Column(String)
    example = Column(String)
    example_translation = Column(String)
    level = Column(String)  # A1, A2, B1, B2
    part_of_speech = Column(String)  # noun, verb, adjective, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    progress = relationship("UserWordProgress", back_populates="word")

class UserWordProgress(Base):
    __tablename__ = 'user_word_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    word_id = Column(Integer, ForeignKey('words.id'))
    stage = Column(Integer, default=0)  # 0-5 для SRS
    next_review = Column(DateTime, default=datetime.utcnow)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="progress")
    word = relationship("Word", back_populates="progress")