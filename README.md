# Job Tracker API

A backend API for tracking job applications, built with Python, FastAPI, and PostgreSQL.

Users can register, log in, and create, retrieve, update, and delete their own job applications. Authentication uses signed JWT access tokens, and application queries enforce user ownership.

## Implemented Features

- Account registration with email normalization and password validation
- Argon2 password hashing
- Login with JWT access tokens that expire after 30 minutes
- Protected current-user endpoint
- Job application creation, listing, retrieval, partial updates, and deletion
- Ownership checks that restrict access to each user's records
- Input validation for required fields, statuses, dates, URLs, and field lengths
- Duplicate-email handling and appropriate HTTP error responses
- PostgreSQL persistence with Alembic migrations
- Interactive API documentation through Swagger UI

## Tech Stack

| Technology      | Purpose                                    |
| --------------- | ------------------------------------------ |
| Python          | Application language                       |
| FastAPI         | API framework and dependency injection     |
| PostgreSQL      | Database                                   |
| SQLAlchemy      | Database models, queries, and transactions |
| Alembic         | Database migrations                        |
| Pydantic        | Request validation and response schemas    |
| pwdlib / Argon2 | Password hashing and verification          |
| PyJWT           | Access token creation and verification     |
| python-dotenv   | Local environment configuration            |

## API Endpoints

| Method | Endpoint                         | Description                                | Authentication |
| ------ | -------------------------------- | ------------------------------------------ | -------------- |
| GET    | `/health`                        | Check that the API is running              | No             |
| POST   | `/auth/register`                 | Register an account                        | No             |
| POST   | `/auth/token`                    | Log in and receive an access token         | No             |
| GET    | `/users/me`                      | Retrieve the authenticated user            | Yes            |
| POST   | `/applications`                  | Create a job application                   | Yes            |
| GET    | `/applications`                  | List the user's applications, newest first | Yes            |
| GET    | `/applications/{application_id}` | Retrieve one owned application             | Yes            |
| PATCH  | `/applications/{application_id}` | Partially update an owned application      | Yes            |
| DELETE | `/applications/{application_id}` | Delete an owned application                | Yes            |

Login accepts form fields named `username` and `password`. The `username` field contains the account's email address.

Protected endpoints require:

```http
Authorization: Bearer <access_token>
```

## Job Application Fields

Applications store a company, job title, status, optional job URL, optional notes, optional application date, and creation/update timestamps.

Supported statuses:

- `saved`
- `applied`
- `interviewing`
- `offer`
- `rejected`

Application ownership is assigned from the authenticated user. Clients cannot choose or update the owner.

## Local Setup

The instructions below use macOS, Homebrew, and Python 3.13.

### 1. Clone the repository

```bash
git clone https://github.com/jb-pryor/job-tracker-api.git
cd job-tracker-api
```

### 2. Create and activate a virtual environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Install and start PostgreSQL

If PostgreSQL is not already installed:

```bash
brew install postgresql@17
brew services start postgresql@17
```

Create the project database once:

```bash
"$(brew --prefix postgresql@17)/bin/createdb" job_tracker
```

### 5. Configure environment variables

Copy the example configuration:

```bash
cp .env.example .env
```

Update `.env` using your local PostgreSQL username:

```dotenv
DATABASE_URL=postgresql+psycopg://YOUR_DATABASE_USER@/job_tracker?host=/tmp
JWT_SECRET_KEY=YOUR_RANDOM_SECRET
```

This database URL uses the local Unix socket created by the Homebrew installation. Other environments may require a different connection URL.

Generate a signing secret:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Paste the generated value into `JWT_SECRET_KEY`.

The `.env` file is ignored by Git. Keep real configuration values out of the repository.

### 6. Apply database migrations

```bash
python -m alembic upgrade head
```

### 7. Run the development server

```bash
python -m uvicorn app.main:app --reload
```

Open:

- Health endpoint: http://127.0.0.1:8000/health
- Interactive documentation: http://127.0.0.1:8000/docs

## Example Application Request

Send this JSON to `POST /applications` after authenticating:

```json
{
  "company": "Example Company",
  "job_title": "Software Engineer I",
  "status": "applied",
  "job_url": "https://example.com/careers/123",
  "notes": "Submitted through the company website.",
  "applied_on": "2026-09-29"
}
```

To update only the status, send this to `PATCH /applications/{application_id}`:

```json
{
  "status": "interviewing"
}
```

Omitted fields remain unchanged. Optional fields can be cleared with `null`; required fields cannot.

## Error Handling

| Status | Meaning                                               |
| ------ | ----------------------------------------------------- |
| `401`  | Missing, invalid, or expired authentication           |
| `404`  | Application does not exist or belongs to another user |
| `409`  | An account with the email already exists              |
| `422`  | Invalid request data                                  |

Successful creation returns `201`. Successful deletion returns `204` with no response body.

## Verification Completed

The following behaviors have been checked manually through the interactive documentation:

- Successful registration and duplicate-email rejection
- Correct and incorrect login credentials
- Protected endpoint access with and without authentication
- Successful application creation and blank-company rejection
- Separate application lists for different users
- Ownership checks for fetching, updating, and deleting records
- Partial updates that preserve omitted fields
- Clearing optional notes and rejecting invalid required-field updates
- Successful deletion and subsequent `404` responses

Automated tests have not been added yet.

## Next Steps

- Status filtering and pagination
- Automated tests with a separate PostgreSQL test database
- GitHub Actions for continuous integration
- Deployment

## Project Status

In development. Authentication and job application CRUD are implemented and manually verified.
