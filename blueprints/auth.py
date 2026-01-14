from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import Student, AdminUser
from forms import StudentRegistrationForm, StudentLoginForm, AdminLoginForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm
from utils.email_sender import send_email
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

auth_bp = Blueprint('auth', __name__)

def send_verification_email(student):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps(student.email, salt='email-confirm')
    
    link = url_for('auth.verify_email', token=token, _external=True)
    
    link = url_for('auth.verify_email', token=token, _external=True)
    
    subject = "Verify your Email - TPO Portal"
    body = f"Dear {student.name},\n\nPlease verify your email by clicking the link below:\n{link}\n\nThis link expires in 1 hour."
    
    if not send_email(subject, [student.email], body):
        flash('Verification email could not be sent. Please check your email configuration or contact support.', 'warning')
    else:
        # We don't need double-flash if registration route also flashes success, 
        # but let's leave success message to the route handler. 
        pass

def send_password_reset_email(user, user_type):
    """Send password reset email to student or admin"""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps(user.email, salt='password-reset')
    
    link = url_for('auth.reset_password', token=token, _external=True)
    
    subject = "Password Reset Request - TPO Portal"
    body = f"Dear {user_name},\n\nYou requested to reset your password. Click the link below to reset:\n{link}\n\nThis link expires in 1 hour.\n\nIf you did not request this, please ignore this email."
    
    if not send_email(subject, [user.email], body):
         print(f"Failed to send password reset email to {user.email}")

def send_password_reset_confirmation(user):
    """Send confirmation email after password reset"""
    subject = "Password Reset Successful - TPO Portal"
    body = f"Dear {user_name},\n\nYour password has been successfully reset.\n\nIf you did not make this change, please contact the administrator immediately."
    
    if not send_email(subject, [user.email], body):
        print(f"Failed to send password reset confirmation to {user.email}")


@auth_bp.route('/')
def index():
    return redirect(url_for('auth.student_login'))

@auth_bp.route('/student/register', methods=['GET', 'POST'])
def student_register():
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        # Handle mutual exclusivity of CGPA and Backlogs
        if form.metric_type.data == 'cgpa':
            cgpa_value = form.cgpa.data
            backlogs_count = 0
        else:  # backlogs
            cgpa_value = None
            # Count backlogs from JSON details
            import json
            backlog_data = json.loads(form.backlog_details.data)
            backlogs_count = len(backlog_data)
        
        student = Student(
            roll_no=form.roll_no.data,
            name=form.name.data,
            fathers_name=form.fathers_name.data,
            college_name=form.college_name.data,
            email=form.email.data.lower(),
            mobile=form.mobile.data,
            department=form.department.data,
            semester=form.semester.data,
            tenth_marks=form.tenth_marks.data or 0,
            twelfth_marks=form.twelfth_marks.data or 0,
            cgpa=cgpa_value,
            backlogs=backlogs_count,
            skills=form.skills.data,
            projects_internship=form.projects_internship.data,
            address=form.address.data,
            gender=form.gender.data,
            dob=form.dob.data,
            is_password_changed=True,
            is_email_verified=False
        )
        
        student.set_password(form.password.data)
        db.session.add(student)
        db.session.flush()  # Get student.id before adding backlogs
        
        # Save backlog details if metric_type is backlogs
        if form.metric_type.data == 'backlogs':
            from models import Backlog
            import json
            backlog_data = json.loads(form.backlog_details.data)
            for entry in backlog_data:
                backlog = Backlog(
                    student_id=student.id,
                    subject_name=entry['subject'],
                    semester=entry['semester']
                )
                db.session.add(backlog)
        
        db.session.commit()
        
        send_verification_email(student)
        
        flash('Registration successful. Please verify your email sent to your registered address before logging in.', 'info')
        return redirect(url_for('auth.student_login'))
    
    return render_template('student_register.html', form=form)

@auth_bp.route('/student/login', methods=['GET', 'POST'])
def student_login():
    form = StudentLoginForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(roll_no=form.roll_no.data).first()
        if student and student.check_password(form.password.data):
            login_user(student)
            
            # Check for forced password change
            if not student.is_password_changed:
                flash('Please change your default password to proceed.', 'warning')
                return redirect(url_for('auth.change_password'))
                
            # Check for email verification
            if not student.is_email_verified:
                flash('Please verify your email address. Check your inbox.', 'warning')
                # Optional: Resend link logic
                logout_user()
                return redirect(url_for('auth.student_login'))

            return redirect(url_for('student.dashboard'))
        flash('Invalid roll number or password', 'danger')
    return render_template('student_login.html', form=form)

@auth_bp.route('/student/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not isinstance(current_user._get_current_object(), Student):
         return redirect(url_for('auth.student_login'))

    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
             flash('Incorrect current password.', 'danger')
             return render_template('change_password.html', form=form)

        current_user.set_password(form.password.data)
        current_user.is_password_changed = True
        current_user.is_email_verified = False # Invalidate until verified
        db.session.commit()
        
        send_verification_email(current_user)
        logout_user()
        
        flash('Password changed successfully. A verification email has been sent to your registered email ID. Please verify to login.', 'info')
        return redirect(url_for('auth.student_login'))
        
    return render_template('change_password.html', form=form)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('The token is expired.', 'danger')
        return redirect(url_for('auth.student_login'))
    except Exception:
        flash('Invalid token.', 'danger')
        return redirect(url_for('auth.student_login'))
        
    student = Student.query.filter_by(email=email).first_or_404()
    if student.is_email_verified:
        flash('Account already verified.', 'success')
    else:
        student.is_email_verified = True
        db.session.commit()
        flash('Email verified! You can now login.', 'success')
        
    return redirect(url_for('auth.student_login'))

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = AdminUser.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin_login.html', form=form)

    return redirect(url_for('auth.student_login'))

@auth_bp.route('/student/forgot-password', methods=['GET', 'POST'])
def student_forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(email=form.email.data.lower()).first()
        if student:
            send_password_reset_email(student, 'student')
            flash('Password reset link has been sent to your email.', 'info')
        else:
            # Don't reveal if email exists or not for security
            flash('If that email is registered, you will receive a password reset link.', 'info')
        return redirect(url_for('auth.student_login'))
    return render_template('forgot_password.html', form=form, user_type='Student')

@auth_bp.route('/admin/forgot-password', methods=['GET', 'POST'])
def admin_forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        admin = AdminUser.query.filter_by(email=form.email.data.lower()).first()
        if admin:
            send_password_reset_email(admin, 'admin')
            flash('Password reset link has been sent to your email.', 'info')
        else:
            # Don't reveal if email exists or not for security
            flash('If that email is registered, you will receive a password reset link.', 'info')
        return redirect(url_for('auth.admin_login'))
    return render_template('forgot_password.html', form=form, user_type='Admin')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired.', 'danger')
        return redirect(url_for('auth.student_login'))
    except Exception:
        flash('Invalid password reset link.', 'danger')
        return redirect(url_for('auth.student_login'))
    
    # Check if it's a student or admin
    user = Student.query.filter_by(email=email).first()
    user_type = 'student'
    if not user:
        user = AdminUser.query.filter_by(email=email).first()
        user_type = 'admin'
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.student_login'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        
        send_password_reset_confirmation(user)
        
        flash('Your password has been reset successfully. You can now login.', 'success')
        if user_type == 'student':
            return redirect(url_for('auth.student_login'))
        else:
            return redirect(url_for('auth.admin_login'))
    
    return render_template('reset_password.html', form=form, user_type=user_type)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('auth.student_login'))
