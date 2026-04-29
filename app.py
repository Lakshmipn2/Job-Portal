from flask import Flask, render_template, redirect, request, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "1896436d2a6a6e30a2373b99679d1418"

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), nullable = False)
    email = db.Column(db.String(30), nullable = False, unique = True)
    phone_number = db.Column(db.String(30), nullable = False)
    password = db.Column(db.String(30), nullable = False)
    role = db.Column(db.String(30), nullable = False)
    resume = db.Column(db.String(200))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(30), nullable = False)
    company_name = db.Column(db.String(30), nullable = False)
    description = db.Column(db.String(300), nullable = False)
    experience = db.Column(db.String(30), nullable = False)
    location = db.Column(db.String(30), nullable = False)
    salary = db.Column(db.String(30), nullable = False)
    contact_info = db.Column(db.String(30), nullable = False)
    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    applications = db.relationship("Application")

class Application(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    applied_on = db.Column(db.DateTime)
    job = db.relationship("Job")
    user = db.relationship("User", foreign_keys=[user_id])
    status = db.Column(db.String(20), default="Pending")

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("home.html")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/register",methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        phone_number = request.form.get("phone_number")
        role = request.form.get("role")

        hashed_password = generate_password_hash(password)

        resume_filename = None
        resume = request.files.get("resume")
        if resume and resume.filename != "":
            filename = secure_filename(resume.filename)
            resume.save(os.path.join(app.root_path, "static/resumes", filename))
            resume_filename = filename

        new_user = User(name=name, email=email, password=hashed_password, phone_number=phone_number, role=role, resume=resume_filename)
        db.session.add(new_user)
        db.session.commit()
    else:
        return render_template("register.html")

    flash("Registration successful! Please login.", "success")
    return redirect("/login")

@app.route("/login",methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if current_user.role == "Job-Seeker":
                return redirect("/jobseeker/dashboard")
            elif current_user.role == "Employer":
                return redirect("/employer/dashboard")
        else:
            flash("Invalid email or password!", "danger")
            return render_template("login.html")
    else:
        return render_template("login.html")

@app.route("/employer/dashboard")
@login_required
def employer_dashboard():
    return render_template("employer_dashboard.html")

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

@app.route("/browse-job")
@login_required
def browse_job():
    jobs = Job.query.all()
    applied_jobs = [a.job_id for a in Application.query.filter_by(user_id=current_user.id).all()]
    return render_template("browse_job.html", jobs=jobs, applied_jobs=applied_jobs)

@app.route("/apply/<int:job_id>")
@login_required
def apply(job_id):
    new_application = Application(user_id = current_user.id, job_id = job_id, applied_on = datetime.now())
    db.session.add(new_application)
    db.session.commit()
    return redirect("/jobseeker/dashboard")

@app.route("/my-applications")
@login_required
def my_applications():
    applications = Application.query.filter_by(user_id=current_user.id).all()
    return render_template("my_applications.html", applications=applications)

@app.route("/employer/applications")
@login_required
def employer_applications():
    jobs = Job.query.filter_by(employer_id=current_user.id).all()
    return render_template("employer_applications.html", jobs=jobs)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/application/accept/<int:application_id>")
@login_required
def accept_application(application_id):
    application = Application.query.get(application_id)
    application.status = "Accepted"
    db.session.commit()
    return redirect("/employer/applications")

@app.route("/application/reject/<int:application_id>")
@login_required
def reject_application(application_id):
    application = Application.query.get(application_id)
    application.status = "Rejected"
    db.session.commit()
    return redirect("/employer/applications")

if __name__ == "__main__":
    app.run(debug=True)