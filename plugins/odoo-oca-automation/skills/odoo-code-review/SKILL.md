---
name: odoo-code-review
description: Review the functional correctness of a pull request in an OCA/Odoo repository and whether the change fits the Odoo/OCA ecosystem - does it do what the PR claims, Odoo ORM/API correctness (compute/depends, create/write, search, sudo, SQL, translations, multi-company), access rights for new models, migration scripts when the data model changes, tests that prove the behaviour, APIs valid on the target version, the right module and extension point, no duplicate of an existing OCA module, no breakage for modules that depend on it. Produces a review plan (plan mode), a pending GitHub review (draft mode) or a submitted review (full mode). Use when asked whether a PR works, is correct, is the right approach or belongs in OCA; a plain "review this PR" runs odoo-pr-review first and then this skill. Does not comment on commit messages, manifest version, CI or style (that is odoo-pr-review). Follows odoo-task-core and ends with odoo-security-review.
---

# Odoo code review (functional correctness and ecosystem fit)

Follow `odoo-task-core` first: arguments, mode, scope gate, task log, and section 9 (the shared
frame for pull request reviews: gathering, TL;DR, delivery per mode, combined runs, closing
security review). This skill adds what a functional OCA review looks at.

Required arguments: `version`, `repo`, `pr`. `module` is derived from the PR files when not
given. Task name for the log and the scope gate: `code-review`.

## 1. What this skill judges, and what it leaves alone

In scope: whether the change works and whether it belongs.

- Does the code do what the PR body and the linked issue say, for every case it touches,
  including the ones the author did not think of (empty recordsets, multi-record, multi-company,
  inactive records, the UI path and the API path).
- Odoo ORM and API correctness on the target version.
- Access rights and migration scripts that the change makes necessary.
- Tests that prove the behaviour, not just tests that exist.
- Ecosystem fit: right module, right extension point, no duplicate of existing OCA work, no
  silent behaviour change for existing users, no breakage for modules that inherit from or
  depend on this one.

Out of scope: commit messages, PR title, manifest version, CI status, formatting, naming,
file layout, README fragments. That is `odoo-pr-review`. When you notice such a problem, do not
comment on it: in a combined run it is already covered; standalone, write it under
**Follow-ups** as `odoo-pr-review pr=<n>` with one line saying what to look at. The one
exception is a CI test failure in the module under review: read it, because it usually points
at a functional problem, and comment on the cause, not on the red job.

## 2. Understand the intent before judging the code

1. Read the PR body, the linked issue and the discussion. Write the claim in one sentence in
   the log's **Context**: "makes X happen when Y". The review measures the diff against that.
2. Read `readme/DESCRIPTION.rst` and the module's models to know what the module promises.
3. Find who else depends on what the PR touches: grep the repo (and the well-known dependants
   listed in the module's README or `gh search code`) for `_inherit` of the models, calls of
   the renamed or changed methods, `inherit_id` of the changed views, `ref=` of the changed
   XML ids. A change that is right for this module and breaks three others is not right.
4. Fetch the head (`git fetch origin pull/N/head:pr-N`) and read the surrounding code, not only
   the diff; the bug is often in the lines the diff did not touch. Read the whole module for
   `[MIG]` and `[ADD]`.

## 3. Review

Work through `references/review-checklist.md` and stop collecting when you have what matters; a
review with four precise comments beats one with forty.

1. **Blockers**: the change does not do what it claims, or breaks a case it must handle; new
   model without `ir.model.access.csv` lines; field removed or renamed without a migration
   script; migration script that cannot run (wrong folder, wrong API, no `openupgradelib`
   guard); API that no longer exists on the target version; `sudo()` or raw SQL that changes
   what a user may see or do without a stated reason; behaviour change without a test; a
   method or field that other OCA modules use, renamed or removed without a shim.
2. **Correctness**: `odoo-task-core/references/odoo-orm-pitfalls.md`. Trace every compute and
   its `@api.depends`; every `create`/`write`/`unlink` override for `super()` and multi-record
   handling; every search for the missing `active`/company filter and the order with `limit=1`;
   onchange vs compute; `ensure_one()` where singleton semantics are assumed; translations
   evaluated at the right time; defaults from `self.env.company`, not the user's first company.
3. **Ecosystem fit**: is this the right module (or should it live in the module that owns the
   model, or in an existing OCA module that already does it: search the repo and
   `gh search repos --owner OCA`); does it use the extension point Odoo offers (`_inherit`,
   hooks, `_get_*` methods, view inheritance) instead of copying core code or monkey-patching;
   is it generic and configurable rather than one customer's rule; does it keep the current
   behaviour as the default for existing users (new behaviour opt-in via a setting or a field
   default); does it pull in Enterprise or a dependency the repo does not accept; if it works
   around a core bug, say that the fix belongs in `odoo/odoo` and the workaround should be
   marked as such.
4. **Class-specific**: for `[MIG]` apply `odoo-module-migration/references/version-changes.md`
   for source..target and check that behaviour is preserved, not just that it installs. For
   `[FIX]` check that the test fails without the fix and that the fix addresses the cause, not
   the symptom. For `[ADD]` check the data model (names, relations, required fields, company
   scoping) because it is hard to change after release. For `[IMP]` check backwards
   compatibility. For `[REF]` check that behaviour is unchanged and the tests still assert
   something.
5. **Tests**: do they exercise the changed path and assert the outcome, cover the constraint
   and permission paths, and would they fail if the change were reverted? A test that only
   calls the method is not a test of the behaviour. Test style and tags are `odoo-pr-review`'s.
6. **Functional sanity**: for UI changes, say that a manual check on runboat is still needed
   and what to click; for reports and wizards, check the demo data makes the path reachable.

Each finding becomes one inline comment with a severity prefix (`blocker:`, `should:`, `nit:`),
the consequence ("this recomputes for every line change", "this returns the first company's
value for a user in company B"), and the fix, as a ```suggestion block when a one-liner does
it. Write for the author, who is usually a volunteer: explain the Odoo mechanism behind the
finding in one sentence when it is not obvious.

## 4. TL;DR specifics

Follow the TL;DR format from `odoo-task-core` section 9. Part 1 opens with `**Status:**`
(ready to merge / needs changes / needs discussion / blocked), what the PR tries to improve in
one sentence, whether that is a good idea for the module and the OCA repo, and the recommended
merge bump. Then only what needs attention: blockers, open questions, risks, missing tests.
Do **not** list what passed. Part 2 is the review body to post.

```markdown
## TL;DR

**Status:** needs changes. Moves the stage default from the view to a compute on
`project.task`; sensible, it fixes the reported bug at the source and keeps the behaviour for
existing users. Merge bump: patch.
Needs attention: no regression test for the reported case; `sudo()` on line 42 is unjustified;
`project_task_stage_mgmt` overrides the same default and will now lose.

**Suggested review response:**
> Thanks for the fix, the compute is the right place for this.
> blocker: please add a test reproducing #123 before merge.
> blocker: `sudo()` in `_compute_stage_id` is not needed, see inline comment.
> should: `project_task_stage_mgmt` sets the same default; see inline comment for a way to let
> both coexist.
> Suggested merge: `ocabot merge patch`.
```

## 5. Deliver

Per mode exactly as `odoo-task-core` section 9 describes. In a combined run (after
`odoo-pr-review` on the same PR) merge the stored `<stamp>_pr-review-comments.json` into your
review payload and write the combined body: your status line first, then the structural
blockers from the PR review, then the bump size and thanks. The verdict is "needs changes"
when either skill found a blocker.

**Follow-ups** suggests `odoo-module-improvement` or porting tasks when the review found work
the automation could do (for example "tests missing": offer `task="add tests for ..."`), and
`odoo-pr-review` when it did not run in the same session.

## 6. Hand-off to the security review

Pass the PR head path, the diff, and the list of files changed. Findings marked `introduced`
at or above `block_full_on_severity` must appear in the review as blockers, phrased safely (see
security skill section "What to say to the maintainers"). Pre-existing findings are not part
of the public review unless the PR touches the same lines.
