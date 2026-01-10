import unittest
from app import create_app, db
from config import Config
from models import Student, AdminUser, Quiz, Question, QuizAttempt

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class StudentQuizTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Setup Data
        self.student = Student(roll_no='101', name='Test Student', email='student@test.com')
        self.student.set_password('pass')
        db.session.add(self.student)
        
        self.quiz = Quiz(title='Math Quiz', time_limit=10)
        db.session.add(self.quiz)
        db.session.commit()
        
        q1 = Question(quiz_id=self.quiz.id, question_text='1+1?', option_a='1', option_b='2', option_c='3', option_d='4', correct_option='B', marks=2)
        q2 = Question(quiz_id=self.quiz.id, question_text='2+2?', option_a='1', option_b='2', option_c='3', option_d='4', correct_option='D', marks=2)
        db.session.add(q1)
        db.session.add(q2)
        db.session.commit()
        
        self.client = self.app.test_client()
        self.client.post('/student/login', data={'roll_no': '101', 'password': 'pass'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_student_can_see_quiz(self):
        response = self.client.get('/student/quizzes')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Math Quiz', response.data)

    def test_student_take_quiz_and_grade(self):
        # Submit correct answers
        response = self.client.post(f'/student/quiz/{self.quiz.id}/start', data={
            f'question_{self.quiz.questions[0].id}': 'B',
            f'question_{self.quiz.questions[1].id}': 'D'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Assessment submitted', response.data)
        self.assertIn(b'Score: 4 / 4', response.data) # 2+2=4 marks
        
        attempt = QuizAttempt.query.first()
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.score, 4)
        self.assertTrue(attempt.passed)

if __name__ == '__main__':
    unittest.main()
