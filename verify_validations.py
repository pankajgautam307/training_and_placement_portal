
from app import app
from forms import StudentRegistrationForm, DriveForm, CompanyForm
from werkzeug.datastructures import MultiDict
from datetime import date, timedelta

def test_student_registration_form():
    print("\nTesting StudentRegistrationForm...")
    with app.test_request_context():
        # Test 1: Invalid Mobile (letters)
        data = MultiDict({
            'roll_no': 'S123',
            'name': 'John Doe',
            'email': 'john@example.com',
            'mobile': 'abcdefghij', # Invalid
            'password': 'password',
            'confirm_password': 'password',
            'department': 'IT',
            'semester': '1'
        })
        form = StudentRegistrationForm(formdata=data)
        if not form.validate():
            print("Caught expected errors (Mobile):", form.errors.get('mobile'))
        else:
            print("Failed to catch invalid mobile!")

        # Test 2: Invalid Name (numbers)
        data['mobile'] = '1234567890'
        data['name'] = 'John 123' # Invalid
        form = StudentRegistrationForm(formdata=data)
        form.validate()
        print("Errors for Name:", form.errors.get('name'))

        # Test 3: Invalid Marks (Range)
        data['name'] = 'John Doe'
        data['tenth_marks'] = '150' # Invalid
        form = StudentRegistrationForm(formdata=data)
        form.validate()
        print("Errors for Tenth Marks:", form.errors.get('tenth_marks'))

def test_drive_form():
    print("\nTesting DriveForm...")
    with app.test_request_context():
        # Test 1: Deadline in past
        today = date.today()
        yesterday = today - timedelta(days=1)
        data = MultiDict({
            'company_id': '1',
            'job_title': 'Dev',
            'deadline': yesterday.strftime('%Y-%m-%d'), # Invalid
            'drive_date': today.strftime('%Y-%m-%d')
        })
        form = DriveForm(formdata=data)
        # Mock choices for select field if needed, or ignore if validation fails before checking choices
        form.company_id.choices = [(1, 'Test Company')]
        
        if not form.validate():
             print("Caught expected errors (Deadline):", form.errors.get('deadline'))

        # Test 2: Drive Date before Deadline
        future = today + timedelta(days=5)
        future_plus = today + timedelta(days=4) # Before deadline
        data['deadline'] = future.strftime('%Y-%m-%d')
        data['drive_date'] = future_plus.strftime('%Y-%m-%d') # Invalid
        form = DriveForm(formdata=data)
        form.company_id.choices = [(1, 'Test Company')]
        form.validate()
        print("Errors for Drive Date:", form.errors.get('drive_date'))

if __name__ == "__main__":
    try:
        test_student_registration_form()
        test_drive_form()
        print("\nVerification Steps Completed.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
