# TutorFlow AI

TutorFlow AI is a private work workspace for an individual tutor. Its frontend is organised around completing the day’s teaching work with minimal interaction overhead.

## Language

**Tutor**:
The authenticated individual who owns and manages their students, lessons, records, and AI drafts.
_Avoid_: User, administrator, staff member

**Teaching loop**:
The tutor’s core work sequence: maintain a student, schedule a lesson, record what happened, and refine AI-assisted communication.
_Avoid_: Workflow, CRM process

**Today-first workspace**:
The product orientation in which the tutor begins with today’s actionable lessons and can continue the next teaching task from there. It does not make finance management the home-screen task.
_Avoid_: Analytics-first dashboard, student-directory-first home

**Actionable dashboard**:
The today-first home screen made of Today’s agenda with two quiet context cards: today’s lesson count and active students.
_Avoid_: Analytics dashboard, finance dashboard

**Primary action**:
The one prominent action on a page that advances the tutor’s most likely next step in the teaching loop.
_Avoid_: Action grid, multi-action toolbar

**Lesson record**:
The single persistent record for a lesson, containing raw notes, a saved AI summary, teacher additions, and parent feedback.
_Avoid_: Chat, lesson journal entry, report collection

**AI draft**:
Generated summary or parent-feedback content that remains editable and is not part of a lesson record until the tutor saves it explicitly.
_Avoid_: AI result, sent feedback, automatic note

**Complete & write record**:
The end-of-lesson action that marks a lesson as completed and takes the tutor directly to its lesson record.
_Avoid_: Separate completion and note-taking tasks

**Lesson summary**:
The structured AI-assisted account of a lesson’s overview, learning progress, strengths, difficulties, and next steps.
_Avoid_: Generic AI text, chatbot response

**Parent feedback**:
The AI-assisted, tutor-reviewed message derived from a saved lesson summary for the tutor to copy and share with a parent.
_Avoid_: Sent message, parent portal notification

**Lesson planning view**:
Either the chronological agenda or calendar presentation of the same set of lessons; the tutor switches between the two views without changing the underlying lesson data.
_Avoid_: Separate agenda and calendar features

**Agenda**:
The default chronological lesson planning view, grouped by date and centred on the tutor’s immediate work.
_Avoid_: Timeline, activity feed

**Weekly agenda**:
The current-week Agenda presentation, grouped by day and navigated with previous and next week controls.
_Avoid_: Endless upcoming list, rolling-seven-day list

**Month calendar**:
The switchable month-grid presentation of the same lesson data shown in Agenda.
_Avoid_: Week calendar, day calendar

**Lesson status exception**:
A cancellation or no-show recorded from a secondary status menu in lesson detail, rather than a prominent action in the planning views.
_Avoid_: Quick-cancel button, deletion

**Scheduled by default**:
The default status of a newly created lesson, while still allowing a tutor to set another status for a historical lesson.
_Avoid_: Required status choice, scheduled-only creation

**History-preserving lesson management**:
The first frontend’s use of lesson statuses, especially Cancelled and No-show, rather than exposing permanent lesson deletion.
_Avoid_: Delete lesson action, destructive schedule cleanup

**Schedule-lesson sheet**:
The shared in-context lesson creation form opened from Agenda or Calendar; it is a slide-over on larger screens and full-screen on mobile.
_Avoid_: Separate agenda/calendar forms, new-lesson route

**Active-student selector**:
The searchable student field in the schedule-lesson sheet, containing only active students. A tutor creates a student before scheduling when the selector has no suitable choice.
_Avoid_: Inline student creation, temporary student

**Guided lesson record**:
The vertical lesson-record flow of raw notes, AI lesson summary, and optional parent feedback. Each step makes its saved and draft status visible.
_Avoid_: Tabbed record, free-form report

**Autosaved raw notes**:
The non-empty raw lesson notes saved in the background after the tutor explicitly starts a lesson record, making them available as input for AI summary generation without a raw-note Save action.
_Avoid_: Automatic AI trigger, draft-only raw note, explicit raw-note Save button

**Start lesson record**:
The tutor’s deliberate action that creates a lesson’s one persistent record and enables background saving of its raw notes.
_Avoid_: Implicit first-keystroke record creation, repeated note creation

**Optional parent feedback**:
The tutor-initiated AI draft generated after a saved lesson summary; it is not a required completion step and is copied rather than sent by TutorFlow.
_Avoid_: Automatic feedback, required parent message

**Manual AI fallback**:
The tutor’s ability to create and save a lesson summary or parent feedback without successful AI generation.
_Avoid_: AI-only lesson record, blocked documentation

**Draft-exit safeguard**:
The decision dialog shown when a tutor leaves an unsaved AI draft, offering Save draft, Discard, or Keep editing.
_Avoid_: Automatic draft persistence, silent draft loss

**Deferred area**:
A completed backend domain that is intentionally excluded from the first frontend release and absent from its navigation.
_Avoid_: Coming soon page, disabled navigation item

**First-time dashboard**:
The empty actionable dashboard shown to a new tutor, which directs them to create their first student instead of using a separate onboarding wizard.
_Avoid_: Forced onboarding flow, direct-to-directory landing

**Student detail sheet**:
A compact operational view opened from the student directory, containing student information, Edit, Archive, and a link to that student’s lessons.
_Avoid_: Student profile page, inline table editor

**Lesson detail sheet**:
The in-context operational view opened over Agenda or Calendar for one lesson. It contains short lesson actions; the guided lesson record opens as a focused page.
_Avoid_: Dedicated lesson page, inline agenda expansion

**Primary navigation**:
The three product areas: Today, Students, and Lessons. It is shown as persistent desktop navigation and bottom navigation on mobile.
_Avoid_: Navigation for every entity, hamburger-only navigation

**Taiwan scheduling format**:
The use of Taiwan-style dates and 24-hour time for tutor-facing lesson schedules.
_Avoid_: 12-hour time, browser-dependent date format

**Visual tone**:
A calm, warm, highly readable operational workspace for sensitive teaching work. Exact visual tokens are defined in DESIGN.md.
_Avoid_: Playful classroom app, dense dark data dashboard

**Product language**:
Traditional Chinese is the primary language for TutorFlow’s interface, with English only where it is familiar and useful.
_Avoid_: Bilingual interface, English-first interface

**Progressive scheduling fields**:
The schedule-lesson sheet initially shows student, date/time, duration, and status; optional location and remark fields appear under More details.
_Avoid_: All-fields scheduling form, omitted context fields

**Duration presets**:
Quick lesson-duration choices for common lengths, with a custom-minute input for all other positive durations.
_Avoid_: Free-form duration text, preset-only duration

**Archive confirmation**:
The deliberate confirmation from Student detail before a student becomes archived and unavailable for newly scheduled lessons.
_Avoid_: Instant archive toggle, permanent deletion

**Progressive filters**:
Search and key date/view controls stay visible, while secondary student and lesson filters live in one Filter panel.
_Avoid_: Always-visible filter grid, filter-free lists

**Load more**:
The explicit list control that appends the next backend page of students or lessons after the initial twenty results.
_Avoid_: Numbered pagination, infinite scroll

**Light-only theme**:
The first frontend’s high-contrast light presentation of TutorFlow’s warm-neutral visual tone.
_Avoid_: Dark-mode toggle, OS-driven theme variations

**React design scaffold**:
The first implementation of the designed interface as reusable React components populated with realistic fixture data before those fixtures are replaced by backend API data.
_Avoid_: Static HTML prototype, API-first visual construction

**Pattern-defining pages**:
The Dashboard, Students, and Lesson Record pages that establish most of TutorFlow’s reusable first-release UI patterns.
_Avoid_: Full visual design of every route, future-domain design

**State-complete design**:
A design pass that includes the important empty, loading, validation, autosave, unsaved-AI-draft, and AI-error states alongside normal populated views.
_Avoid_: Happy-path-only design
