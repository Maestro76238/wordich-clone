import random

class QuizGenerator:
    QUIZ_TYPES = ['translation', 'word', 'fill', 'audio']
    
    @staticmethod
    def generate_quiz(word, context_words=None, with_audio=False):
        if with_audio:
            return QuizGenerator.audio_quiz(word)
        
        quiz_type = random.choice(QuizGenerator.QUIZ_TYPES)
        
        if quiz_type == 'translation':
            return QuizGenerator.translation_quiz(word, context_words)
        elif quiz_type == 'word':
            return QuizGenerator.word_quiz(word, context_words)
        elif quiz_type == 'fill':
            return QuizGenerator.fill_blank_quiz(word)
        else:
            return QuizGenerator.audio_quiz(word)
    
    @staticmethod
    def translation_quiz(word, context_words):
        wrong = []
        if context_words:
            candidates = [w.translation for w in context_words if w.id != word.id]
            if candidates:
                wrong = random.sample(candidates, min(3, len(candidates)))
        
        while len(wrong) < 3:
            wrong.append(f"вариант_{random.randint(1, 100)}")
        
        options = [word.translation] + wrong
        random.shuffle(options)
        
        return {
            'type': 'translation',
            'question': f"Как переводится слово *{word.word}*?",
            'options': options,
            'correct': word.translation,
            'word_id': word.id,
            'points': 10
        }
    
    @staticmethod
    def word_quiz(word, context_words):
        wrong = []
        if context_words:
            candidates = [w.word for w in context_words if w.id != word.id]
            if candidates:
                wrong = random.sample(candidates, min(3, len(candidates)))
        
        while len(wrong) < 3:
            wrong.append(f"word_{random.randint(1, 100)}")
        
        options = [word.word] + wrong
        random.shuffle(options)
        
        return {
            'type': 'word',
            'question': f"Какое слово означает *{word.translation}*?",
            'options': options,
            'correct': word.word,
            'word_id': word.id,
            'points': 10
        }
    
    @staticmethod
    def fill_blank_quiz(word):
        if not word.example:
            return QuizGenerator.translation_quiz(word, None)
        
        example = word.example.replace(word.word, '_____', 1)
        
        return {
            'type': 'fill',
            'question': f"Вставьте пропущенное слово:\n\n_{example}_",
            'hint': word.translation,
            'correct': word.word,
            'word_id': word.id,
            'points': 15
        }
    
    @staticmethod
    def audio_quiz(word):
        return {
            'type': 'audio',
            'question': "🎧 *Прослушай слово и выбери перевод*",
            'word': word.word,
            'word_id': word.id,
            'correct': word.translation,
            'options': [],
            'points': 20,
            'has_audio': True
        }
    
    @staticmethod
    def check_answer(quiz, answer):
        if quiz['type'] == 'fill':
            return answer.lower().strip() == quiz['correct'].lower()
        else:
            return answer == quiz['correct']