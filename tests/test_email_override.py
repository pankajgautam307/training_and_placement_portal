import unittest
from app import create_app, db
from config import Config
from unittest.mock import patch, MagicMock

# Test Config with Override
class OverrideConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_API_TOKEN = 'test-token'
    MAIL_API_URL = 'https://mock.api.com/send' # Force non-Resend URL
    MAIL_OVERRIDE_RECIPIENT = 'safety@test.com'
    
class EmailOverrideTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(OverrideConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        self.app_context.pop()
        
    @patch('utils.email_sender.requests.post')
    def test_send_email_uses_override(self, mock_post):
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'queued'
        mock_post.return_value = mock_response
        
        from utils.email_sender import send_email
        
        # Action: Send email to 'real' user
        original_to = ['actual.user@domain.com']
        success, msg = send_email('Original Subject', original_to, 'Body')
        
        # Verify
        self.assertTrue(success)
        
        # Check what was actually sent
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        json_data = kwargs['json']
        
        # MUST send to override address
        self.assertEqual(json_data['to'], [{'email': 'safety@test.com'}])
        
        # MUST NOT send to original address
        self.assertNotEqual(json_data['to'], [{'email': 'actual.user@domain.com'}])
        
        # MUST mention original recipient in subject
        self.assertIn('[TEST OVERRIDE -> actual.user@domain.com]', json_data['subject'])
        self.assertIn('Original Subject', json_data['subject'])

if __name__ == '__main__':
    import sys
    suite = unittest.TestLoader().loadTestsFromTestCase(EmailOverrideTestCase)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
