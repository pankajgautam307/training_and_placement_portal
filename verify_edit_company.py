
import unittest
from app import create_app, db
from config import Config
from models import AdminUser, Company

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class CompanyEditTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create admin
        admin = AdminUser(username='admin', email='admin@example.com')
        admin.set_password('password')
        db.session.add(admin)
        
        # Create company
        self.company = Company(
            name='Original Name',
            email='original@example.com',
            website='https://original.com',
            location='Original City',
            industry='Original Industry',
            average_salary=5.0
        )
        db.session.add(self.company)
        db.session.commit()
        self.company_id = self.company.id

        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'password'}, follow_redirects=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_edit_company(self):
        print("\n--- Testing Edit Company ---")
        response = self.client.post(f'/admin/company/{self.company_id}/edit', data={
            'name': 'Updated Name',
            'email': 'updated@example.com',
            'website': 'https://updated.com',
            'location': 'Updated City',
            'industry': 'Updated Industry',
            'average_salary': '10.0'
        }, follow_redirects=True)
        
        # Verify redirect
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Company details updated successfully', response.data)
        
        # Verify DB update
        updated_company = Company.query.get(self.company_id)
        self.assertEqual(updated_company.name, 'Updated Name')
        self.assertEqual(updated_company.email, 'updated@example.com')
        self.assertEqual(updated_company.average_salary, 10.0)
        
        print("SUCCESS: Company details updated correctly.")

if __name__ == '__main__':
    unittest.main()
