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

1. **Blockers**: wrong base branch, missing ACL for new models,
   broken migration scripts, tests missing for behavioural changes, PR mixing unrelated changes,
   `sudo()` or raw SQL without justification, API usage removed in the target version.
   A missing version bump is **not** a finding: the OCA bot bumps the manifest at merge time
   (`ocabot merge patch|minor|major|nobump`). State the bump size you recommend in the review
   summary instead, and ask for a manual bump to be dropped unless migration scripts need it.
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
the consequence, and the fix, as a ```suggestion block when a one-liner does it. Detail lives in
those inline comments, anchored to the changed lines; the summary body is the TL;DR part 2
below: verdict (looks good / needs changes / needs discussion), the blockers in one line each,
and thanks. Write for the author, who is usually a volunteer.

Automations never `APPROVE` unless `allow_approve` is true, and never `REQUEST_CHANGES` when
`allow_request_changes` is false; `COMMENT` is always available. A review with blockers in
`full` mode uses `REQUEST_CHANGES` when allowed, otherwise `COMMENT` with the blockers listed.

## 3. Report: TL;DR first

Every review output (the plan file, the task log, the final message to the user) **starts with a
`## TL;DR` section** placed right after the header table and before **Context**. It has two parts,
ten lines at most in total, and it is written for someone who reads nothing else:

**Part 1: PR status.** Three to five lines. State whether the PR is ready (ready to merge /
needs changes / needs discussion / blocked), what it tries to improve in one sentence, whether
that is a good idea for the module and the OCA repo, and the recommended merge bump. Then only
what needs attention: blockers, open questions, risks, missing tests. Do **not** list what
passed (green CI, conventions met, version rules respected); that belongs in the detailed
sections further down.

**Part 2: Suggested review response.** The summary text to post as the review body, three to
six lines, quoted verbatim so it can be copied: verdict, blockers in one line each, bump size
for the merger, thanks. Everything with a file and line (findings, suggestions, nits) goes into
the inline comments on the changed code, not into this summary.

Example:

```markdown
## TL;DR

**Status:** needs changes. Moves the stage default from the view to a compute on
`project.task`; sensible, it fixes the reported bug at the source. Merge bump: patch.
Needs attention: no regression test for the reported case; `sudo()` on line 42 is unjustified.

**Suggested review response:**
> Thanks for the fix, the compute is the right place for this.
> blocker: please add a test reproducing #123 before merge.
> blocker: `sudo()` in `_compute_stage_id` is not needed, see inline comment.
> Suggested merge: `ocabot merge patch`.
```

## 4. Deliver per mode

| mode | deliverable |
|---|---|
| `plan` | `logs/<v>/<repo>/<module>/pr-<n>/<stamp>_review-plan.md`: TL;DR (section 3), PR classification, files to inspect, checks to run, questions to answer, draft of expected comments. No GitHub writes. |
| `draft` | PENDING review created via the API (see `odoo-task-core/references/github-recipes.md`) with the TL;DR part 2 as its body; the review JSON is also saved as `<stamp>_review.json` in the log folder. If a pending review of ours exists, delete and recreate it. |
| `full` | Review submitted with `COMMENT` or `REQUEST_CHANGES`, TL;DR part 2 as its body. If the PR is a draft on GitHub, submit anyway; the author asked for early feedback by opening it. |

In all modes, the task log opens with the TL;DR and its **Outcome** lists the comment count by
severity and the review URL (or JSON path). The final message to the user is the TL;DR followed
by the log path; do not repeat the inline comments there. **Follow-ups** suggests `odoo-module-improvement` or porting tasks when the
review found work the automation could do (for example "tests missing": offer
`task="add tests for ..."`).

## 5. Hand-off to the security review

Pass the PR head path, the diff, and the list of files changed. Findings marked `introduced` at
or above `block_full_on_severity` must appear in the review as blockers, phrased safely (see
security skill section "What to say to the maintainers"). Pre-existing findings are not part of
the public review unless the PR touches the same lines.
