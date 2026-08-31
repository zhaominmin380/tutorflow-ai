import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, type Lesson, type LessonNote, type LessonSummary, type Paginated, type Student, type TutorApi } from './api'
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
    expect(screen.getByRole('heading', { name: '今天也準備好了。' })).toBeVisible()
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

  it('returns the Tutor to sign in without rendering the logout click event', async () => {
    setSession()
    const user = userEvent.setup()
    const api = createApi({ getDashboard: vi.fn().mockResolvedValue({ date: '2026-08-30', month: '2026-08', today_lessons_count: 0, active_students_count: 0 }), listLessons: vi.fn().mockResolvedValue(paged([])), listStudents: vi.fn().mockResolvedValue(paged([])) })
    render(<App api={api} />)

    await user.click(await screen.findByRole('button', { name: '登出' }))

    expect(await screen.findByRole('heading', { name: '今天也準備好了。' })).toBeVisible()
    expect(window.sessionStorage.getItem('tutorflow.session')).toBeNull()
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

  it('replaces Student detail with the editor as soon as the Tutor clicks Edit', async () => {
    setSession(); window.history.pushState({}, '', '/students')
    const user = userEvent.setup()
    const api = createApi({ listStudents: vi.fn().mockResolvedValue(paged([student])) })
    render(<App api={api} />)

    await user.click(await screen.findByRole('button', { name: /陳柏睿/ }))
    const detail = await screen.findByRole('dialog', { name: '陳柏睿' })
    await user.click(within(detail).getByRole('button', { name: '編輯學生' }))

    expect(screen.getAllByRole('dialog')).toHaveLength(1)
    expect(screen.getByRole('dialog', { name: '編輯學生' })).toBeVisible()
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

  it('switches the same Lesson planning data between the Weekly agenda and Month calendar', async () => {
    setSession(); window.history.pushState({}, '', '/lessons')
    const user = userEvent.setup()
    const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Taipei', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())
    const today = `${parts.find((part) => part.type === 'year')?.value}-${parts.find((part) => part.type === 'month')?.value}-${parts.find((part) => part.type === 'day')?.value}`
    const plannedLesson: Lesson = { ...lesson, status: 'scheduled', start_time: `${today}T06:00:00Z` }
    const api = createApi({ listLessons: vi.fn().mockResolvedValue(paged([plannedLesson])), listStudents: vi.fn().mockResolvedValue(paged([student])) })
    render(<App api={api} />)
    expect(await screen.findByRole('button', { name: /14:00.*陳柏睿/ })).toBeVisible()
    await user.click(screen.getByRole('button', { name: '月曆' }))
    await waitFor(() => expect(api.listLessons).toHaveBeenCalledTimes(2))
    const calendarLesson = await screen.findByRole('button', { name: '14:00 陳柏睿' })
    await user.click(calendarLesson)
    const detailSheet = await screen.findByRole('dialog', { name: '陳柏睿' })
    expect(within(detailSheet).getByText('物理')).toBeVisible()
    await user.click(within(detailSheet).getByRole('button', { name: '關閉' }))
    expect(screen.getByRole('button', { name: '14:00 陳柏睿' })).toBeVisible()
  })

  it('keeps cancelled and No-show as secondary Lesson status exceptions without delete', async () => {
    setSession(); window.history.pushState({}, '', '/lessons')
    const user = userEvent.setup()
    const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Taipei', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())
    const today = `${parts.find((part) => part.type === 'year')?.value}-${parts.find((part) => part.type === 'month')?.value}-${parts.find((part) => part.type === 'day')?.value}`
    const plannedLesson: Lesson = { ...lesson, status: 'scheduled', start_time: `${today}T06:00:00Z` }
    const cancelledLesson: Lesson = { ...plannedLesson, status: 'cancelled' }
    const api = createApi({ listLessons: vi.fn().mockResolvedValue(paged([plannedLesson])), listStudents: vi.fn().mockResolvedValue(paged([student])), updateLesson: vi.fn().mockResolvedValue(cancelledLesson) })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: /14:00.*陳柏睿/ }))
    expect(screen.getByText('狀態例外')).toBeVisible()
    expect(screen.getByRole('button', { name: '標記為已取消' })).toBeVisible()
    expect(screen.getByRole('button', { name: '標記為未到' })).toBeVisible()
    expect(screen.queryByRole('button', { name: /刪除/ })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '標記為已取消' }))
    await waitFor(() => expect(api.updateLesson).toHaveBeenCalledWith(31, { status: 'cancelled' }))
    expect(screen.getByText('已取消')).toBeVisible()
  })

  it('lets the Tutor make short scheduling edits from Lesson detail while Location and Remark remain read-only', async () => {
    setSession(); window.history.pushState({}, '', '/lessons')
    const user = userEvent.setup()
    const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Taipei', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())
    const today = `${parts.find((part) => part.type === 'year')?.value}-${parts.find((part) => part.type === 'month')?.value}-${parts.find((part) => part.type === 'day')?.value}`
    const plannedLesson: Lesson = { ...lesson, status: 'scheduled', start_time: `${today}T06:00:00Z`, remark: '帶計算機' }
    const updatedLesson: Lesson = { ...plannedLesson, start_time: `${today}T15:30:00+08:00`, duration_minutes: 90 }
    const api = createApi({ listLessons: vi.fn().mockResolvedValueOnce(paged([plannedLesson])).mockResolvedValue(paged([updatedLesson])), listStudents: vi.fn().mockResolvedValue(paged([student])), updateLesson: vi.fn().mockResolvedValue(updatedLesson) })
    render(<App api={api} />)

    await user.click(await screen.findByRole('button', { name: /14:00.*陳柏睿/ }))
    const detail = await screen.findByRole('dialog', { name: '陳柏睿' })
    expect(within(detail).getByText('大安區')).toBeVisible()
    expect(within(detail).getByText('帶計算機')).toBeVisible()
    await user.click(within(detail).getByRole('button', { name: '編輯課程' }))

    const editor = await screen.findByRole('dialog', { name: '編輯課程' })
    expect(within(editor).queryByLabelText('地點')).not.toBeInTheDocument()
    expect(within(editor).queryByLabelText('備註')).not.toBeInTheDocument()
    fireEvent.change(within(editor).getByLabelText('日期與時間'), { target: { value: `${today}T15:30` } })
    fireEvent.change(within(editor).getByLabelText('自訂課程長度'), { target: { value: '90' } })
    await user.click(within(editor).getByRole('button', { name: '儲存變更' }))

    await waitFor(() => expect(api.updateLesson).toHaveBeenCalledWith(31, { start_time: `${today}T15:30:00+08:00`, duration_minutes: 90 }))
    expect(screen.queryByRole('dialog', { name: '編輯課程' })).not.toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /15:30.*陳柏睿/ })).toBeVisible()
  })

  it('shows the defined Today loading state while the Tutor data is pending', async () => {
    setSession()
    const pending = () => new Promise<never>(() => {})
    const api = createApi({ getDashboard: vi.fn(pending), listLessons: vi.fn(pending), listStudents: vi.fn(pending) })
    render(<App api={api} />)
    expect(await screen.findByText('載入中…')).toBeVisible()
  })

  it('supports the release Teaching loop from sign in through an explicitly saved AI summary', async () => {
    const user = userEvent.setup()
    const createdStudent = { ...student, name: '林語晴' }
    let hasCreatedStudent = false
    let scheduledLesson: Lesson | null = null
    let lessonRecord: LessonNote = { id: 1, lesson_id: 31, raw_note: '開始記錄', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const generatedSummary = { overview: '已完成函數練習。', learning_progress: ['能解一元二次方程式'], strengths: [], difficulties: [], next_steps: [] }
    const api = createApi({
      login: vi.fn().mockResolvedValue(authResult),
      getDashboard: vi.fn().mockResolvedValue({ date: '2026-08-30', month: '2026-08', today_lessons_count: 0, active_students_count: 0 }),
      listStudents: vi.fn().mockImplementation(() => Promise.resolve(paged(hasCreatedStudent ? [createdStudent] : []))),
      createStudent: vi.fn().mockImplementation(() => { hasCreatedStudent = true; return Promise.resolve(createdStudent) }),
      listLessons: vi.fn().mockImplementation(() => Promise.resolve(paged(scheduledLesson ? [scheduledLesson] : []))),
      createLesson: vi.fn().mockImplementation((input) => { scheduledLesson = { ...lesson, student_id: input.student_id, start_time: input.start_time, duration_minutes: input.duration_minutes, status: input.status ?? 'scheduled', location: input.location ?? null, remark: input.remark ?? null }; return Promise.resolve(scheduledLesson) }),
      updateLesson: vi.fn().mockImplementation((_lessonId, input) => { scheduledLesson = { ...(scheduledLesson ?? lesson), ...input }; return Promise.resolve(scheduledLesson) }),
      getLesson: vi.fn().mockImplementation(() => Promise.resolve(scheduledLesson ?? lesson)),
      getStudent: vi.fn().mockResolvedValue(createdStudent),
      getLessonNote: vi.fn().mockRejectedValue(new ApiError(404, 'not found')),
      createLessonNote: vi.fn().mockImplementation((_lessonId, input) => { lessonRecord = { ...lessonRecord, raw_note: input.raw_note }; return Promise.resolve(lessonRecord) }),
      updateLessonNote: vi.fn().mockImplementation((_lessonId, input) => { lessonRecord = { ...lessonRecord, ...input }; return Promise.resolve(lessonRecord) }),
      generateSummary: vi.fn().mockResolvedValue(generatedSummary),
    })
    render(<App api={api} />)

    await user.type(screen.getByLabelText('電子信箱'), tutor.email)
    await user.type(screen.getByLabelText('密碼'), 'password123')
    await user.click(screen.getByRole('button', { name: '登入' }))
    expect(await screen.findByRole('heading', { name: '今日' })).toBeVisible()

    await user.click(screen.getAllByRole('link', { name: '學生' })[0])
    await user.click(await screen.findByRole('button', { name: '新增學生' }))
    const studentSheet = await screen.findByRole('dialog', { name: '新增學生' })
    await user.type(within(studentSheet).getByLabelText('姓名'), createdStudent.name)
    await user.type(within(studentSheet).getByLabelText('學校'), createdStudent.school ?? '')
    await user.type(within(studentSheet).getByLabelText('年級'), createdStudent.grade ?? '')
    await user.type(within(studentSheet).getByLabelText('科目'), createdStudent.subject ?? '')
    await user.click(within(studentSheet).getByRole('button', { name: '儲存學生' }))
    await waitFor(() => expect(api.createStudent).toHaveBeenCalledTimes(1))

    await user.click(screen.getAllByRole('link', { name: '課程' })[0])
    await user.click(await screen.findByRole('button', { name: '安排課程' }))
    const scheduleSheet = await screen.findByRole('dialog', { name: '安排課程' })
    await user.selectOptions(within(scheduleSheet).getByLabelText('選擇學生'), String(createdStudent.id))
    await user.click(within(scheduleSheet).getByRole('button', { name: '安排課程' }))
    await waitFor(() => expect(api.createLesson).toHaveBeenCalledWith(expect.objectContaining({ student_id: createdStudent.id, status: 'scheduled' })))

    const agendaLesson = await screen.findByRole('button', { name: /林語晴/ })
    await user.click(agendaLesson)
    const detailSheet = await screen.findByRole('dialog', { name: '林語晴' })
    await user.click(within(detailSheet).getByRole('button', { name: '完成並撰寫紀錄' }))
    expect(await screen.findByRole('heading', { name: '林語晴的課堂紀錄' })).toBeVisible()

    await user.click(screen.getByRole('button', { name: '開始課堂紀錄' }))
    await user.type(screen.getByLabelText('原始筆記'), '今天完成函數練習。')
    await waitFor(() => expect(api.updateLessonNote).toHaveBeenCalledWith(31, { raw_note: '今天完成函數練習。' }), { timeout: 1600 })
    await user.click(screen.getByRole('button', { name: '生成 AI 摘要' }))
    expect(await screen.findByText('AI 草稿未儲存')).toBeVisible()
    await user.click(screen.getByRole('button', { name: '儲存摘要' }))
    await waitFor(() => expect(api.updateLessonNote).toHaveBeenCalledWith(31, expect.objectContaining({ ai_summary: generatedSummary })))
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

  it.each([
    [409, '請先儲存原始筆記，再生成 AI 摘要。'],
    [502, 'AI 服務暫時發生問題，尚未產生任何內容。你可以重試或自行撰寫。'],
    [503, 'AI 服務目前無法使用或尚未設定。請稍後重試，或自行撰寫。'],
    [504, 'AI 生成逾時，尚未產生任何內容。請重試或自行撰寫。'],
  ])('offers retry and manual summary paths after AI generation fails with %i', async (status, message) => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), generateSummary: vi.fn().mockRejectedValue(new ApiError(status, 'provider error')) })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '生成 AI 摘要' }))
    expect(await screen.findByText(message)).toBeVisible()
    await user.click(screen.getByRole('button', { name: '重試生成 AI 摘要' }))
    await waitFor(() => expect(api.generateSummary).toHaveBeenCalledTimes(2))
    await user.click(screen.getByRole('button', { name: '自行撰寫摘要' }))
    expect(screen.getByLabelText('摘要概覽')).toBeVisible()
  })

  it('offers retry, manual entry, and copy for parent after a saved Lesson summary', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedSummary = { overview: '已儲存的課堂摘要。', learning_progress: [], strengths: [], difficulties: [], next_steps: [] }
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: savedSummary, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), generateFeedback: vi.fn().mockRejectedValue(new ApiError(504, 'timed out')) })
    render(<App api={api} />)
    expect(await screen.findByText('生成家長回饋時，已儲存的課堂內容會傳送至已設定的 AI 服務。')).toBeVisible()
    await user.click(await screen.findByRole('button', { name: '生成家長回饋' }))
    expect(await screen.findByText('AI 生成逾時，尚未產生任何內容。請重試或自行撰寫。')).toBeVisible()
    await user.click(screen.getByRole('button', { name: '重試生成家長回饋' }))
    await waitFor(() => expect(api.generateFeedback).toHaveBeenCalledTimes(2))
    await user.click(screen.getByRole('button', { name: '自行撰寫家長回饋' }))
    expect(screen.getByLabelText('家長回饋')).toBeVisible()
    expect(screen.getByRole('button', { name: '複製給家長' })).toBeVisible()
  })

  it('asks before replacing a saved Lesson summary', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedSummary = { overview: '原本已儲存的摘要。', learning_progress: [], strengths: [], difficulties: [], next_steps: [] }
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: savedSummary, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), updateLessonNote: vi.fn().mockResolvedValue(savedNote) })
    render(<App api={api} />)
    await user.type(await screen.findByLabelText('摘要概覽'), ' 已更新')
    await user.click(screen.getByRole('button', { name: '儲存摘要' }))
    expect(api.updateLessonNote).not.toHaveBeenCalled()
    expect(await screen.findByRole('heading', { name: '覆寫已儲存的摘要？' })).toBeVisible()
    await user.click(screen.getByRole('button', { name: '覆寫摘要' }))
    await waitFor(() => expect(api.updateLessonNote).toHaveBeenCalledWith(31, expect.objectContaining({ ai_summary: expect.objectContaining({ overview: '原本已儲存的摘要。 已更新' }) })))
  })

  it('saves Teacher additions independently without replacing a saved Lesson summary', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedSummary = { overview: '已儲存的課堂摘要。', learning_progress: [], strengths: [], difficulties: [], next_steps: [] }
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: savedSummary, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), updateLessonNote: vi.fn().mockResolvedValue({ ...savedNote, teacher_note: '下次加強基本觀念。' }) })
    render(<App api={api} />)
    await user.type(await screen.findByLabelText('教師補充（選填）'), '下次加強基本觀念。')
    await user.click(screen.getByRole('button', { name: '儲存教師補充' }))
    await waitFor(() => expect(api.updateLessonNote).toHaveBeenCalledWith(31, { teacher_note: '下次加強基本觀念。' }))
    expect(screen.queryByRole('heading', { name: '覆寫已儲存的摘要？' })).not.toBeInTheDocument()
  })

  it('keeps an AI Lesson summary as an editable draft until the Tutor explicitly saves it', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const generatedSummary = { overview: 'AI 產生的課堂摘要。', learning_progress: ['完成練習'], strengths: [], difficulties: [], next_steps: [] }
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), generateSummary: vi.fn().mockResolvedValue(generatedSummary), updateLessonNote: vi.fn().mockResolvedValue({ ...savedNote, ai_summary: generatedSummary }) })
    render(<App api={api} />)
    expect(await screen.findByText('生成 AI 摘要時，已儲存的課堂內容會傳送至已設定的 AI 服務。')).toBeVisible()
    await user.click(screen.getByRole('button', { name: '生成 AI 摘要' }))
    expect(await screen.findByText('AI 草稿未儲存')).toBeVisible()
    expect(screen.getByLabelText('摘要概覽')).toHaveValue(generatedSummary.overview)
    expect(screen.queryByRole('button', { name: '生成家長回饋' })).not.toBeInTheDocument()
    expect(api.updateLessonNote).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: '儲存摘要' }))
    await waitFor(() => expect(api.updateLessonNote).toHaveBeenCalledWith(31, expect.objectContaining({ ai_summary: generatedSummary })))
    expect(await screen.findByRole('button', { name: '生成家長回饋' })).toBeVisible()
  })

  it('shows an in-place generating state and prevents duplicate AI summary requests', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), generateSummary: vi.fn(() => new Promise<never>(() => {})) })
    render(<App api={api} />)
    const generate = await screen.findByRole('button', { name: '生成 AI 摘要' })
    await user.click(generate)
    expect(screen.getByLabelText('摘要生成中')).toBeVisible()
    expect(generate).toBeDisabled()
    await user.click(generate)
    expect(api.generateSummary).toHaveBeenCalledTimes(1)
  })

  it('keeps a manual Lesson summary when an earlier AI request resolves late', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    let resolveSummary: (value: LessonSummary) => void = () => {}
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), generateSummary: vi.fn(() => new Promise<LessonSummary>((resolve) => { resolveSummary = resolve })) })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '生成 AI 摘要' }))
    await user.click(screen.getByRole('button', { name: '自行撰寫' }))
    await user.type(screen.getByLabelText('摘要概覽'), 'Tutor 手動整理的摘要。')
    await act(async () => { resolveSummary({ overview: '晚到的 AI 摘要。', learning_progress: [], strengths: [], difficulties: [], next_steps: [] }) })
    expect(screen.getByLabelText('摘要概覽')).toHaveValue('Tutor 手動整理的摘要。')
  })

  it('keeps manual Parent feedback when an earlier AI request resolves late', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedSummary = { overview: '已儲存的課堂摘要。', learning_progress: [], strengths: [], difficulties: [], next_steps: [] }
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: savedSummary, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    let resolveFeedback: (value: string) => void = () => {}
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), generateFeedback: vi.fn(() => new Promise<string>((resolve) => { resolveFeedback = resolve })) })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '生成家長回饋' }))
    await user.click(screen.getByRole('button', { name: '自行撰寫' }))
    await user.type(screen.getByLabelText('家長回饋'), 'Tutor 手動整理的家長回饋。')
    await act(async () => { resolveFeedback('晚到的 AI 家長回饋。') })
    expect(screen.getByLabelText('家長回饋')).toHaveValue('Tutor 手動整理的家長回饋。')
  })

  it('safeguards an unsaved AI draft with save, discard, and keep-editing actions', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote) })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '自行撰寫' }))
    await user.type(screen.getByLabelText('摘要概覽'), '尚未儲存的摘要。')
    await user.click(screen.getByRole('button', { name: '返回課程' }))
    expect(await screen.findByRole('heading', { name: '離開未儲存的草稿？' })).toBeVisible()
    expect(screen.getByRole('button', { name: '繼續編輯' })).toBeVisible()
    expect(screen.getByRole('button', { name: '捨棄草稿' })).toBeVisible()
    expect(screen.getByRole('button', { name: '儲存草稿' })).toBeVisible()
  })

  it('warns before the browser closes with an unsaved summary draft', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: null, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote) })
    render(<App api={api} />)
    await user.click(await screen.findByRole('button', { name: '自行撰寫' }))
    await user.type(screen.getByLabelText('摘要概覽'), '尚未儲存的摘要。')
    const event = new Event('beforeunload', { cancelable: true })
    fireEvent(window, event)
    expect(event.defaultPrevented).toBe(true)
  })

  it('keeps the requested exit after confirming a replacement summary save', async () => {
    setSession(); window.history.pushState({}, '', '/lessons/31/record')
    const user = userEvent.setup()
    const savedSummary = { overview: '原本已儲存的摘要。', learning_progress: [], strengths: [], difficulties: [], next_steps: [] }
    const savedNote: LessonNote = { id: 1, lesson_id: 31, raw_note: '學生已完成今天的練習。', ai_summary: savedSummary, teacher_note: null, parent_feedback: null, created_at: '2026-08-30T00:00:00Z', updated_at: '2026-08-30T00:00:00Z' }
    const api = createApi({ getLesson: vi.fn().mockResolvedValue(lesson), getStudent: vi.fn().mockResolvedValue(student), getLessonNote: vi.fn().mockResolvedValue(savedNote), updateLessonNote: vi.fn().mockResolvedValue(savedNote), listLessons: vi.fn().mockResolvedValue(paged([])), listStudents: vi.fn().mockResolvedValue(paged([])) })
    render(<App api={api} />)
    await user.type(await screen.findByLabelText('摘要概覽'), ' 已更新')
    await user.click(screen.getByRole('button', { name: '返回課程' }))
    await user.click(await screen.findByRole('button', { name: '儲存草稿' }))
    expect(await screen.findByRole('heading', { name: '覆寫已儲存的摘要？' })).toBeVisible()
    await user.click(screen.getByRole('button', { name: '覆寫摘要' }))
    await waitFor(() => expect(window.location.pathname).toBe('/lessons'))
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
    expect(await screen.findByRole('heading', { name: '今天也準備好了。' })).toBeVisible()
    await user.type(screen.getByLabelText('電子信箱'), tutor.email)
    await user.type(screen.getByLabelText('密碼'), 'password123')
    await user.click(screen.getByRole('button', { name: '登入' }))
    expect(await screen.findByLabelText('原始筆記')).toHaveValue(rawNote)
  })

  it('clears the session and returns to sign in when the API reports unauthorized', async () => {
    setSession()
    const api = createApi({ getDashboard: vi.fn().mockRejectedValue(new ApiError(401, 'expired')) })
    render(<App api={api} />)
    expect(await screen.findByRole('heading', { name: '今天也準備好了。' })).toBeVisible()
    expect(screen.getByRole('alert')).toHaveTextContent('工作階段已結束，請重新登入。')
    expect(window.sessionStorage.getItem('tutorflow.session')).toBeNull()
  })
})
