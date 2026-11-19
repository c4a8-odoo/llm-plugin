---
name: odoo-security-review
description: Local-only security analysis of an Odoo/OCA module (access rights, record rules, sudo, SQL injection, controllers, QWeb/XSS, file handling, secrets, external calls). Runs automatically as the LAST step of every odoo-* task (PR review, code review, migration, porting, improvement; a combined PR + code review on one head gets a single security review) and whenever the user asks for a security review, audit, vulnerability check or hardening of an Odoo module or PR. Writes the report next to the task log and records medium-or-higher findings under security/<odoo_version>/<repo>/<module>/. Never posts anything to GitHub.
---

# Odoo security review

Follow `odoo-task-core` for arguments and log locations. This skill produces two things and
nothing else: a report file next to the task log, and one finding file per medium-or-higher
issue in the security folder. Nothing it produces leaves the machine. Maintainers decide what
to disclose and how; an automation publishing an exploit path to a public PR would do real harm,
so even in `full` mode this skill never comments, pushes or opens issues.

## When it runs

- At the end of every odoo-* task, on the module as it exists after that task (the PR head for
  a PR or code review, the working tree for a migration/port/improvement). The parent task passes
  `version`, `repo`, `module`, `pr`, `workdir` and, when available, the diff of what the parent
  task changed or reviewed. When `odoo-pr-review` and `odoo-code-review` run back to back on the
  same PR head, run once, after the code review; the PR review's log points at the same report.
- Standalone, when a user asks for it. Then run the scope gate and create your own task log
  (`task=security-review`) before doing the review.

## Procedure

1. **Inventory** the module. List models, controllers, wizards, reports, data/demo, security
   files, static JS, manifest keys. Note the Odoo version: what counts as safe differs
   (`attrs` exists in 16, not 17; `<tree>` in 17, not 19).
2. **Baseline vs delta.** Read `references/checklist.md` and work through every category over
   the whole module, but mark each finding as `introduced by this change`, `pre-existing` or
   `unclear`. The parent task needs the distinction: pre-existing issues inform maintainers,
   introduced ones can block a `full` submission.
3. **Grep first, then read.** Each checklist category lists grep patterns; run them over the
   module to find candidates quickly (`git grep -n` in the module folder), then read the
   surrounding code to confirm or discard. A pattern hit is not a finding; a confirmed path from
   an attacker-controlled input to an unwanted effect is.
4. **Classify** each confirmed finding with `references/severity.md`. Be honest about
   exploitability: internal-user-only issues behind proper ACLs are rarely above medium; anything
   reachable with `auth="public"` or by portal users starts at medium.
5. **Write the report** from `assets/report-template.md` to
   `logs/<version>/<repo>/<module>/<pr>/<yyyy-mm-dd>_<HHMM>_security-review.md` (same folder as
   the parent task log). Include everything down to info level; keep each finding to a few lines
   plus location.
6. **Record findings** at or above `security_min_severity` with the helper, one call per finding,
   using the body format in `assets/finding-body-template.md`:

   ```bash
   python .claude/skills/odoo-task-core/scripts/automation.py finding --version 19.0 --repo partner-contact --module partner_contact_access_link --pr pr-1234 --severity high --title "Public controller returns contacts of any company" --location "controllers/main.py:57" --cwe CWE-639 --body-file finding.md
   ```

   The helper appends to `security/<version>/<repo>/<module>/index.md`. Before recording,
   read that index: if the same issue is already listed and still `open`, do not add a duplicate;
   mention in the report that it is already tracked and, if the status changed (fixed by this PR),
   edit the status cell of the existing row and finding file to `fixed <date> <pr>`.
7. **Report back** to the parent task: counts per severity, the report file name, and the list of
   `introduced` findings at or above `block_full_on_severity`. The parent writes only the counts
   and file name into its task log.

## What to say to the maintainers

The parent task (code review, PR body) may mention a finding publicly only in a form that helps
fixing without handing out a recipe: "missing record rule on `project.timeline.config`, any
internal user can read all rows" is fine; a request URL that dumps data is not. Critical findings
in released code are reported privately to the OCA security contact
(security@odoo-community.org) by a human; write that recommendation in the report, do not send it.

## Reference material

- `references/checklist.md`: categories, grep patterns, what makes each one a real finding.
- `references/severity.md`: rubric with Odoo examples per level.
- `assets/report-template.md`, `assets/finding-body-template.md`.
