from ai_tutor import SmartLearnTutor
from quiz_generator import QuizGenerator

if __name__ == '__main__':
    t = SmartLearnTutor()
    q = QuizGenerator()
    print('Tutor client initialized:', t.client is not None)
    print('QuizGenerator client initialized:', q.client is not None)
    print('HuggingFace enabled:', t.use_huggingface, q.use_huggingface)
