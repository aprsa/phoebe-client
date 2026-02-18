"""Server API clients for PHOEBE backend communication.

This module consolidates all HTTP communication with the phoebe-server:
- BaseAPI: Shared connection plumbing (host/port/timeout, base_url, Bearer token)
- SessionAPI: Session lifecycle + auth endpoints (register/login/config)
- PhoebeAPI: PHOEBE command execution via unified execute() method
"""

import requests
from typing import Any

from .exceptions import AuthenticationError, SessionError, CommandError
from .utils.serialization import make_json_serializable

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8001
DEFAULT_TIMEOUT = 120


class BaseAPI:
    """Base class for server API clients.

    Provides common server connection handling (host/port/timeout), base_url,
    and optional Bearer token header for authenticated requests.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._token: str | None = None

    @property
    def base_url(self) -> str:
        return f'http://{self._host}:{self._port}'

    def set_token(self, token: str | None) -> None:
        """Set or clear the Bearer token used for authentication."""
        self._token = token

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {'Content-Type': 'application/json'}
        if self._token:
            headers['Authorization'] = f'Bearer {self._token}'
        return headers


class SessionAPI(BaseAPI):
    """API client for PHOEBE session management and authentication.

    Manages backend session lifecycle (start/end, memory, ports) and
    authentication (register/login, auth config discovery).
    """

    def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        url = f'{self.base_url}{endpoint}'
        try:
            response = requests.request(
                method,
                url,
                headers=self._get_headers(),
                timeout=self._timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status in (401, 403):
                raise SessionError(
                    f'Server authentication failed (status {status}).'
                ) from e
            raise SessionError(f'Request failed: {e}') from e
        except requests.RequestException as e:
            raise SessionError(f'Request failed: {e}') from e

    # ---- auth ---------------------------------------------------------

    def get_auth_config(self) -> dict[str, Any]:
        """Discover the server's auth mode (none/password/jwt/external)."""
        return self._request('GET', '/auth/config')

    def register(self, email: str, password: str, first_name: str = "", last_name: str = "") -> dict[str, Any]:
        """Register a new user (password mode only). Returns {access_token, token_type}."""
        try:
            result = self._request(
                'POST',
                '/auth/register',
                json={
                    'email': email,
                    'password': password,
                    'first_name': first_name,
                    'last_name': last_name,
                },
            )
            # Auto-set token on success
            token = result.get('access_token')
            if token:
                self.set_token(token)
            return result
        except SessionError as e:
            raise AuthenticationError(str(e)) from e

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Log in (password mode only). Returns {access_token, token_type}."""
        try:
            result = self._request(
                'POST',
                '/auth/login',
                json={'email': email, 'password': password},
            )
            token = result.get('access_token')
            if token:
                self.set_token(token)
            return result
        except SessionError as e:
            raise AuthenticationError(str(e)) from e

    def get_me(self) -> dict[str, Any]:
        """Get the current authenticated user's info."""
        return self._request('GET', '/auth/me')

    # ---- sessions -----------------------------------------------------

    def get_sessions(self) -> dict[str, Any]:
        return self._request('GET', '/dash/sessions')

    def start_session(self, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request('POST', '/dash/start-session', json=metadata)

    def end_session(self, session_id: str) -> dict[str, Any]:
        return self._request('POST', f'/dash/end-session/{session_id}')

    def get_memory_usage(self) -> dict[str, Any]:
        return self._request('GET', '/dash/session-memory')

    def get_port_status(self) -> dict[str, Any]:
        return self._request('GET', '/dash/port-status')


class PhoebeAPI(BaseAPI):
    """API client for PHOEBE parameter operations.

    Executes PHOEBE commands via unified execute() method, which POSTs to
    /send/{session_id} with JSON payload. All commands flow through this
    single endpoint with server-side PHOEBE Bundle method dispatch.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
        session_id: str | None = None,
    ):
        super().__init__(host=host, port=port, timeout=timeout)
        self.session_id = session_id

    def set_session_id(self, session_id: str | None):
        self.session_id = session_id

    def execute(self, command: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.session_id:
            raise ValueError('No session ID set. Call set_session_id() first.')

        payload: dict[str, Any] = {**(args or {}), 'command': command}

        try:
            response = requests.post(
                f'{self.base_url}/send/{self.session_id}',
                json=make_json_serializable(payload),
                headers=self._get_headers(),
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status in (401, 403):
                raise CommandError(
                    f'Server authentication failed (status {status}).'
                ) from e
            raise CommandError(f'Command failed: {e}') from e
        except requests.RequestException as e:
            raise CommandError(f'Command failed: {e}') from e
