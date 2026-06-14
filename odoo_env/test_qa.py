"""Unit tests for the odoo_env.qa engine (qa-coverage-ci change).

Strict TDD: each test class drives one unit of the engine.
Run:
    PYTHONPATH=. venv/bin/python -m unittest odoo_env.test_qa
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from odoo_env.qa import failures, threshold
from odoo_env.qa.config import RunnerConfig
from odoo_env.qa.runner import TestRunner


class FailureDetectionTests(unittest.TestCase):
    """REQ-QA-003 — reliable failure detection (ADR 4)."""

    def setUp(self):
        self.is_error_line = failures.is_error_line

    def test_detects_fail_line(self):
        self.assertTrue(self.is_error_line("2026-06-14 10:00:00,000 : FAIL: TestFoo"))

    def test_detects_error_line(self):
        self.assertTrue(self.is_error_line("2026-06-14 10:00:00,000 : ERROR: TestBar"))

    def test_ignores_non_test_colon_lines(self):
        self.assertFalse(self.is_error_line("psql: bad query: something"))
        self.assertFalse(self.is_error_line("violates unique constraint"))

    def test_strips_ansi_before_match(self):
        line = "\x1b[0;31m2026-06-14 : FAIL: TestAnsi\x1b[0m"
        self.assertTrue(self.is_error_line(line))

    def test_clean_line_is_false(self):
        self.assertFalse(
            self.is_error_line("2026-06-14 10:00:00,000 INFO odoo: loading module")
        )

    def test_fail_without_word_is_false(self):
        # ': FAIL:' must be followed by a word char to avoid false positives.
        self.assertFalse(self.is_error_line("status: FAIL: "))

    def test_error_without_word_is_false(self):
        self.assertFalse(self.is_error_line("status: ERROR: "))


class RunnerConfigTests(unittest.TestCase):
    """REQ-QA-007 / REQ-QA-008 — config seam + version-aware demo (ADR 1, 7)."""

    @staticmethod
    def _fake_client(name="dimec", version="17.0", numeric=17.0):
        client = MagicMock()
        client.name = name
        client.version = version
        client.numeric_ver = numeric
        client.base_dir = f"/odoo_ar/odoo-{version}e/{name}/"
        client.get_image_required.return_value = MagicMock(
            name=f"jobiols/odoo-ent:{version}e"
        )
        # MagicMock(name=...) sets the repr, not .name; set explicitly.
        client.get_image_required.return_value.name = f"jobiols/odoo-ent:{version}e"
        return client

    def test_defaults(self):
        cfg = RunnerConfig(
            client="dimec",
            version="17.0",
            base_dir="/odoo_ar/odoo-17.0e/dimec/",
            image="jobiols/odoo-ent:17.0e",
            db_name="dimec_test",
        )
        self.assertEqual(cfg.network, "odoo-net")
        self.assertTrue(cfg.coverage)
        self.assertIn("*/tests/*", cfg.omit)
        self.assertIn("*/__manifest__.py", cfg.omit)

    def test_from_oe_resolves_fields(self):
        cfg = RunnerConfig.from_oe(self._fake_client())
        self.assertEqual(cfg.client, "dimec")
        self.assertEqual(cfg.version, "17.0")
        self.assertEqual(cfg.base_dir, "/odoo_ar/odoo-17.0e/dimec/")
        self.assertEqual(cfg.image, "jobiols/odoo-ent:17.0e")
        self.assertEqual(cfg.db_name, "dimec_test")

    def test_needs_with_demo_flag_true_for_ge19(self):
        # Odoo >=19 no longer loads demo by default; resolver must flag it.
        cfg = RunnerConfig.from_oe(self._fake_client(version="19.0", numeric=19.0))
        self.assertTrue(cfg.needs_with_demo_flag)

    def test_needs_with_demo_flag_false_for_le18(self):
        cfg = RunnerConfig.from_oe(self._fake_client(version="17.0", numeric=17.0))
        self.assertFalse(cfg.needs_with_demo_flag)

    def test_needs_with_demo_flag_false_at_18_boundary(self):
        cfg = RunnerConfig.from_oe(self._fake_client(version="18.0", numeric=18.0))
        self.assertFalse(cfg.needs_with_demo_flag)


class ThresholdTests(unittest.TestCase):
    """REQ-QA-005 (floor) + REQ-QA-006 (ratchet) — ADR 6."""

    def setUp(self):
        self.threshold = threshold
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _write(self, value):
        path = self.root / ".coverage-threshold"
        path.write_text(f"{value}\n", encoding="utf-8")
        return path

    def test_read_floor_default_when_missing(self):
        self.assertEqual(
            self.threshold.read_floor(self.root / ".coverage-threshold"),
            self.threshold.DEFAULT_FLOOR,
        )
        self.assertEqual(self.threshold.DEFAULT_FLOOR, 20)

    def test_read_floor_from_file(self):
        path = self._write(35)
        self.assertEqual(self.threshold.read_floor(path), 35)

    def test_read_floor_ignores_whitespace(self):
        path = self.root / ".coverage-threshold"
        path.write_text("  42  \n", encoding="utf-8")
        self.assertEqual(self.threshold.read_floor(path), 42)

    def test_ratchet_rejects_lower(self):
        self.assertFalse(self.threshold.check_ratchet(master=30, proposed=25))

    def test_ratchet_accepts_higher(self):
        self.assertTrue(self.threshold.check_ratchet(master=30, proposed=40))

    def test_ratchet_accepts_equal(self):
        self.assertTrue(self.threshold.check_ratchet(master=30, proposed=30))

    def test_read_floor_raises_on_malformed(self):
        for bad in ("", "20  # note", "20.5", "twenty"):
            path = self.root / ".coverage-threshold"
            path.write_text(bad, encoding="utf-8")
            with self.assertRaises(ValueError):
                self.threshold.read_floor(path)

    def test_read_floor_rejects_out_of_range(self):
        for bad in ("-5", "150"):
            path = self._write(bad)
            with self.assertRaises(ValueError):
                self.threshold.read_floor(path)


def _config(**kw):
    defaults = {
        "client": "dimec",
        "version": "17.0",
        "base_dir": "/odoo_ar/odoo-17.0e/dimec/",
        "image": "jobiols/odoo-ent:17.0e",
        "db_name": "dimec_test",
    }
    defaults.update(kw)
    return RunnerConfig(**defaults)


class DiscoveryTests(unittest.TestCase):
    """REQ-QA-001 — module test discovery (ADR 3)."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())
        self._orig_cwd = os.getcwd()
        os.chdir(str(self._tmp))

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_module(self, name, with_manifest=True, with_tests=True):
        mod = self._tmp / name
        mod.mkdir()
        if with_manifest:
            (mod / "__manifest__.py").touch()
        if with_tests:
            (mod / "tests").mkdir()
        return mod

    def test_discovers_modules_with_manifest_and_tests(self):
        self._make_module("mod_a")
        self._make_module("mod_b")
        self._make_module("mod_c", with_tests=False)
        self._make_module("mod_d", with_manifest=False)
        self.assertEqual(TestRunner.discover_test_modules(), ["mod_a", "mod_b"])

    def test_discover_empty_returns_empty_list(self):
        self.assertEqual(TestRunner.discover_test_modules(), [])

    def test_discover_does_not_recurse(self):
        mod = self._make_module("mod_a")
        (mod / "nested").mkdir()
        (mod / "nested" / "__manifest__.py").touch()
        (mod / "nested" / "tests").mkdir()
        self.assertEqual(TestRunner.discover_test_modules(), ["mod_a"])


class CommandCompositionTests(unittest.TestCase):
    """REQ-QA-002 / REQ-QA-008 — coverage-wrapped + thin-seed commands (ADR 2, 7)."""

    def test_coverage_cmd_wraps_with_entrypoint_bash(self):
        runner = TestRunner(_config())
        cmd = runner._build_module_cmd("mod_a")
        self.assertIn("--entrypoint", cmd)
        self.assertIn("bash", cmd)
        self.assertIn("-c", cmd)
        joined = " ".join(cmd)
        self.assertIn("coverage run -p", joined)
        self.assertIn("--source", joined)

    def test_coverage_cmd_sets_cov_file_env(self):
        runner = TestRunner(_config())
        cmd = runner._build_module_cmd("mod_a")
        # COVERAGE_FILE in the env section
        joined = " ".join(cmd)
        self.assertIn("COVERAGE_FILE", joined)
        self.assertIn("/opt/odoo/data/.coverage_data", joined)

    def test_coverage_cmd_includes_test_enable_and_stop_after_init(self):
        runner = TestRunner(_config())
        cmd = runner._build_module_cmd("mod_a")
        joined = " ".join(cmd)
        self.assertIn("--test-enable", joined)
        self.assertIn("--stop-after-init", joined)

    def test_coverage_cmd_passes_explicit_db_args(self):
        runner = TestRunner(_config())
        cmd = runner._build_module_cmd("mod_a")
        joined = " ".join(cmd)
        self.assertIn("--db_host", joined)
        self.assertIn("--db_port", joined)
        self.assertIn("--db_user", joined)
        self.assertIn("--db_password", joined)

    def test_coverage_cmd_uses_install_verb(self):
        runner = TestRunner(_config())
        cmd = runner._build_module_cmd("mod_a")
        joined = " ".join(cmd)
        self.assertIn(" -i ", joined)
        self.assertIn("mod_a", joined)

    def test_plain_cmd_no_coverage_when_disabled(self):
        runner = TestRunner(_config(coverage=False))
        cmd = runner._build_module_cmd("mod_a")
        joined = " ".join(cmd)
        self.assertNotIn("coverage", joined)
        self.assertNotIn("--entrypoint", cmd)

    def test_plain_cmd_has_tests_and_db(self):
        runner = TestRunner(_config(coverage=False))
        cmd = runner._build_module_cmd("mod_a")
        joined = " ".join(cmd)
        self.assertIn("--test-enable", joined)
        self.assertIn("--stop-after-init", joined)
        self.assertIn("dimec_test", joined)

    def test_module_cmd_includes_network_and_link(self):
        runner = TestRunner(_config())
        cmd = runner._build_module_cmd("mod_a")
        joined = " ".join(cmd)
        self.assertIn("--network", joined)
        self.assertIn("odoo-net", joined)
        self.assertIn("--link", joined)
        self.assertIn("pg-dimec:db", joined)


class RunAllTests(unittest.TestCase):
    """REQ-QA-003 — first-failure stop orchestration (ADR 4)."""

    def setUp(self):
        self.config = _config()

    def _make_runner(self):
        return TestRunner(self.config)

    def _mock_popen(self, lines, exit_code=0):
        """Return a mock Popen that streams *lines* with *exit_code*."""
        mock = MagicMock()
        mock.__enter__.return_value = mock
        mock.stdout = lines
        mock.wait.return_value = exit_code
        mock.returncode = exit_code
        return mock

    @patch("odoo_env.qa.runner.TestRunner.discover_test_modules")
    @patch("subprocess.Popen")
    def test_run_all_stops_on_fail_line(self, mock_popen, mock_disc):
        mock_disc.return_value = ["mod_a", "mod_b"]
        mock_popen.return_value = self._mock_popen(
            ["log...", "2026-06-14 : FAIL: TestXxx.test_x"], exit_code=0
        )
        runner = self._make_runner()
        self.assertFalse(runner.run_all())
        # mod_b must NOT have been run (stopped at mod_a)
        self.assertEqual(mock_popen.call_count, 1)

    @patch("odoo_env.qa.runner.TestRunner.discover_test_modules")
    @patch("subprocess.Popen")
    def test_run_all_stops_on_nonzero_exit(self, mock_popen, mock_disc):
        mock_disc.return_value = ["mod_a", "mod_b"]
        mock_popen.return_value = self._mock_popen(["clean output"], exit_code=1)
        runner = self._make_runner()
        self.assertFalse(runner.run_all())
        self.assertEqual(mock_popen.call_count, 1)

    @patch("odoo_env.qa.runner.TestRunner.discover_test_modules")
    @patch("subprocess.Popen")
    def test_run_all_all_pass(self, mock_popen, mock_disc):
        mock_disc.return_value = ["mod_a", "mod_b"]
        mock_popen.return_value = self._mock_popen(["clean output"], exit_code=0)
        runner = self._make_runner()
        self.assertTrue(runner.run_all())
        # Both modules must have been run
        self.assertEqual(mock_popen.call_count, 2)

    @patch("odoo_env.qa.runner.TestRunner.discover_test_modules")
    def test_run_all_no_modules(self, mock_disc):
        mock_disc.return_value = []
        runner = self._make_runner()
        self.assertFalse(runner.run_all())


class ReportTests(unittest.TestCase):
    """REQ-QA-004 / REQ-QA-005 — coverage combine + report + threshold (ADR 5, 6)."""

    def setUp(self):
        self.config = _config()
        self._tmp = Path(tempfile.mkdtemp())
        (self._tmp / ".coverage-threshold").write_text("20\n", encoding="utf-8")
        self._orig_cwd = os.getcwd()
        os.chdir(str(self._tmp))

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_runner(self):
        return TestRunner(self.config)

    @patch("subprocess.run")
    def test_report_includes_combine_and_fail_under(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        self.assertTrue(TestRunner(self.config).generate_report())
        self.assertEqual(mock_run.call_count, 1)
        cmd_str = " ".join(mock_run.call_args[0][0])
        self.assertIn("coverage combine", cmd_str)
        self.assertIn("--fail-under=20", cmd_str)

    @patch("subprocess.run")
    def test_report_includes_omit_patterns(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = self._make_runner()
        self.assertTrue(runner.generate_report())
        cmd_str = " ".join(mock_run.call_args[0][0])
        # omit patterns from DEFAULT_OMIT
        self.assertIn("*/tests/*", cmd_str)
        self.assertIn("*/__manifest__.py", cmd_str)

    @patch("subprocess.run")
    def test_report_produces_xml_json_html(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = self._make_runner()
        self.assertTrue(runner.generate_report())
        cmd_str = " ".join(mock_run.call_args[0][0])
        self.assertIn("coverage xml", cmd_str)
        self.assertIn("coverage json", cmd_str)
        self.assertIn("coverage html", cmd_str)

    @patch("subprocess.run")
    def test_report_returns_false_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        runner = self._make_runner()
        self.assertFalse(runner.generate_report())


class ThresholdEnforcementTests(unittest.TestCase):
    """REQ-QA-005 / REQ-QA-006 — check_threshold integration (ADR 6)."""

    def setUp(self):
        self.config = _config()
        self._tmp = Path(tempfile.mkdtemp())
        self._orig_cwd = os.getcwd()
        os.chdir(str(self._tmp))

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write_floor(self, value):
        (self._tmp / ".coverage-threshold").write_text(f"{value}\n", encoding="utf-8")

    def _make_runner(self):
        return TestRunner(self.config)

    @patch("subprocess.check_output")
    def test_check_threshold_passes_when_equal(self, mock_co):
        mock_co.return_value = "30\n"
        self._write_floor(30)
        runner = self._make_runner()
        self.assertTrue(runner.check_threshold())

    @patch("subprocess.check_output")
    def test_check_threshold_rejects_lower(self, mock_co):
        mock_co.return_value = "30\n"
        self._write_floor(25)
        runner = self._make_runner()
        self.assertFalse(runner.check_threshold())

    @patch("subprocess.check_output")
    def test_check_threshold_master_missing_defaults_20(self, mock_co):
        mock_co.side_effect = subprocess.CalledProcessError(128, ["git", "show"])
        self._write_floor(30)
        runner = self._make_runner()
        self.assertTrue(runner.check_threshold())  # 30 >= 20


if __name__ == "__main__":
    unittest.main()
