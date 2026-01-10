import unittest
from app import create_app, db
from config import Config
from models import Quiz, Question, AdminUser

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class QuizTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Admin
        admin = AdminUser(username='admin', email='admin@test.com', role='TPO')
        admin.set_password('pass')
        db.session.add(admin)
        db.session.commit()
        
        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'pass'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_quiz_and_questions(self):
        # Create Quiz
        response = self.client.post('/admin/quiz/new', data={
            'title': 'Test Quiz',
            'description': 'A simple test.',
            'time_limit': 15
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Quiz.query.count(), 1)
        quiz = Quiz.query.first()
        self.assertEqual(quiz.title, 'Test Quiz')
        
        # Add Question
        response = self.client.post(f'/admin/quiz/{quiz.id}', data={
            'question_text': 'What is 2+2?',
            'option_a': '1',
            'option_b': '2',
            'option_c': '3',
            'option_d': '4',
            'correct_option': 'D',
            'marks': 1
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.query.count(), 1)
        q = Question.query.first()
        self.assertEqual(q.correct_option, 'D')

if __name__ == '__main__':
    unittest.main()
