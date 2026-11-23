#!/usr/bin/env python3
"""Helper for the Odoo/OCA automation skills: task logs and security findings.

Standard library only; no configuration file. Everything comes from the arguments, which the
calling skill takes from the caller (see odoo-task-core, section 2).

  log-init    --version V --repo R --module M --pr P --task T --mode MODE [--github OWNER/REPO] [--title ..] [--arguments ..]
  log-finish  --path FILE --status STATUS
  log-move    --version V --repo R --module M --from-pr A --to-pr B
  finding     --version V --repo R --module M --pr P --severity S --title .. (--body .. | --body-file FILE)
              [--location ..] [--cwe ..] [--min-severity medium]

Global options (before the command): --log-root (default logs), --security-root (default
security). Relative roots resolve against the current working directory.
"""
import argparse
import os
import re
import shutil
import sys
from datetime import datetime

SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "log-template.md")


# ----------------------------------------------------------------- helpers
def slug(text, maximum=60):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:maximum].strip("-") or "item"


def write(path, text, append=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a" if append else "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def unique(path):
    base, ext = os.path.splitext(path)
    i = 2
    while os.path.exists(path):
        path = f"{base}-{i}{ext}"
        i += 1
    return path


# ----------------------------------------------------------------- commands
def cmd_log_init(args):
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d_%H%M")
    pr = args.pr
    path = unique(os.path.join(args.log_root, args.version, args.repo, args.module, pr, f"{stamp}_{slug(args.task)}.md"))
    title = args.title or f"{args.task} - {args.module} ({args.repo} {args.version}) - {pr}"
    text = read(TEMPLATE)
    mapping = {
        "title": title, "task": args.task, "mode": args.mode, "version": args.version, "repo": args.repo,
        "github": args.github or f"OCA/{args.repo}", "module": args.module, "pr": pr,
        "started": now.strftime("%Y-%m-%d %H:%M"), "finished": "{{finished}}", "status": "running",
        "arguments": args.arguments or "-",
    }
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", str(value))
    write(path, text)
    print(path)


def cmd_log_finish(args):
    if not os.path.exists(args.path):
        sys.exit(f"log not found: {args.path}")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = read(args.path).replace("{{finished}}", now)
    text = re.sub(r"(?m)^\| status \| .* \|$", f"| status | {args.status} |", text)
    text = re.sub(r"(?m)^\| finished \| .* \|$", f"| finished | {now} |", text)
    write(args.path, text)
    print(args.path)


def cmd_log_move(args):
    base = os.path.join(args.log_root, args.version, args.repo, args.module)
    src, dst = os.path.join(base, args.from_pr), os.path.join(base, args.to_pr)
    if not os.path.isdir(src):
        sys.exit(f"source folder not found: {src}")
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        target = os.path.join(dst, name)
        shutil.move(os.path.join(src, name), target)
        write(target, re.sub(r"(?m)^\| pr \| .* \|$", f"| pr | {args.to_pr} |", read(target)))
    shutil.rmtree(src)
    print(dst)


def cmd_finding(args):
    sev = args.severity.lower()
    if sev not in SEVERITY_RANK:
        sys.exit(f"unknown severity '{args.severity}' (info|low|medium|high|critical)")
    body = read(args.body_file) if args.body_file else args.body
    if not body:
        sys.exit("provide --body or --body-file")
    minimum = args.min_severity.lower()
    if minimum not in SEVERITY_RANK:
        sys.exit(f"unknown --min-severity '{args.min_severity}' (info|low|medium|high|critical)")
    if SEVERITY_RANK[sev] < SEVERITY_RANK[minimum]:
        print(f"below threshold ({sev} < {minimum}): not recorded")
        return
    folder = os.path.join(args.security_root, args.version, args.repo, args.module)
    date = datetime.now().strftime("%Y-%m-%d")
    path = unique(os.path.join(folder, f"{date}_{args.pr}_{sev}_{slug(args.title)}.md"))
    content = (
        f"# {args.title}\n\n| field | value |\n|---|---|\n"
        f"| severity | {sev} |\n| odoo version | {args.version} |\n| repo | {args.repo} |\n"
        f"| module | {args.module} |\n| pr | {args.pr} |\n| location | {args.location or '-'} |\n"
        f"| cwe | {args.cwe or '-'} |\n| recorded | {date} |\n| status | open |\n\n{body}\n"
    )
    write(path, content)
    index = os.path.join(folder, "index.md")
    if not os.path.exists(index):
        write(index, f"# Security findings: {args.module} ({args.repo} {args.version})\n\n"
                     "| recorded | severity | pr | title | file | status |\n|---|---|---|---|---|---|\n")
    name = os.path.basename(path)
    write(index, f"| {date} | {sev} | {args.pr} | {args.title} | [{name}]({name}) | open |\n", append=True)
    print(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log-root", default="logs")
    parser.add_argument("--security-root", default="security")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, *names):
        for n in names:
            p.add_argument(f"--{n}", required=True)

    p = sub.add_parser("log-init"); common(p, "version", "repo", "module", "pr", "task", "mode")
    p.add_argument("--github"); p.add_argument("--title"); p.add_argument("--arguments")
    p.set_defaults(func=cmd_log_init)
    p = sub.add_parser("log-finish"); common(p, "path", "status"); p.set_defaults(func=cmd_log_finish)
    p = sub.add_parser("log-move"); common(p, "version", "repo", "module", "from-pr", "to-pr"); p.set_defaults(func=cmd_log_move)
    p = sub.add_parser("finding"); common(p, "version", "repo", "module", "pr", "severity", "title")
    p.add_argument("--body"); p.add_argument("--body-file"); p.add_argument("--location"); p.add_argument("--cwe")
    p.add_argument("--min-severity", default="medium")
    p.set_defaults(func=cmd_finding)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
