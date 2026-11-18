# Security review: {{module}} ({{repo}} {{version}}) - {{pr}}

| field | value |
|---|---|
| reviewed | {{date}} |
| parent task | {{parent_task}} (mode {{mode}}) |
| scope | whole module, delta marked; head commit {{sha}} |
| odoo version | {{version}} |
| recorded findings | {{recorded_count}} (see security/{{version}}/{{repo}}/{{module}}/) |

## Summary

| severity | introduced | pre-existing | unclear |
|---|---|---|---|
| critical | 0 | 0 | 0 |
| high | 0 | 0 | 0 |
| medium | 0 | 0 | 0 |
| low | 0 | 0 | 0 |
| info | 0 | 0 | 0 |

Blocks full submission: yes/no (introduced findings at or above block_full_on_severity).

## Inventory

Models, controllers (routes with auth level), wizards, reports, security files, assets,
external dependencies. One line each.

## Findings

### [severity] Title (introduced | pre-existing | unclear)

- Location: `path/file.py:line`
- CWE: CWE-xxx
- What: one or two sentences, attacker and effect.
- Fix: concrete change.
- Recorded: yes (file name) / no (below threshold) / duplicate of existing finding <file>

## Checked and clean

Categories from the checklist with no findings, so the next reviewer knows they were covered.

## Recommendations for the maintainers

Only what may be said publicly, phrased for a PR comment, if the parent task wants to use it.
Private disclosure recommendation for critical/high findings in released code.
