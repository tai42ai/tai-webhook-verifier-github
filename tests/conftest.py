"""Bind a capturing app to the ``tai42_app`` handle before any package import, and
provide the registration-capture fixture.

Importing ``tai42_webhook_verifier_github`` (including any of its submodules, which
pull the package ``__init__`` first) runs the module-level
``tai42_app.webhook_verifiers.register(...)`` call, mirroring how the host binds the
app and then imports the module named by the manifest's ``lifecycle_modules``.
Binding a capturing app here lets the suite import the package without an
unbound-handle error; the ``load_registrations`` fixture rebinds a fresh capturing
app so a test can assert exactly what the package registers.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from typing import Any, cast

import pytest
from tai42_contract.app import tai42_app
from tai42_contract.webhooks import WebhookVerifier


class _CaptureVerifiers:
    """Records every verifier registered through
    ``tai42_app.webhook_verifiers.register``."""

    def __init__(self) -> None:
        self.registered: dict[str, WebhookVerifier] = {}

    def register(self, name: str, verifier: WebhookVerifier) -> None:
        # A real app raises on a duplicate name; the capture mirrors that so a
        # double-registration bug surfaces in tests rather than being masked.
        if name in self.registered:
            raise ValueError(f"verifier {name!r} is already registered")
        self.registered[name] = verifier

    def get(self, name: str) -> WebhookVerifier:
        return self.registered[name]


class _CaptureApp:
    def __init__(self) -> None:
        self.webhook_verifiers = _CaptureVerifiers()


# Bind at import time so the first import of the package (its module-level
# register call) has an app to register against.
tai42_app.bind(_CaptureApp())


@pytest.fixture
def load_registrations() -> Iterator[Any]:
    """Return a loader that (re)imports the package under a fresh capturing app
    and hands back the app so the test can read ``app.webhook_verifiers.registered``.

    The previously bound app is restored afterwards so other tests are unaffected.
    """
    previous = cast("Any", tai42_app)._impl

    def load(module_name: str) -> _CaptureApp:
        app = _CaptureApp()
        tai42_app.bind(app)
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)
        return app

    yield load
    tai42_app.bind(previous)
