import random
from datetime import datetime, timedelta
from typing import List, Tuple

class QuizGenerator:
    """Генератор тестов разных типов"""
    
    @staticmethod
    def generate_translation_quiz(word, translation, wrong_options: List[str]) -> dict:
        """Тест на перевод (выбор из 4 вариантов)"""
        options = [translation] + random.sample(wrong_options, min(3, len(wrong_options)))
        random.shuffle(options)
        
        return {
            'type': 'translation',
            'question': f"Как переводится слово '{word}'?",
            'options': options,
            'correct': translation
        }
    
    @staticmethod
    def generate_word_quiz(translation, word, wrong_options: List[str]) -> dict:
        """Тест на выбор слова по переводу"""
        options = [word] + random.sample(wrong_options, min(3, len(wrong_options)))
        random.shuffle(options)
        
        return {
            'type': 'word',
            'question': f"Какое слово означает '{translation}'?",
            'options': options,
            'correct': word
        }
    
    @staticmethod
    def generate_fill_blank_quiz(example, word) -> dict:
        """Тест на заполнение пропуска"""
        blank_example = example.replace(word, '_____', 1)
        
        return {
            'type': 'fill',
            'question': f"Вставьте пропущенное слово:\n\n{blank_example}",
            'answer': word
        }

class SRSManager:
    """Менеджер интервальных повторений"""
    
    @staticmethod
    def get_next_review(stage: int, correct: bool) -> datetime:
        """Рассчитать следующую дату повторения"""
        if not correct:
            return datetime.utcnow() + timedelta(hours=6)
        
        intervals = [0, 1, 3, 7, 14, 30]  # дни для stage 0-5
        days = intervals[min(stage, len(intervals)-1)]
        
        return datetime.utcnow() + timedelta(days=days)
    
    @staticmethod
    def adjust_stage(current_stage: int, correct: bool) -> int:
        """Скорректировать уровень знания"""
        if correct:
            return min(current_stage + 1, 5)
        else:
            return max(current_stage - 1, 0)