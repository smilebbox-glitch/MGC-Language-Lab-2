---
name: change-safety
description: Keep MGC Language Lab Python and frontend changes small, reversible, well-tested and compatible with existing security and company pilot constraints.
---

# Change-safety review

- Trace bug to an executable reproduction or test before refactoring.
- Prefer minimal diff and readable straightforward code; do not redesign unrelated modules.
- Review authentication, session ownership, RBAC, credentials, SQLite/PostgreSQL modes and OIDC boundaries.
- Avoid schema migration, changed deployment defaults and new runtime dependencies unless approved.
- Use regression tests under tests/ and run the corporate preflight where possible.
- Do not modify main, deploy to the company VM or claim verification without recorded test results.

Inspired by https://github.com/DietrichGebert/ponytail ; independently authored project skill, no third-party hooks installed.
