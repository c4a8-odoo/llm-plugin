---
name: odoo-code-review
description: Review a pull request in an OCA/Odoo repository against OCA conventions, Odoo ORM/API correctness, tests and migration rules, then produce a review plan (plan mode), a pending GitHub review (draft mode) or a submitted review (full mode). Use for any request to review, check, assess or comment on an Odoo/OCA PR, including automated review runs over open PRs of in-scope modules. Follows odoo-task-core and ends with odoo-security-review.
---

# Odoo code review

Follow `odoo-task-core` first: arguments, mode, scope gate, task log, closing security review.
This skill adds what a useful OCA review looks like and how each mode delivers it.

Required arguments: `version`, `repo`, `pr`. `module` is derived from the PR files when not
given. Task name for the log and the scope gate: `code-review`.

## 1. Gather

1. `gh pr view` with files, commits, reviews, comments, labels, `isDraft`, `baseRefName`.
   The base branch must equal `version`; if not, log `blocked` (wrong target branch) and stop.
2. Derive the modules touched. Run the scope gate per module. Review only in-scope modules;
   list the others under **Context** in the log.
3. `gh pr diff`, `gh pr checks`, existing inline comments and reviews. If a maintainer already
   asked for changes that are still open, your review adds to it rather than restating it.
4. Fetch the head into the local clone (`git fetch origin pull/N/head:pr-N`) when you need to
   read files beyond the diff, run `pre-commit`, or inspect tests. Reading the whole module is the
   norm for `[MIG]` and `[ADD]` PRs; the diff is enough for small `[FIX]`es.
5. Classify the PR from its title tag: `[ADD]`, `[MIG]`, `[FIX]`, `[IMP]`, `[REF]`, `[I18N]`,
   `[REM]`. The checklist weights differ per class.

## 2. Review

Work through `references/review-checklist.md` in this order and stop collecting when you have
what matters; a review with four precise comments beats one with forty.

1. **Blockers**: wrong base branch, missing or wrong version bump, missing ACL for new models,
   broken migration scripts, tests missing for behavioural changes, PR mixing unrelated changes,
   `sudo()` or raw SQL without justification, API usage removed in the target version.
2. **Correctness**: `odoo-task-core/references/odoo-orm-pitfalls.md`. Trace compute/depends,
   create/write overrides, search loops, onchange-vs-compute, translations.
3. **OCA conventions**: `odoo-task-core/references/oca-conventions.md`. Manifest, README
   fragments, headers, naming, commit messages, PR title. Do not comment on what pre-commit
   enforces; check instead whether CI is green and say so if it is not.
4. **Class-specific**: for `[MIG]` apply `odoo-module-migration/references/version-changes.md`
   for the target version and check the commit sequence (history kept, pre-commit commit, MIG
   commit, old migration scripts removed, version `X.0.1.0.0`). For `[FIX]` check that a test
   reproduces the bug. For `[ADD]` check module naming, dependencies and that it does not
   duplicate an existing OCA module (search the repo and `gh search repos`).
5. **Functional sanity**: does the change do what the PR body claims? If runboat is green and
   the change is UI-related, mention that a manual check on runboat is still needed.

Each finding becomes one inline comment with a severity prefix (`blocker:`, `should:`, `nit:`),
the consequence, and the fix, as a ```suggestion block when a one-liner does it. The summary body
has: verdict (looks good / needs changes / needs discussion), the blockers in one line each, and
thanks. Write for the author, who is usually a volunteer.

Automations never `APPROVE` unless `allow_approve` is true, and never `REQUEST_CHANGES` when
`allow_request_changes` is false; `COMMENT` is always available. A review with blockers in
`full` mode uses `REQUEST_CHANGES` when allowed, otherwise `COMMENT` with the blockers listed.

## 3. Deliver per mode

| mode | deliverable |
|---|---|
| `plan` | `logs/<v>/<repo>/<module>/pr-<n>/<stamp>_review-plan.md`: PR classification, files to inspect, checks to run, questions to answer, draft of expected comments. No GitHub writes. |
| `draft` | PENDING review created via the API (see `odoo-task-core/references/github-recipes.md`); the review JSON is also saved as `<stamp>_review.json` in the log folder. If a pending review of ours exists, delete and recreate it. |
| `full` | Review submitted with `COMMENT` or `REQUEST_CHANGES`. If the PR is a draft on GitHub, submit anyway; the author asked for early feedback by opening it. |

In all modes, the task log's **Outcome** lists the comment count by severity and the review URL
(or JSON path). **Follow-ups** suggests `odoo-module-improvement` or porting tasks when the
review found work the automation could do (for example "tests missing": offer
`task="add tests for ..."`).

## 4. Hand-off to the security review

Pass the PR head path, the diff, and the list of files changed. Findings marked `introduced` at
or above `block_full_on_severity` must appear in the review as blockers, phrased safely (see
security skill section "What to say to the maintainers"). Pre-existing findings are not part of
the public review unless the PR touches the same lines.
