---
name: odoo-tests
description: Guide for writing and improving Odoo tests.
context: fork
---

# Odoo Tests Skill

Purpose: Write, improve, and refactor Odoo module tests following local OCA-style testing patterns.

## When to Use

Use this skill when the task involves:
- Writing new tests for module behavior
- Improving coverage for models, workflows, wizards or access rules
- Fixing broken test code
- Refactoring or adapting tests

Use a test execution skill when the task is primarily about running tests:
- `odoo-tests-run-docker` for CI-parity execution inside docker or podman
- `odoo-tests-run-local` when a working local Odoo installation is already available

## Test File Structure

Odoo tests must follow the OCA convention:
- Place test files in `<module>/tests/` directory
- Test files must be named `test_*.py`
- The `tests/__init__.py` must import all test modules

Example test structure:
```
my_module/
├── tests/
│   ├── __init__.py    # imports test_my_module
│   └── test_my_module.py
```

## Core Rules

- Use Odoo's test framework, not pytest
- Prefer `TransactionCase` or an existing domain-specific base class
- Use `setUpClass` for expensive shared fixtures
- Never depend on demo data
- Fix test code first when failures are caused by bad fixtures or wrong expectations
- Do not weaken implementation to satisfy tests

## Test Design Guidance

### Preferred Patterns
- Reuse an existing local base class before introducing a new one
- Use `Form(...)` for wizard flows and onchange-driven UI behavior
- Add docstrings to test methods
- Assert on business outcomes, not only raw field values
- Mock external HTTP calls narrowly with `unittest.mock.patch`

### What to Cover
- Create/write/unlink flows where business logic exists
- Constraints and validation errors
- Access rights and record rules
- Workflow transitions and side effects
- Wizard execution and returned actions
- Computed fields and onchange behavior
- Cron-triggered or scheduled effects when relevant

## Execution Handoff

After writing or updating tests, pick the correct execution skill:

1. Use `odoo-tests-run-docker` when you need CI parity or do not have a trusted local Odoo installation.
2. Use `odoo-tests-run-local` only when the environment already provides a working Odoo installation, database access, and the required addons path.

Keep command syntax and rerun strategy inside the execution skills instead of duplicating them here.

## Local Conventions

- Align with neighboring tests in the target module first
- Prefer concise but explicit fixtures
- Use `self.env.ref(...)` only for stable dependency XML IDs
- Avoid broad factory abstractions unless the suite already uses them
- Disable tracking in test context when noise or performance matters

## Output Expectations

After using this skill, provide:
- Test files added or changed
- Scenarios now covered
- Any follow-up execution step that still needs to run