# Archive Report — qa-coverage-ci

## Status

Archived. All implementation tasks in `tasks.md` are complete (`[x]`), the
engine and CLI ship in `odoo_env/qa/`, and the CI template ships under
`templates/ci/`.

## Delivered

- `odoo_env/qa/` engine: `failures.py`, `config.py`, `threshold.py`,
  `runner.py`, `__main__.py` (CLI entrypoint).
- `oe --test-all` and `oe -Q all` (auto-discovery of every module with a
  `tests/` folder).
- CI template: `templates/ci/tests.yml`, `.coverage-threshold`,
  `README-badge.md`.
- Post-delivery hardening (v0.16.7): `-Q all`, `--create-test-db` guards
  (seed-first check, `test.zip` overwrite confirm), parameterized
  `_db_exists` SQL, `--with-demo` on Odoo >=19, and CWD-independent
  `--create-test-db` via `Client.custom_modules_dir`.

## Spec consolidation

The `qa-coverage` capability delta was consolidated into
`openspec/specs/qa-coverage/spec.md`.

## Notes

- The `qa-coverage` engine discovery is intentionally CWD-based
  (`TestRunner` scans the current repo). `--create-test-db` is the
  exception: it resolves modules from `Client.custom_modules_dir` and is
  CWD-independent (see `openspec/specs/create-test-db/spec.md`).
