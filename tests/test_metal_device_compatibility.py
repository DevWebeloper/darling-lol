"""Regression test for Metal anti-cheat stealth device reporting and patch integrity."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MetalDeviceCompatibilityTests(unittest.TestCase):
    def test_metal_device_info_host_binary(self):
        """Compile and execute tools/test-metal-device-info.cpp on the host."""
        header_dir = ROOT / "build/darling-src/src/external/metal/private-include"
        if not (header_dir / "Metal/MTLDeviceInfo.h").exists():
            self.skipTest("MTLDeviceInfo.h not found in prepared source")

        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "test-metal-device-info"
            compile_cmd = [
                "c++",
                "-std=c++17",
                f"-I{header_dir}",
                str(ROOT / "tools/test-metal-device-info.cpp"),
                "-o",
                str(binary),
            ]
            comp = subprocess.run(compile_cmd, capture_output=True, text=True)
            self.assertEqual(comp.returncode, 0, f"Compilation failed:\n{comp.stderr}")

            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, f"Execution failed:\n{run.stdout}\n{run.stderr}")
            self.assertIn("METAL_DEVICE_INFO failures=0 pass=1", run.stdout)
            self.assertIn("fallback name is AMD Radeon Pro 5500M", run.stdout)
            self.assertIn("registry ID is 0x100000439", run.stdout)
            self.assertIn("resolveDeviceName anti-cheat stealth defaults and overrides", run.stdout)
            self.assertIn("working set stealth default -> 4294967296", run.stdout)

    def test_metal_patch_anti_cheat_requirements(self):
        """Verify patches/metal.patch contains all anti-cheat stealth requirements."""
        patch_path = ROOT / "patches/metal.patch"
        self.assertTrue(patch_path.exists(), "patches/metal.patch missing")
        content = patch_path.read_text()

        # Stealth default GPU name
        self.assertIn('kFallbackName = "AMD Radeon Pro 5500M"', content)
        self.assertIn('@"AMD Radeon Pro 5500M"', content)

        # Stealth default VRAM (4 GB)
        self.assertIn('4ull << 30', content)

        # Non-zero IOKit registry ID
        self.assertIn('0x100000439ULL', content)

        # Overrides supported: DARLING_METAL_GPU_NAME and DARLING_METAL_USE_HOST_GPU
        self.assertIn('DARLING_METAL_GPU_NAME', content)
        self.assertIn('DARLING_METAL_USE_HOST_GPU', content)
        self.assertIn('DARLING_METAL_VRAM_MB', content)

    def test_metal_patch_applies_cleanly_to_pinned_revision(self):
        """Verify patches/metal.patch applies cleanly to component revision."""
        manifest = json.loads((ROOT / "upstream/manifest.json").read_text())
        component = next(c for c in manifest["components"] if c["patch"] == "patches/metal.patch")
        repo = ROOT / "build/darling-src" / component["path"]
        if not (repo / ".git").exists():
            self.skipTest("pinned metal repo not cloned")

        patch = (ROOT / component["patch"]).read_text()
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
            subprocess.run(["git", "-C", str(repo), "read-tree", component["revision"]], env=env, check=True)
            res = subprocess.run(
                ["git", "-C", str(repo), "apply", "--cached", "--check", "--whitespace=nowarn", "-"],
                input=patch,
                text=True,
                env=env,
                capture_output=True,
            )
            self.assertEqual(res.returncode, 0, f"metal.patch failed to apply to {component['revision']}:\n{res.stderr}")


if __name__ == "__main__":
    unittest.main()
