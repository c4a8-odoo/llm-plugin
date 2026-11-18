# GitHub recipes per mode

All commands use the authenticated `gh` CLI. `OWNER/REPO` is the `github` slug printed by
`check-scope` (for example `OCA/project`), `N` the PR or issue number. Every command that changes
something on GitHub belongs in the task log with the resulting URL.

## Read-only (allowed in every mode)

```bash
# PR metadata, files, existing reviews and comments
gh pr view N --repo OWNER/REPO --json number,title,body,author,state,isDraft,baseRefName,headRefName,headRepositoryOwner,url,files,commits,reviews,comments,labels
gh pr diff N --repo OWNER/REPO                       # unified diff
gh pr checks N --repo OWNER/REPO                     # CI + runboat status
gh api repos/OWNER/REPO/pulls/N/comments             # existing inline review comments
gh api repos/OWNER/REPO/pulls/N/reviews              # existing reviews (look for state PENDING of your own user)
gh api user --jq .login                              # who am I

# find related work
gh pr list --repo OWNER/REPO --state all --search "[MIG] MODULE in:title" --json number,title,state,url,headRefName
gh issue list --repo OWNER/REPO --search "Migration to version 19.0 in:title" --json number,title,url
gh issue view N --repo OWNER/REPO --json title,body,comments

# fetch a PR head into the local clone without touching upstream
git -C work/REPO fetch origin pull/N/head:pr-N
```

## Local checkout and fork (draft and full)

```bash
gh repo clone OWNER/REPO work/REPO -- --branch 19.0
gh repo fork OWNER/REPO --clone=false                       # once; no-op if the fork exists
git -C work/REPO remote add fork https://github.com/FORK_OWNER/REPO.git
git -C work/REPO checkout -b 19.0-mig-MODULE origin/19.0
# ... work, pre-commit, commit ...
git -C work/REPO push -u fork 19.0-mig-MODULE
```

Never `git push origin <version>` and never force-push a branch you did not create in this run.

## Pull requests

```bash
# draft mode
gh pr create --repo OWNER/REPO --base 19.0 --head FORK_OWNER:19.0-mig-MODULE \
  --title "[19.0][MIG] MODULE: Migration to 19.0" --body-file pr-body.md --draft
# full mode: same without --draft, or promote an existing draft
gh pr ready N --repo OWNER/REPO
gh pr comment N --repo OWNER/REPO --body-file comment.md         # full only
gh issue comment N --repo OWNER/REPO --body "..."                # full only (e.g. claim a module on the migration issue)
```

## Reviews

Inline comments need `path`, `line` (line number in the new file, inside a diff hunk) and
`side: "RIGHT"`; for a range add `start_line`. Use ```suggestion fences for concrete replacements.
Put the review payload in a JSON file:

```json
{
  "commit_id": "<head sha from gh pr view --json commits>",
  "body": "Summary of the review. Thanks for the PR.",
  "comments": [
    {"path": "partner_firstname/models/res_partner.py", "line": 42, "side": "RIGHT",
     "body": "`sudo()` here bypasses record rules; reading `partner_id` with the current user is enough.\n\n```suggestion\n        partner = self.partner_id\n```"}
  ]
}
```

```bash
# draft mode: PENDING review, visible only to you until submitted
gh api --method POST repos/OWNER/REPO/pulls/N/reviews --input review.json

# full mode: submit directly (event COMMENT | REQUEST_CHANGES | APPROVE)
#   APPROVE only when defaults.allow_approve is true; REQUEST_CHANGES only when allow_request_changes is true
gh api --method POST repos/OWNER/REPO/pulls/N/reviews --input review.json -f event=COMMENT

# full mode: submit a pending review left by an earlier draft run
gh api --method POST repos/OWNER/REPO/pulls/N/reviews/REVIEW_ID/events -f event=COMMENT -f body="..."
```

GitHub allows one pending review per user per PR. If `gh api .../reviews` shows a PENDING review
of your own user from an earlier run, either submit it (full) or delete and recreate it (draft):
`gh api --method DELETE repos/OWNER/REPO/pulls/N/reviews/REVIEW_ID`.

## Writing good review comments

- One finding per comment, anchored to the line that should change.
- Lead with the consequence ("this recomputes on every line change"), then the fix.
- Prefix the severity the maintainers should feel: `blocker:`, `should:`, `nit:`.
- Do not comment on formatting pre-commit enforces, and do not repeat an existing comment; reply
  to it instead if you add information.
- The summary body states the overall verdict and what remains to be done, in three to six lines.
- Never include anything from the local security review beyond what is directly visible in the
  diff and safe to state publicly (for example "missing access rule" is fine; an exploit path is not).
