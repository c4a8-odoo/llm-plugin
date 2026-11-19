# Functional review checklist

Tick what applies; the class column says where to look hardest. B = blocker, S = should, N = nit.
Structural questions (commits, manifest version, CI, style, docs) are not on this list; they
belong to `odoo-pr-review/references/pr-checklist.md`.

## Intent and behaviour (all classes)

| check | level |
|---|---|
| The diff does what the PR body and linked issue claim; nothing claimed is missing, nothing unclaimed is changed | B |
| Every case the changed code can meet is handled: empty recordset, several records, inactive records, records of another company, records without the optional relation | B |
| The UI path and the API/import path end in the same state (a default set in a view is not a default set in `create`) | S |
| Existing users keep their behaviour unless the PR body says otherwise; new behaviour is opt-in (setting, field default, group) when it changes results | S (B when it silently changes data) |
| Error paths raise `UserError`/`ValidationError` with a translated message the user can act on, not an `AssertionError` or a traceback | S |
| Nothing is computed, written or sent twice (duplicate triggers from a `write` override plus a compute, an onchange plus a constraint) | S |

## Models and business logic

| check | level |
|---|---|
| New model: `ir.model.access.csv` lines for every group that needs it; record rules if data is scoped per company or user | B |
| Compute methods: `@api.depends` precise and complete (missing dependency = stale value), assignment for every record in `self`, no dependency on context or on `self.env.user` for stored fields | B |
| Stored compute on a related chain that can change often: performance checked (number of records recomputed on a single write) | S |
| `create` is `@api.model_create_multi` and handles a list; `write`/`unlink` overrides call `super()` and return its result | B |
| `search` with `limit=1` has an `order`; searches respect `active` and company unless they must not; no `search`/`browse`/`env.ref` inside loops when one query does | S |
| `sudo()` justified in a comment, not fed with user input, and scoped to the smallest call (`.sudo().read(...)`, not the whole flow) | B |
| Raw SQL only when the ORM cannot do it, parametrised, `flush` before and `invalidate` after | B |
| `ensure_one()` where singleton semantics are assumed; methods called on multi-recordsets loop or use `mapped`/`filtered` | S |
| Invariants the UI relies on enforced in the model (`_sql_constraints`/`@api.constrains`), not only in a view attribute | S |
| Multi-company: `check_company=True` on company-scoped relations, `company_id` defaults from `self.env.company`, no cross-company reads via `sudo()` | S |
| Translations: `_()` with lazy formatting; nothing translated at import time; no concatenation of translated fragments | S |
| Dates and times: `fields.Date.context_today`, timezone-aware comparisons, no naive `datetime.now()` stored | S |
| `onchange` only for UI convenience; business rules live in computes or constraints so the API path gets them too | S |
| Default methods and `_order` do not depend on data that may not exist (demo records, a specific company) | S |

## Views and client

| check | level |
|---|---|
| View syntax valid on the target version (`attrs`/`states` gone in 17+, `<list>` in 18+, `t-out` in 16+); the view loads in the installed module | B |
| Inherited views use stable xpaths (`//field[@name='x']`), so other modules inheriting the same view keep working | S |
| Field visibility/readonly conditions match the model rules (a field required in a constraint is required in the form) | S |
| New menus and actions carry groups when they expose restricted data; new buttons check the same rights as the method they call | S |
| OWL components: `setup()` with hooks, state via `useState`, services via `useService`; no DOM access outside `onMounted`; no legacy `odoo.define` in 17+ | B in 17+ |
| Reports and QWeb: `t-out` escaping kept, user HTML sanitised, values from the right record in loops | S |

## Data, demo and migration scripts

| check | level |
|---|---|
| Fields removed, renamed or retyped have `migrations/<version>/` scripts (`openupgradelib`) and the review names a major bump | B |
| Migration scripts idempotent and guarded (`column_exists`, `table_exists`); pre-migrate for schema, post-migrate for data; end-migrate when both are needed | B |
| New data records (`noupdate="1"` for user-editable data) and their XML ids do not collide with existing ones; `ref` targets exist in the declared dependencies | S |
| Demo data exercises the new path and does not break the module's own tests | N |
| Removed or changed data records handled for existing databases (a record renamed in XML without migration becomes a duplicate) | B |

## Tests

| check | level |
|---|---|
| `[FIX]` includes a test that fails before and passes after the fix | S (B for regressions of released modules) |
| New behaviour covered: the happy path plus the constraint/permission path, with assertions on the resulting state, not only "no exception" | S |
| Tests use the same path as the user (the public method, the action, the wizard), not a private helper | S |
| Tests would fail if the change were reverted (no test that passes with or without the fix) | S |
| Multi-company and multi-record cases tested when the code branches on them | S |

## Ecosystem fit

| check | class | level |
|---|---|---|
| The change lives in the module that owns the behaviour; a change to another module's model goes to that module (or a new glue module) | all | S |
| No existing OCA module already provides it (search the repo, `gh search repos --owner OCA "<topic>"`, the OCA apps store); if one does, say which and suggest contributing there | ADD, IMP | B for a duplicate module, S for a duplicate feature |
| Extension points of Odoo used (`_inherit`, `_get_*`/`_prepare_*` hooks, view inheritance, `ir.config_parameter`) instead of copying core code, overriding whole methods or monkey-patching | all | S (B for monkey-patching core) |
| Methods and fields other modules use are not renamed or removed without a deprecation shim or a PR in each dependant | FIX, IMP, REF, MIG | B |
| Generic and configurable: no hard-coded company names, countries, journals, XML ids of a specific deployment | all | S |
| No Enterprise dependency or paid service unless the repo is meant for it; external services configurable and optional | all | B |
| Works around a core bug: the PR says so, links the `odoo/odoo` issue or PR, and keeps the workaround minimal and removable | FIX | S |
| Respects the module's stated scope (`DESCRIPTION.rst`); a feature outside it is a new module, not a growing one | IMP | S |
| Follows what sibling modules in the repo do for the same problem (naming of settings, groups, hooks) so the repo stays consistent | ADD, IMP | N |
| Keeps the module usable without the new optional dependency when the PR adds one (conditional import, separate glue module) | IMP | S |

## Class-specific

| check | class | level |
|---|---|---|
| Every item of `version-changes.md` for source..target handled: grep the module for the removed APIs, check renamed fields of core models, check changed signatures of overridden methods | MIG | B |
| Behaviour preserved after migration: compare with the source branch for every public method and view changed by the migration commit | MIG | B |
| The fix addresses the cause (where the wrong value is produced), not the symptom (where it is displayed) | FIX | S |
| Module and model naming consistent with OCA (`<topic>_<feature>`, model names prefixed by the module's domain); data model reviewed for required fields, relations, company scoping and indexes | ADD | S |
| Backwards compatible for data and for dependants; a changed default documented in `readme/` | IMP | S |
| Behaviour unchanged and tests still meaningful after the refactor | REF | S |

## Things not to comment on

- Formatting, naming, commit messages, manifest version, CI status, README fragments: that is
  `odoo-pr-review`.
- Personal style preferences without a correctness, performance or convention reason.
- Items already raised by another reviewer and still open.
- Pre-existing problems in lines the PR does not touch, unless they make the PR's own change
  wrong; mention them once under **Follow-ups** instead.
