---
name: odoo-tests-run-docker
description: Run Odoo tests in docker or podman using the repository workflow script.
context: fork
---

# Odoo Tests Run Docker Skill

Purpose: Execute Odoo tests inside docker or podman using the repository workflow script for CI-parity runs.

## When to Use

Use this skill when the task involves:
- Running tests and no trusted local Odoo installation is available
- Reproducing CI behavior as closely as possible
- Validating changes before merge with container-based tooling

Prefer this skill over local execution unless the user explicitly has a working local Odoo installation that should be used.

## Execution Rules

Use the workflow script as the single entrypoint for container-based test execution.

Default command:

```bash
bash ./scripts/run-test-workflow.sh
```

This script replays the provided `test.yml` test job on the local working tree and runs the same command order used in CI:

1. `oca_install_addons`
2. `manifestoo -d . check-licenses` 
3. `manifestoo -d . check-dev-status --default-dev-status=Beta`
4. `oca_init_test_database`
5. `oca_run_tests`

The script provisions PostgreSQL with workflow-compatible credentials and runs inside the OCA CI image with `OCA_ENABLE_CHECKLOG_ODOO=1`.

## Script Options

- Run both matrix images (Odoo + OCB):

```bash
bash ./scripts/run-test-workflow.sh --with-ocb
```

- Restrict tests to one module:

```bash
bash ./scripts/run-test-workflow.sh --include <module>
```

- Override the test database name:

```bash
bash ./scripts/run-test-workflow.sh --db <database>
```

- Override the Python version:

```bash
bash ./scripts/run-test-workflow.sh --python-version <python_version>
```

- Override the Odoo version:

```bash
bash ./scripts/run-test-workflow.sh --odoo-version <odoo_version>
```

## Iteration Rules

- Start with the default command while iterating.
- Use `--include <module>` to narrow scope when appropriate.
- Use `--with-ocb` before final validation when CI parity is needed.
- If dependency or manifest checks fail, rerun from the default script command after fixing the issue.
- If only test logic changed, rerun the same command first, then broaden scope if required.

## Runtime Expectations

- Do not run `oca_export_and_push_pot` from this workflow.
- Keep "Detect unreleased dependencies" as an optional, separate local precheck when needed.
- If the script reports that neither docker nor podman is available, stop and use `odoo-tests-run-local` only if a working local Odoo installation is already present.

## Failure Handling

For each failure:
1. Read the traceback fully.
2. Ignore "Detect unreleased dependencies" failures.
3. Decide whether the problem is fixture setup, expectation mismatch, or a real bug.
4. Fix the narrowest issue.
5. Re-run the same workflow command with the narrowest useful flags.
6. Repeat until green or until a genuine implementation defect is isolated.

## Output Expectations

After using this skill, provide:
- Exact command run
- Modules or scope tested
- Pass/fail result summary
- Container/runtime blockers if execution could not start