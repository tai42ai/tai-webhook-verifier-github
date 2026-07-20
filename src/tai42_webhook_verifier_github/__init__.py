"""tai42-webhook-verifier-github — the GitHub webhook-signature verifier plugin.

A per-provider :class:`~tai42_contract.webhooks.WebhookVerifier` for the TAI
platform. Importing this package registers a :class:`GitHubWebhookVerifier` under
the name ``"github"`` on the app handle's ``webhook_verifiers`` facet, so a public
webhook door can bind ``github`` to a topic and have every inbound delivery's
``X-Hub-Signature-256`` HMAC checked before the payload is parsed or dispatched.

This module is import-only: the platform loads it through the manifest's
``lifecycle_modules`` field, which imports the module purely to run the
registration below. ``lifecycle_modules`` are imported WITHOUT going through the
extension registry's validation (only ``extensions_modules`` do), so this is a
plain registration side effect — not an extension.

Its only dependency is ``tai42-contract`` (the interface it registers through); the
HMAC work is pure standard library. It never imports the skeleton — the plugin is
contract-facing.
"""

from __future__ import annotations

from tai42_contract.app import tai42_app

from tai42_webhook_verifier_github.verifier import GitHubWebhookVerifier

# Register on import: the manifest's import-only ``lifecycle_modules`` entry loads
# this package purely to run this call, binding the "github" verifier so a webhook
# door can resolve it by name. Re-registering a name already taken raises loudly.
tai42_app.webhook_verifiers.register("github", GitHubWebhookVerifier())

__all__ = ["GitHubWebhookVerifier"]
