# PHOEBE Client - AI Coding Agent Instructions

## Project Overview
This is a Python SDK (client library) for PHOEBE (PHysics Of Eclipsing BinariEs), providing a client interface to interact with PHOEBE backend services for binary star astrophysics simulations. The SDK is the **middle layer** in a three-tier architecture:

1. **phoebe-server**: Backend API with full PHOEBE library, executes all computations
2. **phoebe-client** (this project): Thin client managing sessions, authentication, API communication, and response deserialization
3. **phoebe-ui**: PHOEBE-free web UI (NiceGUI framework) consuming only the SDK/client

**Critical Architecture Constraint**: The UI layer has NO PHOEBE dependency. All PHOEBE operations happen server-side. The SDK must deserialize server responses into UI-friendly formats without requiring the full PHOEBE library. This is a **hard constraint** - any changes must maintain this separation.

For PHOEBE documentation and command reference:
- Main site: https://phoebe-project.org
- Repository: https://github.com/phoebe-project/phoebe2

**Package Layout**: Single `phoebe_client` package with submodules `auth/`, `utils/`, `config.py`, and `server_api.py`. The `py.typed` marker file enables PEP 561 type checking for downstream consumers.

## Architecture

### Three-Layer SDK Design
- **`PhoebeClient`** (`client.py`): High-level facade exposing common operations with context manager support
- **`SessionAPI`** (`server_api.py`): Backend session lifecycle management (start/end sessions, memory/port status)
- **`PhoebeAPI`** (`server_api.py`): PHOEBE-specific operations via unified `execute()` method
- **`BaseAPI`** (`server_api.py`): Shared server connection plumbing (host/port/timeout, base_url, X-API-Key headers)

All PHOEBE commands flow through `PhoebeAPI.execute(command, args)` which POSTs to `/send/{session_id}` with JSON payload containing `command` key plus command-specific arguments. Server auth uses `X-API-Key` header from `config.toml`.

### Authentication Split
- Client → Server auth: `X-API-Key` header only (configured in `config.toml`). JWT is never sent to the server.
- UI → Client auth: Optional `AuthProvider` (JWT/internal) validates users; token is stored on `PhoebeClient` but not propagated to HTTP headers.

## Key Patterns

### Context Manager Pattern
`PhoebeClient` implements `__enter__`/`__exit__` for automatic session management:
```python
with PhoebeClient(base_url=url) as client:
    client.set_value(twig='period@binary', value=1.5)
    # session auto-created and auto-closed
```

### Session ID Propagation
Sessions return a `session_id` that must be set on `PhoebeAPI` before executing commands:
```python
response = self.sessions.start_session()
self.phoebe.set_session_id(response.get('session_id'))
```

### Serialization Strategy (WIP)
**Current State**: `utils/serialization.py` provides `make_json_serializable()` for NumPy arrays in outbound requests. Recursively handles dicts, lists, tuples, and NumPy types (arrays, integers, floats, bools).

**Active Challenge**: Deserializing PHOEBE/Astropy types (like `phoebe.u.Quantity`) from server responses. Since the UI has NO PHOEBE dependency, the SDK must handle deserialization. Options under consideration:
1. **Lightweight wrapper classes**: Create minimal types mimicking PHOEBE interfaces (e.g., `Quantity`, `Parameter`)
2. **Optional PHOEBE dependency**: Make full PHOEBE optional (`pip install phoebe-client[full]`) with lightweight fallbacks
3. **Structured dictionaries**: Return typed dictionaries with `__type__` metadata that UI can render directly

**Design Constraint**: The SDK is the ONLY layer that can deserialize PHOEBE types since phoebe-ui must remain PHOEBE-free. Balance between type fidelity and dependency weight is critical.

**Implementation Detail**: `PhoebeAPI.execute()` automatically wraps all args through `make_json_serializable()` before POST, so individual methods don't need to handle serialization. Requests include `X-API-Key` and use timeout from `config.toml`.

### PhoebeAPI Method Pattern
`PhoebeClient` provides high-level convenience methods that delegate to `PhoebeAPI.execute()`. The pattern:
```python
# In PhoebeClient (client.py)
def set_value(self, twig: str | None = None, uniqueid: str | None = None, value=None):
    return self.phoebe.set_value(twig=twig, uniqueid=uniqueid, value=value)

# In PhoebeAPI (server_api.py)  
def set_value(self, twig: str | None = None, uniqueid: str | None = None, value: Any = None) -> dict[str, Any]:
    return self.execute(
        command='b.set_value',
        args={'twig': twig, 'uniqueid': uniqueid, 'value': value}
    )
```

**Critical**: `PhoebeAPI.execute()` automatically injects the `command` key into the args dict and serializes via `make_json_serializable()`. The command string (e.g., `'b.set_value'`) maps to server-side PHOEBE Bundle methods.

## Development Workflow

### Setup & Installation
```bash
# Development environment with all tools (activate your venv first)
pip install -e .[dev]

# Include JWT support
pip install -e .[jwt]
```

### Testing
```bash
# Run tests with pytest
pytest

# With coverage
pytest --cov=phoebe_client --cov-report=html
```

### Code Quality
- **Formatter**: Black (line-length=100)
- **Import sorting**: isort (black profile)
- **Type checking**: mypy with strict settings
- **Linting**: flake8

Run formatters before committing:
```bash
black phoebe_client/ tests/ examples/
isort phoebe_client/ tests/ examples/
mypy phoebe_client/
```

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

### Authorization Header
Server auth: `X-API-Key: <api_key>` (from `config.toml`)

### Session Endpoints
- `POST /dash/start-session` → returns `{session_id: ...}`
- `POST /dash/end-session/{session_id}`
- `GET /dash/sessions` → list active sessions

## Common Gotchas

1. **Session ID Required**: `PhoebeAPI.execute()` raises `ValueError` if `session_id` not set. Always call `start_session()` or set manually. The flow: `sessions.start_session()` returns `{session_id: ...}` → pass to `phoebe.set_session_id()`.

2. **Optional Dependencies**: JWT features require `pyjwt` package. JWT is for UI→Client only; never send it to the server.

3. **Context Manager vs Manual**: `with PhoebeClient()` auto-creates session; plain instantiation requires explicit `start_session()`/`end_session()` calls. See `examples/basic_usage.py` vs `examples/explicit_session.py`.

4. **NumPy Serialization**: Always pass PHOEBE parameters through `make_json_serializable()` before JSON encoding to handle arrays. This happens automatically in `PhoebeAPI.execute()`.

5. **Base URL Configuration**: Current default `http://localhost:8001` is temporary. Future versions will use `config.toml` for environment-specific URLs.

6. **PHOEBE Dependency Dilemma**: The SDK must deserialize PHOEBE types from server responses, but should avoid requiring the full PHOEBE library as a hard dependency. The UI layer is completely PHOEBE-free and relies on the SDK for all type handling.

7. **JWT Handling**: When `authenticate()` is called on `PhoebeClient`, the JWT is stored only on the client and not included in any HTTP headers.

8. **Configuration Precedence**: Constructor args > `config.toml` > hardcoded defaults. Config is loaded at import time via stdlib `tomllib`.

## Project-Specific Conventions

- **Type Hints**: All public APIs use type hints; `py.typed` marker included for PEP 561 compliance
- **Exception Hierarchy**: All exceptions inherit from `PhoebeClientError` (see `exceptions.py`). Specialized: `AuthenticationError`, `SessionError`, `CommandError`
- **Python 3.9+ Target**: Uses modern type hints; avoid patterns requiring 3.10+
- **GPL-3.0 License**: Scientific/academic project, keep licensing in mind for dependencies
- **Minimize Dependencies**: SDK is a thin client layer between UI and server. Balance deserialization needs against dependency weight.
- **Three-Tier Philosophy**: UI (PHOEBE-free) → SDK/Client (deserialization & communication) → Server (full PHOEBE computations)
- **Optional Dependencies**: JWT auth requires `pyjwt`. Core functionality works without optional deps.

## Examples Reference

Refer to `examples/` for usage patterns:
- `basic_usage.py`: Context manager with simple operations
- `explicit_session.py`: Manual session lifecycle control
- `with_jwt_auth.py`: External authentication integration
