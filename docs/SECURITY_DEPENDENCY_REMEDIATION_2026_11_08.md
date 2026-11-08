# Proposed dependency security remediation (2026-11-08)

## Why this PR exists

The independent `pip-audit` job in the `chore/codex-toolkit-20261108` PR found **10 published advisories affecting two packages** in the company pilot's pinned requirements:

- Authlib 1.6.12 — 9 advisories including CVE-2026-96760 and CVE-2026-116672; first fully fixed version reported by the scanner: 1.9.1.
- opentelemetry-api 1.44.0 — CVE-2026-114603; fixed version: 1.45.1.

The root package version bumps in this PR are intentionally coordinated:
- Authlib -> 1.9.5 (current patch of the 1.9.x security-fix line).
- OpenTelemetry API, SDK and OTLP HTTP exporter -> 1.45.1.
- OpenTelemetry FastAPI and SQLAlchemy instrumentation -> 0.66b1 (matching the 1.45.1 release family).

## Verification gates

`.github/workflows/security-dependencies.yml` resolves the complete requirements file with pip, performs `pip check`, runs `pip-audit`, tests OAuth/OIDC and telemetry imports, then executes selected auth and metrics runtime tests using disposable local SQLite data.

These checks do NOT prove compatibility with MGC's actual identity provider, real PostgreSQL, certificates, reverse proxy or production telemetry backend. Verify those separately in the staging VM. No production deployment is included.

## Rollout and rollback

1. Review and pass the checks in the draft PR.
2. Perform IT sign-off and a staging build; test OIDC login, logout, token refresh/expiry, roles, audit logs and /metrics.
3. Back up and record current image digest, environment and the deployment version before promoting.
4. Roll forward only through the existing safe-update runbook. Watch authentication errors and telemetry for regression.
5. If necessary, restore the prior approved image/config after IT confirmation.

Do not weaken authentication checks or suppress vulnerability warnings merely to turn the status green.
