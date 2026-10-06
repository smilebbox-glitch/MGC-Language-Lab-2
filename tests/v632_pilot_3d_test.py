from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_3d_section_is_wired_but_heavy_modules_stay_lazy() -> None:
    index = read("static/index.html")
    assert 'data-view="3d"' in index
    assert "/frontend/pilot_3d_v632.js" in index
    assert "/pilot_3d_v632.css" in index
    # Heavy WebGL modules are loaded on demand, never by the cold-start shell.
    assert "/frontend/digital_vehicle_3d_v630.js" not in index
    assert "/frontend/digital_truck_3d_v630.js" not in index

    module = read("static/frontend/pilot_3d_v632.js")
    assert "/frontend/digital_vehicle_3d_v630.js" in module
    assert "/frontend/digital_truck_3d_v630.js" in module
    assert "/digital_vehicle_3d_v630.css" in module


def test_navigation_delegates_3d_view() -> None:
    navigation = read("static/frontend/navigation.js")
    assert "frontend.get('pilot-3d').owns(view)" in navigation


def test_models_expose_factories_and_robust_webgl_context() -> None:
    for rel in ("static/frontend/digital_vehicle_3d_v630.js", "static/frontend/digital_truck_3d_v630.js"):
        source = read(rel)
        assert "create:function" in source
        assert "experimental-webgl" in source
        assert "powerPreference:'low-power'}" in source
        subprocess.run(["node", "--check", str(ROOT / rel)], check=True, cwd=ROOT)
    subprocess.run(["node", "--check", str(ROOT / "static/frontend/pilot_3d_v632.js")], check=True, cwd=ROOT)
