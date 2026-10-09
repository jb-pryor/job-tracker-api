# Job Tracker API

A REST API for tracking job applications, built with Python, FastAPI, and PostgreSQL. Users can register, log in, and manage their own applications, including status, notes, and application dates.

Deployed on Vercel with PostgreSQL hosted on Neon. A separate React and TypeScript frontend provides a dashboard for using the API.

## Live Demo and API

- [Frontend dashboard](https://job-tracker-web-one.vercel.app/)
- [Interactive API documentation](https://job-tracker-api-blush.vercel.app/docs)
- [Frontend repository](https://github.com/jb-pryor/job-tracker-web)

Use the dashboard to register, log in, and manage applications.

To try the API directly, register an account using `/auth/register`, then click **Authorize** in the documentation and enter your email and password. Use your email in the `username` field.

## Features

- Account registration with Argon2 password hashing
- Login with JWT access tokens
- User ownership checks on application endpoints
- Create, retrieve, update, and delete job applications
- Filter applications by status
- Paginate results using `limit` and `offset`
- Input validation and HTTP error responses
- Database migrations with Alembic
- 16 automated tests using a separate PostgreSQL database
- GitHub Actions workflow that runs tests on pushes and pull requests

Supported statuses: `saved`, `applied`, `interviewing`, `offer`, and `rejected`.

## Tech Stack

- **FastAPI** — API routing and interactive documentation
- **Pydantic** — Request validation and response schemas
- **SQLAlchemy / Psycopg** — Database queries and PostgreSQL connectivity
- **PostgreSQL** — Persistent storage
- **Alembic** — Database migrations
- **pwdlib / Argon2** — Password hashing
- **PyJWT** — Access token creation and verification
- **pytest** — Automated testing
- **Vercel / Neon** — API and database hosting

## Local Setup

Requires Python 3.13 and a running PostgreSQL instance.

### 1. Clone the repository

```bash
git clone https://github.com/jb-pryor/job-tracker-api.git
cd job-tracker-api
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate`.

### 3. Configure the database and environment

Create a PostgreSQL database named `job_tracker`. Copy the environment template:

```bash
cp .env.example .env
```

Set the database connection and JWT secret in `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@localhost:5432/job_tracker
JWT_SECRET_KEY=YOUR_RANDOM_SECRET
TEST_DATABASE_URL=postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@localhost:5432/job_tracker_test
```

Use credentials that match your PostgreSQL installation. Generate a JWT secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Keep `.env` out of version control.

### 4. Apply migrations

```bash
python -m alembic upgrade head
```

### 5. Start the API

```bash
python -m uvicorn app.main:app --reload
```

Open the local interactive documentation at:

http://127.0.0.1:8000/docs

## Endpoints

| Method | Endpoint             | Description                                            |
| ------ | -------------------- | ------------------------------------------------------ |
| GET    | `/health`            | Check that the API is responding                       |
| POST   | `/auth/register`     | Create an account                                      |
| POST   | `/auth/token`        | Log in and receive an access token                     |
| GET    | `/users/me`          | Retrieve the authenticated user's profile              |
| POST   | `/applications`      | Create a job application                               |
| GET    | `/applications`      | List applications with status filtering and pagination |
| GET    | `/applications/{id}` | Retrieve one application                               |
| PATCH  | `/applications/{id}` | Update selected application fields                     |
| DELETE | `/applications/{id}` | Delete an application                                  |

The profile and application endpoints require a bearer token. Users can access only their own applications.

Login accepts form fields named `username` and `password`; use the account's email as `username`. Include the returned token in subsequent requests:

```http
Authorization: Bearer <access_token>
```

Access tokens expire after 30 minutes. Password hashes are excluded from user responses.

The `/health` endpoint confirms that the API responds; it does not check database connectivity.

### Example application

```json
{
  "company": "Example Company",
  "job_title": "Junior Software Engineer",
  "status": "applied",
  "job_url": "https://example.com/careers/123",
  "notes": "Applied through the company website.",
  "applied_on": "2026-10-05"
}
```

To filter and paginate a list:

```http
GET /applications?status=applied&limit=20&offset=0
```

The response includes `items`, `total`, `limit`, and `offset`. `total` counts matching applications before pagination.

PATCH requests update only submitted fields. Optional fields such as `notes`, `job_url`, and `applied_on` can be cleared by sending `null`. Company, job title, and status cannot be set to `null`.

## Testing

Tests use a separate database named `job_tracker_test`. Create that database and configure `TEST_DATABASE_URL` in `.env`, then apply migrations to it:

```bash
DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@localhost:5432/job_tracker_test' \
  python -m alembic upgrade head
```

Run the test suite:

```bash
python -m pytest -v
```

The 16 tests cover registration, password hashing, login, protected endpoints, application creation and updates, deletion, ownership checks, validation, filtering, and pagination. Database changes are rolled back after each test.

PostgreSQL must be running, but Uvicorn is not required for testing.

## Continuous Integration

The workflow in `.github/workflows/tests.yml` runs on pushes and pull requests. It installs dependencies, starts a temporary PostgreSQL database, applies migrations, and runs the test suite.

## Deployment

The API runs on Vercel and connects to a PostgreSQL database hosted on Neon. The database connection URL and JWT secret are configured through Vercel environment variables.

Alembic migrations create and update the hosted database schema. Local development and automated tests use separate databases.

The React and TypeScript frontend is deployed separately on Vercel. The API's CORS configuration allows browser requests from:

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `https://job-tracker-web-one.vercel.app`

Registration, login, application creation, and retrieval have been verified on the deployed API.

## Project Structure

```text
app/
    main.py           Application setup and CORS configuration
    database.py       Database connection and sessions
    models.py         Database models
    schemas.py        Input and output schemas
    security.py       Password hashing and JWT handling
    dependencies.py   Authentication dependencies
    routers/          API endpoints
alembic/              Database migrations
tests/                Test fixtures and automated tests
.github/workflows/    GitHub Actions configuration
```

## Status

The backend and frontend are deployed. The API has 16 passing automated tests and a working GitHub Actions workflow.

The dashboard supports registration, login, application creation, editing, status updates, deletion, filtering, and pagination.
