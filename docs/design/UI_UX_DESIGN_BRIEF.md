# TutorFlow AI — UI/UX Design Brief

**Purpose:** Give product and UI designers an implementation-faithful picture of TutorFlow AI as it exists in the backend today. Use this document to design the MVP without inventing controls, status changes, or data that the product cannot currently support.

**Product:** A private workspace for an individual tutor to manage students, lessons, lesson records, AI-assisted teaching notes, and lesson payments.

**Primary user:** A tutor. Every account sees and manages only its own students, lessons, notes, payments, dashboard metrics, and AI usage. There are no student, parent, admin, or staff-facing roles in the current product.

**Reporting locale:** All dashboard and payment month calculations use the `Asia/Taipei` calendar and TWD. Datetimes returned by the API are timezone-aware; present them in the tutor-facing Taipei time consistently.

---

## 1. Product mental model

The core relationship is deliberately simple:

```text
Tutor account
  └─ Student (active or archived)
       └─ Lesson (scheduled / completed / cancelled / no-show)
            ├─ One lesson note at most
            │    ├─ raw teaching notes
            │    ├─ structured AI lesson-summary draft
            │    ├─ teacher additions
            │    └─ parent-feedback draft
            └─ One payment at most
                 └─ pending / paid / cancelled / legacy refunded
```

Design around a tutor moving through this sequence:

1. Create an active student.
2. Schedule a lesson for that student.
3. Record what happened in the lesson.
4. Ask AI to draft a structured summary, review it, and explicitly save it.
5. Optionally add a teacher note, then ask AI to draft parent feedback, review it, and explicitly save it.
6. Create one payment for the lesson and mark it paid when money is received.

The app should feel like a calm, efficient work tool: the tutor is in control; AI is an editable drafting assistant, never an automatic author.

---

## 2. Recommended app structure

Use persistent desktop navigation and a compact mobile navigation. The required product areas are:

| Area | Primary job | Suggested navigation label |
| --- | --- | --- |
| Dashboard | See today’s work and business health | Dashboard |
| Students | Find, add, edit, and archive students | Students |
| Lessons | Schedule and manage lessons | Lessons |
| Lesson record | Capture notes and use AI after a lesson | Reached from a lesson detail view |
| Payments | Track lesson-level receivables and income | Payments |
| Analytics | Review monthly income, lesson, student, and AI usage | Analytics; it may be a Dashboard subpage |
| Account | Show the signed-in tutor’s name/email and sign out locally | Profile / account menu |

The backend does not provide a profile-edit endpoint or a server-side logout endpoint. The account area should therefore show identity and offer **Sign out**, which clears the client-held token; do not design profile editing as a working MVP flow.

### Global shell

- Put the tutor’s name, account menu, and sign-out action in the header/sidebar.
- Make the current section unmistakable.
- Keep a persistent, obvious **Add student** and/or context-sensitive **Schedule lesson** entry point on desktop; on mobile use a floating action button or a primary action in the page header.
- Use one global error pattern (inline alert/toast) and a clear retry action for failed reads and saves.
- Do not imply collaboration, parent accounts, chat, scheduling availability, recurring lessons, lesson reminders, file uploads, invoice downloads, exports, or multi-currency—none has backend support today.

---

## 3. Screen specifications

### A. Authentication

#### Sign in

Fields:

- Email address
- Password

Actions:

- **Sign in** — enabled only when both fields are present.
- Link to **Create an account**.

Show an inline, non-revealing credential error for a `401` response (for example, “Email or password is incorrect.”). Do not reveal whether an email is registered. A valid sign-in returns a token and the tutor’s name/email; route to Dashboard.

#### Create account

Fields and validation:

| Field | Rule |
| --- | --- |
| Name | Required; 1–100 characters after trimming |
| Email | Required valid email address |
| Password | Required; at least 8 characters |

On duplicate email (`409`), show an inline error beside email and preserve the entered name. Successful registration signs the tutor in immediately.

#### Authentication recovery

Any protected API call can return `401` when the token is absent, invalid, expired, or its user is gone. Clear the local session and route to Sign in, with one understandable message such as “Your session has ended. Please sign in again.”

There is no password reset or email verification flow in the backend; leave them out of MVP designs.

---

### B. Dashboard

The default dashboard is a current-day/current-month snapshot. It is not a selectable-month view; monthly comparison belongs in Analytics.

#### Required overview cards

`GET /dashboard` (or `/dashboard/overview`) provides these values:

| Card | Data | Meaning | Useful destination |
| --- | --- | --- | --- |
| Today’s lessons | `today_lessons_count` | All lessons whose start time falls today, regardless of lesson status | Lessons filtered to today |
| This month’s income | `month_income` in TWD | Paid payments whose `paid_at` falls this month | Payments / income analytics |
| Active students | `active_students_count` | Students available for new lessons | Active Students |
| Outstanding payments | `unpaid_payments_count` and `outstanding_payment_amount` in TWD | Pending payments only | Payments filtered to Pending |
| AI drafts generated | `ai_requests_count` | Summary and parent-feedback requests this month, including failed attempts | AI analytics |

Important interpretation rules:

- A scheduled, cancelled, or no-show lesson can appear in the “Today’s lessons” count; status is not filtered there.
- Income means **paid**, not merely billed/pending.
- Outstanding means **pending**, not cancelled, refunded, or paid.
- Values can legitimately be zero. Use intentional empty/zero states rather than a broken-looking dashboard.

#### Recommended content below the cards

The backend does not supply a dedicated “today’s lesson objects” endpoint, but the design can populate a “Today’s agenda” by querying Lessons with `start_date` and `end_date` set to today. Include learner name by resolving `student_id` from the student list/detail client cache or fetching the relevant student; lesson rows themselves contain `student_id`, not student name.

Suggested agenda row: time, student name, duration, location when present, and lesson status. Each row opens its lesson detail. Show a concise empty state with **Schedule lesson** when there are no lessons today.

---

### C. Students

#### Student directory

Use a searchable, filterable list/table on desktop and a stacked card list on mobile.

Every returned student has:

| Data | Display guidance |
| --- | --- |
| `name` | Primary identifier and link to student detail |
| `school`, `grade` | Secondary education context; both are required when creating but can be null in existing data |
| `subject` | Primary subject tag; required when creating but can be null in existing data |
| `hourly_rate` | Optional TWD rate; show “Not set” when null. It is reference information, not automatically applied to payments. |
| `is_active` | Use a clear Active / Archived status chip |
| `note` | Do not make this long free text a dense list column; surface as preview, tooltip, or detail-only field |

Required controls:

- Search input: searches student **name and school**.
- Filters: grade, subject, and Active / Archived / All.
- Sorting: Name (A–Z / Z–A) and Created date (newest / oldest).
- Pagination: default 20; the API supports 1–100 per page.
- **Add student** primary action.

The filters are text values, not backend-provided taxonomy lists. A searchable/selectable input is safe; do not assume controlled dropdown options exist.

#### Add / edit student

Create form:

| Field | Required | Rule / UI treatment |
| --- | --- | --- |
| Name | Yes | 1–100 non-blank characters |
| School | Yes | 1–100 non-blank characters |
| Grade | Yes | 1–50 non-blank characters |
| Subject | Yes | 1–100 non-blank characters |
| Hourly rate | No | Non-negative number; label in TWD; allow blank |
| Internal note | No | Free text |

Edit form exposes the same fields plus the Active / Archived toggle. Be explicit that hourly rate is **not** a bill and does not create or update payments.

#### Archive, not delete

The API’s student “delete” action only changes `is_active` to `false`. Design this as **Archive student**, not “Delete,” and confirm the consequence:

> Archived students remain in history and cannot be selected for new lessons or new payments.

Offer reactivation from the student edit screen. Avoid destructive-delete copy, irreversible wording, or a trash-only UI. Existing lessons and payments remain accessible in the backend after archival.

#### Student detail

Header: name, school, grade, subject, Active/Archived status, optional hourly rate, actions **Edit** and **Archive/Reactivate**.

Content:

- Internal note (if present)
- Lesson history tab/section using `GET /students/{student_id}/lessons`
- Status and date-range filters, sort, and pagination
- **Schedule lesson** only if student is Active

The backend rejects this student-lesson query and lesson creation for archived students. For archived students, retain history but hide/disable new-lesson actions with an explanation.

---

### D. Lessons

#### Lessons index

This is the planning and lesson-history workspace. A calendar, chronological list, or both can be designed; a calendar is a presentation choice, not a separate backend feature.

Each lesson provides:

| Data | Display guidance |
| --- | --- |
| `start_time` | Main date/time; show in Asia/Taipei time |
| `duration_minutes` | Show as a human-readable duration (for example, “60 min”) |
| `student_id` | Resolve to student name in the UI; the lesson response does not include name |
| `status` | Status chip; use the semantic map below |
| `location` | Optional; show “Location not set” in detail, omit from cramped cards when null |
| `remark` | Optional planning context; show a preview/list line or detail body |

Required controls:

- Keyword search across **student name, location, and remark**.
- Student filter.
- Lesson-status filter.
- Inclusive Start date / End date filters (`YYYY-MM-DD` in the API).
- Sorting: date/start time, creation date, or status; ascending/descending.
- Pagination.
- **Schedule lesson** primary action.

Status semantics and visual direction:

| Status | Meaning | Suggested treatment |
| --- | --- | --- |
| `scheduled` | Planned or upcoming lesson | Neutral/brand accent; calendar presence |
| `completed` | Lesson took place | Success green; make “Open lesson record” easy to find |
| `cancelled` | Lesson did not occur | Muted neutral; clearly not income |
| `no_show` | Attendance did not happen | Caution/error color distinct from cancelled |

Do not allow the UI to treat the status as a payment state. The backend does not prevent billing a lesson based on its status, so if product design wants a policy such as “only completed lessons can be billed,” that requires a backend/product decision first.

#### Schedule lesson

Fields:

| Field | Required | Rule / UI treatment |
| --- | --- | --- |
| Student | Yes | Choose from Active students only |
| Start date and time | Yes | Send timezone-aware ISO datetime; display Taipei time |
| Duration | Yes | Positive whole number of minutes |
| Status | Yes | Defaults to Scheduled; offer all four current statuses if creating historical records is useful |
| Location | No | Up to 255 characters |
| Remark | No | Free-text teaching focus/context |

There is no availability, conflict detection, recurring schedule, video link, attendee list, or reminder support. Do not design validation or automation that implies those services exist.

#### Lesson detail and edit

Header: resolved student name, date/time, duration, current status. Include strong links/actions for **Open lesson record**, **Create payment / Open payment** (after resolving payment availability), **Edit lesson**, and **Delete lesson**.

The editable backend fields are only:

- Start date/time
- Duration
- Status

Student, location, and remark are frozen after creation by the current API. In the MVP, show them as read-only in edit mode. Do not show working edit controls for them unless the product also extends the backend.

#### Delete lesson

Lesson deletion is permanent and cascades to its lesson note and payment. Use a high-friction confirmation that names all affected records, for example:

> Delete this lesson permanently? Its lesson record and payment, if any, will also be removed.

This action cannot be undone. A lesson is not archived or cancelled by this action; **Mark cancelled** is the reversible/history-preserving alternative.

---

### E. Lesson record and AI writing workspace

This is the most important product workflow. It should be designed as a focused lesson-detail subpage or a full-screen editor, not as a generic chatbot.

#### Record lifecycle

- A lesson has **zero or one** record; it cannot have multiple separate note entries.
- A new record requires a non-empty raw lesson note.
- There is no record delete action.
- Generated content is a draft until the tutor explicitly saves it.

Suggested page hierarchy:

1. Lesson context header: student name, subject/grade, lesson time, duration, location, and status.
2. **Raw lesson notes** editor (required to create the record; maximum 10,000 characters).
3. **AI lesson summary** structured review panel.
4. **Teacher additions** editor (optional; maximum 5,000 characters).
5. **Parent feedback** editor/review panel (maximum 5,000 characters).
6. A visible saved/draft state and “last saved” timestamp.

#### Raw lesson notes

For a lesson with no record, show an empty state and one primary action: **Create lesson record**. The raw note is required, non-blank, and capped at 10,000 characters. Once saved, this creates the lesson’s only record.

For an existing record, allow editing raw notes and save through the normal record update action. Do not offer a second “create record” action; attempting this is a conflict (`409`).

#### AI lesson-summary draft

The **Generate AI summary** action is available only after a record with a saved, non-empty raw note exists.

Generation returns a structured draft with exactly these sections:

| Section | UI recommendation |
| --- | --- |
| Overview | Editable rich/plain text area |
| Learning progress | Editable repeatable bullet list |
| Strengths | Editable repeatable bullet list |
| Difficulties | Editable repeatable bullet list; an empty list is valid |
| Next steps | Editable repeatable bullet list |

Each list permits up to 10 items; an item must be non-empty and at most 1,000 characters. Overview is required and at most 2,000 characters. Preserve structured editing—do not collapse the returned summary into one opaque text blob.

**Critical persistence rule:** `POST /ai/summary` returns a draft and creates an AI log, but does **not** update the lesson record. Clearly label the result **AI draft — not saved** and present a deliberate **Save summary** action. Saving uses the note update endpoint. If a previous saved summary exists, ask before replacing it; never silently overwrite it.

#### Teacher additions and parent-feedback draft

Teacher additions are optional context that can be saved independently. The **Generate parent feedback** action is only valid after an **AI summary has been saved**. A summary visible only as an unsaved draft is not enough for the backend.

The feedback result is editable text. As with the summary, label it **AI draft — not saved** and require an explicit **Save parent feedback** action. The backend has no direct send-to-parent integration; label the next user action as **Copy for parent** rather than Send.

Recommended button state progression:

```text
No record
  → Save raw notes
  → Generate summary
  → Review/edit summary → Save summary
  → Optionally save teacher additions
  → Generate parent feedback
  → Review/edit feedback → Save parent feedback / Copy for parent
```

#### AI loading, error, and privacy states

- Show an in-place generating state with disabled duplicate-submit buttons; generation can take time.
- `409`: explain the missing prerequisite (“Save raw lesson notes first” or “Save the AI summary before generating parent feedback”).
- `503`: AI is unavailable/unconfigured or paused for required data-processing consent. Keep the tutor’s notes intact and offer retry when appropriate.
- `504`: generation timed out. Offer retry.
- `502`: the provider failed or returned invalid content. Explain that no content was saved and offer retry/edit manually.
- Do not expose internal prompts, provider names, model names, or AI logs in the tutor UI; there is no read API for them.
- Before the first AI action, use concise contextual disclosure that lesson information is sent to the configured AI service, subject to the product’s consent/privacy policy. The backend refuses AI generation until data-processing consent is configured.

---

### F. Payments

Payments are lesson-level receivables, not a general ledger. One lesson can have **at most one** payment record—including a cancelled record—and that payment cannot be recreated after cancellation.

#### Payment list

Use a list/table with:

- Amount in TWD
- Payment status
- Paid date/time (or “Not paid”)
- Internal payment note preview
- Associated lesson link
- Associated student name resolved client-side from `student_id`

Controls:

- Filter by student, status, and month.
- Sort by created date, paid date, amount, or status; ascending/descending.
- Pagination (1–100 per page).
- **Create payment**.

The month filter has a specific behavior: it filters paid records by `paid_at`; all other statuses by `created_at`. Explain this in a tooltip if a user could misread the results.

The backend returns IDs rather than lesson time or student name. The UI needs to resolve those through its student/lesson data, cache, or additional reads. Do not display raw IDs as the primary human-facing content.

#### Create payment

Fields:

| Field | Required | Rule / UI treatment |
| --- | --- | --- |
| Lesson | Yes | Select an owned lesson; validate that it does not already have a payment |
| Amount | Yes | Positive TWD amount; maximum `99,999,999.99`; at most two decimal places |
| Note | No | Up to 5,000 characters; cannot be blank if provided |

Create always produces a **Pending** payment. Do not put status or paid-date controls in the create form. Because there is no “lessons without payments” API nor payment ID on a lesson response, a polished picker may need to query lessons and inspect payments separately; if ambiguity remains, handle a `409` “A payment already exists for this lesson” response gracefully.

#### Payment detail and status changes

Use unambiguous states:

| Status | Meaning | Available MVP actions |
| --- | --- | --- |
| `pending` | Awaiting payment | Edit amount/note; Mark as paid; Cancel payment |
| `paid` | Money received | Correct paid date, amount, or note; status cannot change |
| `cancelled` | Payment record cancelled | Read-only; cannot restore or create another payment for that lesson |
| `refunded` | Legacy historical state | Read-only; no UI action creates it |

**Mark as paid** needs a timezone-aware paid date/time. Prefill “now” in Taipei time but make it editable before save. The API requires `paid_at` when pending becomes paid—do not offer one-click confirmation without this value.

**Cancel payment** is a soft cancellation, not record deletion. It is only possible from Pending; paid and refunded payments cannot be cancelled. A repeated cancel of an already-cancelled payment succeeds silently, but the UI should show it as already cancelled rather than offering the action.

No refund workflow exists. Do not add a Refund button or imply that a paid payment can be reopened.

#### Payment summary

Surface two small read-only summary cards above the list when useful:

- **Monthly income** — paid total and count for a selected month.
- **Outstanding** — pending amount and count across all time.

Do not call pending value “income.” All monetary values are TWD and must retain two-decimal precision in input and display.

---

### G. Analytics

Analytics is read-only and uses a user-selected `YYYY-MM` month for income, lessons, and AI. Default to the current Taipei month. A standard month picker is suitable; do not design arbitrary date-range analytics because the API does not offer it.

#### Income analytics

Show:

- Total paid income (TWD)
- Number of paid payments
- Daily paid-income chart

The endpoint returns every day of the selected month, including zero-value days. Use a daily bar/line chart with meaningful zero-state treatment and a tooltip with date, amount, and paid count. Do not include pending, cancelled, or refunded records.

#### Lesson analytics

Show:

- Total lessons
- Status breakdown: Scheduled, Completed, Cancelled, No-show
- Daily lesson volume chart, ideally stacked by status

Every status count and every day is returned even if zero. Preserve No-show as a visually distinct category from Cancelled.

#### Student analytics

Show current totals only:

- Total students
- Active students
- Archived students

These counts do not take a month and are a helpful compact card group, rather than a time-series chart.

#### AI usage analytics

Show:

- Total requests
- Lesson-summary requests
- Parent-feedback requests
- Successful vs failed requests
- Average generation duration in milliseconds (format conversationally, for example `1.25 s`)

Failed attempts count as requests. This is operational usage information, not a measure of saved or parent-sent feedback. Do not present it as a quality score.

---

## 4. Interaction and data constraints designers must preserve

### Data ownership and privacy

- All data is private to the signed-in tutor. No student switcher across tutors, shared notes, or parent view should be designed for MVP.
- Student notes, lesson notes, AI drafts, and parent feedback can contain sensitive student information. Do not surface their full contents in global search results, activity feeds, or analytics.
- Search operates only where the API supports it: Student name/school in Students; student name/location/remark in Lessons. Payment list has no keyword search.

### API behavior

- Successful API data lives inside `{ success, message, data }`; list results live under `data.items` and `data.pagination`.
- `204 No Content` actions have no response body. Treat the action as successful and refresh/local-update the UI.
- `404` can mean absent *or not owned by the current tutor*. Use a neutral “This item is unavailable” page; never suggest a user ask another tutor for access.
- `422` is field/business validation. Keep entered content and point to the relevant fields where the response identifies them.
- `409` is a real workflow conflict: duplicate lesson note, existing payment for a lesson, missing AI prerequisite, or invalid payment transition. It needs actionable, contextual copy rather than a generic failure toast.

### Empty states

Design intentional empty states for:

| Empty condition | Recommended action |
| --- | --- |
| No students | Add first student |
| No Active students | Reactivate a student or add one before scheduling |
| No lessons | Schedule lesson |
| No lessons today | Schedule lesson / view all lessons |
| Lesson with no record | Create lesson record |
| Note with no saved summary | Save raw notes, then generate summary |
| No payments | Create payment from a lesson |
| No pending payments | Reinforce that outstanding balance is zero |
| No analytics data for a month | Keep zero-valued chart axes/data and state there is no activity |

### Loading and saving

- Use page/skeleton loading for list and analytics views; maintain predictable row/chart geometry.
- Disable only the relevant save/generate action while a request is running. Do not block the tutor from reading other saved content.
- Separate saved from unsaved content in the lesson record. Navigating away with unsaved raw notes or AI drafts should warn the tutor.
- Preserve form input on `422`, network failure, and AI failure.

### Responsive and accessible design baseline

- Design desktop tables with a mobile card/list alternative; avoid horizontally clipped financial or schedule data.
- Do not rely on color alone for lesson/payment statuses. Pair color with labels/icons/patterns.
- Use visible focus states, full keyboard support for forms, modals, menus, tabs, filters, and repeatable AI-summary bullets.
- Connect every input to an explicit label and an error message. Announce save/generate success and failure to assistive technology.
- Use readable data-density modes: roomy operational cards on mobile; dense but scannable tables on larger screens.
- Ensure monetary amounts, status chips, date/time, and primary actions remain clear at 200% zoom.

---

## 5. Exact MVP scope: design now vs. leave for a later product decision

| Design as working MVP | Do not design as working MVP yet |
| --- | --- |
| Register, sign in, client-side sign out | Password reset, email verification, profile editing |
| Student create/edit/archive/reactivate | Permanent student delete, bulk student actions |
| One-off lesson create/edit/status/delete | Recurrence, availability/conflict checking, reminders, external calendar sync |
| One lesson record per lesson | Multiple note entries, note deletion, attachments/media |
| AI summary and feedback as reviewable drafts | Auto-save AI results, direct parent delivery, chat interface, AI history/log viewer |
| One payment per lesson, mark paid, cancel pending | Refunds, payment restoration, invoices, batch billing, online payment collection |
| Dashboard and monthly read-only analytics | Custom date ranges, year-over-year comparison, exports |
| TWD display and Taipei reporting time | Currency switcher, tutor timezone setting |

---

## 6. Handoff checklist for Figma and implementation

Before handoff, include each of the following states in the design file:

- Sign-in, registration, validation, invalid credentials, and expired-session state.
- Student directory: populated, filtered, no results, empty, archived student, and archive confirmation.
- Student form: default, validation, edit, and archived/reactivation state.
- Lessons: list/calendar presentation, date/status filters, create, edit with read-only location/remark/student, each of four status chips, and permanent delete confirmation.
- Lesson record: no record, raw-note editor, generating summary, unsaved summary draft, saved summary, unsaved feedback draft, saved feedback, AI prerequisite/error/unavailable states.
- Payments: list, filters, empty, create pending payment, mark-paid modal with paid datetime, each of four statuses, cancel confirmation, and invalid-transition state.
- Dashboard: zero, normal, and load/error states.
- Analytics: month picker, populated/zero series, all status breakdowns, and loading/error states.
- Desktop and mobile variants, keyboard focus, error text, loading indicators, and destructive confirmation behavior.

## 7. Backend-source reference

This brief reflects the current API and domain contracts in:

- `backend/app/models.py`
- `backend/app/api/v1/`
- `backend/app/schemas/`
- `backend/app/services/`
- `docs/api-design.md`

If a Figma concept needs any item marked “not supported,” treat it as a product/API backlog item rather than a visual-only addition.
