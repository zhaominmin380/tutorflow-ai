# TutorFlow AI - Sprint 6 Specification
## Lesson Domain Module (Codex Implementation Guide)

Version: 1.0

---

# Sprint Goal

完成 Lesson Domain，讓教師可以管理所有課程，並作為 Sprint 7 AI 與 Sprint 8 Payment 的基礎。

完成後必須支援：

- Lesson CRUD
- JWT Authentication
- User Ownership
- Pagination
- Search
- Filter
- Sort
- Swagger
- Tests

---

# Learning Objectives

- Repository Pattern
- Service Layer
- One-to-Many Relationship
- Enum Status
- Business Validation
- Ownership Validation

---

# Folder Structure

```text
app/
├── api/v1/lessons.py
├── services/lesson_service.py
├── repositories/lesson_repository.py
├── schemas/lesson.py
└── tests/test_lessons.py
```

---

# Architecture

```text
Client
  ↓
Router
  ↓
Service
  ↓
Repository
  ↓
PostgreSQL
```

Router 不得直接查詢資料庫。

---

# Functional Requirements

## Create Lesson

Required:
- student_id
- date
- duration
- status

Rules:
- student 必須存在
- student 必須屬於 current_user
- duration > 0
- status 預設 scheduled

## List Lessons

支援：
- Pagination
- Student Filter
- Status Filter
- Date Range
- Sort

僅回傳 current_user 的資料。

## Get Lesson

不存在或非本人皆回傳 404。

## Update Lesson

可修改：
- date
- duration
- status

不可修改：
- id
- student_id
- created_at

## Delete Lesson

採 Soft Delete。

---

# Status

Enum：

- scheduled
- completed
- cancelled

---

# Repository

Implement：

- create()
- get_by_id()
- list()
- update()
- soft_delete()
- list_by_student()

禁止：
- HTTPException
- Depends
- JWT
- Business Logic

---

# Service

Implement：

- create_lesson()
- get_lesson()
- list_lessons()
- update_lesson()
- delete_lesson()

負責：

- Ownership Validation
- Student Validation
- Date Validation
- Duration Validation

---

# Router

只負責：

- Validation
- Depends
- Response
- 呼叫 Service

不得：

- SQLAlchemy Query
- CRUD

---

# APIs

- POST /lessons
- GET /lessons
- GET /lessons/{id}
- PATCH /lessons/{id}
- DELETE /lessons/{id}
- GET /students/{student_id}/lessons

---

# Query

Pagination

?page=1&page_size=20

Status

?status=completed

Student

?student_id=1

Date

?start_date=2026-08-01&end_date=2026-08-31

Sort

?sort=date
?sort=-date

---

# Security

所有 API：

Depends(get_current_user)

Repository 必須限制：

lesson.student.user_id == current_user.id

---

# Testing

完成：

- Create
- List
- Detail
- Update
- Delete
- JWT
- Ownership
- Pagination
- Status Filter
- Student Filter
- Date Range
- Validation

---

# Codex Rules

DO

- Preserve Sprint4 Authentication
- Preserve Student Domain
- Repository Pattern
- Update Swagger
- Update docs/api-design.md
- Add Tests

DON'T

- SQL in Router
- Business Logic in Repository
- Modify Authentication
- Break API Contract

---

# Coding Order

1. Lesson Schema
2. Lesson Repository
3. Lesson Service
4. Lesson Router
5. JWT Protection
6. Query Features
7. Tests
8. Swagger
9. Documentation

---

# Definition of Done

- CRUD 完成
- JWT 正常
- Ownership 正常
- Query 完成
- Swagger 更新
- Tests 全數通過
