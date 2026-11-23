# c4a8-odoo-plugins

Claude Code plugin marketplace for C4A8 Odoo development. This repository is the
**single authoritative source** for AI/agent tooling — agents, skills, and rule
packs used across the Odoo workspaces. AI tooling found anywhere else
(`c4a8-odoo/.github`, old workspace copies) is legacy; the one exception is
`.github/copilot-commit-message-instructions.md` in the dev-volume workspace.

## Install

In Claude Code:

```
/plugin marketplace add c4a8-odoo/llm-plugin
/plugin install odoo-development@c4a8-odoo-plugins
/plugin install odoo-oca-automation@c4a8-odoo-plugins
```

## Plugins

| Plugin | In marketplace | Purpose |
|---|---|---|
| `odoo-development` | yes | Odoo development, review, testing, documentation, and migration agents/skills with per-version rule packs (16.0–19.0). |
| `odoo-oca-automation` | yes | Skills for OCA contribution work: PR reviews, module migrations, commit ports, module improvements, each closed by a local security review. Runnable interactively or from an automation. |
| `odoo-review` | no | Empty stub, reserved. |
| `test-plugin` | no | Smoke-test scaffolding for plugin loading. Not for daily use. |

## odoo-development contents

- **Agents**: `odoo` (development orchestrator), `odoo-migration` (version
  migration orchestrator), `odoo-pr-commit-cleanup` (PR commit-history cleanup),
  `odoo-app-list` (sorts module technical names into the `*_modules.txt` lists).
- **Skills**: `odoo-coding`, `odoo-coding-review`, `odoo-documentation`,
  `odoo-migrate-module`, `odoo-module-scaffold`, `odoo-tests`,
  `odoo-tests-run-docker`, `odoo-tests-run-local`.
- **Rule packs**: `skills/odoo-coding-review/resources/code-rules-*.yaml`
  (cumulative per version) and
  `skills/odoo-migrate-module/resources/migration-rules-*.yaml` (per version hop).

## odoo-oca-automation contents

| Skill | What it does |
|---|---|
| `odoo-task-core` | Shared contract read first by every other skill: arguments, run modes, task log layout, OCA conventions, shared PR-review frame, mandatory closing security review. |
| `odoo-pr-review` | Structural PR review: commit messages and PR title, one change per commit/PR, manifest, CI pipeline, style beyond pre-commit, README fragments. |
| `odoo-code-review` | Functional PR review: does the change work, ORM/API correctness, access rights, migration scripts, meaningful tests, fit with the OCA ecosystem. |
| `odoo-module-migration` | Migrates a module to the next Odoo version following the OCA `[MIG]` process. |
| `odoo-commit-porting` | Forward-/backports commits or merged PRs between version branches (`cherry-pick -x` / `oca-port`); without `commits` it discovers unported work. |
| `odoo-module-improvement` | Fix, feature, tests, docs, performance, CI or hardening change on an existing module, with commit tag and bump-size recommendation. |
| `odoo-security-review` | Local-only security analysis of a module; runs last in every task. Never posts to GitHub. |

A plain "review this PR" runs `odoo-pr-review` first, then `odoo-code-review` on
the same head SHA, with a single security review at the end.

### Arguments

Skills take `key=value` arguments. There is **no configuration file** and nothing
is inferred: the caller passes everything explicitly.

- Task inputs: `mode`, `version`, `repo`, `github` (default `OCA/<repo>`), `module`,
  `pr`, `source_version`, `commits` (`sha,sha` or `pr:<n>`), `issue`, `task`,
  `workdir` (default `work/<repo>`).
- Policy inputs (safe defaults): `fork_owner` (authenticated `gh` user),
  `allow_approve` (`false`), `allow_request_changes` (`false`),
  `block_full_on_severity` (`high`), `security_min_severity` (`medium`),
  `log_root` (`logs`), `security_root` (`security`).

Each skill names its required inputs; a missing one is asked for once
(interactive) or ends the run as `blocked` (non-interactive).

Example:

```
/odoo-oca-automation:odoo-code-review mode=draft version=19.0 repo=partner-contact pr=1234
```

### Modes

| Mode | Allowed |
|---|---|
| `plan` (default) | Read-only; writes markdown under the log folder. |
| `draft` | Local edits, commits, push to the fork, **draft** PRs, **pending** reviews. |
| `full` | Submitted reviews, ready PRs, comments. Never merges; approves or requests changes only when `allow_approve` / `allow_request_changes` is set. An introduced security finding at or above `block_full_on_severity` downgrades the run to draft. |

### Outputs

- Task log: `logs/<version>/<repo>/<module>/<pr>/<yyyy-mm-dd>_<HHMM>_<task>.md`
  (`<pr>` is `pr-<n>`, `local-<branch>` or `no-pr`).
- Security report next to the task log; findings at or above
  `security_min_severity` under `security/<version>/<repo>/<module>/`.
- Helper: `skills/odoo-task-core/scripts/automation.py` (`log-init`,
  `log-finish`, `log-move`, `finding`; Python 3 standard library only) with an
  `automation.ps1` wrapper for PowerShell.

Commits created with AI help carry an `Assisted-by:` trailer, not
`Co-Authored-By:`. The manifest version is not bumped in PRs; the OCA bot bumps it
on merge (`ocabot merge patch|minor|major|nobump`).

## Releasing changes

1. Bump the plugin `version` in `plugins/<name>/plugin.json` **and** its entry in
   both marketplace files, `.claude-plugin/marketplace.json` and
   `.github/plugin/marketplace.json` (keep all three identical; the two
   marketplace files are regular copies, not a symlink).
2. Bump `metadata.version` in both marketplace files when the marketplace itself
   changes (plugins added or removed).
3. Users pick the change up by updating the marketplace and reinstalling/updating
   the plugin in Claude Code.

`docs/legacy-odoo-development-skill.md` preserves the removed `odoo-development`
skill for reference — it documents the workspace conventions (module repo
layout, version policy, author string).
