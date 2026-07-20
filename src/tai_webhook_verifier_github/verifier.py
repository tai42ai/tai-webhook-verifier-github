"""The GitHub webhook-signature verifier.

GitHub signs each webhook delivery with an HMAC-SHA256 over the exact raw request
body, keyed by the shared secret, and presents it in the ``X-Hub-Signature-256``
header as ``"sha256=" + hexdigest``. :class:`GitHubWebhookVerifier` authenticates
an inbound delivery against that scheme, returning ``None`` on success and raising
:class:`~tai_contract.webhooks.WebhookVerificationError` on any verification
failure.

The secret is never carried in the per-binding ``config`` — ``config`` names the
environment variable (``secret_env``) that holds it, resolved here at verify time.
A missing or empty env var is an operator misconfiguration, not a normal
verification failure: it raises loudly (``KeyError`` / ``ValueError``) so the door
fails CLOSED rather than silently treating every delivery as unauthenticated.

Depends only on the standard library (``hmac`` / ``hashlib``) and the pure
:mod:`tai_contract` interface it registers through.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Mapping
from typing import Any

from tai_contract.webhooks import WebhookVerificationError

# GitHub's signature header and its fixed algorithm prefix. The hex digest of an
# HMAC-SHA256 is always 64 characters, so a well-formed value is exactly
# ``sha256=`` followed by 64 hex chars.
_SIGNATURE_HEADER = "X-Hub-Signature-256"
_SIGNATURE_PREFIX = "sha256="
_HEX_DIGEST_LEN = hashlib.sha256().digest_size * 2  # 64


class GitHubWebhookVerifier:
    """Verifies a GitHub webhook delivery's ``X-Hub-Signature-256`` HMAC.

    Registered under the name ``"github"`` on the app handle's
    ``webhook_verifiers`` facet. Satisfies the
    :class:`~tai_contract.webhooks.WebhookVerifier` protocol.
    """

    # The signature authenticates the raw body only, so a GET delivery would ride
    # the payload on the URL unauthenticated. A door that also accepts GET reads
    # this flag (getattr, default False) and rejects GET for a topic bound to this
    # verifier.
    post_only = True

    async def verify(self, body: bytes, headers: Mapping[str, str], config: dict[str, Any]) -> None:
        """Verify a GitHub webhook, or raise
        :class:`~tai_contract.webhooks.WebhookVerificationError`.

        ``body`` is the EXACT raw request bytes — the HMAC is computed over these
        unchanged. ``headers`` are the request headers, looked up
        case-insensitively. ``config`` is ``{"secret_env": "<ENV VAR NAME>"}``;
        the secret is read from ``os.environ`` at call time.

        Fails CLOSED: a missing ``secret_env`` key in ``config``, a missing
        environment variable, or an empty secret value raises loudly
        (``KeyError`` / ``ValueError``) rather than being treated as an ordinary
        signature failure — a misconfigured secret is an operator error, never a
        silent open door.
        """
        # Resolve the secret. A missing config key, a missing env var, or an
        # empty env var is an operator misconfiguration: raise loudly (fail
        # closed), never a WebhookVerificationError that reads like an ordinary
        # bad signature. An empty secret would otherwise still key the HMAC —
        # a forgeable signature anyone can compute.
        secret_env = config["secret_env"]
        secret = os.environ[secret_env].encode("utf-8")
        if not secret:
            raise ValueError(f"webhook secret environment variable {secret_env!r} is set but empty")

        signature = _header_lookup(headers, _SIGNATURE_HEADER)
        if signature is None:
            raise WebhookVerificationError(f"missing {_SIGNATURE_HEADER} header")

        if not signature.startswith(_SIGNATURE_PREFIX):
            raise WebhookVerificationError(f"{_SIGNATURE_HEADER} is not prefixed {_SIGNATURE_PREFIX!r}")

        provided_hex = signature[len(_SIGNATURE_PREFIX) :]
        if len(provided_hex) != _HEX_DIGEST_LEN:
            raise WebhookVerificationError(f"{_SIGNATURE_HEADER} digest is not {_HEX_DIGEST_LEN} hex characters")
        # A well-formed digest is hex. Reject a non-hex value (e.g. a non-ASCII
        # header byte, which Starlette decodes as latin-1) as an ordinary
        # verification failure — a clean 401, never an unhandled parse error.
        try:
            provided_digest = bytes.fromhex(provided_hex)
        except ValueError as exc:
            raise WebhookVerificationError(f"{_SIGNATURE_HEADER} digest is not valid hex") from exc

        expected_digest = hmac.new(secret, body, hashlib.sha256).digest()

        # Constant-time compare (over the raw digest bytes) so a mismatch
        # position cannot be timed out.
        if not hmac.compare_digest(provided_digest, expected_digest):
            raise WebhookVerificationError(f"{_SIGNATURE_HEADER} digest mismatch")


def _header_lookup(headers: Mapping[str, str], name: str) -> str | None:
    """Return the value of ``name`` from ``headers`` case-insensitively.

    HTTP header names are case-insensitive, and the platform may hand this
    verifier a plain ``dict`` rather than a case-folding multidict, so the match
    is done on lower-cased keys rather than assuming the caller normalised them.
    """
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


__all__ = ["GitHubWebhookVerifier"]
