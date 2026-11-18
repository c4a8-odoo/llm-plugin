---
name: odoo-task-core
description: Shared contract for every Odoo/OCA automation skill (odoo-code-review, odoo-module-migration, odoo-commit-porting, odoo-module-improvement, odoo-security-review). Defines the run modes plan/draft/full, the scope gate against config/automation.yaml, the task log layout logs/<odoo_version>/<repo>/<module>/<pr>/, argument parsing, OCA commit and PR conventions, and the mandatory closing security review. Read this FIRST whenever any odoo-* skill runs, whenever the user mentions automation modes, task logs, scope configuration, OCA conventions, or asks how an Odoo automation should behave.
---

# Odoo task core

Every Odoo/OCA task skill in this project is a workflow built on the same frame. This skill
is that frame. Task skills do not repeat it; they say "follow odoo-task-core" and then describe
only what is specific to them. If you are running a task skill, do the steps below in order.

## 1. Lifecycle of a task

1. Parse the arguments (section 2) and resolve the mode (section 3).
2. Run the scope gate (section 4). Out of scope means: write a skipped log, stop.
3. Initialise the task log (section 5) before doing any real work, so a crash still leaves a trace.
4. Do the work the task skill describes, respecting the mode.
5. Run the `odoo-security-review` skill on the module (section 7). Always, in every mode.
6. Finish the log: status, summary, links, follow-ups.

## 2. Arguments

Skills receive `key=value` tokens, in any order. Unknown keys are kept and shown in the log.

| key | meaning | example |
|---|---|---|
| `mode` | `plan`, `draft` or `full` | `mode=draft` |
| `version` | Odoo version the change lands on (target branch) | `version=19.0` |
| `repo` | repo name as listed in the config scope | `repo=partner-contact` |
| `module` | technical module name | `module=partner_firstname` |
| `pr` | PR number in the upstream repo, if one exists | `pr=1234` |
| `source_version` | for migration/porting: where the code comes from | `source_version=18.0` |
| `commits` | comma-separated SHAs or `pr:<n>` for porting | `commits=pr:1180` |
| `issue` | GitHub issue number driving an improvement | `issue=99` |
| `task` | free text describing the improvement | `task="add tests for stage default"` |
| `workdir` | local checkout root; default `work/<repo>` under the project | `workdir=D:/src/project` |

Resolution order for anything missing: explicit argument, then environment variable
`ODOO_AUTOMATION_<KEY>` (for example `ODOO_AUTOMATION_MODE`), then `defaults` in
`config/automation.yaml`. The defaults also name `current_version` (19.0), `next_version`
(20.0) and `previous_version` (18.0); a missing `version` falls back to `current_version`, a
missing `source_version` for a migration to `previous_version` of the target. If `version`, `repo` or `module` cannot be resolved, ask once in an
interactive session; in a non-interactive run, write a `blocked` log and stop.

For `pr`-driven tasks (code review) derive `module` from the files touched by the PR. A PR that
touches several modules is handled once per module that is in scope; modules out of scope are
mentioned in the log but not reviewed.

## 3. Modes

| mode | what you may do | what you may not do |
|---|---|---|
| `plan` | read anything, run read-only git/gh commands, write markdown under the log folder | change code, push, comment, create PRs or reviews |
| `draft` | everything in plan, plus: edit code in a local checkout, commit, push to the fork, open **draft** PRs, create **pending** (unsubmitted) reviews, write comments to the log | submit a review, mark a PR ready, merge, comment publicly, close issues |
| `full` | everything in draft, plus: submit reviews, open ready-for-review PRs, comment on PRs/issues | approve a PR unless `allow_approve` is true, merge, push to protected branches, act outside the task skill's stated scope |

"Full does not wait for a human" means: within what the task skill explicitly covers, you decide
and act. It does not extend what you are allowed to do. When a decision falls outside the skill
(for example a migration needs a data model redesign, or a review finds the PR should be split),
record it under **Blocked / needs human** in the log, do what is still safe, and stop. In `full`
mode a security finding at or above `block_full_on_severity` that is *introduced by the change
you produced* downgrades the submission to draft; say so in the log.

Default mode is whatever `defaults.mode` says (shipped as `plan`). Never promote yourself to a
higher mode than requested.

## 4. Scope gate

Automations must only touch modules listed in `config/automation.yaml`. Check it with the helper:

```bash
python .claude/skills/odoo-task-core/scripts/automation.py check-scope --version 19.0 --repo partner-contact --module partner_firstname --task code-review
```

Exit code 0 means in scope; it prints the `github` slug (owner/repo) to use. Exit code 2 means out
of scope: write a log to `logs/_out_of_scope/<date>_<version>_<repo>_<module>.md` with status
`skipped` and stop. Exit 3 means the config is unreadable: stop with status `blocked`.

Scope is checked against the **target** version (where the change lands). A scope entry without
`odoo_version` applies to every version, so a migration from 18.0 to 19.0 or from 19.0 to 20.0 is
in scope as long as the module is listed for its repo. An entry with `odoo_version: "19.0"` (or a
list of versions) restricts the modules to those versions. Never edit the config file yourself; it
is the human's steering wheel. A module list of `["*"]` means every module of that repo.

## 5. Task log

One short markdown file per task run, roughly one screen long, in:

```
logs/<odoo_version>/<repo>/<module>/<pr>/<yyyy-mm-dd>_<HHMM>_<task>.md
```

`<pr>` is `pr-<number>` when an upstream PR exists. Before a PR exists use `local-<branch>`
(branch name slugified) and, when a PR is created later in the same run, move the folder to
`pr-<number>` with the `log-move` helper and mention the move in the log. Plans that never produce a
branch use `no-pr`.

Create the file with the helper so the layout stays uniform:

```bash
python .claude/skills/odoo-task-core/scripts/automation.py log-init --version 19.0 --repo partner-contact --module partner_firstname --pr pr-1234 --task code-review --mode draft --title "Review of OCA/partner-contact#1234"
```

It prints the path. Fill in the template sections (see `assets/log-template.md`) as you go:
**Context**, **Actions**, **Outcome**, **Security review**, **Blocked / needs human**, **Follow-ups**.
Close it with `log-finish --path <path> --status <status>`. Status values: `planned`, `drafted`,
`completed`, `skipped`, `blocked`, `failed`.

Rules for logs: write facts and links, not transcripts. Never paste tokens, cookies or full
environment dumps. Record every external action (push, PR, comment, review) with its URL. If the
run fails midway, still finish the log with `failed` and what was left behind (branch names,
unpushed commits).

## 6. Working with repositories and GitHub

- Local checkouts live under `work/<repo>/` by default (git-ignored). Clone with
  `gh repo clone <owner>/<repo> work/<repo> -- --branch <version>`; use `git worktree add` for a
  second version of the same repo.
- Push only to the fork named in `defaults.fork_owner`. If it is empty, use the authenticated
  `gh` user's fork (create it with `gh repo fork --clone=false` if needed). Never push to the
  upstream version branches.
- Branch names: `<version>-<type>-<module>[-<topic>]`, for example `20.0-mig-partner_firstname`,
  `19.0-fix-partner_firstname-company_conversion`, `19.0-port-partner_firstname-pr1180`.
- Commit messages and PR titles follow OCA conventions; see `references/oca-conventions.md`.
  Commits produced with AI help carry an `Assisted-by:` trailer, never `Co-Authored-By:`.
- Read `references/github-recipes.md` for the exact `gh` commands that create draft PRs, pending
  reviews, submitted reviews and comments. Draft mode uses the pending/draft variants only.
- Before acting on a PR, read existing comments and reviews so you do not repeat them.

## 7. Closing security review

Every task ends with the `odoo-security-review` skill on the module as it exists after your
changes (or, for a code review, the PR head). It writes `<timestamp>_security-review.md` next to
the task log and records medium-or-higher findings under
`security/<odoo_version>/<repo>/<module>/`. The security review is local only: never post it,
quote it in PR bodies or review comments, or push it. In the task log, the **Security review**
section holds only the counts per severity and the file name.

## 8. Reference material

- `references/oca-conventions.md`: module layout, manifest, README fragments, naming, commit and
  PR message format, version bump rules, OCA bot commands.
- `references/odoo-orm-pitfalls.md`: Odoo API and ORM mistakes worth looking for when reviewing or
  writing code.
- `references/github-recipes.md`: gh/API commands per mode.
- `assets/log-template.md`: the log skeleton the helper fills.
- `scripts/automation.py`: `check-scope`, `list-scope`, `log-init`, `log-finish`, `log-move`,
  `finding`, `config`. Needs Python 3; reads YAML with PyYAML or ruamel.yaml when installed and
  falls back to a built-in parser for the simple config syntax otherwise. `automation.ps1` is a
  thin wrapper with the same arguments for PowerShell users (run with
  `powershell -NoProfile -ExecutionPolicy Bypass -File ...` if script execution is disabled). If
  Python is missing, perform the same steps by hand, matching the layouts described here exactly.
