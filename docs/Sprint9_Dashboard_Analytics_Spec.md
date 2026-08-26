# TutorFlow AI - Sprint 9 Specification
## Dashboard & Analytics Domain (Codex Implementation Guide)

Version: 1.0

## Sprint Goal
建立 Dashboard 與 Analytics 模組，整合 Sprint 5~8 資料。

### Deliverables
- Dashboard API
- Monthly Overview
- Income Analytics
- Student Analytics
- Lesson Analytics
- AI Analytics
- Chart-ready API
- JWT
- Ownership Validation

## Prerequisites
完成 Sprint 4~8，不修改既有 API。

## Folder Structure
app/
- api/v1/dashboard.py
- services/dashboard_service.py
- repositories/dashboard_repository.py
- schemas/dashboard.py
- tests/test_dashboard.py

## Architecture
Client -> Router -> Service -> Repository -> PostgreSQL

所有統計由 SQL Aggregate 完成，不得在 Python 對大量資料自行統計。

## Dashboard Cards
- 今日課程
- 本月課程
- 學生總數
- 啟用學生
- 本月收入
- 未付款金額
- 未付款筆數

## Analytics
Lesson
- completed
- scheduled
- cancelled

Student
- total
- active
- inactive

Payment
- monthly_income
- outstanding_amount
- outstanding_count

AI
- summaries
- feedbacks
- total_requests

## APIs
GET /dashboard
GET /dashboard/overview
GET /dashboard/income
GET /dashboard/students
GET /dashboard/lessons
GET /dashboard/ai

## Repository
Implement
- overview()
- income()
- lesson_statistics()
- student_statistics()
- ai_statistics()

使用 COUNT、SUM、GROUP BY。

## Service
負責：
- Ownership Validation
- Dashboard Response 組裝
- 日期驗證

## Security
所有 API 使用 Depends(get_current_user)。

所有統計限制 current_user.id。

## Performance
禁止：
- SELECT * 後 Python 統計
- N+1 Query

必須：
- SQL Aggregate

## Testing
- Overview
- Income
- Student
- Lesson
- AI
- JWT
- Ownership
- Empty Database
- Large Dataset

## Codex Rules
DO
- Preserve Sprint4~8
- SQL Aggregate
- Update Swagger
- Update docs/api-design.md
- Add Tests

DON'T
- SQL in Router
- Python Aggregate
- Break Existing APIs

## Coding Order
1. Dashboard Schema
2. Repository
3. Service
4. Router
5. Aggregate Queries
6. Tests
7. Swagger
8. Documentation

## Definition of Done
- Dashboard API 完成
- 所有統計正確
- SQL Aggregate
- JWT 正常
- Ownership 正常
- Swagger 更新
- Tests 通過
- 前端可直接串接圖表
