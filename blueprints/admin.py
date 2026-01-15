from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
import io
import os
from extensions import db, mail
from models import Student, AdminUser, EmailLog
from flask_mail import Message
from forms import AdminBulkImportForm
from utils.email_sender import send_email

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ... (existing code) ...

@admin_bp.route('/import/sample')
@login_required
def download_sample():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))

    data = {
        'roll_no': ['101'],
        'name': ['John Doe'],
        'email': ['john@example.com'],
        'mobile': ['9876543210'],
        'department': ['IT'],
        'semester': [5],
        'tenth_marks': [85.5],
        'twelfth_marks': [88.2],
        'cgpa': [8.5],
        'backlogs': [0],
        'skills': ['Python, SQL'],
        'projects': ['Library Management System']
    }
    df = pd.read_csv(io.StringIO("roll_no,name,email,mobile,department,semester,tenth_marks,twelfth_marks,cgpa,backlogs,skills,projects\n101,John Doe,john@example.com,9876543210,IT,5,85.5,88.2,8.5,0,\"Python, SQL\",Library Management System"))
    # Alternatively simpler:
    df = pd.DataFrame(data)
    
    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=student_import_sample.csv"}
    )


def send_welcome_email(student):
    subject = "Welcome to the Training & Placement Portal"
    body = (
        f"Dear {student.name},\n\n"
        f"Your registration has been approved.\n"
        f"You can now log in using your Roll No. ({student.roll_no}) "
        f"and your password.\n\n"
        f"Regards,\nTraining & Placement Office"
    )
    
    # Use the unified send_email utility which handles Resend API/SMTP selection
    if send_email(subject, [student.email], body):
        log = EmailLog(student_id=student.id,
                       email_type='Approval', status='Success')
        db.session.add(log)
    else:
        log = EmailLog(student_id=student.id,
                       email_type='Approval',
                       status='Failed',
                       error_message="Failed to send via send_email utility")
        db.session.add(log)

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from forms import AdminProfileForm
    
    form = AdminProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('admin.profile'))
        
    return render_template('admin_profile.html', form=form)

@admin_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from forms import ChangePasswordForm
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.password.data)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('admin.profile'))
        else:
            flash('Incorrect current password.', 'danger')
            
    return render_template('admin_change_password.html', form=form)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))

    total = Student.query.count()
    pending = Student.query.filter_by(status='Pending').count()
    approved = Student.query.filter_by(status='Approved').count()
    rejected = Student.query.filter_by(status='Rejected').count()
    
    # Calculate percentages for progress bars
    approved_pct = (approved / total * 100) if total > 0 else 0
    pending_pct = (pending / total * 100) if total > 0 else 0
    rejected_pct = (rejected / total * 100) if total > 0 else 0
    
    # Recent pending requests (limit 5)
    recent_pending = Student.query.filter_by(status='Pending').order_by(Student.created_at.desc()).limit(5).all()

    return render_template(
        'admin_dashboard.html',
        total=total, pending=pending, approved=approved, rejected=rejected,
        approved_pct=approved_pct, pending_pct=pending_pct, rejected_pct=rejected_pct,
        recent_pending=recent_pending
    )

@admin_bp.route('/pending')
@login_required
def pending():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
    students = Student.query.filter_by(status='Pending').all()
    return render_template('admin_pending.html', students=students)

@admin_bp.route('/student/<int:student_id>/status', methods=['POST'])
@login_required
def update_status(student_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))

    new_status = request.form.get('status')  # Approved / Rejected
    
    # Simple validation as this is not a WTForm yet (custom small form)
    # But better to check token. Since we will upgrade templates to use CSRF_token in hidden fields.
    
    student = Student.query.get_or_404(student_id)
    student.status = new_status
    if new_status == 'Approved':
        send_welcome_email(student)
    db.session.commit()
    flash(f'Student {student.roll_no} status updated to {new_status}', 'success')
    return redirect(url_for('admin.pending'))

@admin_bp.route('/import', methods=['GET', 'POST'])
@login_required
def bulk_import():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))

    form = AdminBulkImportForm()
    summary = None
    
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        if filename.endswith('.csv'):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)

        inserted, updated, errors = 0, 0, []

        for index, row in df.iterrows():
            row_num = index + 2 # Assuming header is row 1
            try:
                roll_no = str(row['roll_no']).strip()
                if not roll_no:
                    errors.append(f"Row {row_num}: Roll number missing.")
                    continue
                
                # Basic email validation
                email = str(row.get('email', '')).lower().strip()
                if not email or '@' not in email:
                     errors.append(f"Row {row_num} (Roll {roll_no}): Invalid email '{email}'.")
                     continue

                student = Student.query.filter_by(roll_no=roll_no).first()
                if not student:
                    # New Student Check: Check if email exists for another student
                    existing_student = Student.query.filter_by(email=email).first()
                    if existing_student:
                        errors.append(f"Row {row_num} (Roll {roll_no}): Email '{email}' already registered to Roll {existing_student.roll_no}.")
                        continue 

                    cgpa_val = float(row.get('cgpa', row.get('aggregate_cpi', 0)) or 0)
                    backlogs_val = int(row.get('backlogs', 0))
                    if backlogs_val > 0:
                        cgpa_val = 0.0

                    student = Student(
                        roll_no=roll_no,
                        name=row.get('name', ''),
                        email=email,
                        mobile=str(row.get('mobile', '')),
                        department=row.get('department', 'IT'),
                        semester=int(row.get('semester', 1)),
                        tenth_marks=float(row.get('tenth_marks', 0) or 0),
                        twelfth_marks=float(row.get('twelfth_marks', 0) or 0),
                        cgpa=cgpa_val,
                        backlogs=backlogs_val,
                        skills=row.get('skills', ''),
                        projects_internship=row.get('projects', '')
                    )
                    # Default password: roll_no@password
                    student.set_password(f"{roll_no}@password")
                    student.is_password_changed = False
                    student.is_email_verified = False
                    db.session.add(student)
                    try:
                         db.session.flush()
                         inserted += 1
                    except Exception as e:
                         db.session.rollback()
                         errors.append(f"Row {row_num} (Roll {roll_no}): DB Error - {str(e)}")
                         continue
                else:
                    # Update existing student
                    # Check email uniqueness if email is changing
                    existing_student = Student.query.filter_by(email=email).first()
                    if student.email != email and existing_student:
                        errors.append(f"Row {row_num} (Roll {roll_no}): Cannot update email to '{email}'. Already used by Roll {existing_student.roll_no}.")
                        continue

                    student.name = row.get('name', student.name)
                    student.email = email
                    student.mobile = str(row.get('mobile', student.mobile))
                    student.department = row.get('department', student.department)
                    student.semester = int(row.get('semester', student.semester))
                    student.tenth_marks = float(row.get('tenth_marks',
                                                        student.tenth_marks) or 0)
                    student.twelfth_marks = float(row.get('twelfth_marks',
                                                          student.twelfth_marks) or 0)
                    
                    # Mutual Exclusivity Logic for Updates
                    raw_cgpa = row.get('cgpa')
                    raw_backlogs = row.get('backlogs')
                    
                    has_new_cgpa = raw_cgpa is not None and str(raw_cgpa).strip() != '' and float(raw_cgpa) > 0
                    
                    if has_new_cgpa:
                        student.cgpa = float(raw_cgpa)
                        student.backlogs = 0
                        # Clear existing backlogs from DB? Yes for consistency
                        from models import Backlog
                        Backlog.query.filter_by(student_id=student.id).delete()
                    else:
                        # If no new CGPA provided, check if backlogs provided
                        if raw_backlogs:
                             student.cgpa = None
                             backlog_count = 0
                             s_backlogs = str(raw_backlogs).strip()
                             
                             # Try JSON
                             import json
                             from models import Backlog
                             
                             if s_backlogs.startswith('[') and s_backlogs.endswith(']'):
                                 try:
                                     details = json.loads(s_backlogs)
                                     if isinstance(details, list):
                                         # Replace existing backlogs
                                         Backlog.query.filter_by(student_id=student.id).delete()
                                         
                                         for entry in details:
                                             if 'subject' in entry and 'semester' in entry:
                                                 b = Backlog(
                                                     student_id=student.id,
                                                     subject_name=entry['subject'],
                                                     semester=int(entry['semester'])
                                                 )
                                                 db.session.add(b)
                                                 backlog_count += 1
                                 except:
                                     pass
                             
                             if backlog_count == 0 and s_backlogs.isdigit():
                                 backlog_count = int(s_backlogs)
                                 
                             student.backlogs = backlog_count

                    student.skills = row.get('skills', student.skills)
                    student.projects_internship = row.get(
                        'projects', student.projects_internship)
                    
                    try:
                        db.session.flush()
                        updated += 1
                    except Exception as e:
                        db.session.rollback()
                        errors.append(f"Row {row_num} (Roll {roll_no}): Update Error - {str(e)}")
                        continue
            except Exception as e:
                db.session.rollback()
                errors.append(f"Row {row_num}: Unexpected Error - {str(e)}")

        db.session.commit()
        summary = {'inserted': inserted, 'updated': updated, 'errors': errors}

    return render_template('admin_import.html', summary=summary, form=form)

@admin_bp.route('/students')
@login_required
def list_students():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))

    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    
    query = Student.query
    if search_query:
        query = query.filter(
            (Student.name.ilike(f'%{search_query}%')) | 
            (Student.roll_no.ilike(f'%{search_query}%')) |
            (Student.email.ilike(f'%{search_query}%'))
        )
    
    # Order by status (Pending first), then created_at
    students = query.order_by(Student.status.desc(), Student.created_at.desc())\
                    .paginate(page=page, per_page=10)
                    
    return render_template('admin_students.html', students=students, search_query=search_query)

@admin_bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    student = Student.query.get_or_404(student_id)
    # Import locally to avoid circular import issues if placed at top level with some patterns, 
    # though here it should be fine. simpler to put specific form import at top, but for now:
    from forms import StudentEditForm 
    
    form = StudentEditForm(obj=student)
    
    # Pre-populate backlog details if student has backlogs
    if request.method == 'GET':
        if hasattr(student, 'backlogs_list') and student.backlogs_list:
            import json
            backlog_data = [{'subject': b.subject_name, 'semester': b.semester} for b in student.backlogs_list]
            form.backlog_details.data = json.dumps(backlog_data)
            
            
    if form.validate_on_submit():
        # Check uniqueness constraints if changed
        if form.roll_no.data != student.roll_no and Student.query.filter_by(roll_no=form.roll_no.data).first():
            flash('Roll number already exists.', 'danger')
            return render_template('admin_student_edit.html', form=form, student=student)
            
        # Email is read-only
        if form.email.data != student.email:
             if Student.query.filter_by(email=form.email.data).first():
                 flash('Email already exists.', 'danger')
                 return render_template('admin_student_edit.html', form=form, student=student)

        # Handle Mutual Exclusivity
        if form.metric_type.data == 'cgpa':
             form.backlogs.data = 0 
        else:
             # Backlogs
             form.cgpa.data = None
             import json
             try:
                 backlog_data = json.loads(form.backlog_details.data)
                 form.backlogs.data = len(backlog_data)
             except:
                 form.backlogs.data = 0

        form.populate_obj(student)

        # Update Backlog Details in Database
        from models import Backlog
        # Clear existing backlogs
        Backlog.query.filter_by(student_id=student.id).delete()
        
        if form.metric_type.data == 'backlogs':
            import json
            try:
                backlog_data = json.loads(form.backlog_details.data)
                for entry in backlog_data:
                    backlog = Backlog(
                        student_id=student.id,
                        subject_name=entry['subject'],
                        semester=entry['semester']
                    )
                    db.session.add(backlog)
            except:
                pass

        db.session.commit()
        flash('Student updated successfully.', 'success')
        return redirect(url_for('admin.list_students'))
        
    return render_template('admin_student_edit.html', form=form, student=student)

@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.name} ({student.roll_no}) deleted.', 'success')
    return redirect(url_for('admin.list_students'))

@admin_bp.route('/requests')
@login_required
def list_requests():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import ProfileUpdateRequest
    import json
    requests = ProfileUpdateRequest.query.filter_by(status='Pending').order_by(ProfileUpdateRequest.created_at.desc()).all()
    
    # Process requests for display
    # We want to show what changed.
    processed_requests = []
    for req in requests:
        changes = json.loads(req.requested_changes)
        processed_requests.append({
            'id': req.id,
            'student': req.student,
            'changes': changes,
            'created_at': req.created_at
        })
        
    return render_template('admin_requests.html', requests=processed_requests)

@admin_bp.route('/request/<int:req_id>/<action>', methods=['POST'])
@login_required
def handle_request(req_id, action):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import ProfileUpdateRequest
    import json
    from datetime import datetime
    
    req = ProfileUpdateRequest.query.get_or_404(req_id)
    
    if action == 'approve':
        changes = json.loads(req.requested_changes)
        student = req.student
        
        # Apply changes
        # Apply changes
        backlog_details_dump = changes.pop('backlog_details_dump', None)
        
        for field, value in changes.items():
            if hasattr(student, field):
                # Handle dates if necessary, currently stored as YYYY-MM-DD string
                if field in ['dob'] and value:
                     try:
                         value = datetime.strptime(value, '%Y-%m-%d').date()
                     except:
                         pass
                setattr(student, field, value)
        
        # Post-processing for Mutual Exclusivity and Backlog Details
        if 'cgpa' in changes and changes['cgpa'] is not None:
            # If CGPA was updated, clear backlogs
             student.backlogs = 0
             from models import Backlog
             Backlog.query.filter_by(student_id=student.id).delete()
        
        elif 'backlogs' in changes:
            # If backlogs count changed, ensure CGPA is None
             student.cgpa = None
             
             # If we have the dump, let's try to update the details
             if backlog_details_dump:
                 import json
                 try:
                     from models import Backlog
                     # Clear existing first
                     Backlog.query.filter_by(student_id=student.id).delete()
                     
                     details = json.loads(backlog_details_dump)
                     for entry in details:
                         b = Backlog(
                             student_id=student.id,
                             subject_name=entry['subject'],
                             semester=entry['semester']
                         )
                         db.session.add(b)
                 except Exception as e:
                     print(f"Error applying backlog details: {e}")
        
        # If backlogs became 0 (via explicit change to 0 OR switch to CGPA), ensure details are gone
        if student.backlogs == 0:
             from models import Backlog
             Backlog.query.filter_by(student_id=student.id).delete()
        
        req.status = 'Approved'
        flash('Request approved and changes applied.', 'success')
        
    elif action == 'reject':
        req.status = 'Rejected'
        flash('Request rejected.', 'secondary')
        
    db.session.commit()
    return redirect(url_for('admin.list_requests'))

@admin_bp.route('/companies', methods=['GET', 'POST'])
@login_required
def list_companies():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from forms import CompanyForm
    from models import Company
    
    form = CompanyForm()
    if form.validate_on_submit():
        company = Company(
            name=form.name.data,
            email=form.email.data, # Add email
            contact_number=form.contact_number.data, # Add contact number
            website=form.website.data,
            location=form.location.data,
            industry=form.industry.data,
            about=form.about.data,
            required_skills=form.required_skills.data,
            average_salary=form.average_salary.data or 0.0
        )
        db.session.add(company)
        db.session.commit()
        flash('Company added successfully.', 'success')
        return redirect(url_for('admin.list_companies'))
        
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template('admin_companies.html', form=form, companies=companies)

@admin_bp.route('/company/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_company(company_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from forms import CompanyForm
    from models import Company
    
    company = Company.query.get_or_404(company_id)
    form = CompanyForm(obj=company)
    
    if form.validate_on_submit():
        # Check uniqueness of name if changed
        if form.name.data != company.name and Company.query.filter_by(name=form.name.data).first():
             flash('Company name already exists.', 'danger')
             return render_template('admin_company_edit.html', form=form, company=company)

        form.populate_obj(company)
        db.session.commit()
        flash('Company details updated successfully.', 'success')
        return redirect(url_for('admin.list_companies'))
        
    return render_template('admin_company_edit.html', form=form, company=company)

@admin_bp.route('/drives', methods=['GET'])
@login_required
def list_drives():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import PlacementDrive
    drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin_drives.html', drives=drives)

@admin_bp.route('/drive/new', methods=['GET', 'POST'])
@login_required
def create_drive():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from forms import DriveForm
    from models import PlacementDrive, Company
    
    form = DriveForm()
    # Populate company choices
    form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
    
    form = DriveForm()
    # Populate company choices
    form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
    
    if form.validate_on_submit():
        drive = PlacementDrive(
            company_id=form.company_id.data,
            job_title=form.job_title.data,
            job_description=form.job_description.data,
            criteria_10th=form.criteria_10th.data or 0.0,
            criteria_12th=form.criteria_12th.data or 0.0,
            criteria_cgpa=form.criteria_cgpa.data or 0.0,
            allowed_branches=form.allowed_branches.data,
            salary=form.salary.data,
            deadline=getattr(form.deadline, 'data', None),
            drive_date=getattr(form.drive_date, 'data', None),
            venue=form.venue.data,
            mode=form.mode.data
        )
        # wtforms DateField .data is a python date object
        drive.deadline = form.deadline.data
        drive.drive_date = form.drive_date.data
        
        db.session.add(drive)
        db.session.commit()
        flash('Placement Drive posted successfully.', 'success')
        return redirect(url_for('admin.list_drives'))
        
        db.session.add(drive)
        db.session.commit()
        flash('Placement Drive posted successfully.', 'success')
        return redirect(url_for('admin.list_drives'))
        
    
    return render_template('admin_drive_create.html', form=form, title='Post New Placement Drive', submit_text='Post Drive')

@admin_bp.route('/drive/<int:drive_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_drive(drive_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from forms import DriveForm
    from models import PlacementDrive, Company
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    form = DriveForm(obj=drive)
    
    # Populate choices
    form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
    
    if form.validate_on_submit():
        form.populate_obj(drive)
        db.session.commit()
            
        db.session.commit()
        flash('Placement Drive updated successfully.', 'success')
        return redirect(url_for('admin.list_drives'))
        
    return render_template('admin_drive_create.html', form=form, title='Edit Placement Drive', submit_text='Update Drive')

@admin_bp.route('/drive/<int:drive_id>/delete', methods=['POST'])
@login_required
def delete_drive(drive_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import PlacementDrive
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Unlink quizzes manually to be safe (though not strictly required if nullable)
    # This ensures we know exactly what's happening
    for quiz in drive.quizzes_list:
        quiz.drive_id = None
        
    db.session.delete(drive)
    db.session.commit()
    flash(f'Placement Drive "{drive.job_title}" deleted successfully.', 'success')
    return redirect(url_for('admin.list_drives'))

@admin_bp.route('/drive/<int:drive_id>/applicants')
@login_required
def list_applicants(drive_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import PlacementDrive, JobApplication, QuizAttempt, Quiz
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    # Order by Marks (CGPA desc)
    applications = JobApplication.query.filter_by(drive_id=drive.id).join(JobApplication.student).order_by(Student.cgpa.desc()).all()
    
    # Fetch linked quizzes and results
    quizzes = drive.quizzes_list
    results_map = {}
    
    if quizzes:
        quiz_ids = [q.id for q in quizzes]
        attempts = QuizAttempt.query.filter(QuizAttempt.quiz_id.in_(quiz_ids)).all()
        for attempt in attempts:
            results_map[(attempt.student_id, attempt.quiz_id)] = attempt
            
    return render_template('admin_drive_applicants.html', drive=drive, applications=applications, quizzes=quizzes, results_map=results_map)

@admin_bp.route('/application/<int:app_id>/status/<string:status>', methods=['POST'])
@login_required
def update_application_status(app_id, status):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import JobApplication
    
    application = JobApplication.query.get_or_404(app_id)
    if status in ['Shortlisted', 'Rejected', 'Selected']:
        application.status = status
        db.session.commit()
        flash(f'Applicant status updated to {status}.', 'success')
    else:
        flash('Invalid status.', 'warning')
        
    return redirect(url_for('admin.list_applicants', drive_id=application.drive_id))

@admin_bp.route('/tech-match', methods=['GET'])
@login_required
def tech_match():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import Student, Company
    
    # Matching Logic
    match_type = request.args.get('type', 'students') # 'students' or 'companies'
    skills_query = request.args.get('skills', '').strip()
    location_query = request.args.get('location', '').strip()
    min_salary = request.args.get('salary', 0, type=float)
    
    results = []
    
    if match_type == 'students' and skills_query:
        # Find students who have ANY of the skills
        required_skills = [s.strip() for s in skills_query.split(',') if s.strip()]
        
        # Naive approach: Fetch all students and score them
        all_students = Student.query.filter_by(status='Approved').all()
        scored_students = []
        
        for student in all_students:
            student_skills = [s.strip().lower() for s in (student.skills or '').split(',')]
            score = 0
            matches = []
            for req in required_skills:
                # substring match
                if any(req.lower() in s for s in student_skills):
                    score += 1
                    matches.append(req)
            
            if score > 0:
                scored_students.append({
                    'student': student,
                    'score': score,
                    'matches': matches
                })
        
        # Sort by score descending
        results = sorted(scored_students, key=lambda x: x['score'], reverse=True)
        
    elif match_type == 'companies':
        query = Company.query
        
        if location_query:
            query = query.filter(Company.location.ilike(f'%{location_query}%'))
            
        if min_salary > 0:
            query = query.filter(Company.average_salary >= min_salary)
            
        companies = query.all()
        
        # Skill filter
        if skills_query:
            required_skills = [s.strip() for s in skills_query.split(',') if s.strip()]
            scored_companies = []
            for company in companies:
                comp_skills = [s.strip().lower() for s in (company.required_skills or '').split(',')]
                score = 0
                matches = []
                for req in required_skills:
                    if any(req.lower() in s for s in comp_skills):
                        score += 1
                        matches.append(req)
                
                if score > 0:
                    scored_companies.append({
                        'company': company,
                        'score': score,
                        'matches': matches
                    })
            results = sorted(scored_companies, key=lambda x: x['score'], reverse=True)
        else:
            # If no skill filter, just return queried companies
            results = [{'company': c, 'score': 0, 'matches': []} for c in companies]

    return render_template('admin_tech_match.html', results=results, match_type=match_type)

@admin_bp.route('/invite/<int:company_id>', methods=['GET', 'POST'])
@login_required
def invite_company(company_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import Company, DriveInvitation
    from forms import InviteCompanyForm
    
    company = Company.query.get_or_404(company_id)
    form = InviteCompanyForm()
    
    # Pre-populate form on GET
    if request.method == 'GET':
        form.subject.data = "Invitation to Conduct Placement Drive at [College Name]"
        form.message.data = f"""Dear Hiring Team,

We would like to invite {company.name} to conduct a placement drive for our students. 
We have a talented pool of candidates skilled in {company.required_skills or 'relevant technologies'}.

Please let us know your availability.

Regards,
Training & Placement Office"""

    if form.validate_on_submit():
        invitation = DriveInvitation(
            company_id=company.id,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(invitation)
        db.session.commit()
        
        # Send Email
        if company.email:
            success, msg = send_email(form.subject.data, [company.email], form.message.data)
            if success:
                flash(f'Invitation sent to {company.name} ({company.email}).', 'success')
            else:
                flash(f'Invitation recorded but email failed to send. {msg}', 'warning')
        else:
            flash(f'Invitation recorded. Note: Company has no email address.', 'info')
            
        return redirect(url_for('admin.list_companies'))
            
    return render_template('admin_invite_company.html', company=company, form=form)

@admin_bp.route('/invitations')
@login_required
def list_invitations():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import DriveInvitation
    invitations = DriveInvitation.query.order_by(DriveInvitation.sent_at.desc()).all()
    return render_template('admin_invitations.html', invitations=invitations)

# Quiz Management Routes

@admin_bp.route('/quizzes')
@login_required
def list_quizzes():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    from models import Quiz
    from datetime import datetime
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    return render_template('admin_quizzes.html', quizzes=quizzes, datetime=datetime)

@admin_bp.route('/quiz/new', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from forms import QuizForm
    from models import Quiz, PlacementDrive
    
    form = QuizForm()
    # Populate drive choices
    drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    form.drive_id.choices = [(0, 'Select Drive')] + [(d.id, f"{d.job_title} ({d.company.name})") for d in drives]

    if form.validate_on_submit():
        quiz = Quiz(
            title=form.title.data,
            description=form.description.data,
            time_limit=form.time_limit.data,
            pass_percentage=form.pass_percentage.data,
            is_live=False,  # Force draft on creation
            live_at=None    # Force draft on creation
        )
        if form.drive_id.data and form.drive_id.data != 0:
            quiz.drive_id = form.drive_id.data
            
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz created! Now add questions.', 'success')
        return redirect(url_for('admin.view_quiz', quiz_id=quiz.id))
        
    return render_template('admin_quiz_create.html', form=form, title='Create Quiz')

@admin_bp.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from forms import QuizForm
    from models import Quiz, PlacementDrive
    
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuizForm(obj=quiz)
    
    # Populate drive choices
    drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    form.drive_id.choices = [(0, 'Select Drive')] + [(d.id, f"{d.job_title} ({d.company.name})") for d in drives]
    
    if request.method == 'GET':
        form.drive_id.data = quiz.drive_id if quiz.drive_id else 0
        # The form is already populated by QuizForm(obj=quiz) for GET,
        # but explicitly setting pass_percentage here ensures it's handled if obj=quiz
        # somehow misses it or if there's a specific reason to re-assign.
        # In this case, it's redundant but harmless.
        form.pass_percentage.data = quiz.pass_percentage

    if form.validate_on_submit():
        # Validate questions if trying to go live
        if (form.is_live.data or form.live_at.data) and len(quiz.questions) == 0:
            flash('Cannot go live or schedule a quiz without questions. Please add questions first.', 'danger')
            # Reset live fields to prevent incorrect update
            form.is_live.data = False
            form.live_at.data = None
            # Continue to save other changes (title, desc, etc.) but block live status
            
        quiz.title = form.title.data
        quiz.description = form.description.data
        quiz.time_limit = form.time_limit.data
        quiz.pass_percentage = form.pass_percentage.data
        quiz.is_live = form.is_live.data
        quiz.live_at = form.live_at.data
        
        if form.drive_id.data and form.drive_id.data != 0:
             quiz.drive_id = form.drive_id.data
        else:
             quiz.drive_id = None
             
        db.session.commit()
        flash('Quiz updated successfully.', 'success')
        return redirect(url_for('admin.list_quizzes'))
        
    return render_template('admin_quiz_create.html', form=form, title='Edit Quiz', quiz=quiz)

@admin_bp.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def view_quiz(quiz_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import Quiz, Question
    from forms import QuestionForm
    
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuestionForm()
    
    if form.validate_on_submit():
        question = Question(
            quiz_id=quiz.id,
            question_text=form.question_text.data,
            option_a=form.option_a.data,
            option_b=form.option_b.data,
            option_c=form.option_c.data,
            option_d=form.option_d.data,
            correct_option=form.correct_option.data,
            marks=form.marks.data
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added.', 'success')
        return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))
        
    return render_template('admin_quiz_view.html', quiz=quiz, form=form)

@admin_bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        return redirect(url_for('auth.admin_login'))
        
    from models import Question
    from forms import QuestionForm
    
    q = Question.query.get_or_404(question_id)
    form = QuestionForm(obj=q)
    
    if form.validate_on_submit():
        q.question_text = form.question_text.data
        q.option_a = form.option_a.data
        q.option_b = form.option_b.data
        q.option_c = form.option_c.data
        q.option_d = form.option_d.data
        q.correct_option = form.correct_option.data
        q.marks = form.marks.data
        
        db.session.commit()
        flash('Question updated successfully.', 'success')
        return redirect(url_for('admin.view_quiz', quiz_id=q.quiz_id))
        
    return render_template('admin_question_edit.html', form=form, question=q)

@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        return redirect(url_for('auth.admin_login'))
        
    from models import Question
    q = Question.query.get_or_404(question_id)
    quiz_id = q.quiz_id
    db.session.delete(q)
    db.session.commit()
    return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))

@admin_bp.route('/questions/download_sample')
@login_required
def download_sample_questions():
    if not isinstance(current_user._get_current_object(), AdminUser):
        return redirect(url_for('auth.admin_login'))
        
    import io
    import pandas as pd
    
    # Create sample data
    data = {
        'Question Text': ['What is the capital of France?'],
        'Option A': ['London'],
        'Option B': ['Berlin'],
        'Option C': ['Paris'],
        'Option D': ['Madrid'],
        'Correct Option': ['C'],
        'Marks': [1]
    }
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='sample_questions.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@admin_bp.route('/quiz/<int:quiz_id>/import', methods=['POST'])
@login_required
def import_questions(quiz_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        return redirect(url_for('auth.admin_login'))
        
    from models import Quiz, Question
    import pandas as pd
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))
        
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))
        
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        flash('Only Excel files are allowed (.xlsx, .xls)', 'danger')
        return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))
        
    try:
        df = pd.read_excel(file)
        
        # Validate headers roughly
        required_cols = ['Question Text', 'Option A', 'Option B', 'Option C', 'Option D', 'Correct Option', 'Marks']
        if not all(col in df.columns for col in required_cols):
             flash(f'Missing columns. Required: {", ".join(required_cols)}', 'danger')
             return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))
        
        count = 0
        for index, row in df.iterrows():
            if pd.isna(row['Question Text']):
                 continue 
                 
            question = Question(
                quiz_id=quiz.id,
                question_text=str(row['Question Text']),
                option_a=str(row['Option A']),
                option_b=str(row['Option B']),
                option_c=str(row['Option C']),
                option_d=str(row['Option D']),
                correct_option=str(row['Correct Option']).upper().strip(),
                marks=float(row['Marks']) if not pd.isna(row['Marks']) else 1.0
            )
            db.session.add(question)
            count += 1
            
        db.session.commit()
        flash(f'Successfully imported {count} questions.', 'success')
        
    except Exception as e:
        flash(f'Error importing file: {str(e)}', 'danger')
        
    return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))
    db.session.commit()
    flash('Question deleted.', 'success')
    return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))

@admin_bp.route('/quiz/<int:quiz_id>/results')
@login_required
def view_quiz_results(quiz_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        return redirect(url_for('auth.admin_login'))
        
    from models import Quiz, QuizAttempt
    quiz = Quiz.query.get_or_404(quiz_id)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).order_by(QuizAttempt.score.desc()).all()
    
    # Summary Stats
    total_students = len(attempts)
    avg_score = 0
    pass_percentage = 0
    
    if total_students > 0:
        avg_score = sum(a.score for a in attempts) / total_students
        passed_count = sum(1 for a in attempts if a.passed)
        pass_percentage = (passed_count / total_students) * 100
        
    return render_template('admin_quiz_results.html', quiz=quiz, attempts=attempts, 
                           total_students=total_students, avg_score=avg_score, pass_percentage=pass_percentage)

@admin_bp.route('/quiz/<int:quiz_id>/stop', methods=['POST'])
@login_required
def stop_quiz(quiz_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import Quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    quiz.is_live = False
    quiz.live_at = None
    db.session.commit()
    
    flash(f'Quiz "{quiz.title}" has been stopped and is now in Draft mode.', 'warning')
    return redirect(url_for('admin.list_quizzes'))

@admin_bp.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    from models import Quiz
    
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash(f'Quiz "{quiz.title}" deleted successfully.', 'success')
    return redirect(url_for('admin.list_quizzes'))

@admin_bp.route('/quiz/<int:quiz_id>/report')
@login_required
def download_quiz_report(quiz_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        return redirect(url_for('auth.admin_login'))
        
    from models import Quiz, QuizAttempt
    import csv
    import json
    from io import StringIO
    from flask import make_response
    
    quiz = Quiz.query.get_or_404(quiz_id)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()
    
    # Sort attempts by student name
    attempts.sort(key=lambda x: x.student.name)
    
    # Prepare CSV
    si = StringIO()
    cw = csv.writer(si)
    
    # Header: details + question columns
    header = ['Roll No', 'Name', 'Score', 'Total', 'Percentage', 'Result']
    questions = quiz.questions
    # Sort questions by ID or logic
    questions.sort(key=lambda x: x.id)
    
    for i, q in enumerate(questions):
        header.append(f"Q{i+1}: {q.question_text[:30]}...")
        
    cw.writerow(header)
    
    for attempt in attempts:
        row = [
            attempt.student.roll_no,
            attempt.student.name,
            attempt.score,
            attempt.total_marks,
            f"{(attempt.score/attempt.total_marks*100):.1f}%" if attempt.total_marks > 0 else "0%",
            "Passed" if attempt.passed else "Failed"
        ]
        
        # Parse answers
        answers = {}
        if attempt.answers:
            try:
                answers = json.loads(attempt.answers)
            except:
                pass
                
        for q in questions:
            selected = answers.get(str(q.id), "-")
            status = "Correct" if selected == q.correct_option else "Wrong"
            row.append(f"{selected} ({status})")
            
        cw.writerow(row)
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=Quiz_{quiz.id}_Report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@admin_bp.route('/quiz/<int:quiz_id>/report/view')
@login_required
def view_quiz_report(quiz_id):
    if not isinstance(current_user._get_current_object(), AdminUser):
        return redirect(url_for('auth.admin_login'))
        
    from models import Quiz, QuizAttempt
    import json
    
    quiz = Quiz.query.get_or_404(quiz_id)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()
    
    # Sort attempts by student name
    attempts.sort(key=lambda x: x.student.name)
    
    questions = quiz.questions
    questions.sort(key=lambda x: x.id)
    
    report_data = []
    
    for attempt in attempts:
        answers = {}
        if attempt.answers:
            try:
                answers = json.loads(attempt.answers)
            except:
                pass
                
        report_data.append({
            'student': attempt.student,
            'score': attempt.score,
            'total': attempt.total_marks,
            'passed': attempt.passed,
            'answers': answers
        })
        
    return render_template('admin_quiz_report_preview.html', quiz=quiz, questions=questions, report_data=report_data)

# ---------------------------------------------------
# Reporting Section
# ---------------------------------------------------

from io import BytesIO
import pandas as pd
from xhtml2pdf import pisa
from flask import make_response, send_file

def generate_pdf(html_content):
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf)
    if pisa_status.err:
        return None
    pdf.seek(0)
    return pdf

def generate_excel(data, columns):
    df = pd.DataFrame(data, columns=columns)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    output.seek(0)
    return output

@admin_bp.route('/reports/<string:report_type>/<string:file_format>')
@login_required
def download_report(report_type, file_format):
    if not isinstance(current_user._get_current_object(), AdminUser):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.admin_login'))
        
    if file_format not in ['pdf', 'excel']:
        flash('Invalid format', 'danger')
        return redirect(url_for('admin.dashboard'))

    from datetime import datetime
    from models import Student, Company, PlacementDrive, DriveInvitation
    download_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if report_type == 'students':
        students = Student.query.all()
        # Data prep
        data = []
        for s in students:
            data.append({
                'Roll No': s.roll_no,
                'Name': s.name,
                "Father's Name": s.fathers_name,
                "College Name": s.college_name,
                'Email': s.email,
                'Mobile': s.mobile,
                'Department': s.department,
                'Semester': s.semester,
                'CGPA': s.cgpa,
                '10th %': s.tenth_marks,
                '12th %': s.twelfth_marks,
                'Status': s.status,
                'Skills': s.skills,
                'Resume': url_for('static', filename=s.resume_path, _external=True) if s.resume_path else 'N/A'
            })
            
        if file_format == 'excel':
            cols = ['Roll No', 'Name', "Father's Name", "College Name", 'Email', 'Mobile', 'Department', 'Semester', 'CGPA', '10th %', '12th %', 'Status', 'Skills', 'Resume']
            pdf_out = generate_excel(data, cols) 
            return send_file(pdf_out, as_attachment=True, download_name=f"{filename}.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
        else:
            # PDF
            html = render_template('reports/student_report.html', students=students, download_time=download_time)
            pdf = generate_pdf(html)
            if pdf:
                return send_file(pdf, as_attachment=True, download_name=f"{filename}.pdf", mimetype='application/pdf')
            else:
                flash('Error generating PDF', 'danger')
                return redirect(url_for('admin.list_students'))

    elif report_type == 'companies':
        companies = Company.query.all()
        data = []
        for c in companies:
            data.append({
                'Company Name': c.name,
                'Email': c.email,
                'Website': c.website,
                'Location': c.location,
                'Industry': c.industry
            })
            
        if file_format == 'excel':
            cols = ['Company Name', 'Email', 'Website', 'Location', 'Industry']
            excel_out = generate_excel(data, cols)
            return send_file(excel_out, as_attachment=True, download_name=f"{filename}.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            html = render_template('reports/company_report.html', companies=companies, download_time=download_time)
            pdf = generate_pdf(html)
            return send_file(pdf, as_attachment=True, download_name=f"{filename}.pdf", mimetype='application/pdf')

    elif report_type == 'drives':
        drives = PlacementDrive.query.all()
        data = []
        for d in drives:
            data.append({
                'Job Title': d.job_title,
                'Company': d.company.name,
                'Drive Date': d.drive_date.strftime('%Y-%m-%d') if d.drive_date else 'N/A',
                'Venue': d.venue,
                'Mode': d.mode,
                'Deadline': d.deadline.strftime('%Y-%m-%d') if d.deadline else 'N/A',
                'Salary': d.salary,
                'Criteria 10th': d.criteria_10th,
                'Criteria 12th': d.criteria_12th,
                'Criteria CGPA': d.criteria_cgpa,
                'Allowed Branches': d.allowed_branches
            })
            
        if file_format == 'excel':
            cols = ['Job Title', 'Company', 'Drive Date', 'Venue', 'Mode', 'Deadline', 'Salary', 'Criteria 10th', 'Criteria 12th', 'Criteria CGPA', 'Allowed Branches']
            excel_out = generate_excel(data, cols)
            return send_file(excel_out, as_attachment=True, download_name=f"{filename}.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            html = render_template('reports/drive_report.html', drives=drives, download_time=download_time)
            pdf = generate_pdf(html)
            return send_file(pdf, as_attachment=True, download_name=f"{filename}.pdf", mimetype='application/pdf')
            
    elif report_type == 'invitations':
        from models import DriveInvitation
        invitations = DriveInvitation.query.all()
        data = []
        for i in invitations:
            data.append({
                'Company': i.company.name,
                'Subject': i.subject,
                'Status': i.status,
                'Sent At': i.sent_at.strftime('%Y-%m-%d %H:%M'),
                'Responded At': i.responded_at.strftime('%Y-%m-%d %H:%M') if i.responded_at else 'N/A'
            })
            
        if file_format == 'excel':
            cols = ['Company', 'Subject', 'Status', 'Sent At', 'Responded At']
            excel_out = generate_excel(data, cols)
            return send_file(excel_out, as_attachment=True, download_name=f"{filename}.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            html = render_template('reports/invitation_report.html', invitations=invitations, download_time=download_time)
            pdf = generate_pdf(html)
            return send_file(pdf, as_attachment=True, download_name=f"{filename}.pdf", mimetype='application/pdf')

    else:
        flash('Unknown report type', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/drive/<int:drive_id>/report/applicants/<string:file_format>')
@login_required
def download_applicants_report(drive_id, file_format):
    if not isinstance(current_user._get_current_object(), AdminUser):
        return redirect(url_for('auth.admin_login'))
        
    from models import JobApplication, PlacementDrive
    drive = PlacementDrive.query.get_or_404(drive_id)
    applications = JobApplication.query.filter_by(drive_id=drive.id).join(JobApplication.student).all()
    
    from datetime import datetime
    download_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = f"applicants_{drive.job_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    data = []
    for app in applications:
        s = app.student
        data.append({
            'Roll No': s.roll_no,
            'Name': s.name,
            "Father's Name": s.fathers_name,
            "College Name": s.college_name,
            'Email': s.email,
            'Mobile': s.mobile,
            'Status': app.status,
            'Applied Date': app.applied_at.strftime('%Y-%m-%d'),
            'Resume': url_for('static', filename=s.resume_path, _external=True) if s.resume_path else 'N/A'
        })
        
    if file_format == 'excel':
        cols = ['Roll No', 'Name', "Father's Name", "College Name", 'Email', 'Mobile', 'Status', 'Applied Date', 'Resume']
        excel_out = generate_excel(data, cols)
        return send_file(excel_out, as_attachment=True, download_name=f"{filename}.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        html = render_template('reports/applicant_report.html', drive=drive, applications=applications, download_time=download_time)
        pdf = generate_pdf(html)
        return send_file(pdf, as_attachment=True, download_name=f"{filename}.pdf", mimetype='application/pdf')
