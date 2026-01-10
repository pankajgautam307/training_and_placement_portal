import unittest
from app import create_app, db
from config import Config
from models import AdminUser, Student, Company, PlacementDrive, Quiz, Question

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class QuizLinkTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Setup Data
        self.admin = AdminUser(username='admin', email='admin@test.com')
        self.admin.set_password('pass')
        db.session.add(self.admin)
        
        self.student = Student(
            roll_no='101', name='Student', email='s@test.com', mobile='1234567890',
            department='CS', semester=6, status='Approved'
        )
        self.student.set_password('pass')
        db.session.add(self.student)
        
        self.company = Company(name='Test Corp')
        db.session.add(self.company)
        
        self.quiz = Quiz(title='Screening Test', time_limit=10)
        db.session.add(self.quiz)
        
        db.session.commit()
        
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_link_quiz_to_drive(self):
        # 1. Admin Creates Drive LINKED to Quiz
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'pass'})
        
        from datetime import date, timedelta
        future_date = date.today() + timedelta(days=30)
        
        response = self.client.post('/admin/drive/new', data={
            'company_id': self.company.id,
            'job_title': 'Developer',
            'quiz_id': self.quiz.id,
            'deadline': future_date
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        drive = PlacementDrive.query.first()
        if not drive:
            print("FAILED: Drive not created. Response data:")
            print(response.get_data(as_text=True))
        
        self.assertIsNotNone(drive)
        print(f"DEBUG: Drive Deadline: {drive.deadline}, Quiz ID: {drive.quiz_id}")
        self.assertEqual(drive.quiz_id, self.quiz.id)
        
        # 2. Student Applies and Sees Quiz Link
        self.client.get('/auth/logout', follow_redirects=True)
        self.client.post('/student/login', data={'roll_no': '101', 'password': 'pass'})
        
        # Apply
        self.client.post(f'/student/drive/{drive.id}/apply', follow_redirects=True)
        
        # Check Dashboard/Drives page for Link
        response = self.client.get('/student/drives')
        self.assertIn(b'Take Assessment', response.data)
        self.assertIn(f'/student/quiz/{self.quiz.id}/start'.encode(), response.data)

if __name__ == '__main__':
    unittest.main()
