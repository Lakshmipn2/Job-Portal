# Job Portal Web Application
## Description
A web application where job seekers can find and apply for jobs and employers can post jobs and manage applications.
## Features
### Job Seeker
- User registration with resume upload
- Role based login and dashboard
- Browse and search job listings
- Apply for jobs
- View application status (Pending/Accepted/Rejected)
- Notification badges on dashboard
### Employer
- Post job listings
- View all applications received
- Accept or reject applications
- View applicant resumes
### General
- User authentication with password hashing
- Flash messages for feedback
- Responsive UI with Bootstrap
## Tech Stack
- Backend: Python Flask
- Database: SQLite + SQLAlchemy
- Frontend: HTML, CSS, Bootstrap
- Authentication: Flask-login
## How to Run
1. Clone the repository
2. Install dependencies: pip install -r requirements.txt
3. Run the app: python app.py
4. Open browser: http://127.0.0.1:5000
## Project Structure
- job_portal/
- ├── app.py
- ├── requirements.txt
- ├── Procfile
- ├── README.md
- ├── static/
- │   ├── css/
- │   └── resumes/
- └── templates/
## Deployment
Live at: https://job-portal-yh45.onrender.com