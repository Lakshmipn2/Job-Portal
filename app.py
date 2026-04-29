# ============================================
# Job Portal Web Application
# Backend: Flask, SQLAlchemy, Flask-Login
# ============================================

from flask import Flask, render_template, redirect, request, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# ── App Configuration ──────────────────────
app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL", "sqlite:///database.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "1896436d2a6a6e30a2373b99679d1418"

db = SQLAlchemy(app)

# ── Login Manager Setup ──────────────────────
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ── Database Models ──────────────────────

# User Model - stores all users (Job seekers, Employers)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), nullable = False)
    email = db.Column(db.String(30), nullable = False, unique = True)
    phone_number = db.Column(db.String(30), nullable = False)
    password = db.Column(db.String(30), nullable = False)
    role = db.Column(db.String(30), nullable = False) # Job-Seeker or Employer

# Job Model - stores all users (Job seekers, Employers)
class Job(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(30), nullable = False)
    company_name = db.Column(db.String(30), nullable = False)
    description = db.Column(db.String(300), nullable = False)
    experience = db.Column(db.String(30), nullable = False)
    location = db.Column(db.String(30), nullable = False)
    salary = db.Column(db.String(30), nullable = False)
    contact_info = db.Column(db.String(30), nullable = False)
    employer_id = db.Column(db.Integer, db.ForeignKey("user.id")) # Links to Employer
    applications = db.relationship("Application") # All Applications for this job

# Application Model - stores Job Applications made by Job Seekers
class Application(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # Links to Job-Seeker
    job_id = db.Column(db.Integer, db.ForeignKey("job.id")) # Links to Job
    applied_on = db.Column(db.DateTime)
    job = db.relationship("Job")
    user = db.relationship("User", foreign_keys=[user_id])
    status = db.Column(db.String(20), default="Pending") # Pending/Accepted/Rejected

# ── Create all Database Tables ──────────────────────
with app.app_context():
    db.create_all()

# ── Load User for Flask-Login ──────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Routes ──────────────────────

#Homepage
@app.route("/")
def home():
    return render_template("home.html")

# Register - Handles New User Registration
@app.route("/register",methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        phone_number = request.form.get("phone_number")
        role = request.form.get("role")

        # Hash Password before saving
        hashed_password = generate_password_hash(password)

        new_user = User(name=name, email=email, password=hashed_password, phone_number=phone_number, role=role)
        db.session.add(new_user)
        db.session.commit()
    else:
        return render_template("register.html")

    flash("Registration successful! Please login.", "success")
    return redirect("/login")

# Login - Handles User Login and Role based redirect
@app.route("/login",methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Redirect based on Role
            if current_user.role == "Job-Seeker":
                return redirect("/jobseeker/dashboard")
            elif current_user.role == "Employer":
                return redirect("/employer/dashboard")
        else:
            flash("Invalid email or password!", "danger")
            return render_template("login.html")
    else:
        return render_template("login.html")

# Employer Dashnoard
@app.route("/employer/dashboard")
@login_required
def employer_dashboard():
    return render_template("employer_dashboard.html")

# Job Seeker Dashboard - shows Application Status counts
@app.route("/jobseeker/dashboard")
@login_required
def jobseeker_dashboard():
    pending = Application.query.filter_by(
        user_id=current_user.id, status="Pending").count()
    accepted = Application.query.filter_by(
        user_id=current_user.id, status="Accepted").count()
    rejected = Application.query.filter_by(
        user_id=current_user.id, status="Rejected").count()
    return render_template("job_seeker_dashboard.html", 
        pending=pending, accepted=accepted, rejected=rejected)

# Post Job - Allows Employers to Post new Jobs
@app.route("/post-job", methods=["GET", "POST"])
@login_required
def post_job():  
    if request.method == "POST":
        title = request.form.get("title")
        company_name = request.form.get("company_name")
        description = request.form.get("description")
        experience = request.form.get("experience")
        location = request.form.get("location")
        salary = request.form.get("salary")
        contact_info = request.form.get("contact_info")

        new_job = Job(title=title, company_name=company_name, description=description, experience=experience, location=location, salary=salary, contact_info=contact_info, employer_id=current_user.id)
        db.session.add(new_job)
        db.session.commit()
        flash("Job posted successfully!", "success")
        return redirect("/employer/dashboard")
    else:
        return render_template("post_job.html")

# Browse Jobs - shows all Jobs to Job Seekers
@app.route("/browse-job")
@login_required
def browse_job():
    jobs = Job.query.all()
    # Get list of Job IDs already applied by Current User
    applied_jobs = [a.job_id for a in Application.query.filter_by(user_id=current_user.id).all()]
    return render_template("browse_job.html", jobs=jobs, applied_jobs=applied_jobs)

# Apply - saves Job Application to Database
@app.route("/apply/<int:job_id>")
@login_required
def apply(job_id):
    new_application = Application(user_id = current_user.id, job_id = job_id, applied_on = datetime.now())
    db.session.add(new_application)
    db.session.commit()
    return redirect("/jobseeker/dashboard")

# My Applications - shows all Applications of Current Job Seeker
@app.route("/my-applications")
@login_required
def my_applications():
    applications = Application.query.filter_by(user_id=current_user.id).all()
    return render_template("my_applications.html", applications=applications)

# Employer Application - shows all Applications Received by Employer
@app.route("/employer/applications")
@login_required
def employer_applications():
    jobs = Job.query.filter_by(employer_id=current_user.id).all()
    return render_template("employer_applications.html", jobs=jobs)

# Accept Application - Employer Accepts a Job Application
@app.route("/application/accept/<int:application_id>")
@login_required
def accept_application(application_id):
    application = Application.query.get(application_id)
    application.status = "Accepted"
    db.session.commit()
    return redirect("/employer/applications")

# Reject Application - Employer Rejects a Job Application
@app.route("/application/reject/<int:application_id>")
@login_required
def reject_application(application_id):
    application = Application.query.get(application_id)
    application.status = "Rejected"
    db.session.commit()
    return redirect("/employer/applications")

# Logout - Logs out Current User and redirects to Homepage
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)