# TutorFlow AI - Sprint 8 Specification
## Payment & Billing Domain (Codex Implementation Guide)

Version: 1.0

## Sprint Goal
完成 Payment & Billing Domain。

### Deliverables
- Payment CRUD
- Payment Status
- Monthly Statistics
- Outstanding Payments
- Dashboard Foundation
- JWT Authentication
- Ownership Validation

## Prerequisites
- Sprint 4 Authentication
- Sprint 5 Student Domain
- Sprint 6 Lesson Domain
- Sprint 7 AI Teaching Assistant

不得修改既有功能。

## Folder Structure

app/
- api/v1/payments.py
- services/payment_service.py
- repositories/payment_repository.py
- schemas/payment.py
- tests/test_payments.py

## Architecture

Client -> Router -> Service -> Repository -> PostgreSQL

Router 不得直接操作 SQLAlchemy。

## Payment Model

- id
- student_id
- lesson_id
- amount
- status
- paid_at
- note
- created_at
- updated_at

Status(Enum)

- pending
- paid
- cancelled

## Functional Requirements

### Create
- lesson_id 必須存在
- Lesson 屬於 current_user
- amount > 0
- 一堂課只能建立一筆 Payment

### Detail
非本人資料回傳 404。

### List
支援：
- Pagination
- Student Filter
- Status Filter
- Month Filter
- Sort

### Update
允許修改：
- amount
- status
- note
- paid_at

### Delete
Soft Delete（status=cancelled）。

## Statistics

新增：

- monthly_income()
- outstanding_amount()
- outstanding_count()
- paid_count()

供 Sprint 9 Dashboard 使用。

## API

POST /payments
GET /payments
GET /payments/{id}
PATCH /payments/{id}
DELETE /payments/{id}
GET /payments/statistics/monthly
GET /payments/statistics/outstanding

## Repository

Implement：
- create
- get_by_id
- list
- update
- cancel
- monthly_income
- outstanding

禁止：
- HTTPException
- Depends
- Business Logic

## Service

Implement：
- create_payment
- get_payment
- list_payments
- update_payment
- cancel_payment
- monthly_statistics

負責：
- Ownership Validation
- Lesson Validation
- Amount Validation
- Status Transition Validation

## Status Transition

允許：
pending -> paid
pending -> cancelled

禁止：
paid -> pending
cancelled -> paid

## Security

全部使用 Depends(get_current_user)。

Repository 必須限制：

payment.student.user_id == current_user.id

## Testing

- Create
- Detail
- List
- Update
- Cancel
- JWT
- Ownership
- Statistics
- Duplicate Payment
- Invalid Status Transition

## Codex Rules

DO
- Preserve Sprint4~7
- Repository Pattern
- Enum Status
- Update Swagger
- Update docs/api-design.md
- Add Tests

DON'T
- SQL in Router
- Business Logic in Repository
- Break existing APIs

## Coding Order

1. Payment Schema
2. Payment Repository
3. Payment Service
4. Payment Router
5. Statistics
6. JWT
7. Tests
8. Swagger
9. Documentation

## Definition of Done

- Payment CRUD 完成
- One Lesson One Payment
- Statistics 完成
- JWT 正常
- Ownership 正常
- Swagger 更新
- Tests 全數通過
