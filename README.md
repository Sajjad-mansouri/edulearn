# EduLearn — Learning Management System

EduLearn is a full-stack **Learning Management System (LMS)** built with Django, Django REST Framework, and Vanilla JavaScript.

The platform provides separate experiences for students and instructors, supporting course discovery, enrollment, curriculum management, learning progress, assessments, certificates, user profiles, and course payments.

## 🌐 Live Demo

**Live application:** Add your PythonAnywhere URL here.

> EduLearn is currently deployed on PythonAnywhere.

---

## ✨ Features

### 🎓 Student

* Browse and discover courses
* Filter courses by category, subcategory, level, price, and course metadata
* View course details and curriculum
* Enroll in courses
* Purchase paid courses
* Track learning progress
* Resume video lessons from the previous position
* Complete lessons
* Take quizzes
* Submit assignments
* Rate and review courses
* Add courses to a wishlist
* View certificates
* Manage student profile
* View learning statistics
* Manage account settings

### 👨‍🏫 Instructor

* Instructor dashboard
* Create and manage courses
* Manage course sections and lessons
* Add different types of lesson content
* Submit courses for review
* Manage enrolled students
* Manage assignments
* View course-related statistics
* Manage instructor profile
* Manage instructor account settings

### 📚 Course & Curriculum

EduLearn organizes courses into structured curricula.

```text
Course
├── Section
│   ├── Lesson
│   │   └── Lesson Content
│   └── Lesson
└── Section
    └── Lesson
```

Supported lesson content includes:

* Video
* Article
* File
* Quiz
* Assignment
* Live session
* Coding exercise

### 📈 Learning Progress

The platform tracks learning activity and course progress, including:

* Lesson progress
* Video watched time
* Video resume position
* Completion percentage
* Course progress
* Last activity
* Enrollment status
* Course completion

### 📝 Assessments

EduLearn supports assessments as part of the learning experience.

Assessment functionality includes:

* Quizzes
* Questions and choices
* Quiz attempts
* Quiz answers
* Assignments
* Assignment submissions

### 🔐 Authentication & Authorization

The application includes:

* User registration
* Email confirmation
* JWT authentication
* Student and instructor roles
* Role-based permissions
* Protected API endpoints
* Ownership-based authorization
* User sessions
* Login history
* Account security settings

### 👤 Profiles

EduLearn provides dedicated profile functionality for students and instructors.

#### Student Profile

Includes:

* Profile information
* Learning statistics
* Enrolled courses
* Completed courses
* Certificates
* Skills
* Learning goals
* Wishlist
* Learning streak

#### Instructor Profile

Includes:

* Professional information
* Headline
* Biography
* Organization
* Experience
* Expertise
* Education
* Certifications
* Languages
* Website
* LinkedIn
* GitHub
* Publications
* Teaching philosophy
* Published courses

A user can have both student and instructor roles.

---

## 💳 Payments

EduLearn integrates with **Stripe** for course payments.

The current implementation supports:

* One-time course payments
* Stripe payment processing
* Payment status tracking
* Successful payments
* Failed payments
* Stripe payment identifiers
* Enrollment activation after successful payment

The application currently uses **Stripe Test Mode** for development and demonstration.

No real customer charges are processed in the current environment.

> Refund functionality is not currently implemented.

### Payment Flow

```text
Student
   │
   ▼
Select Course
   │
   ▼
Create Payment
   │
   ▼
Stripe Checkout
   │
   ▼
Payment Processing
   │
   ├── Failed
   │
   └── Succeeded
          │
          ▼
   Payment Confirmation
          │
          ▼
      Enrollment
```

Stripe credentials are stored in environment variables and are not committed to the repository.

---

## 📜 Certificates

EduLearn provides certificates for eligible completed courses.

Certificate functionality includes:

* Certificate generation
* PDF certificates
* Certificate storage
* Certificate download
* Certificate delivery

---

## 🔄 Course Publishing

Courses support a structured publishing and review workflow.

```text
Draft
  │
  ▼
Submitted
  │
  ▼
Under Review
  │
  ├──► Changes Requested
  │
  ├──► Rejected
  │
  └──► Approved
          │
          ▼
      Published
```

---

## 🏗️ Architecture

EduLearn uses Django as the backend framework and Django REST Framework for API development.

The frontend communicates with the backend through HTTP APIs using the Fetch API.

```text
┌──────────────────────────┐
│        Frontend          │
│   HTML / CSS / JS        │
└────────────┬─────────────┘
             │
             │ Fetch API
             ▼
┌──────────────────────────┐
│    Django REST API       │
│          DRF             │
└────────────┬─────────────┘
             │
      ┌──────┼───────┐
      │      │       │
      ▼      ▼       ▼
 Serializers Views Permissions
      │      │       │
      └──────┼───────┘
             ▼
┌──────────────────────────┐
│   Services / Selectors   │
│      Business Logic      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│       Django ORM         │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│         Database         │
└──────────────────────────┘
```

The backend separates responsibilities across models, serializers, views/viewsets, permissions, services, and selectors where appropriate.

---

## 🧩 Django Applications

EduLearn is organized into focused Django applications:

| Application    | Responsibility                                                                       |
| -------------- | ------------------------------------------------------------------------------------ |
| `accounts`     | User accounts, authentication, roles, sessions, and account security                 |
| `assessments`  | Quizzes, questions, choices, attempts, answers, assignments, and submissions         |
| `certificates` | Course completion certificates and certificate generation                            |
| `courses`      | Courses, categories, feedback, tags, wishlists, and course-related functionality     |
| `curriculums`  | Sections, lessons, lesson content, videos, articles, files, and curriculum structure |
| `enrollments`  | Course enrollment and student learning progress                                      |
| `instructors`  | Instructor-specific functionality and instructor management                          |
| `payments`     | Stripe payments and payment records                                                  |
| `profiles`     | Student and instructor profile information                                           |

This separation keeps the application domain organized and makes individual areas easier to maintain and test.

---

## 🛠️ Technology Stack

### Backend

* Python
* Django
* Django REST Framework
* Django ORM
* JWT Authentication
* Stripe API

### Frontend

* HTML5
* CSS3
* Vanilla JavaScript
* Fetch API

The frontend does not use React, Vue, Angular, or another JavaScript framework.

### Testing

* pytest
* pytest-django

### Deployment

* PythonAnywhere
* Django WSGI

---

## 📂 Project Structure

```text
edulearn/
├── accounts/
├── assessments/
├── certificates/
├── courses/
├── curriculums/
├── enrollments/
├── instructors/
├── payments/
├── profiles/
│
├── templates/
├── static/
│   ├── css/
│   └── js/
├── media/
├── tests/
├── manage.py
└── requirements.txt
```

Each Django application contains its own domain-specific models, API components, services, and supporting code where applicable.

---

## 🧪 Testing

EduLearn uses **pytest** and **pytest-django** for automated testing.

Tests focus on application behavior and business rules rather than testing Django or Django REST Framework internals.

The test suite covers areas including:

* Model behavior
* Model validation
* Database constraints
* Serializers
* API endpoints
* Authentication
* Authorization
* Permissions
* Ownership rules
* Business logic
* Course functionality
* Enrollment behavior
* Learning progress
* Assessment functionality
* Payment behavior
* Certificate functionality
* Error and edge cases

Run the test suite with:

```bash
pytest
```

---

## ⚙️ Local Development

Clone the repository:

```bash
git clone https://github.com/Sajjad-mansouri/edulearn.git
cd edulearn
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver
```

The application will be available at:

```text
http://127.0.0.1:8000/
```

---

## 🔑 Environment Configuration

Sensitive configuration is provided through environment variables.

Example:

```env
DEBUG=True
SECRET_KEY=your-secret-key

STRIPE_SECRET_KEY=your-stripe-test-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-test-publishable-key
```

Additional environment variables may be required depending on the local configuration.

**Never commit secret keys, passwords, or other sensitive credentials to the repository.**

---

## 🚀 Deployment

EduLearn is currently deployed on **PythonAnywhere**.

The deployed application uses Django's WSGI interface.

```text
             Internet
                 │
                 ▼
       ┌──────────────────┐
       │  PythonAnywhere  │
       │    Web App       │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │   Django / WSGI  │
       └────────┬─────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
    Database        Static / Media
```

The current deployment does **not** depend on:

* PostgreSQL
* Redis
* Nginx
* Gunicorn
* Docker

These technologies are therefore not included in EduLearn's current deployment stack.

---

## 🎯 Project Goals

EduLearn was developed to demonstrate practical experience with:

* Django application architecture
* Django REST Framework
* REST API development
* Authentication and authorization
* Role-based access control
* Course and curriculum management
* Learning progress tracking
* Assessment functionality
* Certificate generation
* Stripe payment integration
* Automated testing
* Responsive frontend development
* Production deployment

---

## 🗺️ Future Improvements

Potential future improvements include:

* Advanced course recommendations
* Improved course search
* Real-time messaging
* Live classes
* Additional assessment functionality
* Advanced instructor analytics
* Enhanced notification features
* Additional payment functionality

---

## 📄 License

This project is currently developed as a portfolio project.

License information can be added when the project is released under a specific open-source license.

---

## 👨‍💻 About

**EduLearn** is a full-stack Learning Management System developed to demonstrate practical experience with Django, Django REST Framework, authentication and authorization, database design, course management, learning progress, assessment systems, Stripe payment integration, automated testing, and frontend development with Vanilla JavaScript.
