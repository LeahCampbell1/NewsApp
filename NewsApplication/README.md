
# News Application

## Overview

A Django-based news publishing application that allows readers, journalists and editors to interact with news content through role-based access control.

The application uses Django REST Framework to provide API functionality for managing publishers, articles, newsletters and subscriptions.

## Features

- User registration and authentication.
- Role-based access for readers, journalists and editors.
- Editors will register their publisher upon account registration.
- Publisher and journalist subscriptions.
- Article creation, editing, deletion and approval.
- Newsletter creation, editing, deletion and approval.
- Editor approval of articles and newsletters.
- Email notifications following content approval.
- Browsing publishers, journalists and published content.
- REST API endpoints for content and subscription management.
- Automated testing with Django's test framework.
- API testing through Postman collections.

## Technologies Used

- Python
- Django
- Django REST Framework
- MariaDB
- HTML and CSS
- Postman
- unittest.mock for testing and mocking external dependencies.

## Installation and Setup

### Prerequisites

- Python 3.10 or later (or the version specified by the project).
- pip
- Git
- MariaDB
- Postman (for API testing)

### 1. Clone the repository

```bash
git clone <https://github.com/LeahCampbell1/NewsApp.git>
```

Navigate to the application directory:

```bash
cd NewsApplication/news_app
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment.

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

If a requirements file is included:

```bash
pip install -r requirements.txt
```

Otherwise:

```bash
pip install django djangorestframework mysqlclient
```

### 4. MariaDB Configuration

- Ensure MariaDB is installed and the service is running.
- Ensure the application database and database user already exist.
- Activate the Django virtual environment.
- Install the MariaDB database connector if not already installed:

```bash
pip install mysqlclient
```

- Verify the existing database configuration in `settings.py`.
- Retain the provided database name, username, password, host and port.
- Ensure the configured database name matches the existing MariaDB database.

The existing database configuration is:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'news_app.db',
        'USER': 'django_user',
        'PASSWORD': 'SuperStrongPassword000',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

- Do not create the MariaDB database or database user as part of these instructions.
- Do not modify the existing database credentials in `settings.py`.

### 5. Check the Django configuration

```bash
python manage.py check
```

### 6. Apply migrations

Generate migrations:

```bash
python manage.py makemigrations
```

Apply migrations to create the application tables:

```bash
python manage.py migrate
```

### 7. Create an administrator account (optional)

```bash
python manage.py createsuperuser
```

### 8. Start the development server

```bash
python manage.py runserver
```

Access the application at:

http://127.0.0.1:8000/

---

## Application Structure

```text
NewsApplication/
│
├── news_app/
│   ├── manage.py
│   ├── good_to_know/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tests.py
│   │   ├── templates/
│   │   └── migrations/
│   │
│   └── project configuration
│
├── postman/
│   └── Postman collections
│
└── README.md
```

## API Endpoints

The application provides REST API endpoints for the following functionality.

### Publishers

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/publishers/` | List publishers |
| GET | `/api/publishers/<publisher_id>/journalists/` | List publisher journalists |
| GET | `/api/publishers/<publisher_id>/articles/` | View publisher articles |
| GET | `/api/publishers/<publisher_id>/newsletters/` | View publisher newsletters |
| GET | `/api/publisher/subscribers/` | View publisher subscribers |

### Journalists

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/journalists/<journalist_id>/articles/` | View journalist articles |
| GET | `/api/journalists/<journalist_id>/newsletters/` | View journalist newsletters |
| GET | `/api/journalist/subscribers/` | View journalist subscribers |

### Article Management

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/journalist/articles/create/` | Create article |
| PUT/PATCH | `/api/journalist/articles/<article_id>/edit/` | Edit article |
| DELETE | `/api/journalist/articles/<article_id>/delete/` | Delete article |
| PUT/PATCH | `/api/publisher/articles/<article_id>/edit/` | Edit publisher article |
| DELETE | `/api/publisher/articles/<article_id>/delete/` | Delete publisher article |

### Newsletter Management

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/journalist/newsletters/create/` | Create newsletter |
| PUT/PATCH | `/api/journalist/newsletters/<newsletter_id>/edit/` | Edit newsletter |
| DELETE | `/api/journalist/newsletters/<newsletter_id>/delete/` | Delete newsletter |
| POST | `/api/publisher/newsletters/create/` | Create publisher newsletter |
| PUT/PATCH | `/api/publisher/newsletters/<newsletter_id>/edit/` | Edit publisher newsletter |
| DELETE | `/api/publisher/newsletters/<newsletter_id>/delete/` | Delete publisher newsletter |

API access is subject to authentication and role-based permissions.

---

## Test Coverage

- Authentication and role-based permissions.
- Reader publisher and journalist subscriptions.
- Newsletter access restrictions.
- Journalist article creation and validation.
- Independent article approval.
- Publisher article approval requirements.
- Editor article approval and deletion.
- Publisher-based access restrictions.
- Approved article API responses.
- Email delivery using mocked email functionality.
- Email failure handling using unittest.mock.patch.
- Mocking external requests where applicable.

### Run all tests

```bash
python manage.py test good_to_know
```

### Run individual test classes

```bash
python manage.py test good_to_know.tests.AuthenticationTests
```

```bash
python manage.py test good_to_know.tests.SubscriptionAPITests
```

```bash
python manage.py test good_to_know.tests.NewsletterAPITests
```

### Run system checks

```bash
python manage.py check
```

---

## Postman API Testing

A `postman` folder is included in the repository containing Postman collections for testing the application's API endpoints.

### Importing the collections

1. Open Postman.
2. Select Import.
3. Browse to the project's `postman` folder.
4. Select the collection JSON files.
5. Import the collections into Postman.

### Running the API

Ensure the Django development server is running:

```bash
python manage.py runserver
```

The default API base URL is:

`http://127.0.0.1:8000`

### Authentication

- Create or use an account for the relevant user role.
- Authenticate using the application's configured authentication method.
- Configure the appropriate credentials, session cookies or authentication token in Postman.
- Include authentication details when testing protected endpoints.

### Recommended Testing Order

1. Publisher endpoints.
2. Reader subscription endpoints.
3. Journalist endpoints.
4. Article management.
5. Newsletter management.
6. Editor approval and management endpoints.
7. Authentication and permission restrictions.

Test endpoints using different user roles to verify that permissions are enforced correctly.

---

## User Roles and Permissions

The application supports three user roles:

| Role | Main responsibilities | Restrictions |
|---|---|---|
| **Reader** | Browse approved content; subscribe and unsubscribe from publishers and journalists; view subscribed content. | Cannot create, edit, delete or approve content; cannot access management functions. |
| **Journalist** | Create and manage their own articles and newsletters; view their subscribers. | Cannot approve content; cannot access editor-only or reader-only functions. |
| **Editor** | Review, edit, delete and approve articles and newsletters associated with their publisher; view publisher subscribers. | Cannot manage content belonging to other publishers without authorisation. |

All permissions are enforced through the application's authentication and authorisation controls.

---

## Future Improvements

Potential future enhancements include:

- Email notifications for new articles and newsletters.
- Improved content search and filtering.
- API pagination.
- Expanded automated test coverage.
- Enhanced API documentation.
- Production deployment.

---

## Project Summary

The News Application provides a role-based publishing platform built with Django and Django REST Framework.

It supports content creation, editorial approval, newsletter management and reader subscriptions, with separate permissions for each user role.

MariaDB provides the relational database backend for application data.

Automated Django tests and Postman collections support application and API testing.
