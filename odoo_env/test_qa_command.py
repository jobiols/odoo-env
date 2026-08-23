import contextlib
import io
import unittest
from unittest.mock import MagicMock, patch

from odoo_env.command import Command, QaCommand, QaVerdict
from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.messages import OeError
from odoo_env.odooenv import OdooEnv
from odoo_env.test_helpers import TEST_CLIENT_MANIFEST, MockArgs, OdooEnvTestCase


class TestQaCommandContract(unittest.TestCase):
    """QaVerdict + QaCommand skeleton contract (REQ-QAJ-001..007)."""

    def test_qa_verdict_has_exactly_three_members(self):
        self.assertEqual(
            {m.name for m in QaVerdict},
            {"PASS", "FAIL_LINE", "ZERO_TESTS"},
        )

    def test_qa_command_is_command_subclass_and_stores_flag(self):
        cmd = QaCommand(
            MagicMock(),
            command=["docker", "run"],
            usr_msg="x",
            any_requested_has_tests=True,
        )
        self.assertIsInstance(cmd, Command)
        self.assertTrue(cmd._any_requested_has_tests)
        self.assertIsNone(cmd._exit_code)


class TestJudgeStream(unittest.TestCase):
    """QaCommand._judge_stream() pure decision logic (REQ-QAJ-001..005)."""

    @staticmethod
    def _make_cmd(any_has_tests):
        return QaCommand(
            MagicMock(),
            command=["docker", "run"],
            usr_msg="test",
            any_requested_has_tests=any_has_tests,
        )

    def _judge(self, lines, any_has_tests):
        cmd = self._make_cmd(any_has_tests)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            verdict = cmd._judge_stream(iter(lines), any_has_tests)
        return verdict, buf.getvalue()

    def test_pass_with_tests_collected(self):
        verdict, _ = self._judge(
            ["INFO: loading", "0 failed, 0 error(s) of 5 tests"], True
        )
        self.assertEqual(verdict, QaVerdict.PASS)

    def test_fail_line_aborts(self):
        verdict, _ = self._judge(
            [
                "INFO: running",
                "2026-01-01 00:00:00,000 1 ERROR test_db odoo.x: FAIL: TestX.test_y",
                "0 failed, 1 error(s) of 5 tests",
            ],
            True,
        )
        self.assertEqual(verdict, QaVerdict.FAIL_LINE)

    def test_zero_tests_with_tests_dir_aborts(self):
        verdict, _ = self._judge(["0 failed, 0 error(s) of 0 tests"], True)
        self.assertEqual(verdict, QaVerdict.ZERO_TESTS)

    def test_zero_tests_without_tests_dir_passes(self):
        verdict, _ = self._judge(["0 failed, 0 error(s) of 0 tests"], False)
        self.assertEqual(verdict, QaVerdict.PASS)

    def test_aggregates_multiple_summary_lines(self):
        verdict, _ = self._judge(
            ["0 failed, 0 error(s) of 2 tests", "0 failed, 0 error(s) of 3 tests"],
            True,
        )
        self.assertEqual(verdict, QaVerdict.PASS)

    def test_ansi_failure_line_reprinted_raw_and_aborts(self):
        ansi = "\x1b[31m2026-06-14 : FAIL: TestAnsi\x1b[0m"
        verdict, printed = self._judge([ansi], True)
        self.assertEqual(verdict, QaVerdict.FAIL_LINE)
        self.assertIn("\x1b[31m", printed)

    def test_failure_gate_fires_before_zero_tests(self):
        # A : FAIL: line plus an `of 0 tests` summary must be FAIL_LINE, not
        # ZERO_TESTS (REQ-QAJ-001 wins over REQ-QAJ-002).
        verdict, _ = self._judge(
            ["2026-06-14 : FAIL: TestX.test_y", "0 failed, 0 error(s) of 0 tests"],
            True,
        )
        self.assertEqual(verdict, QaVerdict.FAIL_LINE)

    def test_unrelated_text_is_not_a_failure(self):
        verdict, _ = self._judge(
            [
                "bad query: something",
                "violates unique constraint",
                "0 failed, 0 error(s) of 1 tests",
            ],
            True,
        )
        self.assertEqual(verdict, QaVerdict.PASS)

    def test_no_summary_line_and_has_tests_dir_is_zero_tests(self):
        # No `of N tests` summary at all leaves aggregate at 0; with a tests/
        # directory that is still a ZERO_TESTS condition (REQ-QAJ-005).
        verdict, _ = self._judge(["INFO: loading modules"], True)
        self.assertEqual(verdict, QaVerdict.ZERO_TESTS)


class TestPtySeam(unittest.TestCase):
    """QaCommand._stream_lines() PTY seam (mocked, no real PTY/Docker)."""

    @staticmethod
    def _make_cmd(any_has_tests=True):
        return QaCommand(
            MagicMock(),
            command=["docker", "run"],
            usr_msg="test",
            any_requested_has_tests=any_has_tests,
        )

    def _run_stream(self, read_side_effect, returncode=0):
        cmd = self._make_cmd()
        process = MagicMock()
        process.returncode = returncode
        with patch("odoo_env.command.pty.openpty", return_value=(3, 4)):
            with patch("odoo_env.command.os.close"):
                with patch("odoo_env.command.subprocess.Popen", return_value=process):
                    with patch(
                        "odoo_env.command.os.read", side_effect=read_side_effect
                    ):
                        lines = list(cmd._stream_lines(["docker", "run"]))
        return lines, cmd._exit_code

    def test_eio_on_child_exit_is_eof(self):
        lines, exit_code = self._run_stream([b"line1\n", OSError()])
        self.assertEqual(lines, ["line1"])
        self.assertEqual(exit_code, 0)

    def test_partial_line_buffering(self):
        lines, exit_code = self._run_stream([b"hel", b"lo\nwor", b"ld\n", b""])
        self.assertEqual(lines, ["hello", "world"])
        self.assertEqual(exit_code, 0)

    def test_invalid_utf8_replaced(self):
        lines, _ = self._run_stream([b"bad\xff\xfe\n", b""])
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("bad"))
        self.assertIn("\ufffd", lines[0])

    def test_exit_code_captured(self):
        _, exit_code = self._run_stream([b"x\n", b""], returncode=7)
        self.assertEqual(exit_code, 7)


class TestQaCommandExecute(unittest.TestCase):
    """QaCommand.execute() orchestration + abort decision order (REQ-QAJ-001..004)."""

    @staticmethod
    def _make_cmd(any_has_tests=True, exit_code=0):
        cmd = QaCommand(
            MagicMock(),
            command=["docker", "run"],
            usr_msg="test",
            any_requested_has_tests=any_has_tests,
        )
        cmd._exit_code = exit_code
        return cmd

    def _execute(self, lines, any_has_tests=True, exit_code=0):
        cmd = self._make_cmd(any_has_tests=any_has_tests, exit_code=exit_code)
        # Feed canned lines to execute()'s decision logic, bypassing the real PTY.
        cmd._stream_lines = MagicMock(return_value=lines)
        with contextlib.redirect_stdout(io.StringIO()):
            cmd.execute()

    def test_execute_passes_on_success(self):
        self._execute(
            ["0 failed, 0 error(s) of 3 tests"], any_has_tests=True, exit_code=0
        )

    def test_execute_raises_on_fail_line(self):
        with self.assertRaises(OeError):
            self._execute(
                ["2026-06-14 : FAIL: TestX.test_y"], any_has_tests=True, exit_code=0
            )

    def test_execute_raises_on_nonzero_exit(self):
        with self.assertRaises(OeError):
            self._execute(["clean"], any_has_tests=False, exit_code=1)

    def test_execute_raises_on_zero_tests(self):
        with self.assertRaises(OeError):
            self._execute(
                ["0 failed, 0 error(s) of 0 tests"], any_has_tests=True, exit_code=0
            )


class TestAnyRequestedHasTests(OdooEnvTestCase):
    """Threading of any_requested_has_tests into QaCommand (REQ-QAJ-002/003)."""

    @staticmethod
    def _make_fake_path(has_tests):
        class FakePath:
            def __init__(self, *parts):
                self._parts = list(parts)

            def __truediv__(self, other):
                return FakePath(*(self._parts + [other]))

            def is_dir(self):
                return self._parts[-1] == "tests" and self._parts[-2] in has_tests

        return FakePath

    def _build_qa(self, modules_to_test, has_tests):
        self.mock_get_manifest.side_effect = lambda path=None: TEST_CLIENT_MANIFEST
        options = MockArgs(
            debug=False, client="test_client", modules_to_test=modules_to_test
        )
        oe = OdooEnv(options)
        on_disk = [m.strip() for m in modules_to_test.split(",")]
        with patch.object(
            EnvironmentManager,
            "discover_modules_in",
            return_value=on_disk,
        ):
            with patch.object(OdooEnv, "_db_exists", return_value=True):
                with patch.object(OdooEnv, "_installed_modules", return_value=set()):
                    with patch.object(
                        EnvironmentManager, "qa", return_value=["fake"]
                    ) as mock_qa:
                        with patch(
                            "odoo_env.odooenv.Path", self._make_fake_path(has_tests)
                        ):
                            oe.build_commands()
        return mock_qa

    def test_module_with_tests_dir_sets_flag_true(self):
        mock_qa = self._build_qa("mod_a,mod_b", {"mod_a"})
        self.assertTrue(mock_qa.call_args.kwargs["any_requested_has_tests"])

    def test_module_without_tests_dir_sets_flag_false(self):
        mock_qa = self._build_qa("mod_a,mod_b", set())
        self.assertFalse(mock_qa.call_args.kwargs["any_requested_has_tests"])

    def test_env_manager_qa_returns_qacommand_with_flag(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        em = EnvironmentManager(oe)
        cmds = em.qa("db", [], ["sale"], any_requested_has_tests=True)
        self.assertEqual(len(cmds), 1)
        cmd = cmds[0]
        assert isinstance(cmd, QaCommand)
        self.assertTrue(cmd._any_requested_has_tests)

    def test_env_manager_qa_flag_defaults_false(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        em = EnvironmentManager(oe)
        cmds = em.qa("db", [], ["sale"])
        cmd = cmds[0]
        assert isinstance(cmd, QaCommand)
        self.assertFalse(cmd._any_requested_has_tests)
