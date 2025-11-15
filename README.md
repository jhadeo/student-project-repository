# student-project-repository

Minimal Django student project submission & review app.

Features 
- Accounts & roles: Students, Faculty, Admin with simple decorators and profile types.
- Project submissions & versioning: upload projects and keep multiple versions.
- Review workflow: faculty can review, approve or reject with feedback.
- Search & filters: dynamic search, status and date-range filters on submissions.
- Soft delete: projects are soft-deletable for auditability.
- Admin overrides: admins can set/override project status while keeping audit trail.

Quick start (Windows cmd)

1. Activate the virtual environment:

```
.\myenv\Scripts\activate.bat
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Run migrations and create a superuser:

```
python .\student_repo\manage.py migrate
python .\student_repo\manage.py createsuperuser
```

4. Run the development server:

```
python .\student_repo\manage.py runserver
```

5. Run tests:

```
python .\student_repo\manage.py test
```

That's it — open http://127.0.0.1:8000/ and log in.
