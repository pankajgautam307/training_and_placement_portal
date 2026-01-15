import unittest
from app import create_app, db
from config import Config
from models import Company, DriveInvitation, AdminUser
from unittest.mock import patch, MagicMock

# Define TestConfig with proper variables
class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
class EmailInvitationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create Admin
        self.admin = AdminUser(username='admin', email='admin@test.com', role='TPO')
        self.admin.set_password('pass')
        db.session.add(self.admin)
        
        # Create Company
        self.company = Company(
            name='Test Corp',
            email='recruiter@testcorp.com',
            required_skills='Python',
            average_salary=10.0
        )
        db.session.add(self.company)
        db.session.commit()
        
        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'pass'})
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    @patch('blueprints.admin.send_email')
    def test_invite_company_calls_send_email(self, mock_send_email):
        # Setup mock to return (True, Msg) tuple - IMPORTANT!
        mock_send_email.return_value = (True, "Success")
        
        # Action: Invite company
        response = self.client.post(f'/admin/invite/{self.company.id}', data={
            'subject': 'Invitation to Drive',
            'message': 'We invite you to our campus.'
        }, follow_redirects=True)
        
        # Assertions
        mock_send_email.assert_called_once()
        args, _ = mock_send_email.call_args
        
        # send_email(subject, recipients, body)
        self.assertEqual(args[0], 'Invitation to Drive')
        self.assertEqual(args[1], ['recruiter@testcorp.com'])
        self.assertIn('We invite you', args[2])
        
        self.assertIn('Invitation sent to Test Corp', response.get_data(as_text=True))
        
if __name__ == '__main__':
    import sys
    suite = unittest.TestLoader().loadTestsFromTestCase(EmailInvitationTestCase)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
