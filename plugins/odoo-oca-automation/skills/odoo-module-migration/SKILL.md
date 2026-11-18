---
name: odoo-module-migration
description: Migrate an OCA/Odoo module from one Odoo version to the next (for example 18.0 to 19.0, or 19.0 to the next version 20.0) following the OCA migration process (claim on the migration issue, branch from the target version, bring the commit history with oca-port or git format-patch, pre-commit commit, adapt code to the target API, bump version, regenerate README, run tests, open the MIG PR). Use whenever the user asks to migrate, port a module to a new version, 'make module X work on 20.0', or an automation iterates over not-yet-migrated modules. Follows odoo-task-core and ends with odoo-security-review.
---

# Odoo module migration

Follow `odoo-task-core` first. Required arguments: `source_version`, `version` (target), `repo`,
`module`. Task name: `module-migration`. Scope is checked against the target version.

A migration is mechanical in its skeleton and judgemental in its middle. The skeleton (branch,
history, pre-commit, version bump, PR) is in `references/migration-process.md`; follow it
literally, because reviewers in OCA repos expect that exact commit shape and reject PRs that
squash history. The middle (adapting the code) uses `references/version-changes.md` plus the
module's own tests and your reading of the target-version core.

## 1. Preflight (every mode)

1. Migration issue: `gh issue list --search "Migration to version <target> in:title"`. Read it:
   is the module listed, already claimed, or already migrated? Also
   `gh pr list --state all --search "[MIG] <module> in:title"`. An open or merged `[MIG]` PR
   means stop with status `skipped` and a log line pointing to it. A stale one (no activity for
   months, conflicts) is noted; you may still proceed in draft/full but the PR body must
   reference it and offer to supersede.
2. Dependencies: every module in `depends` must be installable on the target branch (in the same
   repo or in another OCA repo / core). A missing dependency is a `blocked` log entry naming the
   dependency and the repo where its migration is pending; in `plan` mode it becomes the first item
   of the plan.
3. Target-version core differences: for the Odoo core modules the module inherits from, skim the
   target `odoo/addons/<core module>` for renamed fields/methods the module touches (`git grep`
   each overridden method name in the core checkout, or the GitHub web view when no core clone
   exists).

## 2. Plan mode

Write `<stamp>_migration-plan.md` in the log folder (`no-pr`): preflight findings, dependency
status, the list of changes expected per file (from `version-changes.md` greps over the source
module), estimated risk, test situation, and the exact commands of the skeleton. No branch, no
clone writes beyond `work/` if a clone is needed to grep.

## 3. Draft and full modes

Execute `references/migration-process.md`. Key judgement points:

- **oca-port vs format-patch.** Prefer `oca-port <source> <target> <module> --verbose` when
  the tool is installed (it also lists PRs merged on the source branch after the fork that
  should be ported later). Otherwise `git format-patch ... | git am -3 --keep`. Record which.
- **Pre-commit commit first.** After the history is in, run `pre-commit run -a` (install it per
  `.pre-commit-config.yaml` of the target branch; if the machine lacks Python, note it as blocked
  and skip to code changes, leaving the pre-commit commit for a human). Commit the result as
  `[IMP] <module>: pre-commit auto fixes` with nothing else in it.
- **Code adaptation.** Work version by version if jumping more than one (18 to 20 means
  applying the 19 list, then the 20 list). Grep the module for every removed API in the lists
  and fix each; keep behaviour, do not improve features in a `[MIG]` commit (log improvement
  ideas under **Follow-ups** for `odoo-module-improvement`).
- **Migration scripts.** Remove `migrations/<old versions>/`. Add `migrations/<target>.1.0.0/`
  only if the target core renamed something the module stored data in.
- **Tests.** If an Odoo instance of the target version is available (`workdir` with an
  `odoo-bin`, or docker as described in the process reference), run the module tests and fix
  failures. If not, say so in the log and in the PR body ("tests not run locally; relying on CI").
- **README.** Update `readme/` fragments if the behaviour differs; add yourself/the automation
  owner to `CONTRIBUTORS.rst`; regenerate `README.rst` via pre-commit or `oca-gen-addon-readme`.
- **Commit** `[MIG] <module>: Migration to <target>` with all adaptation changes.
- **PR**: draft mode opens a draft PR; full mode opens it ready for review and comments on the
  migration issue ("Working on <module>: #<pr>") if the module was unclaimed. PR body from
  `references/migration-process.md`.

Stop with `blocked` instead of guessing when: the module depends on core features removed in the
target (no replacement), the data model must change beyond renames, or JS must be rewritten from
legacy widgets to OWL with no equivalent component. Deliver what is safe (history + pre-commit
commit pushed, draft PR with a checklist of what is left) and describe the gap.

## 4. Log and hand-off

Log **Actions** with each command group and the resulting commit SHAs, PR URL, migration issue
comment URL. Move the log folder from `local-<branch>` to `pr-<n>` once the PR exists. Then run
`odoo-security-review` on the migrated module; introduced findings at `block_full_on_severity` or
above keep the PR a draft even in full mode.
