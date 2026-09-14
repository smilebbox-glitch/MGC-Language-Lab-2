from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = (ROOT / "scripts/start_lan_windows.ps1").read_text(encoding="utf-8")
REPAIR = ROOT / "scripts/repair_lan_db_password.ps1"


def test_lan_launcher_repairs_persistent_database_password_before_app_start() -> None:
    assert REPAIR.is_file(), "missing LAN database password reconciliation helper"
    helper = REPAIR.read_text(encoding="utf-8")

    assert '@("compose", "--env-file", $EnvPath, "-f", $ComposePath)' in helper
    assert "& docker @ComposeArgs up -d db" in helper
    assert "ALTER ROLE" in helper
    assert "psql" in helper
    assert "POSTGRES_PASSWORD" in helper
    assert "POSTGRES_USER" in helper

    repair_call = "repair_lan_db_password.ps1"
    app_start = '$composeArgs = @("compose", "--env-file", ".env.lan", "-f", "docker-compose.lan.yml", "up", "-d")'
    assert repair_call in LAUNCHER
    assert app_start in LAUNCHER
    assert LAUNCHER.index(repair_call) < LAUNCHER.index(app_start)


if __name__ == "__main__":
    test_lan_launcher_repairs_persistent_database_password_before_app_start()
    print("PASS: LAN launcher repairs persistent PostgreSQL credentials before app startup")
