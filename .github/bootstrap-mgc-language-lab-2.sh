#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-target}"
SOURCE="${2:-source}"
PREMIUM_COMMIT="ba408aec783c048c7fcf59058c02c0e7e56ba176"

rsync -a --delete \
  --exclude='.git/' \
  --exclude='.github/workflows/' \
  --exclude='.github/bootstrap-mgc-language-lab-2.sh' \
  "$SOURCE/" "$TARGET/"

cat > "$TARGET/tests/test_mgc_language_lab_2_premium.py" <<'PY'
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PremiumHomeContractTest(unittest.TestCase):
    def test_premium_home_is_canonical(self) -> None:
        index = (ROOT / "static/index.html").read_text(encoding="utf-8")
        navigation = (ROOT / "static/frontend/navigation.js").read_text(encoding="utf-8")

        self.assertTrue((ROOT / "static/frontend/premium_home_v631.js").is_file())
        self.assertTrue((ROOT / "static/premium_home_v631.css").is_file())
        self.assertIn('/premium_home_v631.css', index)
        self.assertIn('/frontend/premium_home_v631.js', index)
        self.assertIn("frontend.has('premium-home')", navigation)
        self.assertLess(
            navigation.index("frontend.has('premium-home')"),
            navigation.index("frontend.has('pilot-home')"),
        )
        self.assertIn("v631-premium-home-active", navigation)

    def test_server_compose_uses_language_lab_2_identity(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("name: mgc-language-lab-2", compose)
        self.assertIn("image: mgc-language-lab-2:", compose)


if __name__ == "__main__":
    unittest.main()
PY

pushd "$TARGET" >/dev/null
if python tests/test_mgc_language_lab_2_premium.py; then
  echo 'ERROR: premium contract unexpectedly passed before implementation.' >&2
  exit 1
fi
echo 'RED verified: current source does not expose the premium Language Lab 2 home.'
popd >/dev/null

git -C "$SOURCE" show "$PREMIUM_COMMIT":static/frontend/premium_home_v631.js > "$TARGET/static/frontend/premium_home_v631.js"
git -C "$SOURCE" show "$PREMIUM_COMMIT":static/premium_home_v631.css > "$TARGET/static/premium_home_v631.css"

python3 - "$TARGET" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])

index = root / 'static/index.html'
text = index.read_text(encoding='utf-8')
css_anchor = '<link rel="stylesheet" href="/pilot_simplified_v631.css">'
js_anchor = '<script src="/frontend/pilot_home.js" defer></script>'
if '/premium_home_v631.css' not in text:
    if css_anchor not in text:
        raise SystemExit('pilot CSS anchor not found')
    text = text.replace(css_anchor, css_anchor + '\n  <link rel="stylesheet" href="/premium_home_v631.css">', 1)
if '/frontend/premium_home_v631.js' not in text:
    if js_anchor not in text:
        raise SystemExit('pilot home script anchor not found')
    text = text.replace(js_anchor, js_anchor + '\n  <script src="/frontend/premium_home_v631.js" defer></script>', 1)
index.write_text(text, encoding='utf-8')

nav = root / 'static/frontend/navigation.js'
text = nav.read_text(encoding='utf-8')
text = text.replace(
    '/* v6.0.31: simplified pilot navigation.\n * Games now have one canonical owner: practice-games. The experimental\n * Game Lab / Game World stack remains outside the pilot route.\n */',
    '/* MGC Language Lab 2: premium server navigation.\n * Games keep one canonical owner: practice-games.\n * Home uses the premium automotive workspace; pilot-home is fallback only.\n */',
    1,
)
if 'function syncHomeChrome(view)' not in text:
    marker = '  function setView(view) {'
    if marker not in text:
        raise SystemExit('setView anchor not found')
    helper = """  function syncHomeChrome(view) {
    if (!document.body) return;
    document.body.classList.toggle('v631-premium-home-active', String(view || 'home') === 'home');
  }

"""
    text = text.replace(marker, helper + marker, 1)
set_marker = "  function setView(view) {\n    view = String(view || 'home');\n"
if '    syncHomeChrome(view);' not in text:
    if set_marker not in text:
        raise SystemExit('setView body anchor not found')
    text = text.replace(set_marker, set_marker + '    syncHomeChrome(view);\n', 1)
premium_route = """    if (frontend.has('premium-home') && frontend.get('premium-home').owns(view)) {
      return frontend.get('premium-home').navigate(view);
    }
"""
pilot_route = "    if (frontend.has('pilot-home') && frontend.get('pilot-home').owns(view)) {"
if "frontend.has('premium-home')" not in text:
    if pilot_route not in text:
        raise SystemExit('pilot-home route anchor not found')
    text = text.replace(pilot_route, premium_route + pilot_route, 1)
old_auth = '    showAuth: function () { return legacy().showAuth(); },'
new_auth = """    showAuth: function () {
      syncHomeChrome('auth');
      return legacy().showAuth();
    },"""
if old_auth in text:
    text = text.replace(old_auth, new_auth, 1)
leave_anchor = "    leaveUserSession: function () {\n      frontend.get('app-state').set('user', null);"
if "leaveUserSession: function () {\n      syncHomeChrome('auth');" not in text:
    if leave_anchor not in text:
        raise SystemExit('leaveUserSession anchor not found')
    text = text.replace(
        leave_anchor,
        "    leaveUserSession: function () {\n      syncHomeChrome('auth');\n      frontend.get('app-state').set('user', null);",
        1,
    )
nav.write_text(text, encoding='utf-8')

simplified_test = root / 'tests/v631_simplified_pilot_test.py'
test_text = simplified_test.read_text(encoding='utf-8')
test_text = test_text.replace("        '/frontend/premium_home_v631.js',\n", '', 1)
test_text = test_text.replace("        '/premium_home_v631.css',\n", '', 1)
simplified_test.write_text(test_text, encoding='utf-8')

compose = root / 'docker-compose.yml'
compose_text = compose.read_text(encoding='utf-8')
compose_text = compose_text.replace('name: mgc-languages-dev', 'name: mgc-language-lab-2', 1)
compose_text = compose_text.replace('image: mgc-languages:5.7.1-dev', 'image: mgc-language-lab-2:6.0.31-premium', 1)
compose.write_text(compose_text, encoding='utf-8')
PY

cat > "$TARGET/MGC_LANGUAGE_LAB_2_SERVER.md" <<'MD'
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
MD

pushd "$TARGET" >/dev/null
python -m pip install --upgrade pip
pip install -r requirements.txt

python tests/test_mgc_language_lab_2_premium.py
python tests/v631_simplified_pilot_test.py
python scripts/api_contract_guard.py
python scripts/release_candidate_guard.py --json
python -m compileall -q app.py asgi.py mgc mgc_core scripts
node --check static/frontend/navigation.js
node --check static/frontend/premium_home_v631.js
node --check static/frontend/games_ui_fix_v631.js
node --check static/frontend/practice_games.js
node --check static/frontend/boot.js

MGC_ADMIN_PASSWORD=ci-only-password-not-for-production docker compose config --quiet
docker build -t mgc-language-lab-2:premium .

docker run -d --name mgc-language-lab-2-smoke -p 18081:8000 \
  -e MGC_ADMIN_PASSWORD=ci-only-password-not-for-production \
  mgc-language-lab-2:premium
cleanup() {
  docker logs mgc-language-lab-2-smoke || true
  docker rm -f mgc-language-lab-2-smoke || true
}
trap cleanup EXIT
ready=0
for i in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:18081/health/ready >/tmp/ready.json; then
    cat /tmp/ready.json
    ready=1
    break
  fi
  sleep 2
done
if [ "$ready" -ne 1 ]; then
  echo 'Server did not become ready.' >&2
  exit 1
fi
curl -fsS http://127.0.0.1:18081/ >/tmp/index.html
curl -fsS http://127.0.0.1:18081/frontend/premium_home_v631.js >/tmp/premium.js
curl -fsS http://127.0.0.1:18081/premium_home_v631.css >/tmp/premium.css
grep -q '/frontend/premium_home_v631.js' /tmp/index.html
grep -q '/premium_home_v631.css' /tmp/index.html
grep -q "premium-home" /tmp/premium.js
test -s /tmp/premium.css

trap - EXIT
cleanup

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -A
if git diff --cached --quiet; then
  echo 'No changes to commit.'
  exit 0
fi
git commit -m 'Build MGC Language Lab 2 premium server project'
git push origin HEAD:build/server-premium-design
popd >/dev/null
