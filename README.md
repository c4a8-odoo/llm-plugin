# c4a8-odoo-plugins

Claude Code plugin marketplace for C4A8 Odoo development. This repository is the
**single authoritative source** for AI/agent tooling — agents, skills, and rule
packs used across the Odoo workspaces. AI tooling found anywhere else
(`c4a8-odoo/.github`, old workspace copies) is legacy; the one exception is
`.github/copilot-commit-message-instructions.md` in the dev-volume workspace.

## Install

In Claude Code:

```
/plugin marketplace add c4a8-odoo/llm-plugin
/plugin install odoo-development@c4a8-odoo-plugins
```

## Plugins

| Plugin | Purpose |
|---|---|
| `odoo-development` | The real one: Odoo development, review, testing, documentation, and migration agents/skills with per-version rule packs (16.0–19.0). |
| `test-plugin` | Smoke-test scaffolding for plugin loading. Not for daily use. |
| `odoo-review` | Empty stub, reserved. |

## odoo-development contents

- **Agents**: `odoo` (development orchestrator), `odoo-migration` (version
  migration orchestrator), `odoo-pr-commit-cleanup`.
- **Skills**: `odoo-coding`, `odoo-coding-review`, `odoo-documentation`,
  `odoo-migrate-module`, `odoo-module-scaffold`, `odoo-tests`,
  `odoo-tests-run-docker`, `odoo-tests-run-local`.
- **Rule packs**: `skills/odoo-coding-review/resources/code-rules-*.yaml`
  (cumulative per version) and
  `skills/odoo-migrate-module/resources/migration-rules-*.yaml` (per version hop).

## Releasing changes

1. Bump the plugin `version` in `plugins/<name>/plugin.json` **and** its entry in
   `.github/plugin/marketplace.json` (keep them identical).
2. Users pick the change up by reinstalling/updating the plugin in Claude Code.

`docs/legacy-odoo-development-skill.md` preserves the removed `odoo-development`
skill for reference — it documents the workspace conventions (module repo
layout, version policy, author string).
