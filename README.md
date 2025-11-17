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

1. Create and activate a virtual environment (if you don't already have one):

```
python -m venv myenv
myenv\Scripts\activate.bat
```

Optional: upgrade pip and install dependencies:

```
python -m pip install --upgrade pip
```

2. Run migrations and create a superuser:

```
python .\student_repo\manage.py migrate
python .\student_repo\manage.py createsuperuser
```

3. Run the development server:

```
python .\student_repo\manage.py runserver
```

4. Run tests:

```
python .\student_repo\manage.py test
```

That's it — open http://127.0.0.1:8000/ and log in.

Requirements
- A minimal `requirements.txt` is included containing only the essential pinned packages (e.g. `django-widget-tweaks==1.5.0`).
- To install dependencies in any environment run:

```
python -m pip install -r requirements.txt
```

Don't overwrite `requirements.txt` with a full `pip freeze` unless you intend to capture every package in your current environment. Prefer adding new top-level packages by:

1. Installing locally:
```
python -m pip install <package>
```
2. Pinning the package in `requirements.txt` manually (e.g. `package==1.2.3`) or by copying the single line from a temporary freeze:
```
python -m pip freeze > /tmp/reqs.txt
# copy the single package line you need into requirements.txt
```
This keeps `requirements.txt` minimal and easier to maintain for collaborators and CI.
