# Contributing to tai-webhook-verifier-github

`tai-webhook-verifier-github` is a per-provider **webhook-signature verifier**
plugin for the TAI ecosystem: it authenticates each inbound GitHub delivery by
its `X-Hub-Signature-256` HMAC-SHA256 before the payload is parsed or dispatched.
The hard rule (the plugin rule): **it depends on `tai-contract` only and never
imports the skeleton.** It registers through the `tai_app` handle from
`tai_contract.app` and is loaded by the host from the manifest's
`lifecycle_modules` field by dynamic import — there is no import edge to the
skeleton in either direction.

> A webhook door binds a named verifier to a topic; this plugin supplies the
> `github` verifier.

## Ground rules

- **No skeleton import — ever.** The package is contract-facing; the ban is
  enforced by ruff (`flake8-tidy-imports`), so a stray import fails lint:
  ```bash
  grep -rn "tai_skeleton" src/   # must be empty
  ```
- **Fails closed.** A misconfigured secret (a missing `secret_env` key, a
  missing environment variable, or an empty secret value) raises loudly
  (`KeyError` / `ValueError`) rather than being treated as an ordinary signature
  failure — a misconfigured door is never a silently-unauthenticated one.
- **Loud errors.** No swallowed exceptions, silent fallbacks, or silent
  truncation. A missing header, a malformed signature, or a digest mismatch
  raises `WebhookVerificationError`; an operator misconfiguration raises.
- **The secret never leaves the environment.** It is read from `os.environ` at
  verify time and never carried in the per-binding `config`, a fixture, or a
  test. The only secret in the tree is GitHub's published example placeholder.
- **Constant-time compare.** The final digest check uses `hmac.compare_digest`;
  never replace it with a plain `==`.
- **Typed package** (`py.typed`). Pyright runs clean.

## Layout

- `src/tai_webhook_verifier_github/__init__.py` — the import-only registration
  side effect: `tai_app.webhook_verifiers.register("github", GitHubWebhookVerifier())`.
- `src/tai_webhook_verifier_github/verifier.py` — `GitHubWebhookVerifier` and its
  private header helper.
- `tests/` mirrors `src/`.

## Dev

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

`[tool.uv.sources]` pins `tai-contract` to a sibling `../tai-contract` editable
checkout so changes to the webhooks facet are picked up without a reinstall for
local pytest. The published version floor in `[project].dependencies` is what the
shipped wheel declares; this source override is not part of wheel metadata.

For local cross-repo work, `make dev` editable-installs the sibling `tai-*`
checkouts this package builds on into the venv. While `[tool.uv.sources]` pins
those siblings to local paths, `uv sync` already installs them editable and
`make dev` changes nothing; once the lock resolves them from the registry,
`uv sync` / `uv run` installs the published builds instead, so re-run
`make dev` afterward to restore the editable links.

Before any commit, run a secret scan over `src/` and `tests/` (e.g.
`detect-secrets scan`).

## License

By contributing you agree your contributions are licensed under Apache-2.0.
