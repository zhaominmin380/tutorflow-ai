# TutorFlow AI - Sprint 9 Specification
## Dashboard and Analytics Domain

**Version:** 1.1
**Status:** Ready for implementation
**Scope:** Read-only dashboard and analytics APIs
**Depends on:** Sprint 4 Authentication, Sprint 5 Student, Sprint 6 Lesson, Sprint 7 AI Teaching Assistant, Sprint 8 Payment and Billing

## 1. Sprint Goal

Build a production-ready dashboard and analytics domain that summarizes the authenticated tutor's students, lessons, payments, and AI usage.

The dashboard must:

- expose a backward-compatible overview endpoint;
- provide separate chart-ready analytics endpoints;
- enforce JWT authentication and tutor ownership on every query;
- calculate totals in the database with SQL aggregate functions;
- return deterministic values for empty data sets and month boundaries;
- preserve all existing Sprint 4 to Sprint 8 routes and behavior.

This sprint is read-only. It must not introduce create, update, delete, payment mutation, or AI-provider functionality.

## 2. Existing Architecture to Preserve

Use the existing application layers:

```text
Client
  -> API Router
  -> Pydantic Schema
  -> Dashboard Service
  -> Dashboard Repository
  -> SQLAlchemy Session
  -> PostgreSQL
```

Required files:

```text
backend/app/
  api/v1/dashboard.py
  repositories/dashboard_repository.py
  schemas/dashboard.py
  services/dashboard_service.py

backend/tests/
  test_dashboard.py

docs/
  api-design.md
```

Do not introduce a second database access pattern, a new authentication mechanism, or a separate dashboard model/table. Dashboard values are derived from existing domain tables.

## 3. Data Sources and Definitions

### 3.1 Student ownership

The authenticated user owns a student when:

```text
students.user_id = current_user.id
```

All lesson and payment statistics must reach ownership through the student's `user_id`.

### 3.2 Lesson date and status

- Use `lessons.start_time` for reporting dates.
- Do not use `created_at` to determine when a lesson occurred.
- Lesson statuses are `scheduled`, `completed`, `cancelled`, and `no_show`.
- `today_lessons_count` includes all lessons scheduled for the current local day, regardless of status.
- Lesson status analytics must return a count for every supported status, including statuses with a zero count.

### 3.3 Payment date and status

- Income is based on `payments.paid_at`, not `lessons.start_time` or `payments.created_at`.
- Only payments with status `paid` are included in income totals.
- `pending`, `cancelled`, and `refunded` payments are excluded from income.
- Outstanding payments are payments with status `pending`.
- Monetary values use `Decimal` and are returned as JSON numbers serialized according to the existing Pydantic configuration.
- The application reporting currency is TWD unless the existing payment contract is later extended with multi-currency support.

### 3.4 AI log definitions

AI analytics use the existing `ai_logs` table:

- `log_type = 'summary'` counts lesson summaries.
- `log_type = 'parent_feedback'` counts parent feedback generations.
- `total_requests` is the sum of those two supported dashboard request types.
- `status = 'succeeded'` and `status = 'failed'` are reported separately.
- AI logs are owned directly by `ai_logs.user_id`.
- Failed attempts are included in request counts because they represent actual requests.

If additional AI log types are added in a later sprint, they must not silently change Sprint 9 totals without an explicit specification update.

## 4. Time and Date Rules

- Store timestamps using the existing database convention, normally UTC with timezone information.
- Dashboard reporting uses the `Asia/Taipei` timezone.
- A month is represented by `YYYY-MM`, for example `2026-08`.
- Month ranges are inclusive at the start and exclusive at the end:

```text
[2026-08-01 00:00:00 Asia/Taipei, 2026-09-01 00:00:00 Asia/Taipei)
```

- The service converts local boundaries to the timestamp representation used by the database before querying.
- The current local date is used when the overview endpoint does not receive a month.
- Invalid month values return HTTP 422 using the existing validation error format.
- Leap years, month length, daylight-saving changes, and the final second of a month must be covered by date boundary tests.

## 5. API Authentication and Compatibility

Every endpoint in this specification must depend on the existing `get_current_user` dependency.

```python
current_user = Depends(get_current_user)
```

Unauthenticated requests return HTTP 401. No endpoint accepts a `user_id` from the client.

### 5.1 Backward-compatible routes

The existing route is:

```text
GET /api/v1/dashboard
```

It must remain available and return the overview response. The following route is the explicit equivalent:

```text
GET /api/v1/dashboard/overview
```

Both routes must use the same service method and return the same response contract. The implementation must remove the sample/static response currently used by the placeholder endpoint.

### 5.2 Analytics routes

```text
GET /api/v1/dashboard/income?month=YYYY-MM
GET /api/v1/dashboard/students
GET /api/v1/dashboard/lessons?month=YYYY-MM
GET /api/v1/dashboard/ai?month=YYYY-MM
```

The `month` query parameter is required for income, lesson, and AI analytics. Student statistics are current totals and do not require a month.

## 6. Common Response Envelope

Use the existing `ApiResponse[T]` envelope for successful responses and `ErrorResponse` for documented errors.

Successful responses follow this shape:

```json
{
  "success": true,
  "message": "Dashboard retrieved.",
  "data": {}
}
```

Expected errors:

| Status | Condition |
|---|---|
| 401 | Missing, invalid, or expired JWT |
| 422 | Invalid or missing `month` query parameter |
| 500 | Unexpected server or database failure, handled by existing error middleware |

There is no 404 for analytics caused by missing students, lessons, payments, or AI logs. An empty result is a valid response containing zero values.

## 7. Dashboard Overview API

### Endpoint

```text
GET /api/v1/dashboard
GET /api/v1/dashboard/overview
```

### Query parameters

No required parameters. The service determines the current date and current local month in `Asia/Taipei`.

### Response schema

```json
{
  "date": "2026-08-17",
  "month": "2026-08",
  "today_lessons_count": 3,
  "month_income": 24000.00,
  "active_students_count": 8,
  "unpaid_payments_count": 2,
  "outstanding_payment_amount": 4500.00,
  "ai_requests_count": 12
}
```

Field definitions:

| Field | Definition |
|---|---|
| `date` | Current date in `Asia/Taipei` |
| `month` | Current local month in `YYYY-MM` format |
| `today_lessons_count` | Owned lessons whose `start_time` falls within today's local boundary |
| `month_income` | Owned payments with status `paid` and `paid_at` in the current local month |
| `active_students_count` | Owned students where `is_active = true` |
| `unpaid_payments_count` | Owned payments where status is `pending` |
| `outstanding_payment_amount` | Sum of owned pending payment amounts |
| `ai_requests_count` | Owned summary and parent feedback requests in the current local month |

The existing `unpaid_payments_count` field must remain for backward compatibility. New clients should use the more explicit `outstanding_payment_amount` alongside it.

## 8. Income Analytics API

### Endpoint

```text
GET /api/v1/dashboard/income?month=2026-08
```

### Response schema

```json
{
  "month": "2026-08",
  "currency": "TWD",
  "total_income": 24000.00,
  "paid_count": 12,
  "daily_series": [
    {
      "date": "2026-08-01",
      "amount": 0.00,
      "paid_count": 0
    },
    {
      "date": "2026-08-02",
      "amount": 2000.00,
      "paid_count": 1
    }
  ]
}
```

Rules:

- Include only `paid` payments.
- Group by the local calendar date of `paid_at`.
- Return one ordered series item per calendar day in the requested month, including zero-value days.
- `total_income` must equal the sum of `daily_series.amount`.
- `paid_count` must equal the sum of `daily_series.paid_count`.
- The series must be ordered ascending by date.

## 9. Student Analytics API

### Endpoint

```text
GET /api/v1/dashboard/students
```

### Response schema

```json
{
  "total_students": 10,
  "active_students": 8,
  "inactive_students": 2
}
```

Rules:

- Count only students owned by the authenticated user.
- `total_students = active_students + inactive_students`.
- `active_students` is based on `students.is_active = true`.
- `inactive_students` is based on `students.is_active = false`.
- A missing or null legacy value must follow the existing model contract; it must not be silently counted in both groups.

## 10. Lesson Analytics API

### Endpoint

```text
GET /api/v1/dashboard/lessons?month=2026-08
```

### Response schema

```json
{
  "month": "2026-08",
  "total_lessons": 20,
  "by_status": {
    "scheduled": 6,
    "completed": 10,
    "cancelled": 3,
    "no_show": 1
  },
  "daily_series": [
    {
      "date": "2026-08-01",
      "total": 2,
      "scheduled": 1,
      "completed": 1,
      "cancelled": 0,
      "no_show": 0
    }
  ]
}
```

Rules:

- Count only lessons belonging to students owned by the authenticated user.
- Filter the requested month using `lessons.start_time`.
- Return all supported status keys even when their count is zero.
- Return one ordered daily series item per calendar day in the requested month.
- `total_lessons` must equal the sum of `by_status` values.
- Each daily `total` must equal the sum of that day's status values.

## 11. AI Analytics API

### Endpoint

```text
GET /api/v1/dashboard/ai?month=2026-08
```

### Response schema

```json
{
  "month": "2026-08",
  "total_requests": 12,
  "summary_requests": 8,
  "parent_feedback_requests": 4,
  "succeeded_requests": 10,
  "failed_requests": 2,
  "average_duration_ms": 1840.50
}
```

Rules:

- Filter by `ai_logs.user_id = current_user.id`.
- Filter the requested month using the existing AI log creation timestamp.
- `total_requests = summary_requests + parent_feedback_requests`.
- `succeeded_requests + failed_requests` may be less than `total_requests` if legacy rows contain another status; such rows must not be counted as succeeded or failed.
- Return `0.00` for `average_duration_ms` when there are no eligible duration values, rather than null.
- Do not expose prompts, responses, provider names, or model details from this analytics endpoint.

## 12. Repository Contracts

The repository owns database queries and returns typed, service-ready aggregate results. It must not return ORM entities for dashboard responses.

Recommended methods:

```python
overview(
    db,
    user_id,
    today_start,
    tomorrow_start,
    month_start,
    month_end,
)

income(db, user_id, month_start, month_end)
student_statistics(db, user_id)
lesson_statistics(db, user_id, month_start, month_end)
ai_statistics(db, user_id, month_start, month_end)
```

Repository requirements:

- Use SQLAlchemy aggregate expressions such as `COUNT`, `SUM`, `AVG`, and `GROUP BY`.
- Apply ownership filters inside every query, not only in the service.
- Use explicit selected columns; do not use `SELECT *`.
- Do not load all rows and aggregate them in Python.
- Do not issue one query per student, date, status, or payment.
- Use outer joins or separate aggregates so an empty related table still returns zero values.
- Keep database-specific date-series logic isolated in the repository if PostgreSQL functions are required.
- Return Decimal-compatible monetary values and normalize database `NULL` aggregates to zero.

## 13. Service Responsibilities

The service layer must:

- obtain the current reporting date and timezone-aware month boundaries;
- validate and parse `YYYY-MM` values;
- pass `current_user.id` to every repository method;
- assemble the common response envelope through existing schema conventions;
- normalize zero, empty-series, and aggregate-null results;
- enforce response invariants such as total counts matching status breakdowns;
- keep routers free of SQL and business aggregation logic.

The service must not accept an arbitrary owner ID from a request or infer ownership from a student ID supplied by the client.

## 14. Schema Requirements

Add or update Pydantic schemas for:

- overview response;
- income response and daily income item;
- student statistics response;
- lesson response, status breakdown, and daily lesson item;
- AI statistics response.

Schema requirements:

- Use explicit field types and response models.
- Use `date` for calendar dates and `Decimal` for money.
- Keep the existing overview fields required by the current API contract.
- Add examples and descriptions so Swagger communicates the reporting semantics.
- Do not expose ORM-only fields or raw AI prompt/response content.

## 15. Performance and Database Requirements

- Aggregate in PostgreSQL, not in application memory.
- Avoid N+1 queries.
- Do not query unused columns.
- Reuse existing foreign-key and status indexes where available.
- Confirm that dashboard filters can use indexes on ownership, lesson start time, payment status/paid time, and AI log user/time fields.
- Do not add a dashboard snapshot table in Sprint 9.
- Do not add caching until correctness and invalidation rules are specified.
- Large dataset tests must verify query completion and bounded query count; they do not need to be a benchmark suite.

## 16. Testing Requirements

Add focused tests in `backend/tests/test_dashboard.py` covering:

1. Authenticated overview returns the correct data.
2. Unauthenticated requests return 401 for every dashboard endpoint.
3. `GET /dashboard` and `GET /dashboard/overview` return equivalent data.
4. A user cannot see another user's students, lessons, payments, or AI logs.
5. Empty database returns zero totals, zero monetary values, and empty or zero-filled series according to the response contract.
6. Month parsing accepts valid `YYYY-MM` values and rejects invalid values with 422.
7. Month boundaries include the first instant and exclude the first instant of the next month.
8. Asia/Taipei date conversion assigns timestamps to the correct reporting day.
9. Income includes only paid payments and uses `paid_at`.
10. Pending, cancelled, and refunded payments do not increase income.
11. Outstanding payment count and amount include pending payments only.
12. Student totals correctly separate active and inactive students.
13. Lesson counts correctly group every supported status.
14. AI totals separate summary, parent feedback, succeeded, and failed logs.
15. Chart series are ordered and totals reconcile with their daily or status breakdowns.
16. Swagger exposes the required routes, parameters, response models, and 401/422 responses.

Tests must use the existing test fixtures and authentication helpers. Do not weaken JWT validation or bypass ownership filters just to make dashboard tests pass.

## 17. API Documentation Requirements

Update `docs/api-design.md` with:

- all five dashboard routes;
- authentication requirements;
- query parameter format and timezone rules;
- response field definitions;
- income, lesson, payment, and AI counting semantics;
- empty-data behavior;
- example requests and responses.

The OpenAPI documentation must match the implemented schemas exactly. Do not document fields that are not returned by the endpoint.

## 18. Implementation Order

1. Confirm the existing model field names, enum values, and authentication dependency.
2. Define dashboard Pydantic response schemas.
3. Implement month parsing and `Asia/Taipei` boundary handling in the service layer.
4. Implement repository aggregate queries with ownership filters.
5. Implement the service methods and zero-value normalization.
6. Replace the placeholder dashboard route and add the overview alias route.
7. Add the income, student, lesson, and AI routes.
8. Add unit and API tests, including ownership and boundary cases.
9. Update Swagger metadata and `docs/api-design.md`.
10. Run the existing full test suite and verify that Sprint 4 to Sprint 8 tests still pass.

## 19. Definition of Done

Sprint 9 is complete when:

- all dashboard endpoints are implemented and JWT-protected;
- the existing `GET /api/v1/dashboard` route remains compatible;
- all aggregate queries enforce current-user ownership;
- all totals are calculated with SQL aggregates;
- monthly date and payment semantics are explicit and tested;
- empty data returns stable zero values instead of unexpected nulls;
- income, student, lesson, and AI analytics match the definitions in this document;
- chart-ready series are sorted and internally consistent;
- Swagger and `docs/api-design.md` are updated;
- dashboard tests pass;
- the complete existing test suite passes;
- no unrelated Sprint 4 to Sprint 8 behavior is changed.

## 20. Explicit Non-Goals

The following are outside Sprint 9:

- dashboard frontend implementation;
- export to CSV or Excel;
- custom date ranges beyond monthly analytics;
- multi-currency reporting;
- financial forecasting;
- AI quality scoring or token-cost billing;
- caching, materialized views, or scheduled aggregation jobs;
- administrator or cross-tutor analytics;
- changes to lesson soft-delete behavior;
- changes to existing student, lesson, payment, or AI APIs.
