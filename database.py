from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from datetime import datetime, timedelta
import random
from models import Base, User, Word, UserWordProgress

class Database:
    def __init__(self):
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(
            database_url or 'sqlite:///wordich.db',
            poolclass=NullPool if database_url else None,
            echo=False
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Инициализация словаря при первом запуске
        self._init_dictionary()
    
    def get_session(self):
        return self.Session()
    
    def _init_dictionary(self):
        """Начальное наполнение базы слов"""
        session = self.get_session()
        try:
            # Проверяем, есть ли уже слова
            word_count = session.query(Word).count()
            if word_count == 0:
                # Базовые слова A1-A2 уровня
                words = [
                    # A1 уровень
                    ("hello", "привет", "həˈləʊ", "Hello, how are you?", "Привет, как дела?", "A1", "interjection"),
                    ("goodbye", "до свидания", "ɡʊdˈbaɪ", "Say goodbye to your friends.", "Попрощайся с друзьями.", "A1", "interjection"),
                    ("please", "пожалуйста", "pliːz", "Please sit down.", "Пожалуйста, садитесь.", "A1", "adverb"),
                    ("thank you", "спасибо", "θæŋk juː", "Thank you for your help.", "Спасибо за помощь.", "A1", "phrase"),
                    ("yes", "да", "jes", "Yes, I understand.", "Да, я понимаю.", "A1", "adverb"),
                    ("no", "нет", "nəʊ", "No, I don't want.", "Нет, я не хочу.", "A1", "adverb"),
                    ("cat", "кот", "kæt", "The cat is sleeping.", "Кот спит.", "A1", "noun"),
                    ("dog", "собака", "dɒɡ", "The dog is barking.", "Собака лает.", "A1", "noun"),
                    ("house", "дом", "haʊs", "This is my house.", "Это мой дом.", "A1", "noun"),
                    ("car", "машина", "kɑː", "He has a red car.", "У него красная машина.", "A1", "noun"),
                    # A2 уровень
                    ("beautiful", "красивый", "ˈbjuːtɪfəl", "What a beautiful day!", "Какой прекрасный день!", "A2", "adjective"),
                    ("interesting", "интересный", "ˈɪntrəstɪŋ", "This book is interesting.", "Эта книга интересная.", "A2", "adjective"),
                    ("restaurant", "ресторан", "ˈrestrɒnt", "Let's go to a restaurant.", "Пойдем в ресторан.", "A2", "noun"),
                    ("hospital", "больница", "ˈhɒspɪtəl", "She works in a hospital.", "Она работает в больнице.", "A2", "noun"),
                    ("weather", "погода", "ˈweðə", "The weather is nice today.", "Погода сегодня хорошая.", "A2", "noun"),
                    ("travel", "путешествовать", "ˈtrævəl", "I love to travel.", "Я люблю путешествовать.", "A2", "verb"),
                    ("cook", "готовить", "kʊk", "Can you cook Italian food?", "Ты умеешь готовить итальянскую еду?", "A2", "verb"),
                    ("expensive", "дорогой", "ɪkˈspensɪv", "This phone is expensive.", "Этот телефон дорогой.", "A2", "adjective"),
                    ("cheap", "дешевый", "tʃiːp", "This hotel is cheap.", "Этот отель дешевый.", "A2", "adjective"),
                    ("friendly", "дружелюбный", "ˈfrendli", "The people here are friendly.", "Люди здесь дружелюбные.", "A2", "adjective"),
                ]
                
                for word_data in words:
                    word = Word(
                        word=word_data[0],
                        translation=word_data[1],
                        transcription=word_data[2],
                        example=word_data[3],
                        example_translation=word_data[4],
                        level=word_data[5],
                        part_of_speech=word_data[6]
                    )
                    session.add(word)
                
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error initializing dictionary: {e}")
        finally:
            session.close()
    
    def get_user(self, telegram_id):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            return user
        finally:
            session.close()
    
    def create_user(self, telegram_id, username, first_name, last_name):
        session = self.get_session()
        try:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_daily_words(self, user_id, count=10):
        """Получить слова для ежедневного урока"""
        session = self.get_session()
        try:
            # Слова для повторения (из SRS)
            due_words = session.query(Word).join(UserWordProgress).filter(
                UserWordProgress.user_id == user_id,
                UserWordProgress.next_review <= datetime.utcnow()
            ).order_by(UserWordProgress.next_review).limit(count // 2).all()
            
            # Новые слова
            learned_word_ids = session.query(UserWordProgress.word_id).filter(
                UserWordProgress.user_id == user_id
            ).subquery()
            
            new_words = session.query(Word).filter(
                ~Word.id.in_(learned_word_ids)
            ).limit(count - len(due_words)).all()
            
            return due_words + new_words
        finally:
            session.close()
    
    def update_word_progress(self, user_id, word_id, correct):
        """Обновить прогресс по слову (SRS алгоритм)"""
        session = self.get_session()
        try:
            progress = session.query(UserWordProgress).filter_by(
                user_id=user_id, word_id=word_id
            ).first()
            
            if not progress:
                progress = UserWordProgress(
                    user_id=user_id,
                    word_id=word_id
                )
                session.add(progress)
            
            if correct:
                progress.correct_count += 1
                # SM-2 алгоритм для интервальных повторений
                if progress.stage == 0:
                    progress.stage = 1
                    next_days = 1
                elif progress.stage == 1:
                    progress.stage = 2
                    next_days = 3
                elif progress.stage == 2:
                    progress.stage = 3
                    next_days = 7
                elif progress.stage == 3:
                    progress.stage = 4
                    next_days = 14
                elif progress.stage == 4:
                    progress.stage = 5
                    next_days = 30
                else:
                    next_days = 30
                
                progress.next_review = datetime.utcnow() + timedelta(days=next_days)
            else:
                progress.wrong_count += 1
                progress.stage = max(0, progress.stage - 1)
                progress.next_review = datetime.utcnow() + timedelta(hours=6)
            
            progress.last_reviewed = datetime.utcnow()
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()