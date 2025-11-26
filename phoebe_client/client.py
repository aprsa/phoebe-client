"""Main client library that combines session and PHOEBE operations."""

from typing import Any
from .server_api import SessionAPI, PhoebeAPI
from .auth.base import AuthProvider


class PhoebeClient:
    """Main PHOEBE Client providing unified access."""

    def __init__(self, host: str | None = None, port: int | None = None, auth_provider: AuthProvider | None = None, auto_session: bool = False):
        self.host = host
        self.port = port
        self.auth_provider = auth_provider
        self.jwt_token: str | None = None  # UI authentication token

        self.sessions = SessionAPI(host=host, port=port)
        self.phoebe = PhoebeAPI(host=host, port=port)

        if auto_session:
            self.start_session()

    def start_session(self, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.sessions.start_session(metadata=metadata)
        self.phoebe.set_session_id(response.get('session_id'))
        return response

    def set_session_id(self, session_id: str):
        self.phoebe.set_session_id(session_id)

    def end_session(self, session_id: str):
        self.sessions.end_session(session_id)
        self.phoebe.set_session_id(None)

    def get_sessions(self) -> dict[str, Any]:
        return self.sessions.get_sessions()

    def attach_parameters(self, parameters: list[dict[str, Any]]) -> dict[str, Any]:
        response = self.phoebe.execute(
            command='attach_parameters',
            args={'parameters': parameters}
        )
        return response

    def get_parameter(self, qualifier: str, **kwargs) -> dict[str, Any]:
        return self.phoebe.execute(
            command='get_parameter',
            args={'qualifier': qualifier, **kwargs}
        )

    def is_parameter_constrained(self, uniqueid: str) -> dict[str, Any]:
        response = self.phoebe.execute(
            command='is_parameter_constrained',
            args={'uniqueid': uniqueid}
        )
        return response

    def update_uniqueid(self, twig: str) -> dict[str, Any]:
        return self.phoebe.execute(
            command='update_uniqueid',
            args={'twig': twig}
        )

    def get_value(self, **kwargs) -> Any:
        """
        Get the value of a parameter identified by passed kwargs. Typically,
        kwargs will contain 'uniqueid' if available, or a full set of tags
        (qualifier, context, kind, component, ...) that uniquely identify
        the parameter.
        """
        return self.phoebe.execute(
            command='get_value',
            args=kwargs
        )

    def set_value(self, value, **kwargs) -> dict[str, Any]:
        """
        Set the value of a parameter identified by passed kwargs. Typically,
        kwargs will contain 'uniqueid' if available, or a full set of tags
        (qualifier, context, kind, component, ...) that uniquely identify
        the parameter.
        """
        return self.phoebe.execute(
            command='set_value',
            args={'value': value, **kwargs}
        )

    def add_dataset(self, **kwargs) -> dict[str, Any]:
        return self.phoebe.execute(
            command='add_dataset',
            args=kwargs
        )

    def remove_dataset(self, dataset: str) -> dict[str, Any]:
        return self.phoebe.execute(
            command='remove_dataset',
            args={'dataset': dataset}
        )

    def get_datasets(self) -> dict[str, Any]:
        return self.phoebe.execute(
            command='get_datasets',
            args={}
        )

    def run_compute(self, **kwargs) -> dict[str, Any]:
        return self.phoebe.execute(
            command='run_compute',
            args=kwargs
        )

    def run_solver(self, **kwargs) -> dict[str, Any]:
        return self.phoebe.execute(
            command='run_solver',
            args=kwargs
        )

    def get_bundle(self) -> dict[str, Any]:
        return self.phoebe.execute(
            command='get_bundle',
            args={}
        )

    def load_bundle(self, bundle: str) -> dict[str, Any]:
        return self.phoebe.execute(
            command='load_bundle',
            args={'bundle': bundle}
        )

    def save_bundle(self) -> dict[str, Any]:
        return self.phoebe.execute(
            command='save_bundle',
            args={}
        )

    def __enter__(self):
        if not self.phoebe.session_id:
            self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_session()
