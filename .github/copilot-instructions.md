# PHOEBE Client - AI Coding Agent Instructions

## Project Overview
This is a Python SDK (client library) for PHOEBE (PHysics Of Eclipsing BinariEs), providing a client interface to interact with PHOEBE backend services for binary star astrophysics simulations. The SDK is the **middle layer** in a three-tier architecture:

1. **phoebe-server**: Backend API with full PHOEBE library, executes all computations
2. **phoebe-client** (this project): Thin client managing sessions, authentication, API communication, and response deserialization
3. **phoebe-ui**: PHOEBE-free web UI (NiceGUI framework) consuming only the SDK/client

**Critical Architecture Constraint**: The UI layer has NO PHOEBE dependency. All PHOEBE operations happen server-side. The SDK must deserialize server responses into UI-friendly formats without requiring the full PHOEBE library.

For PHOEBE documentation and command reference:
- Main site: https://phoebe-project.org
- Repository: https://github.com/phoebe-project/phoebe2

**Package Layout**: Single `phoebe_client` package with `utils/` submodule, `server_api.py`, `client.py`, and `exceptions.py`. The `py.typed` marker file enables PEP 561 type checking.

## Architecture

### Two-Layer SDK Design
- **`PhoebeClient`** (`client.py`): High-level facade with auth methods (login/register/set_token) and PHOEBE operations
- **`SessionAPI`** (`server_api.py`): Session lifecycle + auth endpoints (start/end sessions, register/login, auth config discovery)
- **`PhoebeAPI`** (`server_api.py`): PHOEBE-specific operations via unified `execute()` method
- **`BaseAPI`** (`server_api.py`): Shared server connection plumbing (host/port/timeout, base_url, Bearer token)

All PHOEBE commands flow through `PhoebeAPI.execute(command, args)` which POSTs to `/send/{session_id}` with JSON payload. Authentication uses Bearer token (JWT) in the Authorization header.

### Authentication Flow
- `PhoebeClient.get_auth_config()` → discovers server auth mode (none/password/jwt/external)
- `PhoebeClient.login(email, password)` / `register(...)` → obtains JWT from server, auto-sets on both APIs
- `PhoebeClient.set_token(token)` → manually set external JWT (e.g., from upstream novalabs)
- Token propagated to both `SessionAPI` and `PhoebeAPI` via `set_token()`

**No client-side config file**: Host/port/timeout are passed as constructor arguments. No config.toml on the client.

## Key Patterns

### Context Manager Pattern
```python
with PhoebeClient(host="localhost", port=8001) as client:
    client.set_value(twig='period@binary', value=1.5)
    # session auto-created and auto-closed
```

### Auth + Session Pattern
```python
client = PhoebeClient(host="localhost", port=8001)
client.login("user@example.com", "password")  # JWT auto-set
response = client.start_session(metadata={"project_name": "My System"})
# ... do work ...
client.end_session()
```

### PhoebeAPI Method Pattern
`PhoebeClient` provides high-level convenience methods that delegate to `PhoebeAPI.execute()`:
```python
def set_value(self, value, **kwargs):
    return self.phoebe.execute(command="set_value", args={"value": value, **kwargs})
```

`PhoebeAPI.execute()` automatically serializes via `make_json_serializable()` and includes the Bearer token.

## Development Workflow

### Setup & Installation
```bash
pip install -e .[dev]
```

### Testing
```bash
pytest
pytest --cov=phoebe_client --cov-report=html
```

### Code Quality
- **Formatter**: Black (line-length=100)
- **Import sorting**: isort (black profile)
- **Type checking**: mypy with strict settings
- **Linting**: flake8

## API Communication Contract

### Request Structure
All PHOEBE commands POST to `/send/{session_id}` with JSON body:
```json
{
  "command": "b.set_value",
  "twig": "period@binary",
  "value": 1.5
}
```

### Auth Endpoints
- `GET /auth/config` → `{mode: "none"|"password"|"jwt"|"external"}`
- `POST /auth/register` → `{access_token, token_type}`
- `POST /auth/login` → `{access_token, token_type}`
- `GET /auth/me` → `{user_id, email, full_name, role}`

### Session Endpoints
- `POST /dash/start-session` → `{session_id, port, user_id, ...}`
- `POST /dash/end-session/{session_id}`
- `GET /dash/sessions` → sessions owned by current user

### Authorization Header
`Authorization: Bearer <jwt_token>` (set via `set_token()` or auto-set by `login()`/`register()`)

## Common Gotchas

1. **No client config file**: Host/port/timeout are constructor args with defaults (localhost:8001, 120s timeout). No config.toml.
2. **Token propagation**: `login()`/`register()` auto-set token on both `SessionAPI` and `PhoebeAPI`. `set_token()` does the same manually.
3. **Session ID Required**: `PhoebeAPI.execute()` raises `ValueError` if `session_id` not set.
4. **Context Manager**: `with PhoebeClient()` auto-creates session; plain instantiation requires explicit `start_session()`/`end_session()`.
5. **NumPy Serialization**: Always pass through `make_json_serializable()` before JSON encoding. This happens automatically in `execute()`.
6. **Session ownership**: In jwt/external modes, sessions are user-scoped. `get_sessions()` returns only the current user's sessions.

## Project-Specific Conventions

- **Type Hints**: All public APIs use type hints; `py.typed` marker included for PEP 561 compliance
- **Exception Hierarchy**: `PhoebeClientError` → `AuthenticationError`, `SessionError`, `CommandError`
- **Python 3.12+ Target**: Uses modern type hints
- **Minimal Dependencies**: Only `requests` and `numpy` (no pydantic, no JWT libs, no config files)
- **Three-Tier Philosophy**: UI (PHOEBE-free) → SDK/Client (communication) → Server (full PHOEBE computations)
