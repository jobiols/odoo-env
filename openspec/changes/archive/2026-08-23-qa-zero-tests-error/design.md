# Design: qa-zero-tests-error (Part B)

## Overview

This design addresses Part B of issue #128: making `oe -Q` a real QA gate by
detecting test failures and zero-tests conditions instead of trusting Odoo's
exit code. The central challenge is implementing a PTY-based executor that
preserves ANSI colors AND avoids the historical staircase bug, while remaining
fully unit-testable without Docker.

**Requirements covered:** REQ-QAJ-001 through REQ-QAJ-007 (qa-judgement spec).

---

## Architecture Decisions

### ADR-1: The PTY Seam — Separation of I/O and Parsing

**Context:** The PTY execution loop involves POSIX-specific I/O (`pty.openpty`,
`os.read`, `Popen`). Testing this directly would require Docker or complex
system mocking. We need unit tests that verify the parsing/decision logic
independently.

**Decision:** Design a two-layer architecture with a thin, mockable seam:

```
┌─────────────────────────────────────────────────────────────────┐
│                       QaCommand.execute()                       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: I/O Seam (injectable)                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  _stream_lines(cmd) -> Iterator[str]                      │  │
│  │  - pty.openpty() + Popen(stdout=slave, stderr=slave)      │  │
│  │  - os.read(master) loop with EIO handling                 │  │
│  │  - decode + buffer partial lines + split on \n            │  │
│  │  - yield complete lines (colors intact)                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  Layer 2: Pure Parsing/Decision (unit-testable)                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  _judge_stream(lines: Iterable[str], any_has_tests: bool) │  │
│  │  -> QaVerdict                                             │  │
│  │  - reprint each line to stdout (colors intact, flush)     │  │
│  │  - is_error_line() → detect FAIL/ERROR                    │  │
│  │  - parse_test_count() → aggregate collected counts        │  │
│  │  - return verdict: PASS / FAIL_LINE / ZERO_TESTS          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation:**

1. `_stream_lines(cmd: list[str]) -> Iterator[str]` — The I/O seam. Owns all
   PTY mechanics. In production, spawns the docker process via PTY. In tests,
   this method is overridden or monkeypatched to yield canned lines.

2. `_judge_stream(lines: Iterable[str], any_has_tests: bool) -> QaVerdict` —
   The pure parsing/decision method. Consumes an iterable of lines, reprints
   each to stdout with flush, aggregates test counts, detects failure lines.
   Returns a verdict enum. This is 100% unit-testable with synthetic input.

3. `execute()` orchestrates: calls `_stream_lines()`, feeds to `_judge_stream()`,
   obtains exit code from the subprocess, applies final decision logic.

**Rationale:**

- The seam boundary (`_stream_lines`) is thin and well-defined: it produces
  decoded lines, nothing more.
- The parsing/decision logic (`_judge_stream`) is pure: given lines and a bool,
  it returns a verdict. Tests inject synthetic Odoo output directly.
- This mirrors how `TestRunner._run_one` works (Popen + line iteration +
  `is_error_line`), but with PTY instead of PIPE and count aggregation added.

**Alternatives considered:**

- Injecting a collaborator object (e.g., `LineProducer`): adds unnecessary
  indirection for a single override point. A method seam is simpler.
- Testing via subprocess mocking: fragile, couples tests to implementation
  details of the PTY loop.

---

### ADR-2: PTY Mechanics — Colors Without Staircase

**Context:** Commit 44382f1 (issue #126) established that `docker run -t` plus
a plain `Popen(stdout=PIPE)` causes the staircase effect: Docker's `-t` puts
the container's stdout in raw mode where `\n` is not translated to `\r\n`, so
lines cascade rightward. The CI runner solved this by setting `tty=False` in
`RunSpec`, sacrificing colors. Part B needs BOTH colors AND no staircase.

**Decision:** Use a pseudo-terminal (PTY) as the parent-side terminal for
Docker's stdout:

```
┌─────────────────────────────────────────────────────────────────┐
│  Host (Python)                                                  │
│  ┌─────────────────┐                                            │
│  │  PTY master fd  │ ◄─── os.read() loop ─── decode ─── lines   │
│  └────────┬────────┘                                            │
│           │ (real terminal)                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  docker run -t ... (Popen stdout=slave, stderr=slave)       ││
│  │  └─────────────────────────────────────────────────────────┘│
│  │                         │                                    │
│  │           Container sees a tty → Odoo emits ANSI colors      │
│  │           Docker stdout is a tty → ONLCR line discipline     │
│  │                         ▼                                    │
│  │           No staircase + Colors preserved                    │
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Layer 1 (Docker sees a terminal):** The PTY slave fd becomes the stdout/stderr
for `Popen`. Docker's stdout is attached to a real terminal, so the kernel's
line discipline translates `\n` to `\r\n` (ONLCR). No staircase.

**Layer 2 (Odoo sees a terminal):** The `-t` flag in `docker run` allocates a
pseudo-tty for the container. Odoo's `isatty()` returns True, so it emits ANSI
color codes.

**PTY loop specification:**

```python
def _stream_lines(self, cmd: list[str]) -> Iterator[str]:
    master, slave = pty.openpty()
    try:
        process = subprocess.Popen(
            cmd,
            stdout=slave,
            stderr=slave,
            close_fds=True,
            # stdin defaults to DEVNULL when not a tty
        )
        os.close(slave)  # Close slave in parent after spawn

        buffer = b""
        while True:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                # EIO on child exit — treat as EOF, not error
                break
            if not chunk:
                break
            buffer += chunk
            # Split on newlines, keep partial in buffer
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                yield line.decode("utf-8", errors="replace")

        # Yield any remaining partial line
        if buffer:
            yield buffer.decode("utf-8", errors="replace")

        process.wait()
        self._exit_code = process.returncode
    finally:
        os.close(master)
```

**Critical PTY behaviors:**

1. `pty.openpty()` returns `(master, slave)` file descriptors.
2. `Popen(stdout=slave, stderr=slave)` attaches the child's output to the PTY.
3. `os.close(slave)` in the parent after spawn — the child holds its own fd.
4. `os.read(master, N)` blocks until data or EOF.
5. **EIO on child exit:** Reading a PTY master raises `OSError` with `errno.EIO`
   when the child exits and the slave side closes. This is NOT an error — it's
   the normal EOF signal for PTY reads. MUST be caught and treated as EOF.
6. Decode with `errors='replace'` for robustness against broken UTF-8.
7. Buffer partial lines; split on `\n`; yield complete lines.

**Platform constraint:** `pty` module is POSIX-only. This is acceptable because:

- The tool orchestrates Docker, which requires Linux or macOS.
- Windows users would use WSL, which provides POSIX APIs.

**Rationale:**

- This is the only way to get both colors and no staircase simultaneously.
- The CI runner can stay on `tty=False` + PIPE (no colors, no staircase) —
  different execution model, no pty needed there.

---

### ADR-3: Zero-Tests Decision Algorithm

**Context:** Odoo emits `0 failed, 0 error(s) of N tests` summary lines. When
`oe -Q` runs with both `-i` (install) and `-u` (update) phases, there may be
multiple summary lines. A module may exist on disk but have an empty `tests/`
directory (or tests that aren't discovered), resulting in "0 tests collected"
which should be an error only if the module has a `tests/` directory.

**Decision:** Use aggregate counting with a testable-modules precondition:

```
┌───────────────────────────────────────────────────────────────────────┐
│  Zero-Tests Decision Algorithm                                        │
├───────────────────────────────────────────────────────────────────────┤
│  INPUTS:                                                              │
│    - lines: all streamed output lines                                 │
│    - any_requested_has_tests: bool (from OdooEnv.qa preprocessing)    │
│    - exit_code: process exit code                                     │
│    - failure_detected: bool (any is_error_line match)                 │
│                                                                       │
│  ALGORITHM:                                                           │
│    1. aggregate = sum(parse_test_count(line) for line in lines        │
│                       if parse_test_count(line) is not None)          │
│                                                                       │
│    2. IF failure_detected:                                            │
│         → ABORT with "Test failure detected" ERROR                    │
│         (failure-line gate fires BEFORE zero-tests check)             │
│                                                                       │
│    3. IF exit_code != 0:                                              │
│         → ABORT with "Odoo exited with code {exit_code}" ERROR        │
│                                                                       │
│    4. IF aggregate == 0 AND any_requested_has_tests:                  │
│         → ABORT with "0 tests collected" ERROR (REQ-QAJ-002)          │
│                                                                       │
│    5. ELSE:                                                           │
│         → PASS (success)                                              │
└───────────────────────────────────────────────────────────────────────┘
```

**Key behaviors:**

- `aggregate` is the SUM of all `parse_test_count` matches across the entire
  stream. Handles multiple summary lines from `-i` and `-u` phases.
- `parse_test_count(line)` returns `None` for non-summary lines. These do NOT
  contribute 0 to the aggregate — they are ignored.
- If no summary line is seen at all, `aggregate == 0`. The zero-tests gate
  still requires `any_requested_has_tests` to fire.
- `any_requested_has_tests` is a bool computed by `OdooEnv.qa()` BEFORE
  building the `QaCommand`. It answers: "does at least one of the requested
  modules have a `tests/` subdirectory?"

**Rationale:**

- Aggregation handles the multi-phase case correctly (e.g., `of 0 tests` from
  `-i` phase + `of 5 tests` from `-u` phase = 5 total, not 0).
- The `any_requested_has_tests` check prevents false positives when testing
  modules that legitimately have no tests.
- Failure-line detection is an INDEPENDENT gate that fires immediately,
  separate from the zero-tests check.

---

### ADR-4: Modules-with-Tests Threading

**Context:** To evaluate the zero-tests criterion, we need to know whether
any requested module has a `tests/` directory. This must be computed in
`OdooEnv.qa()` where we know the requested modules, then threaded to
`QaCommand` where the judgment happens.

**Decision:** Compute `any_requested_has_tests: bool` in `OdooEnv.qa()` and
pass it to `QaCommand` via constructor:

```
┌─────────────────────────────────────────────────────────────────────┐
│  OdooEnv.qa(modules_to_test)                                        │
│    │                                                                │
│    ├─► modules_list = resolve requested modules                     │
│    │                                                                │
│    ├─► testable_requested = [                                       │
│    │       m for m in modules_list                                  │
│    │       if (Path(custom_modules_dir) / m / "tests").is_dir()     │
│    │   ]                                                            │
│    │                                                                │
│    ├─► any_requested_has_tests = bool(testable_requested)           │
│    │                                                                │
│    └─► return EnvironmentManager.qa(                                │
│            database, install_modules, update_modules,               │
│            any_requested_has_tests=any_requested_has_tests          │
│        )                                                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  EnvironmentManager.qa(..., any_requested_has_tests)                │
│    │                                                                │
│    └─► return [QaCommand(                                           │
│            parent,                                                  │
│            command=docker_cmd_list,                                 │
│            usr_msg=...,                                             │
│            any_requested_has_tests=any_requested_has_tests          │
│        )]                                                           │
└─────────────────────────────────────────────────────────────────────┘
```

**Data shape:** A simple `bool` is sufficient for the criterion. The spec
only requires knowing IF any requested module has tests, not WHICH ones.
However, for a better error message, we could pass the set of testable modules:

```python
# Option A: minimal (bool only)
any_requested_has_tests: bool

# Option B: richer error message (set)
testable_requested: set[str]  # then bool(testable_requested) for criterion
```

**Decision:** Use Option A (`bool`) for simplicity. The error message can say
"0 tests collected but at least one requested module has a tests/ directory"
without naming which one.

**Rationale:**

- Follows the existing pattern: `OdooEnv.qa()` does preprocessing, then
  delegates to `EnvironmentManager.qa()` with the results.
- The testability check reuses `Path.is_dir()` — simple and direct.
- No need for a separate `discover_testable_modules()` helper; inline loop
  suffices.

---

### ADR-5: parse_test_count Location and Shape

**Context:** We need a parser for Odoo's `of N tests` summary line, placed
alongside the existing `is_error_line` in `odoo_env/qa/failures.py`.

**Decision:** Add `parse_test_count` to `odoo_env/qa/failures.py`:

```python
# Pattern for Odoo's test summary line: "0 failed, 0 error(s) of 5 tests"
# Matches "of <N> tests" after ANSI stripping.
TEST_COUNT_PATTERN = re.compile(r"of (\d+) tests")


def parse_test_count(line: str) -> int | None:
    """Extract the test count from an Odoo test summary line.

    Returns the integer N for a line containing "of N tests", or None if
    the line is not a summary line. ANSI escape sequences are stripped
    before matching (consistent with is_error_line).

    Examples:
        "0 failed, 0 error(s) of 5 tests" → 5
        "INFO: Modules loaded." → None
    """
    match = TEST_COUNT_PATTERN.search(strip_ansi(line))
    return int(match.group(1)) if match else None
```

**Consistency with is_error_line:**

- Both strip ANSI escapes before matching.
- Both use compiled regex patterns at module level.
- Both return a simple result (bool vs int|None).

**Rationale:**

- Co-locating parsers in `failures.py` keeps detection logic together.
- `strip_ansi` is reused from the existing code.
- Returning `None` (not 0) for non-matches prevents aggregation bugs.

---

### ADR-6: TTY Enablement for QaCommand

**Context:** The current `EnvironmentManager.qa()` sets `tty=sys.stdin.isatty()`
for the docker command. The CI runner sets `tty=False` explicitly. Part B
needs `tty=True` for the docker `-t` flag so Odoo emits colors, but the PTY
provides the terminal to docker (not stdin).

**Decision:** For `QaCommand`, always request `tty=True` in `RunSpec`:

```
┌───────────────────────────────────────────────────────────────────────┐
│  TTY Layers (Part B QaCommand)                                        │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Parent Process (oe -Q)                                              │
│   ├── PTY master fd ◄──────────────── os.read() loop                  │
│   │                                                                   │
│   └── Popen(                                                          │
│           cmd=["docker", "run", "-t", ...],  # RunSpec.tty=True       │
│           stdout=slave,  # PTY slave fd                               │
│           stderr=slave                                                │
│       )                                                               │
│                                                                       │
│   Docker sees:                                                        │
│     stdout → PTY slave fd → isatty() = True                           │
│     → Docker runs with -t                                             │
│     → Container gets pseudo-tty                                       │
│     → Odoo sees tty → emits colors                                    │
│                                                                       │
│   PTY provides:                                                       │
│     ONLCR line discipline → \n → \r\n translation                     │
│     → No staircase effect                                             │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

**RunSpec changes for QaCommand path:**

- `tty=True` (always, regardless of `sys.stdin.isatty()`)
- `interactive=True` (for `-it` flag combination)

**Why sys.stdin.isatty() no longer matters:**

- The PTY provides the terminal for docker's stdout, not stdin.
- The parent's stdin being a tty or not is irrelevant for the color/staircase
  problem — that's about stdout.
- The PTY master/slave pair is created regardless of parent's stdin.

**Reconciliation with current code:**

- Current: `tty = sys.stdin.isatty()` in `EnvironmentManager.qa()`
- Change: When returning `QaCommand`, always build `RunSpec` with `tty=True`
- The `QaCommand.execute()` overrides `Command.execute()` entirely, so the
  `subprocess_call` path (which uses `subprocess.run`) is not invoked.

**Rationale:**

- The PTY execution is orthogonal to stdin being a tty.
- `tty=True` ensures the `-t` flag is passed to docker.
- The PTY provides the real-terminal line discipline (no staircase).
- This is specific to `QaCommand`; other paths keep existing behavior.

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  oe -Q my_module                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OdooEnv.qa(modules_to_test="my_module")                                │
│  ├─► Resolve modules_list = ["my_module"]                               │
│  ├─► Check modules exist on disk                                        │
│  ├─► Check test DB exists                                               │
│  ├─► Query installed modules from DB                                    │
│  ├─► Partition: install_modules, update_modules                         │
│  ├─► NEW: testable = [m for m if has tests/]                            │
│  ├─►       any_requested_has_tests = bool(testable)                     │
│  └─► return EnvironmentManager.qa(db, install, update,                  │
│              any_requested_has_tests)                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  EnvironmentManager.qa(db, install_modules, update_modules,             │
│                        any_requested_has_tests)                         │
│  ├─► Build RunSpec(tty=True, ...) for docker command                    │
│  ├─► docker_cmd = docker_client.get_run_command(spec)                   │
│  └─► return [QaCommand(parent, command=docker_cmd, usr_msg=...,         │
│              any_requested_has_tests=any_requested_has_tests)]          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OdooEnv.execute(commands)                                              │
│  └─► for command in commands: command.execute()                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  QaCommand.execute()                                                    │
│  ├─► lines = self._stream_lines(self.command)  # PTY I/O                │
│  ├─► verdict = self._judge_stream(lines, self._any_has_tests)           │
│  ├─► exit_code = self._exit_code  # set by _stream_lines                │
│  └─► Apply final decision logic; raise on FAIL/ZERO_TESTS               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Changes

| File | Change |
|------|--------|
| `odoo_env/command.py` | Add `QaCommand(Command)` subclass with PTY-based `execute()`, `_stream_lines()` seam, `_judge_stream()` pure method. |
| `odoo_env/qa/failures.py` | Add `parse_test_count(line) -> int \| None` and `TEST_COUNT_PATTERN` regex. |
| `odoo_env/managers/environment_manager.py` | Modify `qa()` to accept `any_requested_has_tests` and return `QaCommand` instead of plain `Command`. Set `RunSpec.tty=True`. |
| `odoo_env/odooenv.py` | Modify `qa()` to compute `any_requested_has_tests` from requested modules and pass to `EnvironmentManager.qa()`. |
| `odoo_env/test_create_test_db.py` | Add tests for `QaCommand._judge_stream()` with synthetic lines (PASS, FAIL, ZERO_TESTS scenarios), `parse_test_count()`, and `any_requested_has_tests` threading. |

---

## Contracts

### QaCommand Constructor

```python
class QaCommand(Command):
    """QA test runner with PTY streaming and judgement (REQ-QAJ-001..007).

    Overrides execute() to:
    1. Run docker through a PTY (colors + no staircase)
    2. Stream and reprint output line-by-line
    3. Detect test failures via is_error_line
    4. Aggregate test counts via parse_test_count
    5. Abort on failure or zero-tests condition
    """

    def __init__(
        self,
        parent,
        command: list[str],
        usr_msg: str,
        any_requested_has_tests: bool,
    ):
        super().__init__(parent, command=command, usr_msg=usr_msg)
        self._any_requested_has_tests = any_requested_has_tests
        self._exit_code: int | None = None
```

### QaVerdict Enum

```python
from enum import Enum, auto

class QaVerdict(Enum):
    """Result of QA stream judgment."""
    PASS = auto()
    FAIL_LINE = auto()      # is_error_line detected
    ZERO_TESTS = auto()     # aggregate == 0 and any_has_tests
```

### _judge_stream Signature

```python
def _judge_stream(
    self,
    lines: Iterable[str],
    any_has_tests: bool,
) -> QaVerdict:
    """Consume lines, reprint to stdout, detect failures/counts.

    Pure method — testable with synthetic input.
    Does NOT check exit_code; that's execute()'s responsibility.
    """
```

### EnvironmentManager.qa Signature

```python
def qa(
    self,
    database: str,
    install_modules: list[str],
    update_modules: list[str],
    *,
    any_requested_has_tests: bool = False,
) -> list[Command]:
    """Build QA test command with PTY streaming and judgement."""
```

### parse_test_count Signature

```python
def parse_test_count(line: str) -> int | None:
    """Extract test count from Odoo summary line, or None if not a summary."""
```

---

## Test Strategy

### Unit Tests for Pure Logic

**_judge_stream tests** (no Docker, no PTY):

```python
class TestJudgeStream(unittest.TestCase):
    """Tests for QaCommand._judge_stream() (REQ-QAJ-001..005)."""

    def test_pass_with_tests_collected(self):
        """Non-zero aggregate + no failure → PASS."""
        lines = [
            "INFO: Loading modules...",
            "0 failed, 0 error(s) of 5 tests",
        ]
        cmd = self._make_qa_command(any_has_tests=True)
        verdict = cmd._judge_stream(iter(lines), any_has_tests=True)
        self.assertEqual(verdict, QaVerdict.PASS)

    def test_fail_line_aborts(self):
        """is_error_line match → FAIL_LINE verdict."""
        lines = [
            "INFO: Running tests...",
            "2026-01-01 00:00:00,000 1 ERROR test_db odoo.x: FAIL: TestX.test_y",
            "0 failed, 1 error(s) of 5 tests",
        ]
        cmd = self._make_qa_command(any_has_tests=True)
        verdict = cmd._judge_stream(iter(lines), any_has_tests=True)
        self.assertEqual(verdict, QaVerdict.FAIL_LINE)

    def test_zero_tests_with_tests_dir_aborts(self):
        """aggregate==0 + any_has_tests → ZERO_TESTS verdict."""
        lines = [
            "INFO: Installing module...",
            "0 failed, 0 error(s) of 0 tests",
        ]
        cmd = self._make_qa_command(any_has_tests=True)
        verdict = cmd._judge_stream(iter(lines), any_has_tests=True)
        self.assertEqual(verdict, QaVerdict.ZERO_TESTS)

    def test_zero_tests_without_tests_dir_passes(self):
        """aggregate==0 + NOT any_has_tests → PASS."""
        lines = [
            "INFO: Installing module...",
            "0 failed, 0 error(s) of 0 tests",
        ]
        cmd = self._make_qa_command(any_has_tests=False)
        verdict = cmd._judge_stream(iter(lines), any_has_tests=False)
        self.assertEqual(verdict, QaVerdict.PASS)

    def test_aggregates_multiple_summary_lines(self):
        """Sums counts from multiple of N tests lines."""
        lines = [
            "0 failed, 0 error(s) of 2 tests",  # -i phase
            "0 failed, 0 error(s) of 3 tests",  # -u phase
        ]
        # aggregate = 5 (not 3), so not zero-tests
        cmd = self._make_qa_command(any_has_tests=True)
        verdict = cmd._judge_stream(iter(lines), any_has_tests=True)
        self.assertEqual(verdict, QaVerdict.PASS)
```

**parse_test_count tests:**

```python
class TestParseTestCount(unittest.TestCase):
    """Tests for parse_test_count (REQ-QAJ-005)."""

    def test_summary_line_returns_count(self):
        self.assertEqual(parse_test_count("0 failed, 0 error(s) of 5 tests"), 5)

    def test_zero_tests_returns_zero(self):
        self.assertEqual(parse_test_count("0 failed, 0 error(s) of 0 tests"), 0)

    def test_non_summary_returns_none(self):
        self.assertIsNone(parse_test_count("INFO: Modules loaded."))

    def test_ansi_stripped_before_match(self):
        line = "\x1b[32m0 failed, 0 error(s) of 7 tests\x1b[0m"
        self.assertEqual(parse_test_count(line), 7)
```

**any_requested_has_tests threading tests:**

```python
class TestAnyRequestedHasTests(unittest.TestCase):
    """Tests for modules-with-tests computation in OdooEnv.qa()."""

    def test_module_with_tests_dir_sets_flag_true(self):
        # Mock filesystem: my_module/tests/ exists
        ...

    def test_module_without_tests_dir_sets_flag_false(self):
        # Mock filesystem: my_module/ has no tests/ subdir
        ...

    def test_flag_threaded_to_qa_command(self):
        # Verify QaCommand receives the flag from EnvironmentManager.qa()
        ...
```

### PTY Seam Tests

```python
class TestPtySeam(unittest.TestCase):
    """Tests for _stream_lines seam (mocked, no real PTY)."""

    def test_stream_lines_override_for_testing(self):
        """Verify the seam can be overridden with canned lines."""
        cmd = QaCommand(parent, command=["docker", "..."], ...)

        # Override the seam
        def fake_stream_lines(command):
            yield "INFO: Loading..."
            yield "0 failed, 0 error(s) of 3 tests"
            cmd._exit_code = 0

        cmd._stream_lines = fake_stream_lines
        cmd.execute()
        # Verify no exception (PASS case)
```

---

## Rollout Considerations

1. **Backward compatibility:** The change is additive. `QaCommand` is a new
   subclass; reverting `EnvironmentManager.qa()` to return plain `Command`
   restores Part A behavior.

2. **Visual verification:** The no-staircase + colors guarantees must be
   validated by a manual real run on a Docker environment before merge.
   Unit tests verify the logic but cannot prove PTY terminal behavior.

3. **CI impact:** The CI runner (`TestRunner`) is unchanged. It continues
   to use `tty=False` + PIPE (no colors, but also no PTY complexity).

4. **Platform:** POSIX-only (`pty` module). Document this in the code.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| PTY execution near historical staircase bug | ADR-2 specifies exact PTY mechanics; manual verification before merge |
| PTY portability / testability | ADR-1 seam isolates PTY I/O; tests mock the seam |
| False positive on zero-tests | ADR-3 aggregation + `any_requested_has_tests` precondition |
| EIO not caught → spurious error | ADR-2 explicitly specifies EIO handling as EOF |
| Executor divergence from CI runner | Shared parsers (`is_error_line`, `parse_test_count`) |

---

## References

- **Proposal:** `openspec/changes/qa-zero-tests-error/proposal.md`
- **Spec:** `openspec/changes/qa-zero-tests-error/specs/qa-judgement/spec.md`
- **Staircase fix:** Commit 44382f1 (issue #126)
- **Existing patterns:** `TestRunner._run_one` (streaming loop), `Command` subclass pattern
