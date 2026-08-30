export type LessonStatus = 'scheduled' | 'completed' | 'cancelled' | 'no_show'

export interface Tutor {
  id: number
  email: string
  name: string
  created_at: string
  updated_at: string
}

export interface AuthResult {
  access_token: string
  token_type: string
  user: Tutor
}

export interface Student {
  id: number
  user_id: number
  name: string
  school: string | null
  grade: string | null
  subject: string | null
  hourly_rate: number | null
  is_active: boolean
  note: string | null
  created_at: string
  updated_at: string
}

export interface Lesson {
  id: number
  student_id: number
  start_time: string
  duration_minutes: number
  status: LessonStatus
  location: string | null
  remark: string | null
  created_at: string
  updated_at: string
}

export interface LessonSummary {
  overview: string
  learning_progress: string[]
  strengths: string[]
  difficulties: string[]
  next_steps: string[]
}

export interface LessonNote {
  id: number
  lesson_id: number
  raw_note: string | null
  ai_summary: LessonSummary | null
  teacher_note: string | null
  parent_feedback: string | null
  created_at: string
  updated_at: string
}

export interface DashboardOverview {
  date: string
  month: string
  today_lessons_count: number
  active_students_count: number
}

export interface Paginated<T> {
  items: T[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

export interface StudentInput {
  name: string
  school: string
  grade: string
  subject: string
  hourly_rate?: number
  note?: string
  is_active?: boolean
}

export interface LessonInput {
  student_id: number
  start_time: string
  duration_minutes: number
  status?: LessonStatus
  location?: string
  remark?: string
}

export interface StudentQuery {
  page?: number
  page_size?: number
  search?: string
  grade?: string
  subject?: string
  active?: boolean
  sort?: string
}

export interface LessonQuery {
  page?: number
  page_size?: number
  search?: string
  student_id?: number
  status?: LessonStatus
  start_date?: string
  end_date?: string
  sort?: string
}

export interface TutorApi {
  register(input: { name: string; email: string; password: string }): Promise<AuthResult>
  login(input: { email: string; password: string }): Promise<AuthResult>
  getDashboard(): Promise<DashboardOverview>
  listStudents(query?: StudentQuery): Promise<Paginated<Student>>
  getStudent(studentId: number): Promise<Student>
  createStudent(input: StudentInput): Promise<Student>
  updateStudent(studentId: number, input: Partial<StudentInput>): Promise<Student>
  archiveStudent(studentId: number): Promise<void>
  listLessons(query?: LessonQuery): Promise<Paginated<Lesson>>
  getLesson(lessonId: number): Promise<Lesson>
  createLesson(input: LessonInput): Promise<Lesson>
  updateLesson(
    lessonId: number,
    input: Partial<Pick<Lesson, 'start_time' | 'duration_minutes' | 'status'>>,
  ): Promise<Lesson>
  getLessonNote(lessonId: number): Promise<LessonNote>
  createLessonNote(lessonId: number, input: { raw_note: string }): Promise<LessonNote>
  updateLessonNote(
    lessonId: number,
    input: Partial<Pick<LessonNote, 'raw_note' | 'ai_summary' | 'teacher_note' | 'parent_feedback'>>,
  ): Promise<LessonNote>
  generateSummary(lessonId: number): Promise<LessonSummary>
  generateFeedback(lessonId: number): Promise<string>
}

interface ApiEnvelope<T> {
  success: boolean
  message: string
  data: T
}

interface ErrorEnvelope {
  success: false
  message: string
  detail?: string | Array<{ msg?: string }>
}

export class ApiError extends Error {
  readonly status: number
  readonly detail?: ErrorEnvelope['detail']

  constructor(status: number, message: string, detail?: ErrorEnvelope['detail']) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export function isApiError(error: unknown, status?: number): error is ApiError {
  return error instanceof ApiError && (status === undefined || error.status === status)
}

function queryString(values: object): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(values)) {
    if ((typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') && value !== '') {
      query.set(key, String(value))
    }
  }
  const result = query.toString()
  return result ? `?${result}` : ''
}

export function createTutorApi(getToken: () => string | null): TutorApi {
  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const token = getToken()
    const response = await fetch(`/api/v1${path}`, {
      ...init,
      headers: {
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init.headers,
      },
    })

    if (response.status === 204) return undefined as T

    const body = (await response.json()) as ApiEnvelope<T> | ErrorEnvelope
    if (!response.ok) {
      const error = body as ErrorEnvelope
      throw new ApiError(response.status, error.message || '請稍後再試。', error.detail)
    }
    return (body as ApiEnvelope<T>).data
  }

  const json = (body: object): RequestInit => ({ method: 'POST', body: JSON.stringify(body) })
  const patch = (body: object): RequestInit => ({ method: 'PATCH', body: JSON.stringify(body) })

  return {
    register: (input) => request<AuthResult>('/auth/register', json(input)),
    login: (input) => request<AuthResult>('/auth/login', json(input)),
    getDashboard: () => request<DashboardOverview>('/dashboard'),
    listStudents: (input = {}) => request<Paginated<Student>>(`/students${queryString(input)}`),
    getStudent: (studentId) => request<Student>(`/students/${studentId}`),
    createStudent: (input) => request<Student>('/students', json(input)),
    updateStudent: (studentId, input) => request<Student>(`/students/${studentId}`, patch(input)),
    archiveStudent: (studentId) => request<void>(`/students/${studentId}`, { method: 'DELETE' }),
    listLessons: (input = {}) => request<Paginated<Lesson>>(`/lessons${queryString(input)}`),
    getLesson: (lessonId) => request<Lesson>(`/lessons/${lessonId}`),
    createLesson: (input) => request<Lesson>('/lessons', json(input)),
    updateLesson: (lessonId, input) => request<Lesson>(`/lessons/${lessonId}`, patch(input)),
    getLessonNote: (lessonId) => request<LessonNote>(`/lessons/${lessonId}/note`),
    createLessonNote: (lessonId, input) => request<LessonNote>(`/lessons/${lessonId}/note`, json(input)),
    updateLessonNote: (lessonId, input) => request<LessonNote>(`/lessons/${lessonId}/note`, patch(input)),
    generateSummary: async (lessonId) => {
      const result = await request<{ ai_summary: LessonSummary }>('/ai/summary', json({ lesson_id: lessonId }))
      return result.ai_summary
    },
    generateFeedback: async (lessonId) => {
      const result = await request<{ parent_feedback: string }>('/ai/feedback', json({ lesson_id: lessonId }))
      return result.parent_feedback
    },
  }
}
