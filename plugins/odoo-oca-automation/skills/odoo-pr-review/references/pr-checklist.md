# PR structure checklist

Tick what applies; the class column says where to look hardest. B = blocker, S = should, N = nit.
Functional questions (does it work, is it the right approach, are the tests meaningful) are not
on this list; they belong to `odoo-code-review/references/review-checklist.md`.

## PR hygiene (all classes)

| check | level |
|---|---|
| Title `[<version>][TAG] module: summary`; base branch = version | S (B if wrong branch) |
| One logical change per PR; `[MIG]` PRs contain only the migration (fixes go to the source version first, then get ported) | B |
| PR body explains the change and how to test; links the issue (`Closes #`, `Related to #`) or the migration issue (`Part of #`); ports say `Forward-port of #` / `Backport of #` | S |
| Manifest maintainers mentioned in the body or PR comments so they are pinged | N |
| Not a duplicate of an open PR for the same module and topic (`gh pr list --search`) | S |
| Draft status matches the author's intent (a draft asking for review is fine; a ready PR with "WIP" in the title is not) | N |

## Commits

| check | level |
|---|---|
| Every commit `[TAG] module: short imperative summary`; tag matches the content (`[FIX]` for bug fixes, `[IMP]` for improvements, `[REF]` for behaviour-preserving refactors) | S |
| Module name in the commit matches the module touched; several modules listed comma-separated | S |
| Body says why, wrapped at 72 characters; no "fix review", "fixup", "wip", "update", merge commits | S |
| One logical change per commit; formatting-only changes in their own commit | S |
| Ports keep the `(cherry picked from commit <sha>)` trailer | S |
| AI-assisted commits carry an `Assisted-by:` trailer, not `Co-Authored-By:` | N |
| No commits that only revert earlier commits of the same PR (squash them) | N |

## Manifest and metadata

| check | class | level |
|---|---|---|
| Manifest `version` untouched (the OCA bot bumps at merge); the review summary names the bump size for the merge command (patch/minor/major; nobump for README/CI only). A manual bump is a remark to revert, except when migration scripts need the folder name | FIX, IMP, REF | S |
| `[MIG]`: version `X.0.1.0.0`, `installable: True`, old `migrations/` folders removed | MIG | B |
| `[ADD]`: all manifest keys per OCA conventions (`name`, `summary`, `version`, `category`, `website` = repo URL, `author` includes "Odoo Community Association (OCA)", `license`, `depends`, `data`, `demo`, `development_status`, `maintainers`), icon, readme fragments, `security/`, `tests/` | ADD | B |
| `depends` minimal and complete (every `env[...]`, `_inherit`, xml `ref`, `inherit_id` has a dependency); every dependency installable on the target branch | all | S |
| `external_dependencies` declared for every non-Odoo import; the pip name is right | all | B |
| `assets` key used; no XML asset templates (15+) | all | S |
| `data` and `demo` lists match the files present; no stale or missing entries | all | S |
| `development_status` consistent with the change (`Beta` for new modules, not `Production/Stable`) | ADD | N |

## Build pipeline

| check | level |
|---|---|
| All checks reported (`gh pr checks`); a missing job (CI not triggered, runboat not started) is named in the review | S |
| pre-commit job green; if red: one comment asking to run `pre-commit run -a` locally, never a per-hook list | S |
| Test job green; if red: say which test fails, quote the one-line cause, and whether the PR introduced it (compare with the base branch's latest run) | B if the module's tests fail, S if an unrelated module fails on the branch |
| Runboat build exists and is green; UI changes get a reminder that a manual check on runboat is needed | S |
| Codecov: coverage drop only matters when the PR adds untested code | N |
| CI configuration changes (`.github/`, `.pre-commit-config.yaml`, `oca_dependencies.txt`, `test-requirements.txt`) justified in the PR body and limited to what the PR needs | S |
| `test-requirements.txt` / `oca_dependencies.txt` updated when a new external or OCA dependency was added | B |

## Coding style beyond pre-commit

| check | level |
|---|---|
| Python files start with the copyright and license header (`# Copyright <year> <author>` / `# License AGPL-3.0 or later ...`), no encoding line | S |
| Model files named after the model, one model per file; `_inherit` without `_name` unless a new model | S |
| XML ids follow the conventions (`view_<model>_<type>`, `action_<name>`, `menu_<name>`, `rule_<model>_<scope>`, `group_<name>`); one XML file per model or purpose under `views/`, `security/`, `data/` | S |
| User-facing strings wrapped in `_()`, lazy formatting (`_("x %s", y)`); `_logger`, never `print` | S |
| View syntax of the target version (no `attrs`/`states` in 17+, `<list>` not `<tree>` in 18+, `t-out` not `t-esc`/`t-raw` in 16+) | B (install breaks) |
| JS files as ES modules (`/** @odoo-module **/`), no legacy `odoo.define` in 17+; assets globbed per module path, no third-party CDN URLs | S (B in 17+ for legacy define) |
| Tests under `tests/` with `__init__.py` imports; `TransactionCase`/`HttpCase` with `setUpClass`, `tracking_disable`, no `cr.commit`, no sleep; tours and `HttpCase` tagged `post_install -at_install` | S |
| Tests do not depend on demo data of undeclared modules | S |
| No commented-out code, debugging leftovers (`pdb`, `print`, `console.log`), or unrelated whitespace churn | N |
| No `# noqa`, `# pylint: disable` or pre-commit `exclude` added without a one-line reason | S |

## Documentation and generated files

| check | level |
|---|---|
| `readme/DESCRIPTION.rst` describes what and why; `USAGE.rst`/`CONFIGURE.rst` updated when a user must do something new | S |
| `README.rst` and `static/description/index.html` regenerated (pre-commit does it in most repos; otherwise mention `oca-gen-addon-readme`) and consistent with the fragments | N |
| `readme/CONTRIBUTORS.rst` lists the author when the change is more than a typo | N |
| `ROADMAP.rst` lists known limitations introduced by the PR | N |
| `i18n/*.po` and `.pot` untouched (the bot regenerates after merge) | S |
| `migrations/<version>/` folder name matches the manifest version the scripts run for | B |

## Migration-specific (`[MIG]`)

| check | level |
|---|---|
| History preserved (commits from the source branch via `oca-port` or `format-patch`), not a squashed copy | B |
| Separate `[IMP] module: pre-commit stuff` (or black/isort/prettier) commit before the `[MIG]` commit | S |
| `[MIG] module: Migration to <version>` is the last commit and contains only the migration | S |
| Dependencies exist on the target branch (each depend installable there; otherwise the PR body names the blocking PR) | B |
| Migration issue referenced (`Part of #...`) and the module claimed there | N |

## Things not to comment on

- Formatting that pre-commit will fix or already enforces.
- Personal style preferences without a convention behind them.
- Items already raised by another reviewer and still open.
- Whether the change works, is complete or is the right approach: that is `odoo-code-review`.
