# Authentication Flow

## User states

### Guest

- Has no Users record.
- Has no access token.
- Can browse movie list and detail.
- Is redirected to `/login` before protected frontend actions.
- Cannot create interactions or access personalized recommendations.

### Registered User

A registered user has a Users record with a PBKDF2 password hash. Registered
users are further classified by onboarding state.

### First Login

- `onboarding_completed=false`
- Receives a valid JWT after register or login.
- Is routed to `/onboarding`.
- Can update profile and record interactions.
- Cannot access personalized recommendations.

### Returning User

- `onboarding_completed=true`
- Skips onboarding after login/session restoration.
- Can access profile, interactions, and personalized recommendations.

## Registration and login

```text
Register/Login form
  -> authService
  -> centralized apiClient
  -> FastAPI auth route
  -> AuthService
  -> UsersRepository
  -> password verification/hash
  -> JWT issue
  -> profile + token response
  -> First Login or Returning User route
```

Register creates a UUID `user_id`, a uniquely salted password hash, and an
incomplete onboarding profile. Login accepts username or email and updates
`last_active_at`.

## Password security

- Algorithm: PBKDF2-HMAC-SHA256
- Random salt: 16 bytes per password
- Default work factor: 600,000 iterations
- Comparison: constant-time `hmac.compare_digest`
- Storage format:
  `pbkdf2_sha256$iterations$salt$digest`
- Plaintext passwords never enter a repository or response DTO.

## JWT security

Access tokens use HS256 and contain:

- `sub`: canonical `user_id`
- `jti`: unique token identifier
- `iat`: issued-at timestamp
- `exp`: expiration timestamp
- `iss`: configured issuer
- `aud`: configured frontend audience
- `token_type=access`

The authentication middleware validates signature, type, issuer, audience,
issued-at time, and expiration. Valid claims are attached to `request.state`.
Protected dependencies then resolve the current user from Users.

`JWT_SECRET` is required, must be at least 32 bytes, and must differ by
environment.

## Protected request flow

```text
HTTP request
  -> JWTAuthenticationMiddleware
     -> no token: guest request continues
     -> invalid token: 401
     -> valid token: TokenClaims attached
  -> route dependency
     -> public route: no user required
     -> registered route: resolve Users record
     -> personalized route: require onboarding_completed
  -> route/service
```

## Frontend redirect flow

```text
Guest protected action
  -> useInteractions/useMovieActions denies request
  -> navigate /login

First Login session
  -> profile.user_state=first_login
  -> route guard sends user to /onboarding

Onboarding complete
  -> server updates Users
  -> profile.user_state=returning_user
  -> route guard sends user to /

Returning User session
  -> skips onboarding
  -> may open /profile or personalized recommendations
```

The frontend no longer infers onboarding from browser storage. The Users record
is authoritative across browsers and devices.

## Logout

Logout is stateless:

1. Frontend calls `POST /auth/logout` with the current JWT.
2. Backend confirms the session is authenticated and returns `204`.
3. Frontend removes the token even if the network request fails.
4. Any later protected request without a token redirects to login.

The existing five-table schema has no token-revocation store. A stolen token
therefore remains valid until its short expiration. Distributed immediate
revocation would require an approved persistence design.

## Account uniqueness limitation

The immutable Users table has only `user_id` as its key and currently has no
email or username index. AuthService performs case-insensitive uniqueness checks
against existing Users records. Production-scale atomic uniqueness requires
approved email/username lookup indexes or a separate identity provider.
