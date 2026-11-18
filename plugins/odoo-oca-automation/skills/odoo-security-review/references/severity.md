# Severity rubric

Severity combines who can trigger the issue and what it yields. Pick the row that fits the
weakest attacker who can reach the code; then adjust one step down if exploitation needs an
unlikely configuration, one step up if the affected data is personal, financial or credentials.

| level | who can trigger | effect | Odoo examples |
|---|---|---|---|
| **critical** | anonymous or portal user, or any internal user for the worst effects | remote code execution, full database read/write, account takeover, admin privilege | `eval` on request input; SQL injection in a public route; `sudo().write` on `res.users` from a controller; `pickle.loads` of uploaded data; live credentials committed |
| **high** | anonymous/portal user for data access, or internal user for privilege escalation | read or modify other companies'/partners' data, bypass approvals with impact, stored XSS to other users, path traversal | public route with `sudo().search_read` on a request domain; record rule domain `[(1,'=',1)]` on portal-readable model; `fields.Html(sanitize=False)` rendered in portal; zip upload extraction without path checks |
| **medium** | internal user beyond their role, or portal user for limited data | read data outside the user's scope, CSRF on state changes, open redirect, SSRF, information useful for further attacks | `sudo()` on user-supplied ids returning names/counts; `csrf=False` on a state-changing POST; `random` for access tokens; secrets logged at info; CDN-loaded JS |
| **low** | internal user with normal access, or only in unusual setups | minor disclosure, hardening gap, defence in depth missing | missing `timeout` on requests; `readonly` only in view; missing `check_company`; display name leaking a non-sensitive related field |
| **info** | nobody directly | observations worth knowing, good practices missing | `sudo()` with a correct comment but broad scope; permissive ACL on a config model only admins see; dependency not pinned |

## Rules

- Recorded in the security folder: medium and above (configurable via `security_min_severity`).
- Blocks a `full` submission when introduced by the automation's own change: `block_full_on_severity`
  and above (shipped as `high`). Pre-existing findings never block; they are reported.
- A finding that is reachable only by a user who already has `base.group_system` is at most low.
- If you cannot trace a concrete input to the sink, write it as `unclear` in the report with the
  severity it would have if confirmed, and do not record it in the security folder.
- When unsure between two levels, pick the lower one and say why in the finding. Over-rating
  trains maintainers to ignore the folder.

## CWE shortlist

| issue | CWE |
|---|---|
| SQL injection | CWE-89 |
| code injection / eval | CWE-94, CWE-95 |
| missing authorisation / IDOR | CWE-862, CWE-639 |
| incorrect authorisation (record rules, ACL too wide) | CWE-863, CWE-284 |
| privilege escalation via sudo | CWE-269 |
| XSS | CWE-79 |
| CSRF | CWE-352 |
| open redirect | CWE-601 |
| path traversal | CWE-22 |
| unrestricted upload | CWE-434 |
| SSRF | CWE-918 |
| hard-coded credentials | CWE-798 |
| weak randomness | CWE-330 |
| weak hash | CWE-328 |
| missing TLS verification | CWE-295 |
| deserialisation | CWE-502 |
| information exposure | CWE-200 |
| missing timeout / resource exhaustion | CWE-400 |
