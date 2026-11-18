# Improvement playbook

| class | tag | bump | must include | typical traps |
|---|---|---|---|---|
| bug fix | `[FIX]` | patch | regression test; `Fixes #n` | fixing the symptom in the view instead of the compute; forgetting the same bug in a sibling method |
| small feature | `[IMP]` | minor | test of the new path; README USAGE/CONFIGURE update | adding a dependency to make it easy; changing defaults for existing users |
| data model change | `[IMP]` or `[REF]` | major | migration scripts (`openupgradelib`), test that old data still loads | renaming a field without `openupgrade.rename_fields`; removing a selection value others reference |
| refactor | `[REF]` | patch (none if no behaviour change; minor if public API changed) | tests unchanged and green | silently changing behaviour; renaming methods other modules override |
| tests only | `[IMP]` | none or patch (repo habit) | `tests/__init__.py` import; `post_install` tagging when needed | tests depending on demo data from undeclared modules |
| docs | `[IMP]` | none | fragments under `readme/`, regenerated README | editing `README.rst` directly |
| tooling/CI | `[IMP]` | none | passing pre-commit; no functional change | mixing lint fixes with code changes |
| hardening | `[FIX]` | patch (minor if a new group/rule is added) | ACL/rule/test; safe public wording | describing the exploit in the public PR |
| performance | `[IMP]` | patch | measurement or reasoning in the PR body; test still green | changing semantics (active_test, ordering) while optimising |
| translation | `[I18N]` | none | only via Weblate normally; manual `.po` edits are rarely accepted | committing `.pot` by hand |

## Test skeleton

```python
# Copyright 2026 <Author>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProjectTimelineStage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.project = cls.env["project.project"].create({"name": "Test"})

    def test_default_stage_applied_on_create(self):
        task = self.env["project.task"].create({"name": "T", "project_id": self.project.id})
        self.assertEqual(task.stage_id, self.project.type_ids[:1])
```

Add the module to `tests/__init__.py`. Prefer asserting on records and values over on
translated strings. For access tests use `with_user(self.user)` and `assertRaises(AccessError)`.

## Migration script skeleton

```python
# migrations/19.0.2.0.0/pre-migrate.py
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, [("project.task", "project_task", "old_name", "new_name")])
```

`openupgradelib` must be in `external_dependencies` (`"python": ["openupgradelib"]`) when used.
Post-migrate for data that needs the new field to exist; pre-migrate for renames and column moves.

## PR body skeleton

```markdown
<what changed and why, two to five lines>

Closes #<issue>

**How to test**
1. <steps or the test name>

**Compatibility**: <none | migration script included | behaviour change for users who ...>

@<maintainers>
```
