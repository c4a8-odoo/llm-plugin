# Odoo security checklist

Per category: what to grep for, what turns a hit into a finding, and typical severity.
Run greps from the module folder (`git grep -n -E '<pattern>' -- <module>`). The patterns are
starting points, not oracles; read the code around every hit.

## 1. Access control: ACLs and record rules

Grep: `ir.model.access.csv`, `<record model="ir.rule"`, `_name = `, `_inherit = `, `groups=`,
`perm_unlink`, `global`.

Finding when:
- A new model has no `ir.model.access.csv` line at all (nobody can use it; someone adds `sudo()`
  later) or has `perm_write/perm_unlink = 1` for `base.group_user` on data that should be
  restricted (configuration, pricing, HR data). Severity: medium (over-permissive), low (missing).
- A model that carries company or partner data has no record rule, or the rule's `domain_force`
  is `[(1, '=', 1)]`, or the rule is `global="0"` without being attached to a group (then it does
  nothing). Multi-company leak: medium to high depending on data.
- A `groups` attribute on a sensitive field is missing while the view hides it: hiding is not
  access control; `read()` via RPC still returns it. Medium if the field is sensitive.
- A portal/public user group gets `perm_read` on a model without a matching record rule
  restricting rows to the user. High.
- Record rules on `res.partner`, `res.users` or `mail.*` loosened by the module. High.

## 2. Privilege escalation: `sudo()`, `with_user`, `SUPERUSER_ID`

Grep: `\.sudo\(`, `with_user\(`, `SUPERUSER_ID`, `su=True`, `check_access_rights\(`,
`_check_access`, `has_group\(`.

Finding when:
- `sudo()` applied to a recordset built from user-supplied ids, domain or search terms, and the
  result (or a derived value: count, name, existence) is returned to the user. Information
  disclosure, medium; high if the data is personal or financial or the caller is public/portal.
- `sudo().write/unlink/create` on records the user does not own with values from the request.
  High; critical if it reaches `res.users`, `res.groups`, `ir.*`, `res.company`.
- `sudo()` used to bypass a record rule the module itself added (the author worked around their
  own ACL). Medium.
- `sudo()` taken early (`self.env['model'].sudo()`) and then propagated through helper calls so
  the whole call chain runs as superuser. Medium, note as design smell even if no path is proven.
- Acceptable: reading `ir.config_parameter` system settings, sequences, mail templates, creating
  `mail.message`/`mail.activity`, with a comment explaining it. Do not report these.

## 3. SQL injection

Grep: `cr\.execute\(`, `_cr\.execute`, `execute\(f"`, `execute\(".*%`, `\.format\(`, `SQL\(`,
`query\.add_where`, `_where_calc`, `order_by`, `_order`, `psycopg2\.sql`.

Finding when:
- `execute` with f-string, `%` operator or `.format()` where any interpolated value can come from
  outside: field values, context keys, `order`, `groupby`, column or table names derived from
  user input. Critical when reachable by portal/public, high for internal users.
- `_order` / `order` parameter passed through to SQL without validation against known fields.
- Table/column names built from `self._table` or `field.name` are fine; from `self.env.context`
  or request params they are not.
- 17+: `SQL("... %s", value)` is parametrised; `SQL(f"...")` is not. Check which.
- Note also missing `flush`/`invalidate` around raw SQL as low (correctness, but can be used to
  read stale permissions).

## 4. Code evaluation

Grep: `safe_eval\(`, `\beval\(`, `\bexec\(`, `literal_eval`, `pickle`, `marshal`, `__import__`,
`getattr\(.*request`, `importlib`.

Finding when:
- `eval`/`exec` on anything: critical unless the input is a hard-coded literal.
- `safe_eval` on a string that users can write (a configurable domain, a formula field, an email
  template parameter) without the standard `mode="eval"` and locals control. Medium; high if the
  field is editable by non-admin groups (check the ACL of the model that stores it).
- `pickle.loads` / `marshal.loads` on stored or received data. Critical.
- `getattr(record, request.params['method'])()` style dispatch: high.

## 5. Controllers and RPC surface

Grep: `@http\.route`, `auth=`, `csrf=`, `methods=`, `type="json"`, `type="http"`, `request\.env`,
`request\.params`, `request\.httprequest`, `redirect\(`, `website=True`, `cors=`, `@api\.model`
(public RPC entry points on models).

Finding when:
- `auth="public"` or `auth="none"` routes that read or write records without a token check
  (`_document_check_access`, `_check_access_token`, portal `access_token`) or a restrictive
  record rule for the public user. High; critical for write/unlink.
- `csrf=False` on a `POST` route that changes state and is `auth="user"`. Medium (CSRF); high
  if the action is sensitive.
- Open redirect: `redirect(request.params.get("redirect"))` without checking it is a relative URL.
  Medium.
- Routes that return `request.env[...].sudo().search_read(...)` with a domain from the request.
  High.
- Model methods decorated `@api.model` and callable via RPC that return data of other records or
  perform privileged operations; every public method on a model is an RPC endpoint for anyone
  with model access. Medium, raise if it uses `sudo()`.
- JSON routes echoing exceptions with internal detail: info/low.
- `cors="*"` on anything authenticated: medium.

## 6. Templates, QWeb and HTML (XSS)

Grep: `t-raw`, `t-out`, `t-esc`, `Markup\(`, `markupsafe`, `fields\.Html`, `sanitize=False`,
`sanitize_attributes=False`, `sanitize_tags=False`, `strip_style`, `innerHTML`, `\$\(.*\)\.html\(`,
`t-att-href`, `javascript:`, `dangerouslySetInnerHTML`.

Finding when:
- `t-raw` (pre-16) or `t-out` with a `Markup()` wrapper around a value a user can influence
  (names, descriptions, imported text). High.
- `fields.Html(sanitize=False)` writable by non-admin users and rendered to other users (reports,
  portal, mail). High. `sanitize_attributes=False`/`sanitize_tags=False` same reasoning, medium.
- JS: `innerHTML =`, jQuery `.html()`, `.append("<..."+value+"...")` with record data. Medium.
- `t-att-href` with a user-controlled URL (allows `javascript:`). Medium.
- Mail templates (`mail.template` body) interpolating user content via `{{ }}` are escaped by
  default; `| safe` or `Markup` disables it. Medium.

## 7. Files, attachments and paths

Grep: `open\(`, `os\.path`, `os\.remove`, `shutil`, `tempfile`, `zipfile`, `tarfile`, `base64\.b64decode`,
`ir\.attachment`, `content_disposition`, `send_file`, `mimetype`, `request\.httprequest\.files`,
`\.\./`, `file_open\(`.

Finding when:
- Path built from user input without normalisation and prefix check (path traversal). High;
  critical if it reaches write/delete or Odoo's `data_dir`.
- Zip/tar extraction from uploads without member path validation or size limits. High.
- Serving attachments via a custom route without `ir.attachment` access checks (`check('read')`),
  bypassing `res_model`/`res_id` rules. High.
- Uploads with `mimetype` taken from the client and served inline (stored XSS via SVG/HTML). Medium.
- `tools.file_open` with a user-influenced relative path: medium.

## 8. Secrets, crypto, randomness

Grep: `password`, `passwd`, `secret`, `api_key`, `token`, `Bearer`, `hashlib\.md5`, `sha1\(`,
`random\.`, `uuid1`, `hmac`, `verify=False`, `-----BEGIN`.

Finding when:
- Hard-coded credentials, tokens, private keys, even for "test" services. High (critical if they
  look live; recommend rotation, do not paste the value into the report).
- Secrets stored in `ir.config_parameter` without `groups="base.group_system"` on the settings
  field, or logged by `_logger` at info level. Medium.
- `random.random`/`random.choice` for access tokens; should be `secrets` or `uuid4`. Medium.
- MD5/SHA1 for anything security-relevant (passwords, signatures). Medium.
- `requests.get(..., verify=False)`: medium.

## 9. External calls and SSRF

Grep: `requests\.`, `urllib`, `urlopen`, `http\.client`, `socket\.`, `smtplib`, `ftplib`, `timeout`.

Finding when:
- URL built from user-editable configuration or record data and fetched server-side without an
  allowlist (SSRF). Medium; high if the response is returned to the user or if the host can be
  internal (`localhost`, metadata endpoints).
- No `timeout` on outgoing requests: low (DoS via hanging worker), always mention.
- Credentials sent to a URL that is user-configurable: medium.

## 10. Data exposure through the ORM

Grep: `_name_search`, `_search_display_name`, `_compute_display_name`, `name_get`, `_rec_name`,
`search_read`, `read_group`, `_read_group`, `export_data`, `fields_get`, `web_search_read`,
`tracking=True`, `mail.thread`, `_mail_post_access`, `portal.mixin`.

Finding when:
- `_name_search`/display name reveals data from a related record the user may not read
  (searching a partner by a confidential field). Low to medium.
- Fields with `tracking=True` on confidential data that then appears in chatter visible to
  followers/portal. Medium.
- `_mail_post_access = 'read'` on a model where posting should need write. Low to medium.
- `portal.mixin` models whose `_compute_access_url` or `_get_report_base_filename` leaks data
  to users without a token. Medium.
- `fields.Binary(attachment=False)` exposed via `web/content` without `groups`: low.

## 11. Business logic and integrity

Grep: `_sql_constraints`, `@api\.constrains`, `check_company`, `_check_company_auto`,
`readonly=True`, `states=`, `active`, `float_compare`, `float_round`, `Decimal`.

Finding when:
- A state machine (quotation to confirmed, expense to approved) changeable by `write()` of the
  state field without the button method: users with write access skip the approval. Medium.
- Amounts recomputed from client-provided values without server-side validation. Medium.
- `readonly=True` in the view only (the field stays writable via RPC) on fields users must not
  change. Low to medium depending on the field.
- Missing `check_company=True` on `Many2one` to company-dependent models: multi-company data
  mix-up, low to medium.

## 12. Dependencies and manifest

Grep: `external_dependencies`, `requirements.txt`, `pip`, `assets`, `http://`, `cdn`, `<script src=`.

Finding when:
- External JS/CSS loaded from a CDN at runtime (supply chain, CSP). Medium.
- Python dependencies pinned to versions with known CVEs, or unpinned packages that are not in
  Odoo's own requirements. Low to medium; verify before claiming a CVE.
- `auto_install: True` on a module that widens access (installs silently everywhere). Low.

## Not findings (do not report)

- Style, naming, missing tests, performance without a security angle: those belong to the code
  review, not here.
- Odoo core behaviour the module merely inherits unchanged.
- `sudo()` with a correct explanatory comment and no user-controlled input reaching it.
- Hypotheticals that need a compromised admin account to start with.
