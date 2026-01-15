import unittest
from app import create_app, db
from config import Config
from models import Student, AdminUser, Company
from unittest.mock import patch, MagicMock

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_API_TOKEN = 'test-token'
    MAIL_API_URL = 'https://mock.api.com/send'
    # Initially no override
    MAIL_OVERRIDE_RECIPIENT = None

class FullEmailSuiteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create Admin
        self.admin = AdminUser(username='admin', email='admin@test.com', role='TPO')
        self.admin.set_password('pass')
        db.session.add(self.admin)
        
        # Create Student
        self.student = Student(
            roll_no='TEST001',
            name='Test Student',
            email='student@test.com',
            mobile='1234567890',
            password_hash='hash',
            status='Pending',
            department='CS',
            semester=8
        )
        db.session.add(self.student)
        
        # Create Company
        self.company = Company(
            name='Test Corp',
            email='recruiter@testcorp.com'
        )
        db.session.add(self.company)
        db.session.commit()
        
        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'pass'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('utils.email_sender.requests.post')
    def test_full_email_features(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = 'queued'
        mock_post.return_value = mock_resp
        
        from utils.email_sender import send_email
        
        # 1. Registration Verification Email (Manual Call Simulation)
        # Note: In real app this happens on register route, but we test the utility integration here
        print("Testing Registration Verification Email...")
        success, msg = send_email('Verify Email', ['student@test.com'], 'Click link')
        self.assertTrue(success)
        
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['to'], [{'email': 'student@test.com'}])
        
        # 2. Student Approval Email
        print("Testing Student Approval Email...")
        # Reset mock
        mock_post.reset_mock()
        
        response = self.client.post(f'/admin/student/{self.student.id}/status', data={'status': 'Approved'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['to'], [{'email': 'student@test.com'}])
        self.assertIn('Welcome', kwargs['json']['subject'])
        
        # 3. Company Invitation Email
        print("Testing Company Invitation Email...")
        mock_post.reset_mock()
        
        response = self.client.post(f'/admin/invite/{self.company.id}', data={
            'subject': 'Invite',
            'message': 'Come to campus'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['to'], [{'email': 'recruiter@testcorp.com'}])
        
        # 4. Override Feature
        print("Testing Override Feature...")
        # Enable override dynamically
        self.app.config['MAIL_OVERRIDE_RECIPIENT'] = 'safety@test.com'
        mock_post.reset_mock()
        
        success, msg = send_email('Sensitive Subject', ['real@user.com'], 'Body')
        self.assertTrue(success)
        
        args, kwargs = mock_post.call_args
        json_data = kwargs['json']
        self.assertEqual(json_data['to'], [{'email': 'safety@test.com'}])
        self.assertIn('[TEST OVERRIDE -> real@user.com]', json_data['subject'])

if __name__ == '__main__':
    import sys
    suite = unittest.TestLoader().loadTestsFromTestCase(FullEmailSuiteTestCase)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
