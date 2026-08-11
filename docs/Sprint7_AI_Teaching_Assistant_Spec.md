# TutorFlow AI - Sprint 7 Specification
## AI Teaching Assistant & Lesson Notes (Codex Implementation Guide)

Version: 1.1

---

# Sprint Goal

建立 Lesson Note 與 AI 教學助手模組，讓教師以已儲存的課程資料產生 AI 摘要與家長回饋草稿。

完成：

- Lesson Note Create / Detail / Update
- AI Summary Draft
- Parent Feedback Draft
- AI Log
- Versioned Prompt Builder
- AI Provider 抽象層

---

# Prerequisites

必須完成 Sprint 4、5、6。

- 不得修改既有 Authentication、Student、Lesson 功能。
- 必須保留既有 Lesson Note API 路徑 `/lessons/{lesson_id}/note`，不可改為 `/lesson-notes`。
- 所有 API 繼續使用統一的 `ApiResponse` / `ErrorResponse` 格式。

---

# Scope Decisions

## Lesson Note Lifecycle

- 一堂課最多一筆 Lesson Note；資料庫 `lesson_notes.lesson_id` 的 unique constraint 是最終保護。
- Sprint 7 提供 Create、Detail、Update，不提供 DELETE。Lesson Note 視為課程歷程的一部分；未來若需要刪除功能，必須另行定義資料保留與 cascade 規則。
- 重複建立同一堂課的 Note 必須回傳 `409 Conflict`。
- 若資料庫在併發建立時發生 unique constraint error，Repository 必須 rollback，Service 將錯誤轉為 `409 Conflict`。

## AI Draft Persistence

- AI 生成 API 只回傳草稿與建立 AI Log，不得自動覆蓋或寫入 Lesson Note。
- 教師必須透過 `PATCH /lessons/{lesson_id}/note` 明確儲存或修改 `ai_summary`、`teacher_note`、`parent_feedback`。
- AI Summary 必須以已儲存的 `raw_note` 為來源；Parent Feedback 必須以已儲存的 `ai_summary` 與可選的 `teacher_note` 為來源。
- 若執行 Summary 時尚未有 Note 或 `raw_note` 為空，回傳 `409 Conflict`；若執行 Feedback 時 `ai_summary` 為空，也回傳 `409 Conflict`。

---

# Folder Structure

```text
app/
├── api/v1/lesson_notes.py
├── api/v1/ai.py
├── services/lesson_note_service.py
├── services/ai_service.py
├── services/prompt_service.py
├── services/ai_provider.py
├── repositories/lesson_note_repository.py
├── repositories/ai_log_repository.py
├── schemas/lesson_note.py
├── schemas/ai.py
├── tests/test_lesson_notes.py
└── tests/test_ai.py
```

---

# Architecture

```text
Client
  -> Router
  -> LessonNoteService / AIService
  -> LessonRepository + LessonNoteRepository (ownership and source data)
  -> PromptService
  -> AIProvider
  -> AILogRepository / LessonNoteRepository
  -> PostgreSQL
```

Rules:

- Router 只負責 schema validation、Depends、HTTP response 與 Service 呼叫。
- LessonNoteRepository 與 AILogRepository 不得包含 HTTPException、Depends、Prompt 或 AI provider 呼叫。
- `AIProvider` 是唯一可呼叫外部 AI SDK / HTTP API 的抽象層。
- 不得讓資料庫 transaction 包住長時間的 AI 網路呼叫。

---

# Domain Model

## Lesson Note

欄位沿用現有 model：

- `lesson_id`
- `raw_note`
- `ai_summary`
- `teacher_note`
- `parent_feedback`

`teacher_note` 是教師對 AI 摘要的補充或修正，並作為 Parent Feedback prompt 的可選上下文；不得在 Sprint 7 移除。

## AI Log

每次 AI 呼叫（成功或失敗）都應建立一筆 log。現有欄位 `log_type` 必須保留，並建議新增 migration 支援：

- `lesson_id`：追蹤來源課程
- `log_type`：`summary` 或 `parent_feedback`
- `provider`
- `model`
- `prompt_version`
- `status`：`succeeded` 或 `failed`
- `error_message`：失敗時的安全錯誤訊息
- `duration_ms`
- `prompt`
- `response`
- `created_at`

不得在 log 中保存 API key、Authorization header 或供應商原始敏感 metadata。

---

# API Contract

所有以下 API 都必須使用 `Depends(get_current_user)`。Lesson 不存在或不屬於 current user 時一律回傳 `404 Not Found`，避免洩漏資源存在與否。

## Lesson Notes

- `POST /lessons/{lesson_id}/note`
  - 建立一筆 Note，回傳 `201 Created`。
  - `raw_note` 必須是非空白字串；其他欄位可選。
  - 已有 Note 時回傳 `409 Conflict`。

- `GET /lessons/{lesson_id}/note`
  - 回傳該 Lesson 的 Note。
  - 尚未建立 Note 時回傳 `404 Not Found`。

- `PATCH /lessons/{lesson_id}/note`
  - 支援更新 `raw_note`、`ai_summary`、`teacher_note`、`parent_feedback`。
  - 不可修改 `id`、`lesson_id`、`created_at`。
  - 不存在的 Note 回傳 `404 Not Found`。

## AI Summary

- `POST /ai/summary`
  - Request：`{ "lesson_id": 1 }`。
  - Service 必須驗證 Lesson owner，讀取其 Student 與已儲存的 Note / `raw_note`。
  - 產生草稿、建立 AI Log、回傳 `200 OK`；不得更新 Note。

Response 的 `data.ai_summary` 必須是可驗證的結構化資料：

```json
{
  "overview": "string",
  "learning_progress": ["string"],
  "strengths": ["string"],
  "difficulties": ["string"],
  "next_steps": ["string"]
}
```

## Parent Feedback

- `POST /ai/feedback`
  - Request：`{ "lesson_id": 1 }`。
  - Service 必須驗證 Lesson owner，讀取已儲存的 Note、`ai_summary` 與可選 `teacher_note`。
  - 產生家長回饋草稿、建立 AI Log、回傳 `200 OK`；不得更新 Note。

Response：

```json
{
  "parent_feedback": "string"
}
```

---

# Ownership and Validation

- 所有 Lesson Note、AI Summary、Parent Feedback 操作都必須先驗證 `lesson.student.user_id == current_user.id`。
- Service 不得信任 client 傳入的 Student、Lesson 內容、AI Summary 或 Parent Feedback 作為 prompt 的資料來源。
- `raw_note`、`teacher_note` 與 AI response 需設定合理的長度上限；空白字串要以 validation error 拒絕。
- Provider 回傳的結構化 Summary 必須經 Pydantic schema 驗證。無法驗證時回傳 provider failure，不得保存為成功結果。

---

# Prompt Builder

Prompt 必須集中於 `PromptService`，不得寫在 Router、Repository 或 endpoint decorator。

必須提供：

- `build_summary_prompt(lesson, student, raw_note)`
- `build_feedback_prompt(lesson, student, ai_summary, teacher_note)`

Prompt 規則：

- 每個 prompt template 都有固定 `prompt_version`。
- 明確要求輸出指定 JSON schema，避免只依賴自然語言格式。
- 指定回饋語言、家長可讀性與不得捏造未提供的學習事實。
- 限制輸入資料只包含任務所需的個資。

---

# AI Provider Abstraction

定義可替換的 `AIProvider` 介面，例如：

```text
generate(prompt, response_schema) -> AIProviderResult
```

`AIProviderResult` 至少包含 provider、model、content、duration_ms；失敗時應拋出明確的 provider exception。

Requirements:

- provider API key 只能由設定／環境變數讀取，不得由 client 傳入或寫入 log。
- 設定明確 timeout、有限次數 retry 與 rate-limit 行為。
- 對非同步或長時間生成，先採同步、有 timeout 的實作；若平均延遲不符合 HTTP request 時限，再另行設計 job queue，不得在 Sprint 7 混入未定義的背景任務。
- 測試必須使用 fake provider，不得呼叫真實 AI provider。

---

# Error Contract

| Situation | Status | Behavior |
| --- | --- | --- |
| Missing or foreign Lesson | 404 | Return unified error response |
| Missing Lesson Note | 404 | Return unified error response |
| Duplicate Lesson Note | 409 | Return unified error response |
| Missing raw note or AI summary source | 409 | Return unified error response |
| Invalid request or blank / oversized field | 422 | Return unified validation error |
| Provider configuration unavailable | 503 | Log failed attempt without secrets |
| Provider timeout | 504 | Log failed attempt |
| Provider rate limit or upstream failure | 502 or 503 | Log failed attempt |
| Invalid provider structured output | 502 | Log failed attempt |

---

# Privacy and Retention

- Lesson Note、prompt、response 都可能包含學生個資，只允許該 Lesson owner 存取。
- 定義 AI Log 的保存期限與清理機制；預設不得無限期保留 raw prompt / response。
- 在使用第三方 provider 前，產品必須明確說明資料傳輸與取得必要同意。
- 記錄與監控資料應採最小化原則；必要時遮罩敏感資訊。

---

# Repository

## LessonNoteRepository

Implement：

- `create()`
- `get_by_lesson()`
- `update()`

## AILogRepository

Implement：

- `create()`

禁止：

- Business Logic
- HTTPException
- Depends
- Prompt handling
- AI provider call

---

# Service

## LessonNoteService

- `create_note()`
- `update_note()`
- `get_note()`
- Lesson ownership validation
- One-note conflict conversion

## AIService

- `generate_summary()`
- `generate_parent_feedback()`
- Lesson ownership and source-note validation
- Provider error conversion
- Success and failure AI Log creation

## PromptService

- `build_summary_prompt()`
- `build_feedback_prompt()`

---

# Testing

必須完成：

- Lesson Note Create、Detail、Update
- Duplicate Lesson Note 回傳 `409`
- Lesson / Note ownership 與 JWT
- AI Summary 與 Parent Feedback 成功流程
- AI generated draft 不會自動覆蓋 Note
- AI Log 成功與失敗紀錄
- 缺少 raw note / ai summary 回傳 `409`
- Provider timeout、rate limit、configuration error、invalid structured output
- PromptService 輸出包含預期資料與 prompt version
- 全部 AI test 使用 fake provider
- Swagger 與 `docs/api-design.md` 更新

---

# Coding Order

1. Schemas and response contracts
2. Repository and migration design
3. Prompt Service
4. AIProvider abstraction and fake provider
5. AI Service
6. LessonNote Service
7. Routers and JWT protection
8. Tests
9. Swagger and documentation

---

# Definition of Done

- Lesson Note Create / Detail / Update 完成
- Existing Lesson Note API paths preserved
- JWT 與 ownership 正常
- AI Summary 與 Parent Feedback 產生 draft，不自動覆蓋 Note
- Structured Summary schema validation
- AI Log 成功與失敗可追蹤
- Prompt version 與 Provider abstraction 完成
- Provider failure contract 完成
- Privacy / retention decisions documented
- Tests、Swagger、API documentation 更新
