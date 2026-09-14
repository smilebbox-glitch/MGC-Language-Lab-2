# MGC Language Lab 2 — Premium Server Build

This repository is the server-deployable MGC Language Lab 2 pilot.

## Canonical interface

The approved premium automotive home is the canonical home screen. The legacy simplified `pilot-home` module remains only as an internal fallback and is not the primary UI.

## Local/server Docker start

Create `.env` with at least a strong admin password:

```env
MGC_ADMIN_PASSWORD=replace-with-a-strong-password
```

Then build and start:

```bash
docker compose build
docker compose up -d
docker compose ps
```

Default development port is `8080` unless `MGC_PORT` is set.

## Production/VM profiles

Production-oriented compose files and VM deployment scripts from the current language-service runtime are included in this repository. Use the appropriate `.env.*.example` file and the corresponding deployment guide before exposing the service outside a trusted LAN.

## Design regression guard

`tests/test_mgc_language_lab_2_premium.py` prevents the premium home assets and routing from being removed accidentally.
