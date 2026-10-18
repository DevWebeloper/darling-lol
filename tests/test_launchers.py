import os
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestLeagueLauncher(unittest.TestCase):
    def setUp(self):
        self.desktop_repo = REPO_ROOT / "launchers/league.desktop"
        self.launch_script = REPO_ROOT / "scripts/launch-fork.sh"

    def test_launch_script_exists_and_executable(self):
        """Verify launch script exists and is executable."""
        self.assertTrue(self.launch_script.is_file(), "scripts/launch-fork.sh must exist")
        self.assertTrue(os.access(self.launch_script, os.X_OK), "scripts/launch-fork.sh must be executable")

    def test_desktop_file_exists_and_valid(self):
        """Verify launchers/league.desktop has Name=League and required fields."""
        self.assertTrue(self.desktop_repo.is_file(), "launchers/league.desktop must exist")
        content = self.desktop_repo.read_text()
        self.assertIn("Name=League", content)
        self.assertIn("Icon=league", content)
        self.assertIn("StartupWMClass=Riot Client", content)

    def test_fork_launcher_dry_run(self):
        """Verify running launch script with --dry-run passes without executing game."""
        res = subprocess.run([str(self.launch_script), "--dry-run"], capture_output=True, text=True, check=False)
        self.assertEqual(res.returncode, 0, f"--dry-run failed: {res.stderr}")
        self.assertIn("[DRY-RUN] Fork Launcher Validation", res.stdout)


if __name__ == "__main__":
    unittest.main()
