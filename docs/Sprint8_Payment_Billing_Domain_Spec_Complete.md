# TutorFlow AI - Sprint 8 Specification
## Payment & Billing Domain (Complete Implementation Guide)

Version: 1.1  
Status: Ready for implementation  
Scope: Backend API, database model, statistics, security, tests, and deployment notes

---

## 1. Sprint Goal

完成 Payment & Billing Domain，讓教師可以為課程建立付款紀錄、追蹤付款狀態、查詢未付款資料，並提供月度收入統計供後續 Dashboard 使用。

Sprint 8 必須完成：

- Payment Create / Detail / List / Update
- Payment cancellation through soft delete semantics
- Payment status transition validation
- One Lesson One Payment constraint
- JWT authentication and ownership validation
- Monthly income statistics
- Outstanding payment amount and count
- Swagger and API documentation
- PostgreSQL migration
- Automated tests

---

## 2. Prerequisites and Compatibility

必須先完成 Sprint 4、5、6、7：

- Sprint 4: Authentication and JWT
- Sprint 5: Student Domain
- Sprint 6: Lesson Domain
- Sprint 7: Lesson Note and AI Teaching Assistant

Compatibility rules:

- 不修改既有 Authentication、Student、Lesson、Lesson Note 與 AI API 路徑。
- 保留既有 `Payment` model 的 `lesson_id` 關聯與 PostgreSQL migration chain。
- 所有 API 維持 `ApiResponse` / `ErrorResponse` 統一格式。
- 所有 production schema 變更必須透過 Alembic migration，不依賴 `Base.metadata.create_all()` 升級既有資料表。
- Sprint 8 不處理退款流程；既有 `refunded` enum 值必須保留以避免破壞既有資料，但不可由 Sprint 8 API 主動產生。

---

## 3. Scope Decisions

### 3.1 Payment Ownership

Payment 的業務所有權來自 Lesson：

```text
payment.lesson.student.user_id == current_user.id
```

Client 不得透過 request body 指定任意 `student_id` 作為權限依據。建立 Payment 時，Service 必須先取得屬於 current user 的 Lesson，再由 Lesson 推導 Student。

### 3.2 One Lesson One Payment

- 一堂 Lesson 最多一筆 Payment。
- `payments.lesson_id` 必須有 database unique constraint。
- Concurrent create 發生 unique violation 時，Repository rollback，Service 回傳 `409 Conflict`。
- 已取消的 Payment 仍然保留，因此同一堂 Lesson 不能重新建立第二筆 Payment。
- Sprint 8 不提供 restore 或 re-open cancelled payment；未來若需要，必須另訂狀態流程。

### 3.3 Soft Delete / Cancellation

DELETE Payment 不會真的刪除資料，而是將 `status` 改為 `cancelled`。

- 只有 `pending` Payment 可以被取消。
- `paid` Payment 不可透過 DELETE 取消，回傳 `409 Conflict`。
- `cancelled` Payment 再次 DELETE 必須保持冪等，回傳 `204 No Content`，或依產品決定回傳 `409`；本 Sprint 採 `204`。
- `cancelled` Payment 不計入收入與未付款統計。

### 3.4 Amount and Currency

- `amount` 使用 `Decimal`，資料庫型別為 `NUMERIC(10, 2)`。
- `amount` 必須大於 `0`。
- Sprint 8 暫不新增多幣別欄位，所有金額使用系統設定的單一營運貨幣。
- API response 將金額序列化為字串，避免浮點數誤差。

### 3.5 Existing Refunded Status

目前既有 model 已包含 `refunded` 狀態。為維持相容性：

- migration 不得移除 `refunded` enum 值。
- List、Detail 與統計必須能讀取 `refunded` Payment。
- Sprint 8 的 PATCH 不允許建立或轉換至 `refunded`。
- `refunded` 不計入 monthly income，也不計入 outstanding amount/count。

---

## 4. Domain Model

### 4.1 Payment Fields

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `id` | integer | yes | Primary key |
| `student_id` | integer | yes | FK to `students.id`; derived from Lesson |
| `lesson_id` | integer | yes | FK to `lessons.id`; unique |
| `amount` | decimal | yes | Greater than `0`, precision `10,2` |
| `status` | enum | yes | `pending`, `paid`, `cancelled`, `refunded` |
| `paid_at` | datetime | no | Required when status becomes `paid` |
| `note` | text | no | Maximum 5000 characters; blank rejected when supplied |
| `created_at` | datetime | yes | Server generated |
| `updated_at` | datetime | yes | Server generated |

### 4.2 Constraints and Indexes

Required constraints:

- Primary key on `id`
- Foreign key `student_id -> students.id` with `ON DELETE CASCADE`
- Foreign key `lesson_id -> lessons.id` with `ON DELETE CASCADE`
- Unique constraint on `lesson_id`
- Index on `student_id`
- Index on `status`
- Index on `paid_at`
- Check constraint `amount > 0`

The service must also verify that `payment.student_id == lesson.student_id` when creating or updating a Payment. Database constraints protect row integrity; Service validation protects cross-table business consistency.

### 4.3 Existing Schema Reconciliation

The current base schema stores Payment by `lesson_id` and does not yet contain all Sprint 8 fields. The Sprint 8 migration must:

1. Add `student_id` if it does not exist.
2. Backfill `student_id` from `lessons.student_id`.
3. Reject or report orphaned Payment rows before adding the non-null foreign key.
4. Add `note` if it does not exist.
5. Preserve existing payment statuses, including `refunded`.
6. Add missing indexes and constraints.
7. Update the Alembic revision only after the data backfill succeeds.

Migration must be tested against a PostgreSQL database containing existing Payment rows, not only an empty database.

---

## 5. Status Model

### 5.1 Allowed Statuses

```text
pending
paid
cancelled
refunded
```

### 5.2 Transition Matrix

| Current | Requested | Result |
| --- | --- | --- |
| `pending` | `paid` | Allowed; `paid_at` required |
| `pending` | `cancelled` | Allowed |
| `pending` | `pending` | Allowed as idempotent update |
| `paid` | `pending` | Rejected with `409` |
| `paid` | `cancelled` | Rejected with `409` |
| `paid` | `refunded` | Rejected in Sprint 8 |
| `cancelled` | `paid` | Rejected with `409` |
| `cancelled` | `pending` | Rejected with `409` |
| `cancelled` | `cancelled` | Allowed as idempotent update |
| `refunded` | anything | Rejected with `409` |

### 5.3 `paid_at` Rules

- `pending` Payment may have `paid_at = null`.
- Changing `pending -> paid` requires a supplied `paid_at`; if omitted, Service may use the current UTC time only if that behavior is explicitly selected. Sprint 8 uses validation error `422` when omitted.
- `paid` Payment must have non-null `paid_at`.
- `cancelled` and `refunded` Payment must not contribute to income statistics even if legacy data contains `paid_at`.
- Updating `paid_at` on a `paid` Payment is allowed only for correction and must not change status.

---

## 6. Architecture

```text
Client
  -> Payment Router
  -> Payment Service
  -> Payment Repository
  -> PostgreSQL
```

Rules:

- Router handles schema validation, dependencies, HTTP status codes, and response envelopes.
- Service handles ownership, Lesson validation, amount validation, status transitions, and statistics semantics.
- Repository handles SQLAlchemy queries, persistence, aggregation, rollback, and row locking where required.
- Repository must not import `HTTPException`, `Depends`, or request schemas.
- Router must not contain SQLAlchemy queries.
- Statistics queries must be implemented in Repository, not calculated from a truncated paginated list in Service.
- Payment create/update status transitions should use a transaction and row lock where PostgreSQL concurrency can cause conflicting updates.

### 6.1 Suggested Folder Structure

```text
backend/
├── alembic/versions/<revision>_payment_billing.py
├── app/api/v1/payments.py
├── app/repositories/payment_repository.py
├── app/schemas/payment.py
├── app/services/payment_service.py
└── tests/test_payments.py
```

---

## 7. Schemas

### 7.1 PaymentCreate

Request body:

```json
{
  "lesson_id": 1,
  "amount": "1200.00",
  "note": "August tutoring fee"
}
```

Rules:

- `lesson_id` must be a positive integer.
- `amount` must be greater than `0` and no more than two decimal places.
- `note` is optional, maximum 5000 characters.
- `student_id`, `status`, `paid_at`, `id`, `created_at`, and `updated_at` are not accepted on create.
- Unknown fields must return `422`.

### 7.2 PaymentUpdate

All fields are optional, but at least one field must be supplied:

```json
{
  "amount": "1300.00",
  "status": "paid",
  "paid_at": "2026-08-20T12:00:00Z",
  "note": "Paid by bank transfer"
}
```

Rules:

- `lesson_id` and `student_id` cannot be changed.
- Status transition rules are always enforced, including when multiple fields are updated together.
- Blank `note` is rejected when supplied.
- `paid_at` must be timezone-aware ISO 8601 when supplied.
- An empty PATCH body returns `422`.

### 7.3 PaymentResponse

```json
{
  "id": 1,
  "student_id": 3,
  "lesson_id": 8,
  "amount": "1200.00",
  "status": "paid",
  "paid_at": "2026-08-20T12:00:00Z",
  "note": "Paid by bank transfer",
  "created_at": "2026-08-01T10:00:00Z",
  "updated_at": "2026-08-20T12:00:00Z"
}
```

---

## 8. API Contract

Base URL: `/api/v1`  
Authentication: `Authorization: Bearer <access_token>`  
All endpoints require `Depends(get_current_user)`.

### 8.1 POST `/payments`

Create one Payment for a Lesson owned by the current user.

Responses:

- `201`: created
- `401`: missing or invalid JWT
- `404`: Lesson missing, inactive, or owned by another user
- `409`: Payment already exists for the Lesson
- `422`: invalid amount, note, or request fields

### 8.2 GET `/payments`

List Payments owned by the current user.

Query parameters:

| Parameter | Default | Rules |
| --- | --- | --- |
| `page` | `1` | Minimum `1` |
| `page_size` | `20` | Range `1..100` |
| `student_id` | null | Positive integer |
| `status` | null | Allowed enum value |
| `month` | null | `YYYY-MM`, based on `paid_at` for paid rows and `created_at` otherwise |
| `sort` | `-created_at` | `amount`, `paid_at`, `created_at`, `status`, `-` prefix for descending |

The response must include the standard pagination object. Cancelled and refunded records remain queryable when explicitly filtered.

### 8.3 GET `/payments/{payment_id}`

Return one Payment owned by the current user.

Return `404` for both missing and foreign Payments to avoid resource enumeration.

### 8.4 PATCH `/payments/{payment_id}`

Update `amount`, `status`, `paid_at`, or `note` after Service validation.

Responses:

- `200`: updated
- `401`: missing or invalid JWT
- `404`: missing or foreign Payment
- `409`: invalid status transition or paid Payment cancellation
- `422`: invalid body or amount/date format

The specific validation error for `pending -> paid` without `paid_at` is `422`.
Other invalid status transitions remain `409 Conflict`.

### 8.5 DELETE `/payments/{payment_id}`

Soft-delete by changing `pending -> cancelled`.

Responses:

- `204`: cancelled or already cancelled
- `401`: missing or invalid JWT
- `404`: missing or foreign Payment
- `409`: Payment is already paid or refunded

### 8.6 GET `/payments/statistics/monthly`

Return monthly income statistics.

Query:

```http
GET /api/v1/payments/statistics/monthly?month=2026-08
```

`month` is required and uses `YYYY-MM`. Month boundaries use the application reporting timezone, configured as `Asia/Taipei` for this product, while stored datetimes remain timezone-aware.

Response:

```json
{
  "success": true,
  "message": "Monthly payment statistics retrieved.",
  "data": {
    "month": "2026-08",
    "monthly_income": "3600.00",
    "paid_count": 3,
    "currency": "TWD"
  }
}
```

Only `paid` Payments whose `paid_at` falls inside the requested month are included.

### 8.7 GET `/payments/statistics/outstanding`

Return outstanding pending payment totals for the current user.

Response:

```json
{
  "success": true,
  "message": "Outstanding payments retrieved.",
  "data": {
    "outstanding_amount": "2400.00",
    "outstanding_count": 2,
    "currency": "TWD"
  }
}
```

Only `pending` Payments are included. Cancelled, paid, and refunded Payments are excluded.

---

## 9. Repository Contract

`PaymentRepository` must provide:

- `create(db, lesson, amount, note)`
- `get_by_id(db, payment_id, user_id)`
- `list(db, user_id, filters, pagination, sort)`
- `update(db, payment, data)`
- `cancel(db, payment)`
- `monthly_income(db, user_id, month_start, month_end)`
- `outstanding(db, user_id)`

Repository requirements:

- Ownership filters must be applied in SQL joins, not after fetching rows.
- `get_by_id` and list queries must join through `Lesson -> Student -> User`.
- Duplicate create must catch only unique violations, rollback, and expose a domain error to Service.
- Aggregate queries must return database-level sums and counts.
- Repository methods must not return HTTP exceptions.

---

## 10. Service Contract

`PaymentService` must provide:

- `create_payment()`
- `get_payment()`
- `list_payments()`
- `update_payment()`
- `cancel_payment()`
- `monthly_statistics()`
- `outstanding_statistics()`

Service responsibilities:

- Validate Lesson ownership and active status.
- Derive `student_id` from Lesson.
- Validate amount and note.
- Enforce one Payment per Lesson.
- Enforce all status transitions.
- Enforce `paid_at` rules.
- Convert domain errors to router-level HTTP responses.
- Never call an external provider; Payment is a local database domain.

---

## 11. Security and Ownership

- All Payment endpoints require JWT.
- Client-provided `student_id` must not be trusted for authorization.
- Foreign Payments return `404`, not `403`.
- Payment statistics must filter by `current_user.id`.
- No Payment response may expose another user's Lesson or Student data.
- Amount, status, and note values must be validated before persistence.
- API error responses must not expose SQL statements, database URLs, or internal exception traces.

---

## 12. Error Contract

| Situation | Status | Behavior |
| --- | --- | --- |
| Missing or foreign Lesson | `404` | Unified error response |
| Missing or foreign Payment | `404` | Unified error response |
| Duplicate Payment for Lesson | `409` | Unified conflict response |
| Invalid status transition | `409` | Explain allowed transition |
| Paid Payment cancellation | `409` | Payment remains unchanged |
| Invalid amount or blank note | `422` | Validation error |
| Invalid month or sort value | `422` | Validation error |
| Database or unexpected failure | `500` | Generic error without SQL details |

All errors must follow:

```json
{
  "success": false,
  "message": "Request failed.",
  "detail": "Payment status transition is not allowed."
}
```

---

## 13. Statistics Semantics

### Monthly Income

```text
SUM(payment.amount)
WHERE payment.status = 'paid'
  AND payment.paid_at >= month_start
  AND payment.paid_at < month_end
  AND owner = current_user
```

### Outstanding Amount

```text
SUM(payment.amount)
WHERE payment.status = 'pending'
  AND owner = current_user
```

### Outstanding Count

```text
COUNT(payment.id)
WHERE payment.status = 'pending'
  AND owner = current_user
```

The statistics must not use the result of `GET /payments` pagination because page size would produce incorrect totals.

---

## 14. Testing Requirements

### Unit Tests

- Payment schema accepts valid amount and rejects zero/negative amount.
- Payment schema rejects more than two decimal places if enforced at schema level.
- Payment schema rejects blank or oversized note.
- Status transition matrix is fully tested.
- Monthly boundary uses inclusive start and exclusive end.
- Repository maps only unique violations to duplicate domain errors.

### API Tests

- Create Payment returns `201`.
- Detail returns the owner's Payment.
- Foreign Payment returns `404`.
- List pagination works.
- Student, status, month, and sort filters work.
- Update amount and note works.
- `pending -> paid` requires `paid_at`.
- Paid Payment cannot be cancelled.
- DELETE changes pending Payment to cancelled.
- Repeated DELETE on cancelled Payment is idempotent.
- Duplicate Payment returns `409`.
- Monthly statistics return correct sum and paid count.
- Outstanding statistics return correct amount and count.
- All endpoints reject missing or invalid JWT.
- All errors use the unified response envelope.

### Database Tests

- Fresh database migration creates the complete Payment schema.
- Existing Payment rows are backfilled with `student_id`.
- Migration preserves existing `refunded` values.
- Unique and foreign key constraints exist after migration.
- Migration SQL is generated successfully for PostgreSQL.

---

## 15. Documentation and Swagger

Update `docs/api-design.md` with:

- Payment request and response examples.
- Query parameter definitions.
- Status transition behavior.
- Cancellation semantics.
- Monthly and outstanding statistics examples.
- Error status codes.
- JWT requirement.

FastAPI Swagger must expose:

- Request schemas for create and update.
- Payment response schemas.
- Query parameter validation.
- `401`, `404`, `409`, and `422` response documentation.

---

## 16. Migration and Deployment Gate

Before deployment:

```powershell
cd C:\Users\dcyin\Desktop\files\tutorflow-ai\backend
alembic upgrade head
alembic current
```

The migration must complete before the application receives traffic. `Base.metadata.create_all()` is for local development only and must not be treated as a production migration mechanism.

After deployment, verify:

```http
GET /health
GET /health/db
GET /api/v1/payments/statistics/outstanding
```

---

## 17. Coding Order

1. Reconcile current Payment model and migration requirements.
2. Define Payment enum, database constraints, and schemas.
3. Implement Payment Repository and aggregate queries.
4. Implement Payment Service and status transition matrix.
5. Implement JWT-protected Payment Router.
6. Add monthly and outstanding statistics endpoints.
7. Add migration and existing-data backfill tests.
8. Add API, ownership, transition, and statistics tests.
9. Update Swagger and `docs/api-design.md`.
10. Run tests, Ruff, migration SQL generation, and diff checks.

---

## 18. Definition of Done

- Payment Create / Detail / List / Update completed.
- DELETE implements cancellation without physical deletion.
- One Lesson One Payment is protected by database constraint and Service validation.
- Amount, note, `paid_at`, and status transitions are validated.
- JWT and ownership checks are complete for every endpoint.
- Monthly income and outstanding statistics use database aggregates.
- Existing `refunded` data remains compatible but is not created by Sprint 8.
- PostgreSQL migration handles both fresh and existing databases.
- Swagger and `docs/api-design.md` are updated.
- Tests cover success, validation, ownership, duplicate, transitions, cancellation, and statistics.
- `unittest`, Ruff, Alembic SQL generation, and `git diff --check` pass.
- Existing Sprint 4-7 APIs remain behaviorally compatible.
