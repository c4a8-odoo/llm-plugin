# Version-to-version changes

Checklist per migration step, with grep patterns to find affected code. This is a working
summary from the OCA migration wiki pages and Odoo release notes; items marked `(verify)` are
known to vary or to have landed in a point release, so confirm them against the target branch
(`git grep` in an `odoo/odoo` checkout of the target version, or the wiki page) before relying
on them. When a grep hits nothing, move on; when it hits, read the core implementation on the
target branch to see what replaced it.

## 14.0 -> 15.0

| area | change | grep |
|---|---|---|
| assets | asset bundles move from XML `<template inherit_id="web.assets_backend">` to the manifest `assets` key | `assets_backend`, `assets_frontend`, `assets_common`, `inherit_id="web\.` |
| qweb js templates | `qweb` manifest key stays in 15 but templates may move to `web.assets_qweb` bundle | `"qweb"` |
| python | `odoo.tools.pycompat` removals; `werkzeug` 2 (`url_encode` from `werkzeug.urls`) | `pycompat`, `werkzeug\.` |
| mail | `message_post` returns message; `mail.thread` methods renamed `_message_log` etc. (verify) | `message_post\(`, `_message_` |
| views | `<field widget="many2many_tags" options="{'no_create': True}">` unchanged; `kanban` templates use `t-name="kanban-box"` | - |
| tests | `odoo.tests.common.SavepointCase` deprecated alias of `TransactionCase` | `SavepointCase` |
| website | `website.layout` structure changes; snippets with `data-snippet` | `website\.layout` |

## 15.0 -> 16.0

| area | change | grep |
|---|---|---|
| js modules | legacy `odoo.define` replaced by ES modules `/** @odoo-module **/`; OWL 2 (`setup()` instead of constructor, `useState`, no `willStart` mutations) | `odoo\.define`, `Widget\.extend`, `willStart`, `mounted` |
| qweb | `t-esc` deprecated, `t-raw` removed, use `t-out`; trusted HTML via `Markup` | `t-raw`, `t-esc` |
| views | `fields_view_get` -> `get_view`; `_fields_view_get` -> `_get_view` | `fields_view_get` |
| translations | translated `Char`/`Text`/`Html` stored as JSONB; raw SQL on them needs `->>'en_US'`; `ir.translation` model removed | `ir\.translation`, `_get_translation`, `translate=True` with SQL |
| manifest | `qweb` key removed, templates go to `web.assets_backend`/`web.assets_qweb` (verify per repo) | `"qweb"` |
| orm | `_name_search` gains `name_get_uid`? (verify), `name_search` kept; `fields.Many2one(check_company=True)` default behaviour change for `company_id` domains | `_name_search` |
| orm | `env.ref(..., raise_if_not_found)` unchanged; `self.env.user.company_ids` vs `company_id` conventions | - |
| mail | `mail.template` body uses inline QWeb `{{ }}` instead of Jinja `${}` | `\$\{`, `%\s*if`, `body_html` |
| accounting | `account.move.line` fields reshuffle (`price_subtotal`, `tax_ids` on moves); `_get_computed_*` methods renamed | `account\.move` overrides |
| tests | `TransactionCase.setUpClass` convention; `SavepointCase` removed | `SavepointCase` |
| python | Python 3.10 baseline; `datetime.utcnow` still OK | - |

## 16.0 -> 17.0

| area | change | grep |
|---|---|---|
| views | `attrs` and `states` removed; use `invisible="expr"`, `readonly="expr"`, `required="expr"`, `column_invisible` for list columns | `attrs=`, `states=` |
| views | `<field name="..." groups="..."/>` unchanged; `<tree>` still valid (becomes `<list>` in 18) | - |
| orm | `name_get` removed -> `_compute_display_name` (`display_name` is a stored-less computed field with `@api.depends`) | `name_get` |
| orm | `_name_search` signature `(name, domain=None, operator='ilike', limit=None, order=None)` returning a Query/ids (verify) | `_name_search` |
| orm | `_read_group` new signature `(domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None)` returning tuples; public `read_group` kept | `_read_group\(`, `read_group\(` |
| orm | `fields.Many2one(..., ondelete=...)` unchanged; `fields.Properties` matured; `_check_company_auto` conventions | - |
| orm | `user_has_groups` deprecated (removed 18) -> `self.env.user.has_group()`; `self.user_has_groups` in views `groups=` unaffected | `user_has_groups` |
| sql | `odoo.tools.SQL` wrapper introduced; `Query.where_clause` tuple API changes; `_where_calc` returns Query | `_where_calc`, `where_clause` |
| web client | legacy views and `web.basic_fields` removed; everything OWL; `registry.category("fields")`; `useService("orm")` | `basic_fields`, `web\.AbstractField`, `FieldChar`, `require\(` |
| controllers | `request.env.user` fine; `request.render` unchanged; `http.route` `readonly` param added (verify) | - |
| mail | `mail.thread` `_message_get_suggested_recipients` signature; `message_post` `partner_ids` only; `mail.activity` changes | `_message_get_suggested_recipients` |
| python | Python 3.10 baseline; `distutils` removed in 3.12 (CI runs 3.10) | `distutils` |
| tests | `@tagged` unchanged; `odoo.tests.Form` API unchanged | - |

## 17.0 -> 18.0

| area | change | grep |
|---|---|---|
| views | `<tree>` -> `<list>`; `view_mode="tree,form"` -> `"list,form"`; `<field ... widget="handle">` unchanged | `<tree`, `</tree>`, `view_mode=".*tree` |
| orm | `user_has_groups` removed -> `self.env.user.has_group()`; `has_group` accepts comma-separated groups (verify) | `user_has_groups` |
| orm | `_name_search` removed -> `_search_display_name(operator, value)` returning a domain | `_name_search` |
| orm | `search_fetch`, `fetch` promoted; `read` with `load=None` conventions | - |
| orm | `fields.Many2one` `delegate` unchanged; `fields.Selection` `ondelete` required for added selection values on inherited fields (since 13, enforced) | `selection_add` |
| orm | `_compute_display_name` is the only way; `display_name` depends must be declared | `name_get` |
| orm | `env.cr.execute` with `SQL()` objects recommended; `psycopg2.sql` still works | - |
| web client | `web.assets_backend` unchanged; `@web/core/l10n/translation` `_t`; `env.services.orm`; kanban templates `t-name="card"` replaces `kanban-box` (verify) | `kanban-box` |
| web client | `tree` arch in JS `views` registry becomes `list` | `"tree"` in JS |
| mail | `mail.thread` `_track_subtype`, `_mail_track`, `message_post` `body` must be `Markup` or escaped string; `mail.template` `email_layout_xmlid` | `message_post\(` |
| python | Python 3.10 minimum, 3.12 supported; `pkg_resources` deprecated -> `importlib.metadata` | `pkg_resources` |
| accounting | `account.move` `l10n` restructuring; `account.payment.register` wizard changes | `account\.` overrides |
| website | `website.page` / snippets `data-snippet` options rework; `s_` snippet naming | `snippets` |

## 18.0 -> 19.0 (verify everything; branch still moving at time of writing)

| area | change | grep |
|---|---|---|
| users/groups | `res.users.groups_id` -> `group_ids`; `res.groups` gains `privilege_id`; `implied_ids` semantics; `category_id` on groups moved (verify) | `groups_id`, `implied_ids` |
| views | `<tree>` no longer accepted; `attrs` long gone; `<form>` `js_class` conventions | `<tree` |
| orm | `fields.Char(trim=...)` kept; `_rec_names_search` for display name search; `_order` on `display_name` | `_rec_names_search` |
| orm | `read_group` public API deprecated in favour of `_read_group`/`formatted_read_group` (verify) | `read_group\(` |
| web client | `@web/views/...` paths reorganised; `useService("action")` unchanged | import paths |
| python | Python 3.11 minimum (verify); `typing` features allowed | - |
| mail | `mail.thread` `_notify_thread` and `_message_auto_subscribe` changes | `_notify_` |

## 19.0 -> 20.0 (next version; fill in from the OCA wiki page and odoo/odoo master as it stabilises)

| area | change | grep |
|---|---|---|
| process | the OCA "Migration to version 20.0" issue and `20.0` branches appear shortly after the Odoo release; until then, treat 20.0 work as plan-only | - |
| views | anything still using `<tree>`, `attrs`, `states`, `t-esc` is dead code by now | `<tree`, `attrs=`, `states=`, `t-esc` |
| users/groups | the 19.0 groups rework (`group_ids`, privileges) is the baseline; check `implied_ids` usage and group xml ids referenced in `security/` | `groups_id`, `implied_ids` |
| orm | watch `read_group` deprecation status, `_search_display_name`, `search_fetch` adoption | `read_group\(`, `_name_search` |
| web client | follow import path moves under `@web/`; check OWL version in `web/static/lib/owl` | import paths |
| python | confirm minimum Python version in `odoo/setup.py` / `requirements.txt` of 20.0 | - |

Add rows here as the 20.0 migration guide fills in; mark each as verified with the commit or
wiki revision you checked.

## Always, every step

- Manifest `version` string; drop `qweb`/`description` keys; `license` present.
- `migrations/` folders for old versions removed.
- Core modules the module depends on: check they still exist (`hr_expense` splits, `website_*`
  merges, `l10n_*` renames) and that fields/methods overridden still exist on the target branch.
- Demo data referencing core xml ids: verify the ids exist on the target.
- `i18n/` untouched.
- Run the module's tests on the target; failures there are the most reliable migration guide.
