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
