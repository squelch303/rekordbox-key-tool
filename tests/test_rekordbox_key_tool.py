"""Tests for rekordbox-key-tool. Standard library only: python -m unittest"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import rekordbox_key_tool as tool  # noqa: E402

EXAMPLE = ROOT / "test_data" / "example.xml"
SCRIPT = ROOT / "rekordbox_key_tool.py"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8",
    )


def tonalities(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    return {t.get("Name"): t.get("Tonality") for t in root.find("COLLECTION")}


class ConvertKeyTests(unittest.TestCase):
    def check(self, raw: str, expected: str | None, status: str):
        self.assertEqual(tool.convert_key(raw), (expected, status), raw)

    def test_full_wheel_standard_notation(self):
        wheel = {
            "Abm": "1A", "B": "1B", "Ebm": "2A", "F#": "2B", "Bbm": "3A", "Db": "3B",
            "Fm": "4A", "Ab": "4B", "Cm": "5A", "Eb": "5B", "Gm": "6A", "Bb": "6B",
            "Dm": "7A", "F": "7B", "Am": "8A", "C": "8B", "Em": "9A", "G": "9B",
            "Bm": "10A", "D": "10B", "F#m": "11A", "A": "11B", "C#m": "12A", "E": "12B",
        }
        for raw, camelot in wheel.items():
            self.check(raw, camelot, "converted")

    def test_enharmonics(self):
        self.check("G#m", "1A", "converted")
        self.check("Gb", "2B", "converted")
        self.check("A#m", "3A", "converted")
        self.check("Dbm", "12A", "converted")

    def test_long_and_unicode_forms(self):
        self.check("F# minor", "11A", "converted")
        self.check("Ab Major", "4B", "converted")
        self.check("A min", "8A", "converted")
        self.check("C maj", "8B", "converted")
        self.check("A♭m", "1A", "converted")
        self.check("F♯", "2B", "converted")
        self.check("  Am  ", "8A", "converted")

    def test_camelot(self):
        self.check("8A", "8A", "already")
        self.check("12B", "12B", "already")
        self.check("8a", "8A", "converted")
        self.check("08A", "8A", "converted")
        self.check("13A", None, "unknown")

    def test_open_key(self):
        self.check("1m", "8A", "converted")
        self.check("1d", "8B", "converted")
        self.check("6m", "1A", "converted")
        self.check("12m", "7A", "converted")
        self.check("12d", "7B", "converted")

    def test_combined_formats(self):
        self.check("Am/8A", "8A", "converted")
        self.check("8A - Am", "8A", "converted")
        self.check("Am | 8A", "8A", "converted")
        self.check("Am/9A", None, "unknown")  # parts disagree: leave it alone

    def test_empty_and_unknown(self):
        self.check("", None, "empty")
        self.check("   ", None, "empty")
        self.check("H", None, "unknown")
        self.check("xyz", None, "unknown")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.xml = self.tmp / "rekordbox.xml"
        shutil.copy(EXAMPLE, self.xml)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_dry_run_writes_nothing(self):
        before = self.xml.read_bytes()
        result = run_cli("--input", str(self.xml), "--dry-run", "-v")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("4  converted to Camelot", result.stdout)
        self.assertEqual(self.xml.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["rekordbox.xml"])

    def test_output_file(self):
        out = self.tmp / "fixed.xml"
        result = run_cli("--input", str(self.xml), "--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tonalities(out), {
            "Already Camelot": "8A", "Standard Minor": "8A", "Standard Major": "8B",
            "MIK Long Form": "11A", "Flat Notation": "3A", "No Key": "",
        })

    def test_drop_mode_writes_fixed_copy(self):
        before = self.xml.read_bytes()
        result = run_cli(str(self.xml))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.xml.read_bytes(), before)
        self.assertEqual(tonalities(self.tmp / "rekordbox_fixed.xml")["Standard Minor"], "8A")

    def test_inplace_makes_backup_and_never_overwrites_it(self):
        original = self.xml.read_bytes()
        self.assertEqual(run_cli("--input", str(self.xml), "--inplace").returncode, 0)
        self.assertEqual((self.tmp / "rekordbox.xml.bak").read_bytes(), original)
        self.assertEqual(tonalities(self.xml)["Standard Minor"], "8A")

        self.assertEqual(run_cli("--input", str(self.xml), "--inplace").returncode, 0)
        self.assertEqual((self.tmp / "rekordbox.xml.bak").read_bytes(), original)
        self.assertEqual(len(list(self.tmp.glob("rekordbox.xml.*.bak"))), 1)

    def test_inplace_dry_run_makes_no_backup(self):
        self.assertEqual(run_cli("--input", str(self.xml), "--inplace", "--dry-run").returncode, 0)
        self.assertFalse((self.tmp / "rekordbox.xml.bak").exists())

    def test_output_same_as_input_is_refused(self):
        result = run_cli("--input", str(self.xml), "--output", str(self.xml))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--inplace", result.stderr)

    def test_output_and_inplace_is_refused(self):
        result = run_cli("--input", str(self.xml), "--output", str(self.tmp / "x.xml"), "--inplace")
        self.assertNotEqual(result.returncode, 0)

    def test_invalid_xml_gives_clean_error(self):
        self.xml.write_text("not xml", encoding="utf-8")
        result = run_cli("--input", str(self.xml), "--dry-run")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a valid XML file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_version(self):
        result = run_cli("--version")
        self.assertIn(tool.__version__, result.stdout)

    def test_no_update_check_flag(self):
        result = run_cli("--input", str(self.xml), "--dry-run", "--no-update-check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("new version", result.stdout)


class UpdateCheckTests(unittest.TestCase):
    DAY = 86400

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.state = self.tmp / "sub" / "update-check.json"
        self.calls = 0

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def fetcher(self, tag):
        def fetch():
            self.calls += 1
            if isinstance(tag, Exception):
                raise tag
            return tag
        return fetch

    def check(self, tag, now):
        return tool.check_for_update(self.state, now=now, fetch=self.fetcher(tag))

    def test_parse_version(self):
        self.assertEqual(tool.parse_version("v1.2.0"), (1, 2, 0))
        self.assertEqual(tool.parse_version("1.2"), (1, 2, 0))
        self.assertIsNone(tool.parse_version("v2.0.0-beta1"))
        self.assertIsNone(tool.parse_version("nightly"))

    def test_newer_release_is_reported(self):
        self.assertEqual(self.check("v99.0.0", now=1000), "99.0.0")
        self.assertEqual(self.calls, 1)

    def test_same_or_older_release_is_not_reported(self):
        self.assertIsNone(self.check(f"v{tool.__version__}", now=1000))
        self.assertIsNone(self.check("v0.1.0", now=1000 + 30 * self.DAY))

    def test_asks_github_at_most_once_per_interval_but_keeps_notice(self):
        self.assertEqual(self.check("v99.0.0", now=1000), "99.0.0")
        self.assertEqual(self.check("v99.0.0", now=1000 + 6 * self.DAY), "99.0.0")
        self.assertEqual(self.calls, 1)
        self.check("v99.0.0", now=1000 + 7 * self.DAY)
        self.assertEqual(self.calls, 2)

    def test_network_failure_is_silent_and_not_retried_every_run(self):
        self.assertIsNone(self.check(OSError("offline"), now=1000))
        self.assertIsNone(self.check(OSError("offline"), now=1000 + self.DAY))
        self.assertEqual(self.calls, 1)

    def test_failure_keeps_last_known_version(self):
        self.check("v99.0.0", now=1000)
        self.assertEqual(self.check(OSError("offline"), now=1000 + 8 * self.DAY), "99.0.0")

    def test_corrupt_state_file_is_ignored(self):
        self.state.parent.mkdir(parents=True)
        self.state.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.check("v99.0.0", now=1000), "99.0.0")

    def test_clock_going_backwards_triggers_a_check(self):
        self.check("v1.0.0", now=1000 + 30 * self.DAY)
        self.check("v1.0.0", now=1000)
        self.assertEqual(self.calls, 2)


if __name__ == "__main__":
    unittest.main()
