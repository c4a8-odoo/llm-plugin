# Porting recipes

`SRC`/`TGT` versions, `MOD` module, `OWNER/REPO` upstream, `FORK` fork owner.

## Finding unported work

```bash
# preferred: oca-port lists merged SRC PRs touching MOD that are missing on TGT (no changes made with --dry-run)
oca-port SRC TGT MOD --dry-run --verbose

# manual: commits on SRC touching MOD since the branches diverged
git log --oneline --no-merges origin/TGT..origin/SRC -- MOD
# and for each candidate, check whether TGT already carries it
git log origin/TGT --grep="cherry picked from commit <sha>" --oneline
git log origin/TGT --oneline --fixed-strings --grep="<subject without tag>" -- MOD

# the PR a commit came from
gh api "repos/OWNER/REPO/commits/<sha>/pulls" --jq '.[].number'
# merged PRs of SRC touching MOD, most recent first
gh pr list --repo OWNER/REPO --base SRC --state merged --search "MOD in:title" --json number,title,mergedAt,url --limit 50
```

Ignore: `[UPD]` bot commits, `Translated using Weblate`, `Update translation files`,
`[BOT] post-merge updates`, `[ADD] setup.py`, `[MIG]` commits of the source version itself.

## Cherry-picking

```bash
cd work/REPO
git fetch origin SRC TGT
git checkout -b TGT-port-MOD-pr<N> origin/TGT
git cherry-pick -x <sha1> <sha2>            # original order
# conflict:
git status --short                          # UU files
# edit, then
git add <files> && git cherry-pick --continue
# a commit that is entirely irrelevant on TGT (e.g. only touches removed code):
git cherry-pick --skip                      # and say so in the PR body
```

Keep the trailer `(cherry picked from commit <sha>)`; it is how oca-port and reviewers detect
ports. When `-x` is lost because the commit had to be rewritten, add the trailer by hand.

## Typical conflict causes and resolutions

| cause | resolution |
|---|---|
| manifest `version` differs | take TGT's version string, then apply the correct bump (patch/minor) |
| `README.rst` / `static/description/index.html` | take TGT's version; regenerate with pre-commit |
| `attrs`/`states` in the fix, TGT is 17+ | rewrite as `invisible=`/`readonly=` expressions |
| `<tree>` in the fix, TGT is 18+ | use `<list>` |
| `name_get` / `_name_search` touched | re-implement in `_compute_display_name` / `_search_display_name` |
| `read_group` internals | check `_read_group` tuple API on TGT |
| i18n `.po` conflicts | `git checkout --theirs`? No: drop the `.po` hunk entirely, translations are regenerated |
| tests use fixtures renamed on TGT | adapt test, mention in the adaptation commit |

## Version bump in a port

The port PR gets its own bump on TGT. If the cherry-picked commit changed `"version": "18.0.1.2.1"`,
the conflict resolution sets `"version": "19.0.1.0.1"` (TGT current + patch). Never leave a SRC
version string in a TGT manifest; pre-commit does not catch it, CI does not either, but the
OCA bot will refuse `ocabot merge` with a bump that does not match.

## Backports

Same mechanics, reversed. Additionally: a backport must not introduce behaviour that exists only
on newer versions (new fields, new dependencies); if the fix relies on them, it is not a backport
candidate; log `blocked` with the reason. Backports of security fixes to versions still supported
by OCA are worth the effort; backports of features are usually declined by maintainers; mention
this in the plan.

## PR and cross-references

```bash
git push -u fork TGT-port-MOD-pr<N>
gh pr create --repo OWNER/REPO --base TGT --head FORK:TGT-port-MOD-pr<N> \
  --title "[TGT][FIX] MOD: <original summary>" --body-file pr-body.md --draft
# full mode only
gh pr comment <N> --repo OWNER/REPO --body "Forward-ported to TGT in #<new pr>"
```
