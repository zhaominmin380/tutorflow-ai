import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, createTutorApi, type AuthResult } from './api'

const session: AuthResult = {
  user: { id: 7, name: 'Tutor', email: 'tutor@example.com', created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z' },
  csrf_token: 'session-bound-csrf', expires_at: '2026-10-31T00:00:00Z',
}
const success = (data: unknown) => new Response(JSON.stringify({ success: true, data }), { status: 200 })

describe('Cookie session API', () => {
  afterEach(() => { vi.unstubAllGlobals() })

  it('restores cookies and sends the restored CSRF token only with changes', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(success(session)).mockResolvedValueOnce(success({})).mockResolvedValueOnce(success({}))
    vi.stubGlobal('fetch', fetch)
    const api = createTutorApi()
    expect(await api.getSession()).toEqual(session)
    await api.listStudents()
    await api.createStudent({ name: 'Student', school: 'School', grade: 'G7', subject: 'Math' })
    expect(fetch).toHaveBeenNthCalledWith(1, '/api/v1/auth/session', expect.objectContaining({ credentials: 'same-origin', cache: 'no-store', headers: { 'X-TutorFlow-Request': '1' } }))
    const readHeaders = fetch.mock.calls[1][1].headers
    expect(readHeaders).not.toHaveProperty('X-CSRF-Token')
    expect(readHeaders).not.toHaveProperty('Authorization')
    expect(fetch.mock.calls[2][1].headers['X-CSRF-Token']).toBe(session.csrf_token)
  })

  it('uses browser login and registration rather than JavaScript-held bearer credentials', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(success(session)).mockResolvedValueOnce(success(session))
    vi.stubGlobal('fetch', fetch)
    const api = createTutorApi()
    const credentials = { email: 'tutor@example.com', password: 'password123', remember_me: true }
    await api.login(credentials)
    await api.register({ ...credentials, name: 'Tutor' })
    expect(fetch.mock.calls[0][0]).toBe('/api/v1/auth/session')
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual(credentials)
    expect(fetch.mock.calls[1][0]).toBe('/api/v1/auth/session/register')
    expect(fetch.mock.calls[1][1].headers).not.toHaveProperty('Authorization')
  })

  it('sends CSRF during logout and discards it only after server revocation succeeds', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(success(session))
      .mockRejectedValueOnce(new TypeError('offline'))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(success({}))
    vi.stubGlobal('fetch', fetch)
    const api = createTutorApi()
    await api.getSession()
    await expect(api.logout()).rejects.toThrow('offline')
    await api.logout()
    expect(fetch.mock.calls[1][1].headers['X-CSRF-Token']).toBe(session.csrf_token)
    expect(fetch.mock.calls[2][1].headers['X-CSRF-Token']).toBe(session.csrf_token)
    expect(fetch.mock.calls[2][1].method).toBe('DELETE')
    await api.createStudent({ name: 'Student', school: 'School', grade: 'G7', subject: 'Math' })
    expect(fetch.mock.calls[3][1].headers).not.toHaveProperty('X-CSRF-Token')
  })

  it('surfaces a server-expired session as unauthorized for the app to handle', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: false, message: 'Request failed.' }), { status: 401 })))
    await expect(createTutorApi().getSession()).rejects.toBeInstanceOf(ApiError)
  })
})
