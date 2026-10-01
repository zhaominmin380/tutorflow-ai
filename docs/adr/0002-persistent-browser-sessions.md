# Use revocable cookie sessions for the browser

TutorFlow's same-origin React and FastAPI deployment uses server-managed browser
sessions for persistent login. The default session lasts 30 days from sign-in,
without a rolling renewal or an earlier inactivity deadline. A checked-by-default
keep-signed-in option lets the Tutor opt out on shared devices, using an eight-hour
server limit and a non-persistent cookie instead.

Only a random session identifier is placed in an HttpOnly cookie. The database
stores its SHA-256 hash, Tutor ownership, creation time, and absolute expiry.
HTTPS production uses a host-only Secure cookie with SameSite=Strict. Cookie-authenticated
mutations require a session-bound CSRF header. Browser sign-in and registration
require a custom header, and cross-origin credentialed CORS access is not enabled.

On reopening, the frontend restores identity and an in-memory CSRF token from
the server. Authentication credentials are not kept in localStorage or sessionStorage.
An unauthorized response returns to sign-in; connectivity failures offer retry.
Sign-out revokes only the current device session and follows the existing
draft-exit safeguard before leaving a lesson record.

Existing short-lived Bearer JWT endpoints remain available for API clients and
Swagger. PWA installation and offline editing are separate, deferred work.
