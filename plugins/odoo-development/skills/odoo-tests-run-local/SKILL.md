---
name: odoo-tests-run-local
description: Run Odoo tests against an existing local Odoo installation when already running inside a docker container.
context: fork
---

# Odoo Tests Run Local Skill

Purpose: Execute Odoo tests against an already available local Odoo installation when docker-based execution is not the right fit.

## When to Use

Use this skill when the task involves:
- Running tests in a workstation or VM that already has Odoo installed
- Iterating on tests with a known local database and addons path
- Using existing local launch/configuration conventions instead of containerized CI parity

Do not use this skill unless the environment already provides:
- A working Odoo executable or repository-specific launcher
- A known addons path
- Database access for the target test database

## Execution Rules

- Prefer repository-provided local commands or existing developer documentation first.
- If no repo-specific wrapper exists, use the installed Odoo executable already configured in the environment.
- Do not invent missing addons paths, config files, or database names.
- Keep the test target as narrow as possible while iterating.

Typical local execution shapes:

```bash
/usr/bin/python3 /src/odoo/odoo-bin --config=/src/config/odoo.conf --addons-path=<addons_path> -d <database> -i <module> --test-enable --test-tags /<module> --stop-after-init
```

For an already installed module under test, prefer update over install when appropriate:

```bash
/usr/bin/python3 /src/odoo/odoo-bin --config=/src/config/odoo.conf --addons-path=<addons_path> -d <database> -u <module> --test-enable --test-tags /<module> --stop-after-init
```

If the local environment uses `odoo-bin`, a wrapper script, or a config file, adapt the command to that existing setup rather than normalizing it.

## Iteration Rules

- Re-run the narrowest module or test tag first.
- Reuse the same local database unless the failure indicates a dirty or incompatible state.
- If failures point to environment drift rather than code, stop and report the blocker instead of switching implicitly to docker.

## Failure Handling

For each failure:
1. Read the traceback fully.
2. Distinguish environment/configuration failures from real test failures.
3. Fix only the narrowest code or fixture issue when the failure is actionable.
4. Re-run the same local command with the narrowest useful scope.
5. Escalate when the environment itself is incomplete or inconsistent.

## Output Expectations

After using this skill, provide:
- Exact local command run
- Local Odoo executable or launcher used
- Database and module scope tested
- Pass/fail result summary
- Environment blockers if execution could not proceed