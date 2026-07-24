# 第三階段：API Design（API 契約設計）

> **目標：完成所有 API
> 契約（Contract），讓前後端可以依照同一份規格開發。**

## Step 1：建立 API 清單

### Auth

-   POST /auth/register
-   POST /auth/login
-   GET /auth/me

### Students

-   GET /students
-   GET /students/{id}
-   POST /students
-   PATCH /students/{id}
-   DELETE /students/{id}

### Lessons

-   GET /lessons
-   GET /lessons/{id}
-   POST /lessons
-   PATCH /lessons/{id}
-   DELETE /lessons/{id}

### Lesson Notes

-   POST /lessons/{id}/note
-   PATCH /lessons/{id}/note

### Payments

-   GET /payments
-   PATCH /payments/{id}

### Dashboard

-   GET /dashboard

### AI

-   POST /ai/summary
-   POST /ai/feedback

## Step 2：定義 Request Body

以 Student Create 為例： - name - school - grade - subject - hourly_rate

## Step 3：定義 Response Body

統一回傳完整資源與 created_at。

## Step 4：定義 Error Response

統一使用： - detail

## Step 5：HTTP Status Code

-   200 OK
-   201 Created
-   204 No Content
-   400 Bad Request
-   401 Unauthorized
-   403 Forbidden
-   404 Not Found
-   409 Conflict
-   422 Validation Error
-   500 Internal Server Error

## Step 6：Pagination

-   page
-   page_size
-   total
-   total_pages

## Step 7：Sorting

-   sort=name
-   sort=created_at
-   sort=-created_at

## Step 8：Searching

-   search=王

## Step 9：Filtering

-   grade
-   subject
-   active

## Step 10：Swagger 規範

每支 API 定義： - Tags - Summary - Description - Response Model - Status
Code

## Step 11：建立 Pydantic Schemas

schemas/ - auth.py - user.py - student.py - lesson.py - lesson_note.py -
payment.py - dashboard.py - common.py

每個 Schema： - Create - Update - Response - ListResponse

## Step 12：建立統一 Response Model

成功： - success - message - data

失敗： - success - message

## Step 13：建立 API Version

使用 /api/v1/

## Step 14：建立 Router 架構

app/api/v1/ - auth.py - students.py - lessons.py - lesson_notes.py -
payments.py - dashboard.py - ai.py

## Step 15：建立 API 文件

docs/api-design.md

包含： - API 清單 - Request - Response - Error Response - HTTP Status -
Pagination - Filter - Search - Sort

# Sprint 3 Checklist

-   [x] 建立完整 API 清單
-   [x] 定義 Request / Response
-   [x] 統一 Error Response
-   [x] HTTP Status Code
-   [x] Pagination
-   [x] Sorting
-   [x] Searching
-   [x] Filtering
-   [x] Swagger 規範
-   [x] Pydantic Schemas
-   [x] Response Model
-   [x] API Version
-   [x] Router 架構
-   [x] API 文件

# 下一階段

JWT Authentication（註冊、登入、取得目前使用者）
