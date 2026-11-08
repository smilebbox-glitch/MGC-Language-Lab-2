# Agent guidance — MGC Language Lab

Corporate training service (Python 3.12, FastAPI, server-side logic, vanilla frontend assets). The public repository contains no authorization to upload company information to external services.

## Product constraints
- Respect the v6.0.31 simplified company pilot documented in README.md. Do not restore removed 3D, XP, AI assistant or experimental games without explicit user direction.
- Keep Russian, Standard Mandarin Chinese (characters + pinyin) and English content accurate for automotive assembly, welding, painting, stamping, logistics and quality.
- Keep existing auth/session isolation, PostgreSQL, corporate deployment, LAN and offline behavior intact.
- Do not leak employee accounts, coursework or internal terms to external APIs.
- Avoid heavy new packages, CDN assets, automatic browser downloads or unapproved telemetry.

## Quality gates
- Run narrowly relevant Python tests from tests/ and python scripts/company_pilot_preflight.py --strict-corporate when supported by the environment.
- Don't claim production readiness without actual validation.
- Keep changes in feature branches and review before merge/deployment.

## Codex project skills
- .agents/skills/frontend-quality/SKILL.md
- .agents/skills/learning-content-qa/SKILL.md
- .agents/skills/change-safety/SKILL.md

These project skills do not install third-party binaries or plugins on the server.
