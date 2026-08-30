import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, type Lesson, type LessonNote, type Paginated, type Student, type TutorApi } from './api'
import App from './App'

const tutor = { id: 7, email: 'tutor@example.com', name: '許雅涵', created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
const authResult = { access_token: 'session-token', token_type: 'bearer', user: tutor }
const student: Student = { id: 11, user_id: 7, name: '陳柏睿', school: '建國中學', grade: '高二', subject: '物理', hourly_rate: null, is_active: true, note: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
const lesson: Lesson = { id: 31, student_id: 11, start_time: '2026-08-30T06:00:00Z', duration_minutes: 60, status: 'completed', location: '大安區', remark: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }

function paged<T>(items: T[]): Paginated<T> { return { items, pagination: { page: 1, page_size: 20, total: items.length, total_pages: 1 } } }
function createApi(overrides: Partial<TutorApi> = {}): TutorApi { return { register: vi.fn(), login: vi.fn(), getDashboard: vi.fn(), listStudents: vi.fn(), getStudent: vi.fn(), createStudent: vi.fn(), updateStudent: vi.fn(), archiveStudent: vi.fn(), listLessons: vi.fn(), getLesson: vi.fn(), createLesson: vi.fn(), updateLesson: vi.fn(), getLessonNote: vi.fn(), createLessonNote: vi.fn(), updateLessonNote: vi.fn(), generateSummary: vi.fn(), generateFeedback: vi.fn(), ...overrides } }
function setSession() { window.sessionStorage.setItem('tutorflow.session', JSON.stringify({ accessToken: authResult.access_token, user: tutor })) }

describe('TutorFlow application', () => {
  beforeEach(() => { window.sessionStorage.clear(); window.history.pushState({}, '', '/') })
  afterEach(() => { cleanup(); vi.restoreAllMocks() })

  it('shows sign in before a Tutor has a session', () => {
    render(<App api={createApi()} />)
    expect(screen.getByRole('heading', { name: '登入 TutorFlow' })).toBeVisible()
    expect(screen.getByRole('button', { name: '登入' })).toBeVisible()
    expect(screen.getByRole('tab', { name: '建立帳號' })).toBeVisible()
  })

  it('starts a session and takes the Tutor to the first-time Today workspace', async () => {
    const user = userEvent.setup()
    const api = createApi({ login: vi.fn().mockResolvedValue(authResult), getDashboard: vi.fn().mockResolvedValue({ date: '2026-08-30', month: '2026-08', today_lessons_count: 0, active_students_count: 0 }), listLessons: vi.fn().mockResolvedValue(paged([])), listStudents: vi.fn().mockResolvedValue(paged([])) })
    render(<App api={api} />)
    await user.type(screen.getByLabelText('電子信箱'), tutor.email)
    await user.type(screen.getByLabelText('密碼'), 'password123')
    await user.click(screen.getByRole('button', { name: '登入' }))
    expect(await screen.findByRole('heading', { name: '今日' })).toBeVisible()
    expect(screen.getByRole('heading', { name: '先建立第一位學生' })).toBeVisible()
    expect(api.login).toHaveBeenCalledWith({ email: tutor.email, password: 'password123' })
    expect(window.sessionStorage.getItem('tutorflow.session')).toContain('session-token')
  })

  it('creates a Student from the directory and sends the Tutor-entered details to the shared API seam', async () => {
    setSession(); window.history.pushState({}, '', '/students')
    const user = userEvent.setup()
    const api = createApi({ listStudents: vi.fn().mockResolvedValue(paged([])), createStudent: vi.fn().mockResolvedValue(student) })
    render(<App api={api} />)
    await screen.findByRole('heading', { name: '學生' })
    await user.click(screen.getByRole('button', { name: '新增學生' }))
    await user.type(screen.getByLabelText('姓名'), student.name)
    await user.type(screen.getByLabelText('學校'), student.school ?? '')
    await user.type(screen.getByLabelText('年級'), student.grade ?? '')
    await user.type(screen.getByLabelText('科目'), student.subject ?? '')
    await user.click(screen.getByRole('button', { name: '儲存學生' }))
    await waitFor(() => expect(api.createStudent).toHaveBeenCalledWith({ name: '陳柏睿', school: '建國中學', grade: '高二', subject: '物理', hourly_rate: undefined, note: undefined }))
  })

  it('keeps entered Student details and names the invalid field after a 422 response', async () => {
    setSession(); window.history.pushState({}, '', '/students')
    const user = userEvent.setup()
    const api = createApi({ listStudents: vi.fn().mockResolvedValue(paged([])), createStudent: vi.fn().mockRejectedValue(new ApiError(422, 'invalid', [{ msg: 'required', loc: ['body', 'name'] }] as never)) })
    render(<App api={api} />)
    await screen.findByRole('heading', { name: '學生' })
    await user.click(screen.getByRole('button', { name: '新增學生' }))
    await user.type(screen.getByLabelText('姓名'), student.name)
    await user.type(screen.getByLabelText('學校'), student.school ?? '')
    await user.type(screen.getByLabelText('年級'), student.grade ?? '')
    await user.type(screen.getByLabelText('科目'), student.subject ?? '')
    await user.click(screen.getByRole('button', { name: '儲存學生' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('請檢查：姓名')
    expect(screen.getByLabelText('姓名')).toHaveValue(student.name)
  })

  it('keeps raw notes autosaved while AI content remains an explicit Tutor save', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const newNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '開始記錄', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockRejectedValue(new ApiError(404, 'not found')), createLessonNote: vi.fn().mockResolvedValue(newNote), updateLessonNote: vi.fn().mockImplementation((_lessonId: number, input: Partial<LessonNote>) => Promise.resolve({ ...newNote, ...input })) })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '開始課堂紀錄' }))
    await user.type(await screen.findByLabelText('原始筆記'), '今天完成二次函數練習。')
    await waitFor(() => expect(api.updateLessonNote).toHaveBeenCalledWith(31, { raw_note: '今天完成二次函數練習。' }), { timeout: 1600 })
    await user.click(screen.getByRole('button', { name: '自行撰寫' }))
    await user.type(screen.getByLabelText('摘要概覽'), '完成二次函數的基礎練習。')
    await user.click(screen.getByRole('button', { name: '儲存摘要' }))
    await waitFor(() => expect(api.updateLessonNote).toHaveBeenCalledWith(31, expect.objectContaining({ ai_summary: expect.objectContaining({ overview: '完成二次函數的基礎練習。' }) })))
    await user.click(screen.getByRole('button', { name: '自行撰寫' }))
    expect(await screen.findByLabelText('家長回饋')).toBeVisible()
  })

  it('clears the session and returns to sign in when the API reports unauthorized', async () => {
    setSession()
    const api = createApi({ getDashboard: vi.fn().mockRejectedValue(new ApiError(401, 'expired')) })
    render(<App api={api} />)
    expect(await screen.findByRole('heading', { name: '登入 TutorFlow' })).toBeVisible()
    expect(window.sessionStorage.getItem('tutorflow.session')).toBeNull()
  })
})
