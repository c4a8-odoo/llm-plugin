# Pull request review frame

Shared procedure for `odoo-pr-review` (structure) and `odoo-code-review` (function). Both skills
run inside this frame and add only their own checklist and TL;DR wording. Section numbers below
are referenced from the skills as "task-core section 9".

## 9.1 Gather

1. `gh pr view` with files, commits, reviews, comments, labels, `isDraft`, `baseRefName`.
   The base branch must equal `version`; if not, log `blocked` (wrong target branch) and stop.
2. Derive the modules touched. Without a `module` argument review all of them; with one,
   review only the named modules and list the others under **Context** in the log.
3. `gh pr diff`, `gh pr checks`, existing inline comments and reviews. If a maintainer already
   asked for changes that are still open, your review adds to it rather than restating it.
4. Fetch the head into the local clone (`git fetch origin pull/N/head:pr-N`) when you need to
   read files beyond the diff, run `pre-commit`, or inspect tests. Reading the whole module is
   the norm for `[MIG]` and `[ADD]` PRs; the diff is enough for small `[FIX]`es.
5. Classify the PR from its title tag: `[ADD]`, `[MIG]`, `[FIX]`, `[IMP]`, `[REF]`, `[I18N]`,
   `[REM]`. The checklists weight differently per class.
6. Record the head SHA in the log's **Context**; combined runs (9.5) key on it.

## 9.2 Comments

Each finding becomes one inline comment with a severity prefix (`blocker:`, `should:`, `nit:`),
the consequence, and the fix, as a ```suggestion block when a one-liner does it. Detail lives in
those inline comments, anchored to the changed lines; the summary body is the TL;DR part 2 (9.3).
Findings without a line in the diff (commit messages, a missing CI job, the PR body) go into the
summary body as one short list. Write for the author, who is usually a volunteer.

Automations never `APPROVE` unless `allow_approve` is true, and never `REQUEST_CHANGES` when
`allow_request_changes` is false; `COMMENT` is always available. A review with blockers in
`full` mode uses `REQUEST_CHANGES` when allowed, otherwise `COMMENT` with the blockers listed.

## 9.3 Report: TL;DR first

Every review output (the plan file, the task log, the final message to the user) **starts with a
`## TL;DR` section** placed right after the header table and before **Context**. It has two parts,
ten lines at most in total, and it is written for someone who reads nothing else.

**Part 1: PR status.** Three to five lines. The skill says which word opens it (`**Structure:**`
for the PR review, `**Status:**` for the code review), followed by the verdict (ready / needs
changes / needs discussion / blocked), one sentence on what the PR does, the recommended merge
bump (`patch`, `minor`, `major`, `nobump`), then only what needs attention: blockers, open
questions, risks. Do **not** list what passed; that belongs in the detailed sections below.

**Part 2: Suggested review response.** The summary text to post as the review body, three to
six lines, quoted verbatim so it can be copied: verdict, blockers in one line each, bump size
for the merger, thanks. Everything with a file and line goes into the inline comments, not
into this summary.

In a combined run the final message to the user carries one TL;DR: the code review's part 1
followed by the PR review's part 1 line(s) that still need attention, and one merged part 2
(status line, functional blockers, structural blockers, bump size, thanks).

## 9.4 Deliver per mode

| mode | deliverable |
|---|---|
| `plan` | `logs/<v>/<repo>/<module>/pr-<n>/<stamp>_<task>-plan.md`: TL;DR, PR classification, files to inspect, checks to run, questions to answer, draft of expected comments. No GitHub writes. |
| `draft` | PENDING review created via the API (see `github-recipes.md`) with the TL;DR part 2 as its body; the review JSON is also saved as `<stamp>_<task>-review.json` in the log folder. If a pending review of ours exists from an earlier run, delete and recreate it. |
| `full` | Review submitted with `COMMENT` or `REQUEST_CHANGES`, TL;DR part 2 as its body. If the PR is a draft on GitHub, submit anyway; the author asked for early feedback by opening it. |

In all modes, the task log opens with the TL;DR and its **Outcome** lists the comment count by
severity and the review URL (or JSON path). The final message to the user is the TL;DR followed
by the log path; do not repeat the inline comments there.

## 9.5 Combined runs

A plain "review this PR" runs `odoo-pr-review` and then `odoo-code-review` on the same head
SHA. Rules:

- Both skills get the same arguments from the caller, and each writes its own task log in
  the same `pr-<n>` folder.
- GitHub gets **one** review per run. The PR review does not create it; it stores its comments
  as `<stamp>_pr-review-comments.json` (bare array of comment objects) in the log folder and
  notes the path under **Outcome**. The code review merges that file into its payload (recipe in
  `github-recipes.md`), writes the merged body, and creates (draft) or submits (full) the review.
- The verdict of the merged review is "needs changes" when either skill found a blocker.
- The security review runs once, after the code review. The PR review's **Security review**
  section names that report; it does not run its own.
- If the code review cannot run (blocked, or the caller asked for the PR review alone), the PR review's
  stored comments are posted by the PR review itself before the run ends, and its log says why
  the code review was skipped.

When only one skill runs, it does everything above itself, and its **Follow-ups** offer the
other skill with the arguments to run it.

## 9.6 Hand-off to the security review

Pass the PR head path, the diff, and the list of files changed. Findings marked `introduced` at
or above `block_full_on_severity` must appear in the review as blockers, phrased safely (see the
security skill's "What to say to the maintainers"). Pre-existing findings are not part of the
public review unless the PR touches the same lines. In `full` mode such a finding downgrades the
submission to a pending review, as section 3 of the contract says.
