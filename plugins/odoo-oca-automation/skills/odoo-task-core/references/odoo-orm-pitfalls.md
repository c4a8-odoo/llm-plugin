# Odoo API and ORM pitfalls

Things that compile, pass a smoke test and still hurt in production. Use this list when
reviewing code or before committing your own. Each item: what to look for, why it matters,
what to do instead.

## Records and recordsets

- **Singleton assumptions.** `self.field` on a multi-record `self` raises `ValueError: Expected singleton`.
  Loop with `for rec in self:` or call `self.ensure_one()` when a single record is a hard requirement.
- **Modifying `self` while iterating** (`self -= rec`, `self.write` in a loop over `self`) gives
  surprising results; collect into a new recordset first.
- **`browse()` without existence check.** `self.env["res.partner"].browse(id)` never fails; accessing
  a field on a missing id does. Use `.exists()` when ids come from outside.
- **Comparing records with ids.** `rec.partner_id == 5` is always False. Compare records with records
  or use `.id`.

## Compute, depends, onchange

- **Missing `@api.depends`** triggers stale values; **too broad `@api.depends`** (for example on `*_ids`)
  recomputes on every line change. Depend on the precise field paths.
- **Compute without assignment for every record** leaves some records with the previous or default
  value (and in 13+ raises at flush). Assign inside the loop for every `rec`.
- **Stored compute depending on context or on `self.env.user`** is wrong by construction; use
  `@api.depends_context` for non-stored, or do not store.
- **`@api.onchange` for business logic.** Onchange only runs in the UI; imports, RPC and other
  modules bypass it. Prefer computed fields with `readonly=False` (store=True) in 13+.
- **Computed field written by `write()` override** while also having a compute: pick one source
  of truth.

## Search and performance

- **Queries in loops.** `search`, `search_count`, `browse().field` access and `env.ref` inside
  `for rec in self:` scale linearly. Prefetch (`self.mapped("partner_id")`), use `read_group` /
  `_read_group`, or search once with `in` and group in Python.
- **`search([])` with `limit=1` without `order`** returns an arbitrary record. State the order.
- **`active_test`**: `search` hides archived records unless `with_context(active_test=False)`;
  `browse` and `x2many` fields do not. Decide which you need.
- **`sudo()` before `search`** bypasses record rules and multi-company filtering; it is also an
  information disclosure (see the security checklist). Use `with_company`, `with_user`, or
  `check_access_rights` explicitly instead.
- **`mapped` on large recordsets then `filtered` in Python** when a domain would do.
- **`cr.execute` with string formatting.** Never. Use parameters (`%s` with a tuple) or the `SQL`
  helper in 17+. Also remember to `invalidate`/`flush` around raw SQL: `self.env.flush_all()` before
  reading, `self.env.invalidate_all()` (or targeted `invalidate_recordset`) after writing.

## Create and write

- **`create` not decorated with `@api.model_create_multi`** or treating `vals` as a dict when it
  is a list. In 13+ `vals_list` is the norm; 18 removes single-dict `create` for new overrides.
- **Override of `write` that reads `self.field` after `super()`** to detect change: compare before
  and after explicitly, or use the `vals` dict.
- **Default values via `default=lambda self: self.env.user.company_id`** on a company-dependent field
  should use `self.env.company`.
- **Commit inside business code** (`self.env.cr.commit()`) breaks the transaction model; only in
  crons/queue jobs with a clear reason.

## Security and access (details in the security checklist)

- `sudo()` without a comment explaining why. `with_user(SUPERUSER_ID)` same.
- Public controllers (`auth="public"`/`"none"`) returning records without a `_check_access` or
  access token check.
- `fields.Html(sanitize=False)`, `t-raw` (removed in 16), `Markup()` on user input.
- Missing `ir.model.access.csv` lines for new models (installing with no ACL is silently
  "no access"; then someone adds `sudo()`).

## Views and client side

- `attrs`/`states` in 17+ views fail at load; `<tree>` in 18+ emits a deprecation and breaks in 19.
- `t-esc` is deprecated since 16, `t-raw` removed; use `t-out` and `Markup` for trusted HTML.
- JS: legacy `odoo.define` modules are gone in 17 for most of the web client; use ES modules with
  `/** @odoo-module **/` and `@web` imports; OWL 2 lifecycle (`setup()` instead of constructor).
- Asset bundles belong in the manifest `assets` key, not in XML `<template inherit_id="web.assets_backend">`
  (removed in 15+).

## Translations and strings

- `_("Text %s" % value)` translates after formatting (never matches); use `_("Text %s", value)` (14+)
  or `_("Text %(name)s", name=value)`.
- f-strings inside `_()` have the same problem.
- Strings built by concatenation cannot be translated as a unit.

## Tests

- Tests that depend on demo data from other modules without declaring the dependency.
- `TransactionCase` tests that call `cr.commit()`.
- Missing `tracking_disable=True` in `setUpClass` context, which slows tests and creates mail noise.
- HttpCase tours not tagged `post_install`.
- Tests asserting on translated strings or on `display_name` formatting that another module may change.

## Migration-sensitive APIs

- `name_get` (removed 17) -> `_compute_display_name`.
- `_name_search` signature changes (17) and removal in favour of `_search_display_name` (18).
- `fields_view_get` -> `get_view` (16), `_get_view` (17).
- `read_group` kept, but internal `_read_group` signature changed in 17 (`domain, groupby, aggregates`).
- `user_has_groups` deprecated (17) -> `self.env.user.has_group()`.
- `fields.Char(translate=True)` stored as JSONB since 16: raw SQL on translated fields must use
  `->>'en_US'` or the ORM.
Check the version-change reference of the migration skill for the complete list per version.
