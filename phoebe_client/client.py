"""Main client library that combines session and PHOEBE operations."""

from typing import Any
from .server_api import SessionAPI, PhoebeAPI, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_TIMEOUT


class PhoebeClient:
    """Main PHOEBE Client providing unified access.

    Parameters
    ----------
    host : str
        Server hostname (default "localhost").
    port : int
        Server port (default 8001).
    timeout : int
        Request timeout in seconds (default 120).
    auto_session : bool
        If True, automatically start a session on construction.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
        auto_session: bool = False,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout

        self.sessions = SessionAPI(host=host, port=port, timeout=timeout)
        self.phoebe = PhoebeAPI(host=host, port=port, timeout=timeout)

        if auto_session:
            self.start_session()

    # ---- auth ---------------------------------------------------------

    def get_auth_config(self) -> dict[str, Any]:
        """Discover the server's auth mode."""
        return self.sessions.get_auth_config()

    def register(self, email: str, password: str, first_name: str = "", last_name: str = "") -> dict[str, Any]:
        """Register a new user. Auto-sets token on both APIs."""
        result = self.sessions.register(email, password, first_name, last_name)
        # Propagate token to PhoebeAPI
        self.phoebe.set_token(self.sessions._token)
        return result

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Log in. Auto-sets token on both APIs."""
        result = self.sessions.login(email, password)
        self.phoebe.set_token(self.sessions._token)
        return result

    def set_token(self, token: str | None) -> None:
        """Manually set a Bearer token (e.g. external JWT)."""
        self.sessions.set_token(token)
        self.phoebe.set_token(token)

    def get_me(self) -> dict[str, Any]:
        """Get current authenticated user info."""
        return self.sessions.get_me()

    # ---- sessions -----------------------------------------------------

    def start_session(self, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.sessions.start_session(metadata=metadata)
        self.phoebe.set_session_id(response.get("session_id"))
        return response

    def set_session_id(self, session_id: str):
        self.phoebe.set_session_id(session_id)

    def end_session(self, session_id: str | None = None):
        sid = session_id or self.phoebe.session_id
        if sid:
            self.sessions.end_session(sid)
            if sid == self.phoebe.session_id:
                self.phoebe.set_session_id(None)

    def get_sessions(self) -> dict[str, Any]:
        return self.sessions.get_sessions()

    # ---- PHOEBE operations -------------------------------------------

    def set_morphology(self, morphology: str) -> dict[str, Any]:
        return self.phoebe.execute(command="set_morphology", args={"morphology": morphology})

    def attach_parameters(self, parameters: list[dict[str, Any]]) -> dict[str, Any]:
        return self.phoebe.execute(command="attach_parameters", args={"parameters": parameters})

    def get_parameter(self, qualifier: str, **kwargs) -> dict[str, Any]:
        return self.phoebe.execute(command="get_parameter", args={"qualifier": qualifier, **kwargs})

    def is_parameter_constrained(self, uniqueid: str) -> dict[str, Any]:
        return self.phoebe.execute(command="is_parameter_constrained", args={"uniqueid": uniqueid})

    def update_uniqueid(self, twig: str) -> dict[str, Any]:
        return self.phoebe.execute(command="update_uniqueid", args={"twig": twig})

    def get_value(self, **kwargs) -> Any:
        """Get the value of a parameter identified by kwargs."""
        return self.phoebe.execute(command="get_value", args=kwargs)

    def set_value(self, value, **kwargs) -> dict[str, Any]:
        """Set the value of a parameter identified by kwargs."""
        return self.phoebe.execute(command="set_value", args={"value": value, **kwargs})

    def add_dataset(self, **kwargs) -> dict[str, Any]:
        return self.phoebe.execute(command="add_dataset", args=kwargs)

    def remove_dataset(self, dataset: str) -> dict[str, Any]:
        return self.phoebe.execute(command="remove_dataset", args={"dataset": dataset})

    def get_datasets(self) -> dict[str, Any]:
        return self.phoebe.execute(command="get_datasets", args={})

    def run_compute(self, **kwargs) -> dict[str, Any]:
        return self.phoebe.execute(command="run_compute", args=kwargs)

    def run_solver(self, **kwargs) -> dict[str, Any]:
        return self.phoebe.execute(command="run_solver", args=kwargs)

    def get_bundle(self) -> dict[str, Any]:
        return self.phoebe.execute(command="get_bundle", args={})

    def load_bundle(self, bundle: str) -> dict[str, Any]:
        return self.phoebe.execute(command="load_bundle", args={"bundle": bundle})

    def save_bundle(self) -> dict[str, Any]:
        return self.phoebe.execute(command="save_bundle", args={})

    # ---- context manager ----------------------------------------------

    def __enter__(self):
        if not self.phoebe.session_id:
            self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_session()
