---
name: odoo-module-improvement
description: Implement a general improvement in an OCA/Odoo module on a given version branch - bug fix from an issue, missing tests, new small feature, README/usage docs, performance fix, pre-commit or CI repair, access-rights hardening - with the right OCA commit tag, a bump-size recommendation for the merge bot, migration scripts when the data model changes, and a FIX/IMP/REF PR. Use whenever the user asks to fix, improve, refactor, add tests to, document or harden an existing Odoo/OCA module, or an automation picks up an issue for a module it names. Not for version migrations (odoo-module-migration) or ports (odoo-commit-porting). Follows odoo-task-core and ends with odoo-security-review.
---

# Odoo module improvement

Follow `odoo-task-core` first. Required arguments: `version`, `repo`, `module`, and either
`issue=<n>` or `task="<description>"`. Task name: `module-improvement`.

An improvement PR is judged by OCA reviewers on three things: it does one thing, it proves it
with a test, and its commit tag and recommended bump size match the change. Keep those three in
view and the rest follows. The manifest `version` itself is not edited: the OCA bot bumps it at
merge time (`ocabot merge patch|minor|major|nobump`).

## 1. Understand before touching

1. Read the issue (`gh issue view`) or the task text. Restate the expected behaviour in one
   sentence in the log **Context**; if you cannot, the task is under-specified: `plan` mode writes
   the open questions, `draft`/`full` log `blocked` with those questions unless a reasonable
   default is obvious (say which default you took).
2. Check for existing work: `gh pr list --state all --search "<module> <keywords> in:title"`,
   issue comments, linked PRs. Existing open PR solving it: `skipped`, link it.
3. Read the module fully (it is small enough in most OCA repos): models, views, security, tests,
   README fragments. Note the current manifest version and the tests' structure.
4. Classify the change with `references/improvement-playbook.md` (fix, feature, refactor, tests,
   docs, tooling, hardening) to get the commit tag, bump size and expectations.

## 2. Plan mode

`<stamp>_improvement-plan.md` in the log folder (`no-pr`): restated goal, root cause (for fixes,
with file:line), files to change, test(s) to add with their assertions, bump size for the merge
command, migration
script need, README fragments to touch, risks, PR title/body draft.

## 3. Draft and full modes

1. Branch `<version>-<fix|imp|ref>-<module>-<topic>` from `origin/<version>`.
2. **Test first for fixes.** Write the test that reproduces the bug; run it if an Odoo is
   available (it should fail); then fix; run again. Without a runnable Odoo, still write the
   test and say in the PR body that it was not executed locally.
3. Implement the smallest change that meets the restated goal. Follow
   `odoo-task-core/references/oca-conventions.md` and avoid everything in
   `odoo-task-core/references/odoo-orm-pitfalls.md`. No drive-by refactors in the same commit;
   note them under **Follow-ups**.
4. Do not edit the manifest `version`; the OCA bot bumps it when the PR is merged. Decide the
   bump size and write it in the PR body: data model changes (new stored field with required
   data, renamed/removed field, changed selection) are **major** and need
   `migrations/<new version>/pre-migrate.py` or `post-migrate.py` with `openupgradelib`; because
   the folder name must match, this is the one case where the PR bumps the manifest by hand and
   asks for `ocabot merge nobump`. New optional field or new feature: **minor**. Pure fix:
   **patch**. Docs/CI only: **nobump**.
5. README fragments: `DESCRIPTION.rst`/`USAGE.rst`/`CONFIGURE.rst` when user-visible behaviour
   changes; `CONTRIBUTORS.rst` for the author; `ROADMAP.rst` if you leave a known limitation.
6. `pre-commit run -a`, then one commit per logical change: `[FIX] <module>: <summary>` with a
   body giving the cause and `Fixes #<issue>` if there is one.
7. Push to the fork, PR `[<version>][FIX] <module>: <summary>`; body: what/why, how to test,
   `Closes #<issue>`, `@maintainers`. Draft in draft mode; ready in full mode. Full mode may also
   comment on the issue with the PR link, one line.
8. If the fix also applies to other supported versions, say so in **Follow-ups** with ready
   `odoo-commit-porting` arguments; do not port in the same run.

Stop with `blocked` when: the fix requires changing Odoo core behaviour, a dependency outside
the repo, or a design decision the issue does not settle (two valid behaviours). Deliver the
test and analysis anyway (draft PR with the failing test is useful to maintainers).

## 4. Log and hand-off

**Actions** with commits and URLs; **Outcome** with PR; move the log folder to `pr-<n>`. Then
`odoo-security-review`: introduced findings at `block_full_on_severity` or above keep the PR a
draft; hardening tasks should additionally re-check the specific finding they were meant to fix
and mark it `fixed` in the security index when the PR resolves it.
