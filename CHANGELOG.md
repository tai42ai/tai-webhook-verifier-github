# Changelog

All notable changes to `tai42-webhook-verifier-github` are documented here; the
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Until 1.0.0 the API is not stable: **minor (0.x) releases may contain breaking
changes.**

## [Unreleased]

First release (0.1.0) in preparation — nothing published yet.

### Added

- `GitHubWebhookVerifier` — verifies a GitHub webhook delivery's
  `X-Hub-Signature-256` header (HMAC-SHA256 over the exact raw request body,
  compared in constant time with `hmac.compare_digest`). Returns `None` on
  success and raises `WebhookVerificationError` on a missing header, a wrong
  algorithm prefix, a wrong-length or non-hex digest, or a digest mismatch.
- Registration on import: importing the package binds the verifier under the name
  `"github"` on the `tai42_app.webhook_verifiers` facet, so the host loads it
  through the manifest's `lifecycle_modules` field.
- `secret_env` config: the per-binding `config` names the environment variable
  holding the shared secret; the secret is resolved from `os.environ` at verify
  time and never carried in the config. **Fails closed** — a missing key or
  missing env var raises loudly rather than treating the delivery as
  unauthenticated.
- `post_only = True`: signals a webhook door to reject GET for a topic bound to
  this verifier, since the HMAC authenticates the raw body only.
