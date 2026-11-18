# Review checklist

Tick what applies; the class column says where to look hardest. B = blocker, S = should, N = nit.

## PR hygiene (all classes)

| check | level |
|---|---|
| Title `[<version>][TAG] module: summary`, base branch = version | S (B if wrong branch) |
| One logical change per PR; `[MIG]` PRs contain only the migration (fixes go to the source version first, then get ported) | B |
| Commit messages follow `[TAG] module: ...`; no "fixup", "wip", merge commits | S |
| CI green (`gh pr checks`); if red, the review says which job and why | B if tests fail, S if only lint |
| PR body explains the change and how to test; links issue / migration issue | S |
| Author added to `readme/CONTRIBUTORS.rst` when the change is more than a typo | N |

## Manifest and metadata

| check | class | level |
|---|---|---|
| Manifest `version` untouched (the OCA bot bumps at merge); the review summary names the bump size for the merge command (patch/minor/major; nobump for README/CI). A manual bump is a remark to revert, except when migration scripts need the folder name | FIX, IMP, REF | S |
| `[MIG]`: version `X.0.1.0.0`, `installable: True`, old `migrations/` folders removed | MIG | B |
| `[ADD]`: all manifest keys per OCA conventions, `development_status`, `maintainers`, icon, readme fragments, `security/`, tests | ADD | B |
| `depends` minimal and complete (every `env[...]`, `_inherit`, xml `ref` has a dependency) | all | S |
| `external_dependencies` declared for every non-Odoo import | all | B |
| `assets` key used, no XML asset templates (15+) | all | S |

## Models and business logic

| check | level |
|---|---|
| New model: `ir.model.access.csv` lines for every group that needs it; record rules if data is scoped | B |
| Compute methods: `@api.depends` precise, assignment for every record, no store+context dependency | B |
| `create` is `@api.model_create_multi` and handles a list | S (B in 17+) |
| `write`/`unlink` overrides call `super()` and return its result | B |
| No `search`/`browse`/`env.ref` inside loops without need; no `search([])` with `limit=1` without order | S |
| `sudo()` justified in a comment and not fed with user input | B |
| Raw SQL parametrised, flush/invalidate around it | B |
| Translations `_()` on user-facing strings, lazy formatting (`_("x %s", y)`) | S |
| `ensure_one()` where singleton semantics are assumed | S |
| `_sql_constraints`/`@api.constrains` for invariants the UI relies on | S |
| Multi-company: `check_company`, `company_id` defaults from `self.env.company` | S |
| Removed/renamed fields have migration scripts (`openupgradelib`) and a major bump | B |

## Views and client

| check | level |
|---|---|
| No `attrs`/`states` in 17+; `<list>` not `<tree>` in 18+; `t-out` not `t-esc`/`t-raw` in 16+ | B |
| Inherited views use stable xpaths (`//field[@name='x']`), not `position` on volatile structure | S |
| New menus/actions have groups when they expose restricted data | S |
| JS as ES modules (`/** @odoo-module **/`), OWL components with `setup()`, no legacy `odoo.define` in 17+ | B in 17+ |
| Assets globbed per module path; no third-party CDN URLs | S |
| Reports: `t-out` escaping, no inline user HTML without sanitize | S |

## Tests

| check | level |
|---|---|
| `[FIX]` includes a test that fails before and passes after | S (B for regressions of released modules) |
| New features covered: at least the happy path plus the constraint/permission path | S |
| `TransactionCase` with `setUpClass`, `tracking_disable`, no `cr.commit`, no sleep | S |
| Tour/`HttpCase` tagged `post_install -at_install` | S |
| Tests do not depend on demo data of undeclared modules | S |

## Documentation

| check | level |
|---|---|
| `readme/DESCRIPTION.rst` describes what and why; `USAGE.rst`/`CONFIGURE.rst` when a user must do something | S |
| `README.rst` and `static/description/index.html` regenerated (pre-commit does it in most repos; if not, mention `oca-gen-addon-readme`) | N |
| `ROADMAP.rst` lists known limitations introduced by the PR | N |

## Migration-specific (`[MIG]`)

| check | level |
|---|---|
| History preserved (commits from the source branch via `oca-port` or `format-patch`), not a squashed copy | B |
| Separate `[IMP] module: pre-commit stuff` (or black/isort/prettier) commit before the `[MIG]` commit | S |
| Every item of `version-changes.md` for source..target handled; grep the module for the removed APIs | B |
| Dependencies exist on the target branch (check each depend is installable there) | B |
| `i18n/*.po` left untouched (bot regenerates), `.pot` not hand-edited | S |
| Migration issue referenced (`Part of #...`) | N |

## Things not to comment on

- Formatting that pre-commit will fix or already enforces.
- Personal style preferences without a correctness, performance or convention reason.
- Items already raised by another reviewer and still open.
