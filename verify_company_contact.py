
import unittest
from app import create_app, db
from config import Config
from models import AdminUser, Company
import logging

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class CompanyContactTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create admin
        admin = AdminUser(username='admin', email='admin@example.com')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()

        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'password'}, follow_redirects=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_company_with_contact(self):
        print("\n--- Testing Add Company with Contact Number ---")
        response = self.client.post('/admin/companies', data={
            'name': 'Contact Test Company',
            'email': 'contact@example.com',
            'contact_number': '9876543210', # Valid 10 digit
            'website': 'https://example.com',
            'location': 'City',
            'industry': 'Tech',
            'average_salary': '5.0'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        company = Company.query.filter_by(name='Contact Test Company').first()
        self.assertIsNotNone(company)
        self.assertEqual(company.contact_number, '9876543210')
        print("SUCCESS: Company added with contact number.")

    def test_validation_contact_number(self):
        print("\n--- Testing Contact Number Validation (Invalid) ---")
        response = self.client.post('/admin/companies', data={
            'name': 'Invalid Contact Company',
            'email': 'invalid@example.com',
            'contact_number': '123', # Invalid (too short)
        }, follow_redirects=True)
        
        company = Company.query.filter_by(name='Invalid Contact Company').first()
        self.assertIsNone(company)
        if b'Contact number must be exactly 10 digits' in response.data or b'Invalid' in response.data:
             print("SUCCESS: Validation error displayed for invalid contact number.")
        else:
             print("FAILURE: Validation error NOT displayed.")

if __name__ == '__main__':
    unittest.main()
