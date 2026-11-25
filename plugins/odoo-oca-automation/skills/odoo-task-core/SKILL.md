---
name: odoo-task-core
description: Shared contract for every Odoo/OCA automation skill (odoo-pr-review, odoo-code-review, odoo-module-migration, odoo-commit-porting, odoo-module-improvement, odoo-security-review). Defines the run modes plan/draft/full, the explicit task inputs every caller must supply (no configuration file), the task log layout logs/<odoo_version>/<repo>/<module>/<pr>/, argument parsing, OCA commit and PR conventions, the shared frame for pull request reviews (gathering, TL;DR, delivery per mode, combined structural + functional runs), and the mandatory closing security review. Read this FIRST whenever any odoo-* skill runs, whenever the user mentions automation modes, task logs, task arguments, OCA conventions, or asks how an Odoo automation should behave.
---

# Odoo task core

Every Odoo/OCA task skill in this project is a workflow built on the same frame. This skill
is that frame. Task skills do not repeat it; they say "follow odoo-task-core" and then describe
only what is specific to them. If you are running a task skill, do the steps below in order.

## 1. Lifecycle of a task

1. Parse the arguments (section 2) and resolve the mode (section 3).
2. Check the inputs (section 4). A missing required input means: ask once, or stop as `blocked`.
3. Initialise the task log (section 5) before doing any real work, so a crash still leaves a trace.
4. Do the work the task skill describes, respecting the mode.
5. Run the `odoo-security-review` skill on the module (section 7). Always, in every mode.
6. Finish the log: status, summary, links, follow-ups.

## 2. Arguments

Skills receive `key=value` tokens, in any order. Unknown keys are kept and shown in the log.
There is no configuration file: everything a task needs comes from these arguments, given
explicitly by the caller (the user or the automation that starts the run).

Task inputs:

| key | meaning | example |
|---|---|---|
| `mode` | `plan`, `draft` or `full` | `mode=draft` |
| `version` | Odoo version the change lands on (target branch) | `version=19.0` |
| `repo` | repo name | `repo=partner-contact` |
| `github` | upstream `owner/repo` slug; default `OCA/<repo>` | `github=OCA/partner-contact` |
| `module` | technical module name; comma-separated for several | `module=partner_firstname` |
| `pr` | PR number in the upstream repo, if one exists | `pr=1234` |
| `source_version` | for migration/porting: where the code comes from | `source_version=18.0` |
| `commits` | comma-separated SHAs or `pr:<n>` for porting | `commits=pr:1180` |
| `issue` | GitHub issue number driving an improvement | `issue=99` |
| `task` | free text describing the improvement | `task="add tests for stage default"` |
| `workdir` | local checkout root; default `work/<repo>` under the current directory | `workdir=D:/src/project` |

Policy inputs (optional; the default is the safe choice, so the caller only names them to loosen
or tighten a run):

| key | meaning | default |
|---|---|---|
| `fork_owner` | GitHub owner of the fork to push to | the authenticated `gh` user |
| `allow_approve` | `full` mode may submit `APPROVE` reviews | `false` |
| `allow_request_changes` | `full` mode may submit `REQUEST_CHANGES` reviews | `false` |
| `block_full_on_severity` | introduced security finding at or above this level downgrades `full` to draft | `high` |
| `security_min_severity` | lowest severity recorded under `security/` | `medium` |
| `log_root` | root folder of the task logs | `logs` |
| `security_root` | root folder of recorded security findings | `security` |

Nothing is inferred: there is no fallback to environment variables, a config file or a "current"
Odoo version. `version` and `source_version` are always given by the caller.

For `pr`-driven tasks (`pr-review`, `code-review`) `module` may be left out; it is then the set
of modules the PR touches, all of them reviewed. When `module` is given, only those modules are
reviewed; other modules the PR touches are mentioned in the log but not reviewed. Section 9
describes the frame both review skills share.

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

Default mode is `plan` when the caller gives none. Never promote yourself to a higher mode than
requested.

## 4. Required inputs

Each task skill names its required arguments (always `version` and `repo`; `module` except for
PR-driven tasks; `source_version` for migrations and ports; `pr`, `commits`, `issue` or `task`
as the skill says). The caller decides which repos and modules an automation may touch by what
it passes; the skills do not keep their own list. Never guess a missing value from the
repository, branch names or earlier runs.

When a required input is missing or ambiguous (for example `version=19` or a `repo` that does
not exist under `github`):

- interactive session: ask the caller once, naming every missing input in one question;
- non-interactive run: write a task log with status `blocked` listing the missing inputs (use
  `pr=no-pr` and `module=_unknown` for any part of the log path that is itself missing) and stop.

Record every input the run used, defaults included, in the log's `arguments` field so the run
can be repeated exactly.

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
python .claude/skills/odoo-task-core/scripts/automation.py log-init --version 19.0 --repo partner-contact --github OCA/partner-contact --module partner_firstname --pr pr-1234 --task code-review --mode draft --title "Review of OCA/partner-contact#1234" --arguments "mode=draft version=19.0 repo=partner-contact pr=1234"
```

It prints the path. Pass `--log-root <log_root>` before the command when the caller set
`log_root`. Fill in the template sections (see `assets/log-template.md`) as you go:
**Context**, **Actions**, **Outcome**, **Security review**, **Blocked / needs human**, **Follow-ups**.
Close it with `log-finish --path <path> --status <status>`. Status values: `planned`, `drafted`,
`completed`, `skipped`, `blocked`, `failed`.

Rules for logs: write facts and links, not transcripts. Never paste tokens, cookies or full
environment dumps. Record every external action (push, PR, comment, review) with its URL. If the
run fails midway, still finish the log with `failed` and what was left behind (branch names,
unpushed commits).

## 6. Working with repositories and GitHub

- Local checkouts live under `work/<repo>/` by default (git-ignored). Clone with
  `gh repo clone <github> work/<repo> -- --branch <version>`; use `git worktree add` for a
  second version of the same repo.
- Push only to the fork of `fork_owner`. If the caller gave none, use the authenticated
  `gh` user's fork (create it with `gh repo fork --clone=false` if needed). Never push to the
  upstream version branches.
- Branch names: `<version>-<type>-<module>[-<topic>]`, for example `20.0-mig-partner_firstname`,
  `19.0-fix-partner_firstname-company_conversion`, `19.0-port-partner_firstname-pr1180`.
- Commit messages and PR titles follow OCA conventions; see `references/oca-conventions.md`.
  Commits produced with AI help carry an `Assisted-by:` trailer, never `Co-Authored-By:`.
- Read `references/github-recipes.md` for the exact `gh` commands that create draft PRs, pending
  reviews, submitted reviews and comments. Draft mode uses the pending/draft variants only.
- **No `@` mentions in draft PRs.** Whenever you open a draft PR (draft mode, or full mode
  downgraded to draft), never write `@<login>` in its title, body or commits: GitHub notifies
  on mentions even in drafts. List the people to ping as plain text instead, under a line
  `To notify when ready: <login>, <login>` (logins without `@`). The `@` mentions are sent
  only when the PR becomes ready for review, as a separate comment (see
  `references/github-recipes.md`). Ready-for-review PRs opened in full mode mention people
  directly in the body as usual. Never list or mention the manifest maintainers in either case:
  the OCA bot notifies them automatically.
- Before acting on a PR, read existing comments and reviews so you do not repeat them.

## 7. Closing security review

Every task ends with the `odoo-security-review` skill on the module as it exists after your
changes (or, for a PR review, the PR head). It writes `<timestamp>_security-review.md` next to
the task log and records medium-or-higher findings under
`security/<odoo_version>/<repo>/<module>/`. The security review is local only: never post it,
quote it in PR bodies or review comments, or push it. In the task log, the **Security review**
section holds only the counts per severity and the file name.

One PR head gets one security review: when `odoo-pr-review` and `odoo-code-review` run on the
same head SHA in one session (section 9), the review runs once after the last skill and both
logs name the same report file.

## 8. Reference material

- `references/oca-conventions.md`: module layout, manifest, README fragments, naming, commit and
  PR message format, version bump rules, OCA bot commands.
- `references/pr-review-frame.md`: the shared procedure for pull request reviews (section 9).
- `references/odoo-orm-pitfalls.md`: Odoo API and ORM mistakes worth looking for when reviewing or
  writing code.
- `references/github-recipes.md`: gh/API commands per mode.
- `assets/log-template.md`: the log skeleton the helper fills.
- `scripts/automation.py`: `log-init`, `log-finish`, `log-move`, `finding`. Needs Python 3
  (standard library only) and reads no configuration; roots and thresholds come from its flags
  (`--log-root`, `--security-root`, `finding --min-severity`). `automation.ps1` is a
  thin wrapper with the same arguments for PowerShell users (run with
  `powershell -NoProfile -ExecutionPolicy Bypass -File ...` if script execution is disabled). If
  Python is missing, perform the same steps by hand, matching the layouts described here exactly.

## 9. Pull request reviews

Two skills review PRs, each with its own task name and checklist, and they share one frame:

| skill | task | judges |
|---|---|---|
| `odoo-pr-review` | `pr-review` | structure: commit messages and PR title, one change per commit/PR, manifest changes, build pipeline, coding style beyond pre-commit, docs fragments |
| `odoo-code-review` | `code-review` | function: does the change do what it claims, ORM/API correctness, access rights, migration scripts, meaningful tests, fit with the module and the OCA ecosystem |

A request to review a PR that does not name one aspect means both, in that order:
`odoo-pr-review` first (cheap, catches what the author must fix anyway), then
`odoo-code-review` on the same head SHA. A request about commits, CI, style or the manifest
means the PR review alone; a request about whether the change works, is correct or is the
right approach means the code review alone. Each skill stays inside its column: a structural
finding noticed during the code review (or the reverse) is not commented on but handed to the
other skill (**Follow-ups** when standalone, nothing when the other skill runs in the same
session).

Full procedure, shared rules for gathering, the TL;DR format every review output starts with,
delivery per mode, combined runs and the security hand-off: `references/pr-review-frame.md`.
