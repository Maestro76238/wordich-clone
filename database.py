# В начало database.py добавь:
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime, timedelta
from models import Base, User, Word, UserWordProgress, UserStats
from config import Config

class Database:
    def __init__(self):
        database_url = Config.DATABASE_URL
        if database_url and database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(
            database_url or 'sqlite:///wordich.db',
            poolclass=NullPool if database_url else None,
            echo=False
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        self.init_dictionary()
    
    def get_session(self):
        return self.Session()
    
    def init_dictionary(self):
        session = self.get_session()
        try:
            if session.query(Word).count() > 0:
                return
            
            words_data = [
                # A1 - Базовые слова
                ("hello", "привет", "həˈləʊ", "Hello, how are you?", "Привет, как дела?", "A1", "interjection", "greetings", 1000),
                ("goodbye", "до свидания", "ɡʊdˈbaɪ", "Say goodbye to your friends.", "Попрощайся с друзьями.", "A1", "interjection", "greetings", 900),
                ("please", "пожалуйста", "pliːz", "Please sit down.", "Пожалуйста, садитесь.", "A1", "adverb", "politeness", 950),
                ("thank you", "спасибо", "θæŋk juː", "Thank you for your help.", "Спасибо за помощь.", "A1", "phrase", "politeness", 980),
                ("yes", "да", "jes", "Yes, I understand.", "Да, я понимаю.", "A1", "adverb", "basics", 990),
                ("no", "нет", "nəʊ", "No, I don't want.", "Нет, я не хочу.", "A1", "adverb", "basics", 990),
                ("cat", "кот", "kæt", "The cat is sleeping.", "Кот спит.", "A1", "noun", "animals", 800),
                ("dog", "собака", "dɒɡ", "The dog is barking.", "Собака лает.", "A1", "noun", "animals", 850),
                ("house", "дом", "haʊs", "This is my house.", "Это мой дом.", "A1", "noun", "home", 880),
                ("car", "машина", "kɑː", "He has a red car.", "У него красная машина.", "A1", "noun", "transport", 820),
                ("book", "книга", "bʊk", "I read a book.", "Я читаю книгу.", "A1", "noun", "education", 780),
                ("pen", "ручка", "pen", "Give me a pen.", "Дай мне ручку.", "A1", "noun", "education", 700),
                ("water", "вода", "ˈwɔːtə", "I need water.", "Мне нужна вода.", "A1", "noun", "food", 850),
                ("food", "еда", "fuːd", "The food is good.", "Еда хорошая.", "A1", "noun", "food", 860),
                ("school", "школа", "skuːl", "I go to school.", "Я иду в школу.", "A1", "noun", "education", 800),
                
                # A2 - Повседневные слова
                ("beautiful", "красивый", "ˈbjuːtɪfəl", "What a beautiful day!", "Какой прекрасный день!", "A2", "adjective", "description", 750),
                ("interesting", "интересный", "ˈɪntrəstɪŋ", "This book is interesting.", "Эта книга интересная.", "A2", "adjective", "description", 740),
                ("restaurant", "ресторан", "ˈrestrɒnt", "Let's go to a restaurant.", "Пойдем в ресторан.", "A2", "noun", "food", 720),
                ("hospital", "больница", "ˈhɒspɪtəl", "She works in a hospital.", "Она работает в больнице.", "A2", "noun", "places", 680),
                ("weather", "погода", "ˈweðə", "The weather is nice today.", "Погода сегодня хорошая.", "A2", "noun", "nature", 710),
                ("travel", "путешествовать", "ˈtrævəl", "I love to travel.", "Я люблю путешествовать.", "A2", "verb", "travel", 730),
                ("cook", "готовить", "kʊk", "Can you cook Italian food?", "Ты умеешь готовить итальянскую еду?", "A2", "verb", "food", 690),
                ("expensive", "дорогой", "ɪkˈspensɪv", "This phone is expensive.", "Этот телефон дорогой.", "A2", "adjective", "shopping", 700),
                ("cheap", "дешевый", "tʃiːp", "This hotel is cheap.", "Этот отель дешевый.", "A2", "adjective", "shopping", 680),
                ("friendly", "дружелюбный", "ˈfrendli", "The people here are friendly.", "Люди здесь дружелюбные.", "A2", "adjective", "people", 720),
                
                # B1 - Средний уровень
                ("achieve", "достигать", "əˈtʃiːv", "You can achieve anything.", "Ты можешь достичь всего.", "B1", "verb", "success", 650),
                ("benefit", "польза", "ˈbenɪfɪt", "Regular exercise has many benefits.", "Регулярные упражнения приносят много пользы.", "B1", "noun", "health", 630),
                ("challenge", "вызов", "ˈtʃælɪndʒ", "Learning a language is a challenge.", "Изучение языка - это вызов.", "B1", "noun", "learning", 640),
                ("develop", "развивать", "dɪˈveləp", "We need to develop new skills.", "Нам нужно развивать новые навыки.", "B1", "verb", "growth", 660),
                ("environment", "окружающая среда", "ɪnˈvaɪrənmənt", "We must protect the environment.", "Мы должны защищать окружающую среду.", "B1", "noun", "nature", 620),
                ("government", "правительство", "ˈɡʌvənmənt", "The government makes laws.", "Правительство создает законы.", "B1", "noun", "politics", 600),
                ("important", "важный", "ɪmˈpɔːtnt", "This is very important.", "Это очень важно.", "B1", "adjective", "basics", 700),
                ("knowledge", "знания", "ˈnɒlɪdʒ", "Knowledge is power.", "Знания - сила.", "B1", "noun", "learning", 680),
                ("language", "язык", "ˈlæŋɡwɪdʒ", "English is a global language.", "Английский - глобальный язык.", "B1", "noun", "learning", 710),
                ("opportunity", "возможность", "ˌɒpəˈtjuːnəti", "Take every opportunity.", "Используй каждую возможность.", "B1", "noun", "success", 650),
                
                # B2 - Выше среднего
                ("accommodation", "жилье", "əˌkɒməˈdeɪʃn", "We need to find accommodation.", "Нам нужно найти жилье.", "B2", "noun", "travel", 550),
                ("approximately", "приблизительно", "əˈprɒksɪmətli", "Approximately 100 people came.", "Пришло приблизительно 100 человек.", "B2", "adverb", "numbers", 520),
                ("consequence", "последствие", "ˈkɒnsɪkwəns", "Think about the consequences.", "Подумай о последствиях.", "B2", "noun", "logic", 530),
                ("demonstrate", "демонстрировать", "ˈdemənstreɪt", "Let me demonstrate how it works.", "Позволь мне продемонстрировать, как это работает.", "B2", "verb", "teaching", 540),
                ("especially", "особенно", "ɪˈspeʃəli", "I love fruits, especially apples.", "Я люблю фрукты, особенно яблоки.", "B2", "adverb", "emphasis", 560),
                ("furthermore", "кроме того", "ˌfɜːðəˈmɔː", "Furthermore, we need more time.", "Кроме того, нам нужно больше времени.", "B2", "adverb", "writing", 510),
                ("generally", "в целом", "ˈdʒenrəli", "Generally, it's a good idea.", "В целом, это хорошая идея.", "B2", "adverb", "opinion", 520),
                ("however", "однако", "haʊˈevə", "However, we must be careful.", "Однако мы должны быть осторожны.", "B2", "adverb", "contrast", 580),
                ("incredible", "невероятный", "ɪnˈkredəbl", "That's incredible news!", "Это невероятные новости!", "B2", "adjective", "emotion", 550),
                ("nevertheless", "тем не менее", "ˌnevəðəˈles", "Nevertheless, we succeeded.", "Тем не менее, мы добились успеха.", "B2", "adverb", "contrast", 500),
            ]
            
            for wd in words_data:
                word = Word(
                    word=wd[0], translation=wd[1], transcription=wd[2],
                    example=wd[3], example_translation=wd[4], level=wd[5],
                    part_of_speech=wd[6], topic=wd[7], frequency=wd[8]
                )
                session.add(word)
            
            session.commit()
            print(f"Dictionary initialized with {len(words_data)} words")
            
        except Exception as e:
            session.rollback()
            print(f"Error initializing dictionary: {e}")
        finally:
            session.close()
    
    def get_or_create_user(self, telegram_id, username=None, first_name=None, last_name=None):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                session.flush()
                
                stats = UserStats(user_id=user.id)
                session.add(stats)
                session.commit()
                
                self.assign_initial_words(session, user.id)
            
            return user
        finally:
            session.close()
    
    def assign_initial_words(self, session, user_id, count=50):
        words = session.query(Word).filter_by(level='A1').limit(count).all()
        for word in words:
            progress = UserWordProgress(
                user_id=user_id,
                word_id=word.id,
                stage=0,
                next_review=datetime.utcnow()
            )
            session.add(progress)
        session.commit()
    
    def get_daily_words(self, user_id, count=None):
        session = self.get_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return []
            
            count = count or user.daily_words
            
            due_words = session.query(Word).join(UserWordProgress).filter(
                UserWordProgress.user_id == user_id,
                UserWordProgress.next_review <= datetime.utcnow()
            ).order_by(
                UserWordProgress.next_review,
                UserWordProgress.stage
            ).limit(count).all()
            
            if len(due_words) < count:
                learned_ids = session.query(UserWordProgress.word_id).filter(
                    UserWordProgress.user_id == user_id
                ).subquery()
                
                new_words = session.query(Word).filter(
                    Word.level <= user.level,
                    ~Word.id.in_(learned_ids)
                ).order_by(
                    Word.frequency.desc()
                ).limit(count - len(due_words)).all()
                
                for word in new_words:
                    progress = UserWordProgress(
                        user_id=user_id,
                        word_id=word.id,
                        stage=0,
                        next_review=datetime.utcnow()
                    )
                    session.add(progress)
                
                session.commit()
                due_words.extend(new_words)
            
            return due_words
            
        finally:
            session.close()
    
    def update_word_progress(self, user_id, word_id, correct):
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
            
            stats = session.query(UserStats).filter_by(user_id=user_id).first()
            if not stats:
                stats = UserStats(user_id=user_id)
                session.add(stats)
            
            stats.total_reviews += 1
            if correct:
                stats.correct_reviews += 1
                progress.correct_count += 1
                progress.stage = min(progress.stage + 1, Config.MAX_STAGE)
                
                if progress.stage == 1:
                    interval = 1
                elif progress.stage == 2:
                    interval = 3
                elif progress.stage == 3:
                    interval = 7
                elif progress.stage == 4:
                    interval = 14
                elif progress.stage == 5:
                    interval = 30
                    if not progress.mastered_at:
                        progress.mastered_at = datetime.utcnow()
                        stats.total_words_learned += 1
                else:
                    interval = 0
            else:
                stats.correct_reviews = max(0, stats.correct_reviews - 1)
                progress.wrong_count += 1
                progress.stage = max(0, progress.stage - 2)
                interval = 0.25
            
            progress.review_count += 1
            progress.last_reviewed = datetime.utcnow()
            
            if interval > 0:
                progress.next_review = datetime.utcnow() + timedelta(days=interval)
            else:
                progress.next_review = datetime.utcnow() + timedelta(hours=6)
            
            user = session.query(User).get(user_id)
            today = datetime.utcnow().date()
            if user.last_active.date() == today - timedelta(days=1):
                user.streak += 1
                stats.current_streak = user.streak
                if user.streak > stats.longest_streak:
                    stats.longest_streak = user.streak
            elif user.last_active.date() < today - timedelta(days=1):
                user.streak = 1
                stats.current_streak = 1
            
            user.last_active = datetime.utcnow()
            
            weekday = datetime.utcnow().weekday()
            if stats.last_week_activity:
                stats.last_week_activity[weekday] += 1
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_stats(self, user_id):
        session = self.get_session()
        try:
            user = session.query(User).get(user_id)
            stats = session.query(UserStats).filter_by(user_id=user_id).first()
            
            if not user or not stats:
                return None
            
            level_progress = {}
            for level in Config.LEVELS:
                total = session.query(Word).filter_by(level=level).count()
                learned = session.query(UserWordProgress).join(Word).filter(
                    UserWordProgress.user_id == user_id,
                    Word.level == level,
                    UserWordProgress.stage >= 3
                ).count()
                level_progress[level] = {
                    'total': total,
                    'learned': learned,
                    'percent': (learned / total * 100) if total > 0 else 0
                }
            
            due_today = session.query(UserWordProgress).filter(
                UserWordProgress.user_id == user_id,
                UserWordProgress.next_review <= datetime.utcnow() + timedelta(days=1)
            ).count()
            
            return {
                'user': user,
                'stats': stats,
                'level_progress': level_progress,
                'due_today': due_today,
                'accuracy': (stats.correct_reviews / stats.total_reviews * 100) if stats.total_reviews > 0 else 0
            }
            
        finally:
            session.close()