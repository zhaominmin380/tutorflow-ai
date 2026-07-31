# TutorFlow AI

# Sprint 5 Specification (Codex Implementation Guide)

> Version: 1.0 Goal: Student Management Module Target: Codex Tech:
> FastAPI + SQLAlchemy 2.0 + PostgreSQL + Pydantic v2

------------------------------------------------------------------------

# 1. Sprint Objective

完成 Student Management Module，正式從 Authentication 進入 Business
Domain。

完成後系統需具備：

-   Student CRUD
-   JWT 保護
-   User Ownership
-   Pagination
-   Search
-   Filter
-   Sort
-   統一 Response Model
-   Repository / Service Architecture
-   Swagger Documentation
-   Unit Tests

------------------------------------------------------------------------

# 2. Learning Objectives

Codex 應維持以下架構原則：

-   Router 不直接操作資料庫
-   Repository 不包含商業邏輯
-   Service 處理所有商業邏輯
-   所有 API 使用 JWT
-   Response Model 全部統一

------------------------------------------------------------------------

# 3. Folder Structure

    app/
    ├── api/v1/students.py
    ├── repositories/student_repository.py
    ├── services/student_service.py
    ├── schemas/student.py
    ├── models/student.py
    └── tests/test_students.py

------------------------------------------------------------------------

# 4. Functional Requirements

## Create Student

建立學生

必要欄位

-   name
-   school
-   grade
-   subject

選填

-   note

自動

-   user_id=current_user.id

------------------------------------------------------------------------

## List Students

支援

-   pagination
-   search
-   filter
-   sort

只可看自己的學生。

------------------------------------------------------------------------

## Detail

GET /students/{id}

若不存在：

404

若非本人：

404（避免資訊外洩）

------------------------------------------------------------------------

## Update

允許更新：

-   name
-   school
-   grade
-   subject
-   note
-   is_active

不可修改

-   id
-   user_id
-   created_at

------------------------------------------------------------------------

## Delete

Soft Delete

    is_active=False

不可真正刪除資料。

------------------------------------------------------------------------

# 5. API Contract

POST /students

GET /students

GET /students/{id}

PATCH /students/{id}

DELETE /students/{id}

Response 使用 ApiResponse。

------------------------------------------------------------------------

# 6. Repository Responsibilities

只能：

-   create
-   get_by_id
-   list
-   update
-   soft_delete

Repository 不可：

-   驗證權限
-   raise HTTPException
-   使用 Depends

------------------------------------------------------------------------

# 7. Service Responsibilities

負責：

-   Ownership Validation
-   Duplicate Validation（若需要）
-   Search 組裝
-   Filter 組裝
-   Sort 組裝
-   呼叫 Repository

------------------------------------------------------------------------

# 8. Router Responsibilities

Router 僅：

-   Request Validation
-   Depends(get_db)
-   Depends(get_current_user)
-   呼叫 Service
-   回傳 Response

不得直接：

-   session.query(...)
-   db.execute(...)
-   SQLAlchemy CRUD

------------------------------------------------------------------------

# 9. Security

所有 API

    Depends(get_current_user)

Repository Query 必須：

    student.user_id == current_user.id

------------------------------------------------------------------------

# 10. Query Parameters

Pagination

    ?page=1
    &page_size=20

Search

    ?search=John

搜尋：

-   name
-   school

Filter

    ?grade=8

    ?subject=Math

    ?active=true

Sort

    ?sort=name

    ?sort=-created_at

------------------------------------------------------------------------

# 11. Pydantic Schemas

建立：

-   StudentCreate
-   StudentUpdate
-   StudentResponse
-   StudentListResponse

Field Validation：

-   name 長度限制
-   school 長度限制
-   note Optional

------------------------------------------------------------------------

# 12. Error Handling

401 Unauthorized

404 Student Not Found

422 Validation Error

500 Internal Error

全部維持統一 ErrorResponse。

------------------------------------------------------------------------

# 13. Swagger

每個 API 必須：

-   summary
-   description
-   response_model
-   responses

------------------------------------------------------------------------

# 14. Testing

至少完成：

Authentication

-   JWT Required
-   Unauthorized

CRUD

-   Create
-   Detail
-   List
-   Update
-   Delete

Query

-   Pagination
-   Search
-   Filter
-   Sort

Ownership

-   User A 不可存取 User B

Validation

-   Empty name
-   Invalid grade

------------------------------------------------------------------------

# 15. Acceptance Checklist

## Architecture

-   [x] Repository 不含商業邏輯
-   [x] Service 不直接寫 SQL
-   [x] Router 不直接 CRUD

## Security

-   [x] JWT 正常
-   [x] Ownership 正常

## API

-   [x] Create
-   [x] List
-   [x] Detail
-   [x] Update
-   [x] Delete

## Query

-   [x] Pagination
-   [x] Search
-   [x] Filter
-   [x] Sort

## Documentation

-   [x] Swagger
-   [x] docs/api-design.md 更新

## Tests

-   [x] 全部通過

## Code Quality

-   [x] 型別完整
-   [x] Ruff/Formatter 無問題（Sprint 5 相關檔案已通過 Ruff）
-   [x] git diff --check 通過

------------------------------------------------------------------------

# 16. Coding Order (Important)

Codex 必須依序完成：

1.  Student Model
2.  Student Schema
3.  Student Repository
4.  Student Service
5.  Student Router
6.  JWT Protection
7.  Search
8.  Filter
9.  Sort
10. Pagination
11. Tests
12. Swagger
13. Documentation

禁止跳步。

------------------------------------------------------------------------

# 17. Definition of Done

Sprint 5 完成條件：

-   Student CRUD 可正常操作
-   JWT 保護全部 API
-   Search / Filter / Sort / Pagination 完成
-   Swagger 完整
-   Unit Tests 全部通過
-   API Contract 更新
-   無重大 Code Smell
-   維持 Repository / Service / Router 三層架構
