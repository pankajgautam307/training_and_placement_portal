from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, IntegerField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Optional
from models import Student, AdminUser

class StudentRegistrationForm(FlaskForm):
    roll_no = StringField('Roll Number', validators=[DataRequired(), Length(min=2, max=20)])
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    fathers_name = StringField("Father's Name", validators=[DataRequired(), Length(max=120)]) # New
    college_name = StringField('College Name', validators=[DataRequired(), Length(max=200)]) # New
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile', validators=[DataRequired(), Length(min=10, max=15)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    address = StringField('Address')
    department = SelectField('Department', choices=[('', 'Select'), ('IT', 'Information Technology'), ('CS', 'Computer Science')], validators=[DataRequired()])
    semester = IntegerField('Semester', validators=[DataRequired(), NumberRange(min=1, max=6)])
    
    tenth_marks = FloatField('10th Percentage', validators=[Optional()])
    twelfth_marks = FloatField('12th Percentage', validators=[Optional()])
    cgpa = FloatField('Diploma CGPA', validators=[Optional()])
    
    skills = StringField('Skills')
    projects_internship = TextAreaField('Projects / Internships')
    
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_roll_no(self, roll_no):
        student = Student.query.filter_by(roll_no=roll_no.data).first()
        if student:
            raise ValidationError('Roll number already registered.')

    def validate_email(self, email):
        student = Student.query.filter_by(email=email.data).first()
        if student:
            raise ValidationError('Email already registered.')


class StudentLoginForm(FlaskForm):
    roll_no = StringField('Roll Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters.")])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Change Password')

class AdminProfileForm(FlaskForm):
    username = StringField('Username', render_kw={'readonly': True})
    email = StringField('Email', render_kw={'readonly': True})
    name = StringField('Name', validators=[Optional(), Length(max=100)])
    designation = StringField('Designation', validators=[Optional(), Length(max=100)])
    college_name = StringField('College Name', validators=[Optional(), Length(max=200)])
    mobile = StringField('Mobile Number', validators=[Optional(), Length(min=10, max=15)])
    submit = SubmitField('Update Profile')


class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class AdminBulkImportForm(FlaskForm):
    file = FileField('Upload Excel/CSV', validators=[
        FileRequired(),
        FileAllowed(['xlsx', 'xls', 'csv'], 'Excel or CSV files only!')
    ])
    submit = SubmitField('Import')

class StudentEditForm(FlaskForm):
    roll_no = StringField('Roll Number', validators=[DataRequired(), Length(min=2, max=20)])
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    fathers_name = StringField("Father's Name", validators=[Length(max=120)]) # New
    college_name = StringField('College Name', validators=[Length(max=200)]) # New
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'readonly': True, 'class': 'bg-secondary text-light'})
    mobile = StringField('Mobile', validators=[DataRequired(), Length(min=10, max=15)])
    
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    address = StringField('Address')
    
    department = SelectField('Department', choices=[('', 'Select'), ('IT', 'Information Technology'), ('CS', 'Computer Science')], validators=[DataRequired()])
    semester = IntegerField('Semester', validators=[DataRequired(), NumberRange(min=1, max=6)])
    
    tenth_marks = FloatField('10th Percentage', validators=[Optional()])
    twelfth_marks = FloatField('12th Percentage', validators=[Optional()])
    cgpa = FloatField('Diploma CGPA', validators=[Optional()])
    
    skills = StringField('Skills')
    projects_internship = TextAreaField('Projects / Internships')
    
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')])
    submit = SubmitField('Update Student')

class StudentProfileForm(FlaskForm):
    # Similar to StudentEditForm but no read-only email (displayed as static text in template usually or read-only field)
    # Actually user said "update details except email".
    # We can reuse similar fields but might want to exclude 'status' and 'roll_no' if that's also immutable for student.
    # Usually Roll No and Email are Identity.
    
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    fathers_name = StringField("Father's Name", validators=[Length(max=120)]) # New
    college_name = StringField('College Name', validators=[Length(max=200)]) # New
    mobile = StringField('Mobile', validators=[DataRequired(), Length(min=10, max=15)])
    
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    address = StringField('Address')
    
    # Department/Semester might be updatable or fixed. Let's allow update for now.
    department = SelectField('Department', choices=[('', 'Select'), ('IT', 'Information Technology'), ('CS', 'Computer Science')])
    semester = IntegerField('Semester', validators=[NumberRange(min=1, max=6), Optional()])
    
    tenth_marks = FloatField('10th Percentage', validators=[Optional()])
    twelfth_marks = FloatField('12th Percentage', validators=[Optional()])
    cgpa = FloatField('Diploma CGPA', validators=[Optional()])
    
    skills = StringField('Skills')
    projects_internship = TextAreaField('Projects / Internships')
    
    profile_photo = FileField('Profile Photo', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    resume = FileField('Resume (PDF)', validators=[
        FileAllowed(['pdf'], 'PDFs only!')
    ])
    
    submit = SubmitField('Save Changes')

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    website = StringField('Website', validators=[Optional(), Length(max=200)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    industry = StringField('Industry', validators=[Optional(), Length(max=100)])
    about = TextAreaField('About Company')
    required_skills = StringField('Required Skills (comma separated)', validators=[Optional()])
    average_salary = FloatField('Average Salary (LPA)', validators=[Optional()])
    submit = SubmitField('Save Company')

class DriveForm(FlaskForm):
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    # quiz_id removed
    job_title = StringField('Job Title', validators=[DataRequired(), Length(max=100)])
    job_description = TextAreaField('Job Description')
    
    criteria_10th = FloatField('Min 10th %', validators=[Optional()])
    criteria_12th = FloatField('Min 12th %', validators=[Optional()])
    criteria_cgpa = FloatField('Min Diploma CGPA', validators=[Optional()])
    allowed_branches = StringField('Allowed Branches (e.g. IT,CS)')
    
    salary = StringField('Salary / CTC', validators=[Length(max=50)])
    deadline = DateField('Application Deadline', format='%Y-%m-%d', validators=[Optional()])
    drive_date = DateField('Drive Date', format='%Y-%m-%d', validators=[Optional()])
    
    venue = StringField('Venue', validators=[Optional(), Length(max=200)]) # New
    mode = SelectField('Mode', choices=[('Offline', 'Offline'), ('Online', 'Online')], default='Offline') # New
    
    submit = SubmitField('Post Drive')

class InviteCompanyForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Invitation')

from wtforms import DateTimeLocalField, BooleanField

class QuizForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    time_limit = IntegerField('Time Limit (Minutes)', validators=[DataRequired(), NumberRange(min=1)])
    pass_percentage = FloatField('Passing Percentage', validators=[DataRequired()], default=50.0)
    
    drive_id = SelectField('Link to Placement Drive', coerce=int, validators=[DataRequired()])
    is_live = BooleanField('Make Live Instantly?')
    live_at = DateTimeLocalField('Or Schedule Live At', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    
    submit = SubmitField('Save Quiz')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question', validators=[DataRequired()])
    option_a = StringField('Option A', validators=[DataRequired()])
    option_b = StringField('Option B', validators=[DataRequired()])
    option_c = StringField('Option C', validators=[DataRequired()])
    option_d = StringField('Option D', validators=[DataRequired()])
    correct_option = SelectField('Correct Option', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    marks = IntegerField('Marks', default=1, validators=[DataRequired()])
    submit = SubmitField('Add Question')
