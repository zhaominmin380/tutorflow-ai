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

  it('loads another Lesson page only when the Tutor explicitly asks for more', async () => {
    setSession(); window.history.pushState({}, '', '/lessons')
    const user = userEvent.setup()
    const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Taipei', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())
    const today = `${parts.find((part) => part.type === 'year')?.value}-${parts.find((part) => part.type === 'month')?.value}-${parts.find((part) => part.type === 'day')?.value}`
    const firstLesson: Lesson = { ...lesson, start_time: `${today}T14:00:00+08:00` }
    const secondLesson: Lesson = { ...lesson, id: 32, start_time: `${today}T16:00:00+08:00` }
    const api = createApi({
      listLessons: vi.fn().mockImplementation((query) => Promise.resolve(query?.page === 2
        ? { items: [secondLesson], pagination: { page: 2, page_size: 20, total: 2, total_pages: 2 } }
        : { items: [firstLesson], pagination: { page: 1, page_size: 20, total: 2, total_pages: 2 } },
      )),
      listStudents: vi.fn().mockResolvedValue(paged([student])),
    })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '載入更多課程' }))
    await waitFor(() => expect(api.listLessons).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2, page_size: 20 })))
    expect(await screen.findByText('16:00–17:00')).toBeVisible()
    expect(screen.queryByRole('button', { name: '載入更多課程' })).not.toBeInTheDocument()
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

  it('keeps raw notes visible and blocks navigation after autosave fails', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const newNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '開始記錄', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockRejectedValue(new ApiError(404, 'not found')), createLessonNote: vi.fn().mockResolvedValue(newNote), updateLessonNote: vi.fn().mockRejectedValue(new Error('offline')) })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '開始課堂紀錄' }))
    await user.type(await screen.findByLabelText('原始筆記'), '學生今天完成函數複習。')
    expect(await screen.findByText('儲存失敗，請重試')).toBeVisible()
    await user.click(screen.getByRole('button', { name: '返回課程' }))
    expect(await screen.findByRole('heading', { name: '原始筆記尚未儲存' })).toBeVisible()
    expect(screen.getByLabelText('原始筆記')).toHaveValue('學生今天完成函數複習。')
  })

  it('creates a Lesson record only once while the deliberate start request is pending', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockRejectedValue(new ApiError(404, 'not found')), createLessonNote: vi.fn(() => new Promise<LessonNote>(() => {})) })
    render(<App api={api} />)
    const start = await screen.findByRole('button', { name: '開始課堂紀錄' })
    await user.click(start)
    await user.click(start)
    expect(api.createLessonNote).toHaveBeenCalledTimes(1)
    expect(start).toBeDisabled()
  })

  it('restores a raw note after a 401 autosave when the same Tutor signs in again', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const rawNote = '學生今天完成函數複習。'
    const newNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '開始記錄', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({
      login: vi.fn().mockResolvedValue(authResult),
      getLesson: vi.fn().mockResolvedValue(lesson),
      getStudent: vi.fn().mockResolvedValue(student),
      getLessonNote: vi.fn().mockRejectedValueOnce(new ApiError(404, 'not found')).mockResolvedValue(newNote),
      createLessonNote: vi.fn().mockResolvedValue(newNote),
      updateLessonNote: vi.fn().mockRejectedValueOnce(new ApiError(401, 'expired')).mockResolvedValue({ ...newNote, raw_note: rawNote }),
    })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '開始課堂紀錄' }))
    await user.type(await screen.findByLabelText('原始筆記'), rawNote)
    expect(await screen.findByRole('heading', { name: '登入 TutorFlow' })).toBeVisible()
    await user.type(screen.getByLabelText('電子信箱'), tutor.email)
    await user.type(screen.getByLabelText('密碼'), 'password123')
    await user.click(screen.getByRole('button', { name: '登入' }))
    expect(await screen.findByLabelText('原始筆記')).toHaveValue(rawNote)
  })

  it('clears the session and returns to sign in when the API reports unauthorized', async () => {
    setSession()
    const api = createApi({ getDashboard: vi.fn().mockRejectedValue(new ApiError(401, 'expired')) })
    render(<App api={api} />)
    expect(await screen.findByRole('heading', { name: '登入 TutorFlow' })).toBeVisible()
    expect(window.sessionStorage.getItem('tutorflow.session')).toBeNull()
  })
})
