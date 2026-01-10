from datetime import datetime
from flask_login import UserMixin
from extensions import db, bcrypt

class Student(UserMixin, db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    fathers_name = db.Column(db.String(120), nullable=True) # New field
    college_name = db.Column(db.String(200), nullable=True) # New field
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10))
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255))
    department = db.Column(db.String(20), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    tenth_marks = db.Column(db.Float)
    twelfth_marks = db.Column(db.Float)
    cgpa = db.Column(db.Float)
    skills = db.Column(db.Text)
    projects_internship = db.Column(db.Text)
    profile_photo = db.Column(db.String(120), nullable=True)
    resume_path = db.Column(db.String(200), nullable=True)
    resume_data_path = db.Column(db.String(200), nullable=True) # Path to JSON file with extra details
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    is_password_changed = db.Column(db.Boolean, default=False)
    is_email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"S-{self.id}"


class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='TPO')
    
    name = db.Column(db.String(100), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    college_name = db.Column(db.String(200), nullable=True)
    mobile = db.Column(db.String(15), nullable=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"A-{self.id}"


class ProfileUpdateRequest(db.Model):
    __tablename__ = 'profile_update_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    requested_changes = db.Column(db.Text, nullable=False) # JSON
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='profile_requests')


class EmailLog(db.Model):
    __tablename__ = 'email_logs'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    email_type = db.Column(db.String(50))
    status = db.Column(db.String(20))
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    location = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    about = db.Column(db.Text)
    required_skills = db.Column(db.Text) # Comma-separated or JSON
    average_salary = db.Column(db.Float, default=0.0) # LPA
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    drives = db.relationship('PlacementDrive', backref='company', cascade='all, delete-orphan')

class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text)
    
    # Eligibility Criteria
    criteria_10th = db.Column(db.Float, default=0.0)
    criteria_12th = db.Column(db.Float, default=0.0)
    criteria_cgpa = db.Column(db.Float, default=0.0)
    allowed_branches = db.Column(db.String(100)) # stored as "IT,CS" etc
    
    salary = db.Column(db.String(50)) # e.g. "5 LPA"
    deadline = db.Column(db.DateTime)
    drive_date = db.Column(db.DateTime)
    
    venue = db.Column(db.String(200)) # New field
    mode = db.Column(db.String(50), default='Offline') # New field (Online/Offline)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # quiz_id and quiz relationship removed. Access quizzes via backref 'quizzes_list'
    
    applications = db.relationship('JobApplication', backref='drive', cascade='all, delete-orphan')

class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False)
    status = db.Column(db.String(20), default='Applied') # Applied, Shortlisted, Rejected, Selected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='applications')

class DriveInvitation(db.Model):
    __tablename__ = 'drive_invitations'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Sent') # Sent, Accepted, Declined
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)

    company = db.relationship('Company', backref='invitations')

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True) # Optional link to company
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=True)
    drive = db.relationship('PlacementDrive', backref='quizzes_list')
    
    is_live = db.Column(db.Boolean, default=False)
    live_at = db.Column(db.DateTime, nullable=True)
    
    time_limit = db.Column(db.Integer, default=30) # Minutes
    pass_percentage = db.Column(db.Float, default=50.0) # percentage required to pass
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='quiz', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', cascade='all, delete-orphan')

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False) # 'A', 'B', 'C', or 'D'
    marks = db.Column(db.Integer, default=1)

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_marks = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.Column(db.Text) # JSON string of selected options: {'question_id': 'option', ...}
    
    student = db.relationship('Student', backref='quiz_attempts')
