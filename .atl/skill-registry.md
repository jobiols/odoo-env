# Skill Registry — odoo-env

Generated: 2026-04-12

## User Skills

| Skill | Trigger |
|-------|---------|
| branch-pr | When creating a pull request, opening a PR, or preparing changes for review |
| go-testing | When writing Go tests, using teatest, or adding test coverage *(not applicable — Python project)* |
| issue-creation | When creating a GitHub issue, reporting a bug, or requesting a feature |
| judgment-day | When user says "judgment day", adversarial review, dual review |
| skill-creator | When user asks to create a new skill or document patterns for AI |

## SDD Skills (auto-managed by orchestrator)

sdd-explore, sdd-propose, sdd-spec, sdd-design, sdd-tasks, sdd-apply, sdd-verify, sdd-archive, sdd-init, sdd-onboard

## Project Conventions

- Global instructions: `~/.claude/CLAUDE.md`
- No project-level CLAUDE.md found
- Architecture: Command pattern — new behaviors go in `command.py` as subclasses
- Tests: `PYTHONPATH=. venv/bin/python -m unittest discover -s odoo_env -p "test_*.py"`

## Compact Rules

### branch-pr
Create branch from issue number. PR title = "feat/fix: short description (#issue)". Body: Summary + Test plan.

### issue-creation
Issue title = type + short description. Body: context, expected vs actual, steps to reproduce.

### judgment-day
Launch two blind judge sub-agents simultaneously. Synthesize findings. Apply fixes. Re-judge until both pass or escalate after 2 iterations.

### skill-creator
Follow Agent Skills spec. Include: purpose, trigger, execution contract, rules, return format.
