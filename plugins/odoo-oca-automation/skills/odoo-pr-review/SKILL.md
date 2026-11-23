---
name: odoo-pr-review
description: Review the structure of a pull request in an OCA/Odoo repository - OCA commit messages and PR title, one logical change per commit and PR, manifest changes (version left to the bot, depends, external_dependencies, installable), the build pipeline (pre-commit, test jobs, runboat, codecov - which job fails and why) and coding style that pre-commit does not enforce (headers, naming, file layout, README fragments, i18n, test hygiene). Produces a review plan (plan mode), a pending GitHub review (draft mode) or a submitted review (full mode). Use when asked to check a PR's commits, manifest, CI, style or OCA conventions; a plain "review this PR" runs this skill first and then odoo-code-review. Does not judge whether the change works (that is odoo-code-review). Follows odoo-task-core and ends with odoo-security-review.
---

# Odoo PR review (structure)

Follow `odoo-task-core` first: arguments, mode, required inputs, task log, and section 9 (the shared
frame for pull request reviews: gathering, TL;DR, delivery per mode, combined runs, closing
security review). This skill adds what a structural OCA review looks at.

Required arguments: `version`, `repo`, `pr`. `module` limits the review to those modules;
without it, every module the PR touches is reviewed. Task name for the log: `pr-review`.

## 1. What this skill judges, and what it leaves alone

In scope: everything a maintainer checks before reading the code for meaning.

- Commit messages, PR title and body, commit granularity and order.
- Manifest and metadata changes.
- The build pipeline: which CI job is red, why, and whether the PR caused it.
- Coding style and module layout beyond what pre-commit enforces, test hygiene, documentation
  fragments, translations files.

Out of scope: whether the change is correct, complete, tested for the right behaviour, or the
right approach for the module and the OCA ecosystem. That is `odoo-code-review`. When you notice
such a problem while reading, do not comment on it: in a combined run leave it to the code
review; standalone, write it under **Follow-ups** as `odoo-code-review pr=<n>` with one line
saying what to look at.

## 2. Review

Work through `references/pr-checklist.md` and stop collecting when you have what matters; a
review with four precise comments beats one with forty.

1. **Blockers**: wrong base branch; unrelated changes in one PR; a `[MIG]` PR that also fixes
   or improves (fixes go to the source version first, then get ported); squashed history in a
   `[MIG]`; `external_dependencies` missing for a new import; CI red because the module's tests
   fail; `[MIG]` manifest version not `X.0.1.0.0` or `installable` false.
2. **Commits**: `[TAG] module: imperative summary`, tag matches the content, body says why, no
   `fixup`/`wip`/merge commits, cherry-pick trailers kept on ports, `Assisted-by:` trailer on
   AI-assisted commits (never `Co-Authored-By:`). One logical change per commit; for `[MIG]`
   the sequence history -> pre-commit commit -> `[MIG]` commit.
3. **Manifest and metadata**: `odoo-task-core/references/oca-conventions.md`. A missing version
   bump is **not** a finding: the OCA bot bumps at merge time (`ocabot merge patch|minor|major|nobump`).
   State the bump size you recommend in the review summary; ask for a manual bump to be dropped
   unless migration scripts need the new folder name. Check `depends`, `external_dependencies`,
   `installable`, `development_status`, `maintainers`, `assets`.
4. **Build pipeline**: `gh pr checks`. For every red or missing job say which job, the cause in
   one line, and whether the PR caused it (compare with the latest run on the base branch;
   `gh run view <id> --log-failed` for the log). pre-commit red: one comment asking to run
   `pre-commit run -a`, never a list of the individual hook complaints. Runboat missing or
   failed to build: say so and why (usually a dependency not on the branch). Codecov drop: nit,
   and only when the PR adds untested code.
5. **Coding style beyond pre-commit**: license header, file and XML id naming, one model per
   file, `_()` on user-facing strings, `_logger` not `print`, `tests/` layout and test hygiene
   (`TransactionCase`, `setUpClass`, `tracking_disable`, tags, no `cr.commit`, no sleep), views
   using the syntax of the target version, assets declared in the manifest. Never comment on
   what pre-commit will fix or already enforces; check that CI is green instead.
6. **Documentation and generated files**: `readme/` fragments updated when behaviour or setup
   changes, `CONTRIBUTORS.rst` for non-trivial changes, generated `README.rst` /
   `index.html` consistent with the fragments, `i18n/` untouched (the bot regenerates).

Each finding becomes one inline comment with a severity prefix (`blocker:`, `should:`, `nit:`),
the consequence, and the fix, as a ```suggestion block when a one-liner does it. Commit message
findings have no line in the diff: one comment in the review body for all of them, quoting the
expected message. Write for the author, who is usually a volunteer.

## 3. TL;DR specifics

Follow the TL;DR format from `odoo-task-core` section 9. Part 1 opens with `**Structure:**`
(ready / needs changes / blocked), one sentence on the shape of the PR (class, number of
commits, what moves), the recommended merge bump, then only what needs attention. Part 2 is the
review body to post: verdict, blockers in one line each, commit message expectations if any,
bump size, thanks.

```markdown
## TL;DR

**Structure:** needs changes. One `[FIX]` commit on `project_task_default_stage`, base 19.0 ok,
pre-commit green, test job red. Merge bump: patch.
Needs attention: test job fails in `test_project_task_default_stage` (introduced by the PR);
manifest version bumped by hand; commit title tagged `[IMP]` for a bug fix.

**Suggested review response:**
> Thanks for the PR. Two things before a functional review:
> blocker: the test job is red (`test_default_stage_on_create`), see the checks tab.
> should: please revert the manifest version bump, the bot does it at merge; and retag the
> commit `[FIX] project_task_default_stage: ...` since it fixes #123.
> Suggested merge: `ocabot merge patch`.
```

## 4. Deliver

Per mode exactly as `odoo-task-core` section 9 describes. In a combined run (this skill
followed by `odoo-code-review` on the same PR) store your comments as
`<stamp>_pr-review-comments.json` in the log folder and leave the GitHub review to the code
review; standalone, create or submit the review yourself.

**Follow-ups** suggests `odoo-code-review` when it did not run in the same session, and
`odoo-module-improvement` for work the automation could do (for example "pre-commit repair" or
"regenerate README").

## 5. Hand-off to the security review

Per `odoo-task-core` section 9. In a combined run the security review runs once, after the
code review; your log's **Security review** section then names that report.
