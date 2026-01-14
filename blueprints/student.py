from flask import Blueprint, render_template, redirect, url_for, flash, send_file, request
from flask_login import login_required, current_user
from models import Student, Quiz, QuizAttempt, Question
from extensions import db

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user._get_current_object(), Student):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.student_login'))
    
    if not current_user.is_password_changed:
        flash('You must change your password first.', 'warning')
        return redirect(url_for('auth.change_password'))
        
    if not current_user.is_email_verified:
        flash('Please verify your email address.', 'warning')
        return redirect(url_for('auth.student_login'))

    return render_template('student_dashboard.html', student=current_user)

@student_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if not isinstance(current_user._get_current_object(), Student):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.student_login'))
        
    # Import locally to avoid circular import
    from forms import StudentProfileForm
    from models import ProfileUpdateRequest
    from extensions import db
    import json
    from datetime import date
    
    
    form = StudentProfileForm(obj=current_user)
    
    # Pre-populate backlog details if student has backlogs
    # Pre-populate backlog details if student has backlogs
    if request.method == 'GET':
        print(f"DEBUG: Checking backlogs for user {current_user.id}")
        if hasattr(current_user, 'backlogs_list'):
            print(f"DEBUG: Backlogs list count: {len(current_user.backlogs_list)}")
            if current_user.backlogs_list:
                import json
                backlog_data = [{'subject': b.subject_name, 'semester': b.semester} for b in current_user.backlogs_list]
                json_data = json.dumps(backlog_data)
                print(f"DEBUG: JSON data to load: {json_data}")
                form.backlog_details.data = json_data
            else:
                print("DEBUG: Backlogs list is empty")
        else:
            print("DEBUG: No backlogs_list attribute")
    
    if form.validate_on_submit():
        from werkzeug.utils import secure_filename
        import os
        from flask import current_app
        
        if current_user.status == 'Pending':
            # Handle mutual exclusivity
            if form.metric_type.data == 'cgpa':
                current_user.cgpa = form.cgpa.data
                current_user.backlogs = 0
                # Clear existing backlog details
                from models import Backlog
                Backlog.query.filter_by(student_id=current_user.id).delete()
            else:  # backlogs
                current_user.cgpa = None
                # Parse and save backlog details
                import json
                backlog_data = json.loads(form.backlog_details.data)
                current_user.backlogs = len(backlog_data)
                
                # Clear existing and add new backlog details
                from models import Backlog
                Backlog.query.filter_by(student_id=current_user.id).delete()
                for entry in backlog_data:
                    backlog = Backlog(
                        student_id=current_user.id,
                        subject_name=entry['subject'],
                        semester=entry['semester']
                    )
                    db.session.add(backlog)
            
            # Direct Update: Populate manual to avoid FileStorage overwriting string path
            # roll_no and email are not editable via this form (immutable identity)
            current_user.name = form.name.data
            current_user.fathers_name = form.fathers_name.data
            current_user.college_name = form.college_name.data
            current_user.mobile = form.mobile.data
            current_user.dob = form.dob.data
            current_user.gender = form.gender.data
            current_user.address = form.address.data
            current_user.department = form.department.data
            current_user.semester = form.semester.data
            current_user.tenth_marks = form.tenth_marks.data
            current_user.twelfth_marks = form.twelfth_marks.data
            current_user.skills = form.skills.data
            current_user.projects_internship = form.projects_internship.data
            
            # Handle Files
            if form.profile_photo.data:
                f = form.profile_photo.data
                filename = secure_filename(f"{current_user.roll_no}_photo_{f.filename}")
                path = os.path.join(current_app.root_path, 'static/uploads/profiles', filename)
                f.save(path)
                current_user.profile_photo = f"uploads/profiles/{filename}"
                
            if form.resume.data:
                f = form.resume.data
                filename = secure_filename(f"{current_user.roll_no}_resume_{f.filename}")
                path = os.path.join(current_app.root_path, 'static/uploads/resumes', filename)
                f.save(path)
                current_user.resume_path = f"uploads/resumes/{filename}"
                
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('student.dashboard'))
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('student.dashboard'))
        
        elif current_user.status == 'Approved':
            # Handle Files immediately (as agreed)
            files_uploaded = False
            # Check if data is string (existing filename) or empty
            if form.profile_photo.data and not isinstance(form.profile_photo.data, str):
                f = form.profile_photo.data
                if f.filename: # Ensure it has a filename
                    filename = secure_filename(f"{current_user.roll_no}_photo_{f.filename}")
                    path = os.path.join(current_app.root_path, 'static/uploads/profiles', filename)
                    f.save(path)
                    current_user.profile_photo = f"uploads/profiles/{filename}"
                    files_uploaded = True
                
            if form.resume.data and not isinstance(form.resume.data, str):
                f = form.resume.data
                if f.filename: # Ensure it has a filename
                    filename = secure_filename(f"{current_user.roll_no}_resume_{f.filename}")
                    path = os.path.join(current_app.root_path, 'static/uploads/resumes', filename)
                    f.save(path)
                    current_user.resume_path = f"uploads/resumes/{filename}"
                    files_uploaded = True
                
            if files_uploaded:
                db.session.commit()

            # Request Approval for other fields
            changes = {}
            for field in form:
                # Exclude fields that don't exist in Student model or shouldn't be updated
                # ALSO exclude 'cgpa' and 'backlogs' here, we will handle them manually to enforce mutual exclusivity
                if field.name not in ['csrf_token', 'submit', 'profile_photo', 'resume', 'metric_type', 'backlog_details', 'cgpa', 'backlogs']:
                    old_val = getattr(current_user, field.name)
                    new_val = field.data
                    
                    # Store only if changed
                    if str(old_val) != str(new_val):
                         changes[field.name] = str(new_val) if isinstance(new_val, date) else new_val
            
            # Manually handle mutual exclusivity for CGPA and Backlogs
            if form.metric_type.data == 'cgpa':
                if str(current_user.cgpa) != str(form.cgpa.data):
                    changes['cgpa'] = form.cgpa.data
                # Ensure backlogs is zero in request if it wasn't before
                if current_user.backlogs != 0:
                     changes['backlogs'] = 0
            else: # backlogs
                # Ensure CGPA is None in request if it wasn't before
                if current_user.cgpa is not None:
                    changes['cgpa'] = None
                
                # Calculate backlog count
                import json
                try:
                    backlog_details_json = form.backlog_details.data
                    if backlog_details_json:
                        backlog_data = json.loads(backlog_details_json)
                        new_backlog_count = len(backlog_data)
                        if current_user.backlogs != new_backlog_count:
                             changes['backlogs'] = new_backlog_count
                        
                        # Note: We can't easily store pending changes for the 'Backlog' table in this flat 'changes' dict 
                        # designed for Student model columns. 
                        # For now, if student is 'Approved', changing backlogs might require more complex logic 
                        # if we want to preview the *details* in admin panel.
                        # However, storing the integer count is a good start.
                        # Realistically, for 'Approved' students, we might want to auto-approve the details 
                        # or store them in a special field in ProfileUpdateRequest if we extended it.
                        # Given the current system constraints, we'll store the Count change.
                        # The Admin will see "Backlogs: 0 -> 2". 
                        # The details won't be in the pending request JSON structure easily unless we hack it.
                        
                        changes['backlog_details_dump'] = backlog_details_json # Store it potentially for admin custom handling
                    
                except:
                    pass
            
            if changes:
                existing_req = ProfileUpdateRequest.query.filter_by(student_id=current_user.id, status='Pending').first()
                if existing_req:
                    flash('You already have a pending profile update request.', 'warning')
                else:
                    req = ProfileUpdateRequest(
                        student_id=current_user.id,
                        requested_changes=json.dumps(changes)
                    )
                    db.session.add(req)
                    db.session.commit()
                    flash('Changes submitted for Admin approval. Files uploaded immediately.', 'info')
            elif files_uploaded:
                 flash('Files uploaded successfully.', 'success')
            else:
                flash('No changes detected.', 'info')
                
            return redirect(url_for('student.dashboard'))
            
            
    return render_template('student_profile_edit.html', form=form)

@student_bp.route('/drives')
@login_required
def list_drives():
    if not isinstance(current_user._get_current_object(), Student):
         return redirect(url_for('auth.student_login'))
         
    if current_user.status != 'Approved':
        flash('Your account is pending approval. You cannot browse jobs yet.', 'warning')
        return redirect(url_for('student.dashboard'))
         
    from models import PlacementDrive, JobApplication
    from datetime import datetime
    
    # Get active drives (deadline not passed)
    drives = PlacementDrive.query.filter(PlacementDrive.deadline >= datetime.utcnow().date()).order_by(PlacementDrive.created_at.desc()).all()
    
    # Get IDs of drives already applied to
    applied_drive_ids = [app.drive_id for app in current_user.applications]
    
    return render_template('student_drives.html', drives=drives, applied_drive_ids=applied_drive_ids, student=current_user, datetime=datetime)

    return render_template('student_drives.html', drives=drives, applied_drive_ids=applied_drive_ids, student=current_user)

@student_bp.route('/resume/data', methods=['POST'])
@login_required
def save_resume_data():
    if not isinstance(current_user._get_current_object(), Student):
         return "Unauthorized", 401
         
    import os
    import json
    from flask import current_app, jsonify
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    # Validation limits/sanitization could be added here
    
    filename = f"{current_user.roll_no}_resume_data.json"
    upload_folder = os.path.join(current_app.root_path, 'static/uploads/resume_data')
    os.makedirs(upload_folder, exist_ok=True)
    
    path = os.path.join(upload_folder, filename)
    with open(path, 'w') as f:
        json.dump(data, f)
        
    current_user.resume_data_path = f"uploads/resume_data/{filename}"
    db.session.commit()
    
    return jsonify({'success': True})

def get_resume_data(student):
    import os
    import json
    from flask import current_app
    
    default_data = {
        'aim': '',
        'hobbies': '',
        'strengths': '',
        'weaknesses': '',
        'achievements': '',
        'school_10_name': '',
        'school_10_year': '',
        'school_12_name': '',
        'school_12_year': ''
    }
    
    if student.resume_data_path:
        path = os.path.join(current_app.root_path, 'static', student.resume_data_path)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    saved_data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_data.update(saved_data)
            except:
                pass
    return default_data

@student_bp.route('/resume/builder')
@login_required
def resume_builder():
    resume_data = get_resume_data(current_user._get_current_object())
    return render_template('student_resume_preview.html', resume_data=resume_data)

@student_bp.route('/resume/generate', methods=['POST'])
@login_required
def generate_resume():
    if not isinstance(current_user._get_current_object(), Student):
         return redirect(url_for('auth.student_login'))
         
    template_name = request.form.get('template', 'modern')
    # Validate template name to prevent LFI
    if template_name not in ['modern', 'classic', 'minimal', 'creative', 'professional']:
        template_name = 'modern'
    
    # Reload fresh data
    resume_data = get_resume_data(current_user._get_current_object())
        
    html = render_template(f'resume_templates/{template_name}.html', student=current_user, r=resume_data)
    
    from xhtml2pdf import pisa
    from io import BytesIO
    
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    
    if pisa_status.err:
        flash('Error generating PDF', 'danger')
        return redirect(url_for('student.resume_builder'))
        
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"{current_user.roll_no}_Resume.pdf",
        mimetype='application/pdf'
    )

@student_bp.route('/resume/preview-html')
@login_required
def preview_resume_html():
    if not isinstance(current_user._get_current_object(), Student):
         return "Unauthorized", 401
         
    template_name = request.args.get('template', 'modern')
    if template_name not in ['modern', 'classic', 'minimal', 'creative', 'professional']:
        template_name = 'modern'
    
    resume_data = get_resume_data(current_user._get_current_object())
        
    return render_template(f'resume_templates/{template_name}.html', student=current_user, preview=True, r=resume_data)

@student_bp.route('/drive/<int:drive_id>/apply', methods=['POST'])
@login_required
def apply_drive(drive_id):
    if not isinstance(current_user._get_current_object(), Student):
         return redirect(url_for('auth.student_login'))
         
    from models import PlacementDrive, JobApplication
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Check if already applied
    if JobApplication.query.filter_by(student_id=current_user.id, drive_id=drive.id).first():
        flash('You have already applied for this drive.', 'warning')
        return redirect(url_for('student.list_drives'))
        
    # Check Eligibility
    reasons = []
    if (current_user.tenth_marks or 0) < drive.criteria_10th:
        reasons.append(f"10th Marks < {drive.criteria_10th}%")
    if (current_user.twelfth_marks or 0) < drive.criteria_12th:
        reasons.append(f"12th Marks < {drive.criteria_12th}%")
    if (current_user.cgpa or 0) < drive.criteria_cgpa:
        reasons.append(f"Diploma CGPA < {drive.criteria_cgpa}")
    
    if drive.allowed_branches:
        allowed = [b.strip().lower() for b in drive.allowed_branches.split(',')]
        if current_user.department.lower() not in allowed:
             reasons.append(f"Department '{current_user.department}' not eligible.")
             
    if reasons:
        flash(f'Not Eligible: {", ".join(reasons)}', 'danger')
        return redirect(url_for('student.list_drives'))
        
    # Apply
    application = JobApplication(student_id=current_user.id, drive_id=drive.id)
    db.session.add(application)
    db.session.commit()
    
    flash(f'Successfully applied for {drive.job_title} at {drive.company.name}!', 'success')
    return redirect(url_for('student.list_drives'))

@student_bp.route('/quizzes')
@login_required
def list_quizzes():
    if not isinstance(current_user._get_current_object(), Student):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.student_login'))
        
    from models import Quiz, QuizAttempt, JobApplication
    from datetime import datetime
    
    # Get IDs of drives applied to
    applied_drive_ids = [app.drive_id for app in current_user.applications]
    
    # Filter quizzes: 
    # 1. Linked to one of the applied drives
    # 2. Is Live (is_live=True OR live_at <= now)
    
    now = datetime.now()
    
    # Using python filtering for complex OR logic if simple query is hard, 
    # or use sqlalchemy logic.
    # Quiz.drive_id.in_(applied_drive_ids) AND (Quiz.is_live == True OR Quiz.live_at <= now)
    
    quizzes_query = Quiz.query.filter(Quiz.drive_id.in_(applied_drive_ids))
    all_quizzes = quizzes_query.all()
    
    available_quizzes = []
    for quiz in all_quizzes:
        is_live_now = quiz.is_live or (quiz.live_at and quiz.live_at <= now)
        if is_live_now:
            attempt = QuizAttempt.query.filter_by(student_id=current_user.id, quiz_id=quiz.id).first()
            available_quizzes.append({
                'quiz': quiz,
                'attempt': attempt
            })
            
    # Optional: If you want to show "Upcoming" quizzes, handle that separately or include them with a "locked" status.
    # User said: "not accessible to anyone until admin makes it live". So we hide them.
        
    return render_template('student_quizzes.html', quizzes=available_quizzes)

@student_bp.route('/quiz/<int:quiz_id>/start', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    if not isinstance(current_user._get_current_object(), Student):
        flash('Unauthorized', 'danger')
        return redirect(url_for('auth.student_login'))
        
    quiz = Quiz.query.get_or_404(quiz_id)
    from datetime import datetime
    
    # Access Control Check
    # 1. Check if applied to drive
    applied_drive_ids = [app.drive_id for app in current_user.applications]
    if quiz.drive_id not in applied_drive_ids:
        flash('Access Denied. You must apply to the associated Placement Drive to take this quiz.', 'danger')
        return redirect(url_for('student.list_quizzes'))
        
    # 2. Check if Live
    if not (quiz.is_live or (quiz.live_at and quiz.live_at <= datetime.now())):
         flash('This quiz is not live yet.', 'warning')
         return redirect(url_for('student.list_quizzes'))
    
    # Check if already attempted
    existing_attempt = QuizAttempt.query.filter_by(student_id=current_user.id, quiz_id=quiz.id).first()
    if existing_attempt:
        flash('You have already taken this assessment.', 'info')
        return redirect(url_for('student.list_quizzes'))
        
    if request.method == 'POST':
        import json
        
        # Grade the quiz
        score = 0
        total_questions = len(quiz.questions)
        answers_data = {}
        
        for question in quiz.questions:
            selected_option = request.form.get(f'question_{question.id}')
            answers_data[str(question.id)] = selected_option
            
            if selected_option and selected_option == question.correct_option:
                score += question.marks
        
        # Determine pass/fail 
        total_marks = sum(q.marks for q in quiz.questions)
        percentage = (score / total_marks * 100) if total_marks > 0 else 0
        
        # Use dynamic pass percentage
        required_percentage = quiz.pass_percentage if quiz.pass_percentage is not None else 50.0
        passed = percentage >= required_percentage
        
        attempt = QuizAttempt(
            student_id=current_user.id,
            quiz_id=quiz.id,
            score=score,
            total_marks=total_marks,
            passed=passed,
            answers=json.dumps(answers_data)
        )
        db.session.add(attempt)
        db.session.commit()
        
        flash(f'Assessment submitted. Your score: {score}/{total_marks}', 'success' if passed else 'warning')
        return redirect(url_for('student.list_quizzes'))
        
    return render_template('student_take_quiz.html', quiz=quiz)
