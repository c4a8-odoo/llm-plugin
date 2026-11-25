---
name: odoo-commit-porting
description: Port commits or whole pull requests of an OCA/Odoo module between version branches (forward-port an 18.0 fix to 19.0, backport a 19.0 fix to 18.0, port to the next version 20.0) with git cherry-pick -x or oca-port, adapt them to the target API, and open the port PR (the OCA bot bumps the version on merge). Use whenever the user asks to forward-port, backport, cherry-pick, 'apply this fix to 19.0 too', or an automation checks which merged PRs are missing on newer branches. Follows odoo-task-core and ends with odoo-security-review.
---

# Odoo commit porting

Follow `odoo-task-core` first. Required arguments: `source_version`, `version` (target), `repo`,
`module`, and either `commits=<sha,sha>` or `commits=pr:<n>`. Task name: `commit-porting`.
Without `commits`, the task is a **discovery** run: find what is missing on the target and
propose ports (plan) or port the oldest unported PR (draft/full).

Porting preserves authorship and the original message, so maintainers can trace a fix across
branches. Rewriting a fix by hand loses that trail; only do it when the cherry-pick is
unrecognisable after conflict resolution, and then say so in the commit body.

## 1. Identify what to port

- `commits=pr:<n>`: `gh pr view n --json commits,title,body,mergedAt,state`. Only merged PRs are
  ported (an unmerged fix may still change). Take the merge commit's parents' range or the listed
  commit SHAs; skip bot commits (`[UPD] README.rst`, `[UPD] addons table`, translation updates by
  `oca-transbot`/weblate), they are regenerated on the target.
- `commits=<sha,...>`: fetch each, read its message and files; refuse (log `blocked`) if a commit
  touches modules other than `module` unless the caller named them in `module` too.
- Discovery (`references/porting-recipes.md` section "finding unported work"): compare merged PRs
  on the source branch touching the module with the target branch history (`oca-port` does this
  natively, grep for `(cherry picked from commit` trailers and subjects otherwise).

Check the target first: is the fix already there under a different shape (fixed differently, or
the code path gone)? `git log origin/<target> --oneline -- <module>` plus a read of the relevant
function. Already present means status `skipped` with the evidence.

## 2. Plan mode

`<stamp>_porting-plan.md` in the log folder (`no-pr`): list of commits with SHA, author, subject,
files; already-ported checks; expected conflicts (files that differ between branches); API changes
between source and target touching those files (from
`odoo-module-migration/references/version-changes.md`); recommended bump size for the merge
command (the bot bumps on merge, the PR does not); PR title and body.

## 3. Draft and full modes

1. Branch `<target>-port-<module>-pr<n>` (or `-<short sha>`) from `origin/<target>`.
2. `git cherry-pick -x <sha>` in original order. On conflict: resolve in favour of the target
   branch's structure while keeping the fix's intent; keep the `(cherry picked from commit ...)`
   trailer; add a line `Conflicts resolved in: <files>` to the message body when resolution was
   non-trivial.
3. Adapt to the target API in a **separate follow-up commit** `[FIX] <module>: adapt port to <target>`
   when the change is more than a line or two; tiny adaptations may go into the cherry-picked
   commit with a note in the body.
4. Leave the manifest `version` at the target branch's current value: the OCA bot bumps it on
   merge (`ocabot merge patch|minor`). If the source commit bumped the version, drop that hunk
   rather than carrying a source version string. Name the bump size in the PR body. Only a port
   that ships `migrations/<version>/` scripts sets the version by hand (then merge `nobump`).
5. `pre-commit run -a`; tests if an Odoo of the target version is available.
6. Push to the fork; PR titled with the **original tag and summary**, prefixed with the target:
   `[19.0][FIX] partner_firstname: keep lastname on company conversion`. Body:

   ```markdown
   Forward-port of #<source pr> (<source version>) to <target>.   # or Backport of ...

   <original PR description, shortened>

   Adaptations for <target>: <none | list>

   To notify when ready: <original author> <!-- draft PR: plain logins, never @ -->
   @<original author> 
   ```

   Draft PR in draft mode; ready PR in full mode. A draft PR never contains `@` mentions
   (odoo-task-core section 6). In full mode also comment on the source PR:
   "Forward-ported to <target> in #<n>" (one line, no more).

7. Several PRs to port for the same module: one port PR per source PR unless they are
   interdependent; interdependent ones go in one PR, listed in the body.

## 4. Log and hand-off

**Actions**: per commit, source SHA -> new SHA and whether conflicts were resolved. **Outcome**:
PR URL. **Follow-ups**: the remaining unported PRs discovered. Move the log folder to `pr-<n>`.
Run `odoo-security-review` on the ported module; findings `introduced` by the port at
`block_full_on_severity` or above keep the PR a draft.
