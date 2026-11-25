# OCA migration process (skeleton)

Based on the OCA/maintainer-tools wiki page "Migration to version X.0" (one page per version,
`https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-<X>.0`). Fetch the page for the
target version once per run; it carries the version-specific notes that this file summarises.

Placeholders: `SRC` source version (18.0), `TGT` target version (19.0), `MOD` module, `REPO`
repo name, `OWNER/REPO` upstream slug, `FORK` fork owner.

## 1. Clone and branch

```bash
gh repo clone OWNER/REPO work/REPO -- --branch TGT
cd work/REPO
git remote add fork https://github.com/FORK/REPO.git   # once
git fetch origin SRC TGT
git checkout -b TGT-mig-MOD origin/TGT
```

## 2. Bring the module with its history

Option A, `oca-port` (recommended; `pip install oca-port`):

```bash
oca-port SRC TGT MOD --verbose          # run from the repo root on branch TGT-mig-MOD
# It applies the module's history from SRC, reports PRs merged in SRC that are not in TGT,
# and may offer to create the branch and PR itself. Answer its prompts; in automation use
# --non-interactive if the installed version supports it, otherwise drive it step by step.
```

Option B, plain git:

```bash
git format-patch --keep-subject -o /tmp/mig-MOD origin/TGT..origin/SRC -- MOD
git am -3 --keep /tmp/mig-MOD/*.patch
# conflicts: resolve, `git am --continue`; skip pure .po/.pot patches with `git am --skip` when they conflict
```

After either option the module exists on the branch with its SRC history, untouched.

## 3. Pre-commit commit

```bash
pre-commit install            # uses TGT branch .pre-commit-config.yaml
pre-commit run -a             # repeat until stable; it may fail on things step 4 will fix
git add -A MOD && git commit -m "[IMP] MOD: pre-commit auto fixes"
```

Some repos keep the historical message `[IMP] MOD: black, isort, prettier`; either is accepted.
If pre-commit cannot run on this machine, skip the commit, log it under **Blocked / needs human**,
and say so in the PR body.

## 4. Adapt the module

Apply `version-changes.md` for every version step. Always:

- `__manifest__.py`: `"version": "TGT.1.0.0"`, `installable: True`, drop keys gone in TGT.
- Delete `MOD/migrations/<versions older than TGT>/`.
- Grep for removed APIs listed per version and fix each occurrence.
- Views: run the version-specific view rules (attrs/states, tree/list, t-esc).
- JS/OWL: check `static/src` against the target web client.
- Tests: adjust imports and APIs; add `tracking_disable` if missing.
- `readme/CONTRIBUTORS.rst`: add the migrator with the version in brackets, e.g.
  `* Jane Doe <jane@example.com> (migration to TGT)`.
- `readme/HISTORY.rst`: only if the repo uses it.
- README regeneration: pre-commit hook `oca-gen-addon-readme` in most repos; otherwise
  `oca-gen-addon-readme --repo-name REPO --branch TGT --addon-dir MOD`.

Commit:

```bash
git add -A MOD && git commit -m "[MIG] MOD: Migration to TGT"
```

Extra fixes discovered during migration that also apply to SRC belong in a separate `[FIX]` PR
on SRC first (then ported); if they only make sense on TGT, add them as separate `[FIX]` commits
after the `[MIG]` commit in the same PR and mention them in the body.

## 5. Test

```bash
# with a local Odoo TGT checkout + database
python odoo-bin -d test_MOD -i MOD --test-enable --stop-after-init --addons-path=<paths>
# or with docker (example; adapt image/version)
docker run --rm -v "$PWD":/mnt/extra-addons odoo:TGT -d test -i MOD --test-enable --stop-after-init
```

Without a runnable Odoo, at minimum: `python -m py_compile` on all files, `xmllint --noout` on
XML, `pre-commit run -a`, and a careful read of every view against the target schema.

## 6. Push and PR

```bash
git push -u fork TGT-mig-MOD
gh pr create --repo OWNER/REPO --base TGT --head FORK:TGT-mig-MOD \
  --title "[TGT][MIG] MOD: Migration to TGT" --body-file pr-body.md --draft   # drop --draft in full mode
```

PR body template:

```markdown
Migration of `MOD` from SRC to TGT.

Part of #<migration issue number>

**Changes beyond the mechanical migration**
- <bullet per notable adaptation, e.g. "attrs replaced by invisible/readonly expressions">
- <ports of SRC PRs included or deliberately left out, with numbers>

**Testing**
- <tests run locally: yes/no; what CI should show>
```

Full mode only, if the module was unclaimed on the migration issue:

```bash
gh issue comment <migration issue> --repo OWNER/REPO --body "Working on MOD: #<pr number>"
```

## 7. After merge (not for the automation)

The OCA bot adds the module to the migration issue checklist and regenerates translations.
Nothing to do; note in **Follow-ups** which SRC PRs oca-port reported as not yet ported so a
`odoo-commit-porting` task can pick them up.
