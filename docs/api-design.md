# TutorFlow AI API Design

Base URL: `/api/v1`

## Response Format

Success:

```json
{
  "success": true,
  "message": "Resource retrieved.",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Validation error.",
  "detail": []
}
```

Authentication errors use the same format:

```json
{
  "success": false,
  "message": "Request failed.",
  "detail": "Could not validate credentials."
}
```

## HTTP Status Codes

- `200 OK`: request succeeded
- `201 Created`: resource created
- `204 No Content`: resource deleted
- `400 Bad Request`: invalid business request
- `401 Unauthorized`: missing or invalid authentication
- `403 Forbidden`: authenticated user cannot access resource
- `404 Not Found`: resource does not exist
- `409 Conflict`: duplicated or conflicting resource
- `422 Validation Error`: request schema validation failed
- `500 Internal Server Error`: unexpected server error

## Pagination, Sorting, Searching, Filtering

List endpoints support:

- `page`: page number, starts at `1`
- `page_size`: number of records per page, max `100`
- `sort`: ascending field, for example `name`
- `sort`: descending field, for example `-created_at`
- `search`: fuzzy search keyword, for example `search=王`

Student filters:

- `grade`
- `subject`
- `active`

Lesson filters:

- `student_id`
- `status`

Payment filters:

- `status`

List response data:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0
  }
}
```

## Auth

TutorFlow AI uses JWT access tokens. Passwords are stored as bcrypt hashes and are never returned by the API.

JWT payload:

- `sub`: authenticated user id
- `email`: authenticated user email
- `exp`: token expiration time

Bearer token usage:

```http
Authorization: Bearer <access_token>
```

Swagger `/docs` exposes an `Authorize` button through FastAPI `OAuth2PasswordBearer`, so protected APIs can be tested without a frontend. The Swagger OAuth2 form uses the hidden token endpoint `/api/v1/auth/token`; application clients should use `/api/v1/auth/login`.

### POST `/auth/register`

Create a teacher account. The backend checks duplicate email, hashes the password, stores the user, and returns a JWT access token with the created user.

Request:

```json
{
  "email": "teacher@example.com",
  "password": "password123",
  "name": "Demo Teacher"
}
```

Response `201`:

```json
{
  "success": true,
  "message": "User registered.",
  "data": {
    "access_token": "<jwt-access-token>",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "teacher@example.com",
      "name": "Demo Teacher",
      "created_at": "2026-07-23T12:00:00Z",
      "updated_at": "2026-07-23T12:00:00Z"
    }
  }
}
```

### POST `/auth/login`

Login with email and password. Only valid credentials receive a JWT access token.

Request:

```json
{
  "email": "teacher@example.com",
  "password": "password123"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "User logged in.",
  "data": {
    "access_token": "<jwt-access-token>",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "teacher@example.com",
      "name": "Demo Teacher",
      "created_at": "2026-07-23T12:00:00Z",
      "updated_at": "2026-07-23T12:00:00Z"
    }
  }
}
```

Invalid credentials return `401 Unauthorized`.

### GET `/auth/me`

Return the current authenticated teacher. This endpoint requires a valid Bearer token.

Authentication failure cases return `401 Unauthorized`:

- Missing token
- Invalid token
- Expired token
- Token user no longer exists

## Students

### GET `/students`

Requires a valid Bearer token. Supports `page`, `page_size`, `sort`, `search`, `grade`, `subject`, `active`.

### GET `/students/{id}`

Return one student.

### POST `/students`

Create a student.

Request:

```json
{
  "name": "王小明",
  "school": "Demo Junior High",
  "grade": "G7",
  "subject": "Math",
  "hourly_rate": "1200.00",
  "note": "Needs more algebra practice."
}
```

### PATCH `/students/{id}`

Partially update a student.

### DELETE `/students/{id}`

Delete a student. Returns `204 No Content`.

## Lessons

### GET `/lessons`

Supports `page`, `page_size`, `sort`, `search`, `student_id`, `status`.

### GET `/lessons/{id}`

Return one lesson.

### POST `/lessons`

Create a lesson.

Request:

```json
{
  "student_id": 1,
  "start_time": "2026-07-23T19:00:00Z",
  "duration_minutes": 60,
  "status": "scheduled",
  "location": "Online",
  "remark": "Focus on linear equations."
}
```

### PATCH `/lessons/{id}`

Partially update a lesson.

### DELETE `/lessons/{id}`

Delete a lesson. Returns `204 No Content`.

## Lesson Notes

### POST `/lessons/{id}/note`

Create a lesson note.

Request:

```json
{
  "raw_note": "Covered linear equations.",
  "ai_summary": "Student practiced solving linear equations.",
  "teacher_note": "Reviewed and adjusted the AI summary.",
  "parent_feedback": "Strong progress today."
}
```

### PATCH `/lessons/{id}/note`

Partially update a lesson note.

## Payments

### GET `/payments`

Supports `page`, `page_size`, `sort`, `search`, `status`.

### PATCH `/payments/{id}`

Update payment amount, status, or paid time.

Request:

```json
{
  "amount": "1200.00",
  "status": "paid",
  "paid_at": "2026-07-23T20:00:00Z"
}
```

## Dashboard

### GET `/dashboard`

Return dashboard counters:

- `today_lessons_count`
- `month_income`
- `active_students_count`
- `unpaid_payments_count`

## AI

### POST `/ai/summary`

Generate lesson summary.

Request:

```json
{
  "lesson_id": 1,
  "raw_note": "Covered linear equations."
}
```

### POST `/ai/feedback`

Generate parent feedback.

Request:

```json
{
  "lesson_id": 1,
  "ai_summary": "Student practiced solving linear equations.",
  "teacher_note": "Reviewed and adjusted the AI summary."
}
```
