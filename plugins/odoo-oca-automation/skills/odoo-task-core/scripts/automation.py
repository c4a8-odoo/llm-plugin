#!/usr/bin/env python3
"""Helper for the Odoo/OCA automation skills: scope gate, task logs, security findings.

Reads config/automation.yaml (PyYAML or ruamel.yaml if installed, otherwise a built-in
parser for the simple subset the config uses). Standard library apart from that.

  config
  list-scope  [--version V] [--repo R]
  check-scope --version V --repo R --module M [--task T]      exit 0 / 2 (out of scope) / 3 (config error)
  log-init    --version V --repo R --module M --pr P --task T --mode MODE [--title ..] [--arguments ..] [--out-of-scope]
  log-finish  --path FILE --status STATUS
  log-move    --version V --repo R --module M --from-pr A --to-pr B
  finding     --version V --repo R --module M --pr P --severity S --title .. (--body .. | --body-file FILE) [--location ..] [--cwe ..]

Scope entries may omit `odoo_version`; such an entry applies to every version.
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TEMPLATE = os.path.join(HERE, "..", "assets", "log-template.md")
DEFAULT_CONFIG = os.path.join(PROJECT_ROOT, "config", "automation.yaml")


# ----------------------------------------------------------------- yaml loading
def load_yaml(text):
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ImportError:
        pass
    try:
        from ruamel.yaml import YAML  # type: ignore

        return YAML(typ="safe").load(text)
    except ImportError:
        pass
    return _mini_yaml(text)


def _scalar(token):
    token = token.strip()
    if token == "" or token in ("~", "null", "Null", "NULL"):
        return None
    if token in ("true", "True", "TRUE"):
        return True
    if token in ("false", "False", "FALSE"):
        return False
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        return [_scalar(t) for t in _split_flow(inner)] if inner else []
    if re.fullmatch(r"-?\d+", token):
        return int(token)
    if re.fullmatch(r"-?\d+\.\d+", token) and not re.fullmatch(r"\d+\.0", token):
        return float(token)
    return token


def _split_flow(text):
    out, cur, quote = [], "", None
    for ch in text:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch == ",":
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def _strip_comment(line):
    out, quote = "", None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out += ch
    return out.rstrip()


def _mini_yaml(text):
    """Block mappings, block sequences, flow sequences and plain scalars. Enough for the config."""
    lines = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = _strip_comment(raw)
        if stripped.strip():
            lines.append((len(raw) - len(raw.lstrip()), stripped.strip()))

    def parse(i, indent):
        if i >= len(lines):
            return None, i
        if lines[i][1].startswith("- "):
            items = []
            while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
                content = lines[i][1][2:].strip()
                if ":" in content and not content.startswith("[") and not content.startswith(("'", '"')):
                    # mapping that starts on the dash line: re-inject as an indented line
                    lines[i] = (indent + 2, content)
                    value, i = parse(i, indent + 2)
                    items.append(value)
                else:
                    items.append(_scalar(content))
                    i += 1
            return items, i
        mapping = {}
        while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
            key, _, rest = lines[i][1].partition(":")
            key = key.strip().strip("\"'")
            rest = rest.strip()
            i += 1
            if rest:
                mapping[key] = _scalar(rest)
            elif i < len(lines) and lines[i][0] > indent:
                mapping[key], i = parse(i, lines[i][0])
            elif i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
                mapping[key], i = parse(i, indent)
            else:
                mapping[key] = None
        return mapping, i

    result, _ = parse(0, lines[0][0] if lines else 0)
    return result


# ----------------------------------------------------------------- helpers
def slug(text, maximum=60):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:maximum].strip("-") or "item"


def read_config(path):
    try:
        with open(path, encoding="utf-8") as fh:
            cfg = load_yaml(fh.read())
    except (OSError, ValueError) as exc:
        print(f"cannot read config {path}: {exc}", file=sys.stderr)
        sys.exit(3)
    except Exception as exc:  # yaml parser errors
        print(f"cannot parse config {path}: {exc}", file=sys.stderr)
        sys.exit(3)
    if not isinstance(cfg, dict):
        print(f"config {path} must be a mapping", file=sys.stderr)
        sys.exit(3)
    return cfg


def default(cfg, name, fallback):
    value = (cfg.get("defaults") or {}).get(name)
    return fallback if value in (None, "") else value


def root_path(cfg, key, fallback):
    rel = str(default(cfg, key, fallback))
    return rel if os.path.isabs(rel) else os.path.join(PROJECT_ROOT, rel)


def entry_versions(entry):
    """None when the entry applies to every version, else the list of versions as strings."""
    raw = entry.get("odoo_version", entry.get("odoo_versions"))
    if raw in (None, "", "*", ["*"]):
        return None
    if isinstance(raw, (list, tuple)):
        return [str(v) for v in raw]
    return [str(raw)]


def entry_github(cfg, entry):
    return entry.get("github") or f"{default(cfg, 'github_org', 'OCA')}/{entry.get('repo')}"


def resolve_scope(cfg, version, repo, module, task=None):
    for entry in cfg.get("scope") or []:
        if str(entry.get("repo")) != repo:
            continue
        versions = entry_versions(entry)
        if versions is not None and version not in versions:
            continue
        mods = [str(m) for m in (entry.get("modules") or [])]
        if module not in mods and "*" not in mods:
            continue
        tasks = entry.get("tasks") or []
        github = entry_github(cfg, entry)
        if task and tasks and task not in tasks:
            return {"in_scope": False, "reason": f"task '{task}' not allowed for {repo} ({version})", "github": github}
        return {"in_scope": True, "github": github, "tasks": tasks, "reason": "listed",
                "versions": versions or "any"}
    return {"in_scope": False, "reason": f"module '{module}' not listed for {repo} ({version})", "github": None}


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
def cmd_config(args, cfg):
    print(json.dumps(cfg, indent=2))


def cmd_list_scope(args, cfg):
    for entry in cfg.get("scope") or []:
        versions = entry_versions(entry)
        if args.version and versions is not None and args.version not in versions:
            continue
        if args.repo and str(entry.get("repo")) != args.repo:
            continue
        shown = args.version or (",".join(versions) if versions else "*")
        for m in entry.get("modules") or []:
            print(f"{shown}\t{entry.get('repo')}\t{entry_github(cfg, entry)}\t{m}")


def cmd_check_scope(args, cfg):
    res = resolve_scope(cfg, args.version, args.repo, args.module, args.task)
    print(json.dumps(res))
    sys.exit(0 if res["in_scope"] else 2)


def cmd_log_init(args, cfg):
    log_root = root_path(cfg, "log_root", "logs")
    scope = resolve_scope(cfg, args.version, args.repo, args.module)
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d_%H%M")
    if args.out_of_scope:
        pr = args.pr or "no-pr"
        path = os.path.join(log_root, "_out_of_scope", f"{stamp}_{args.version}_{args.repo}_{args.module}.md")
        status = "skipped"
    else:
        if not args.pr:
            sys.exit("missing --pr")
        pr = args.pr
        path = unique(os.path.join(log_root, args.version, args.repo, args.module, pr, f"{stamp}_{slug(args.task)}.md"))
        status = "running"
    title = args.title or f"{args.task} - {args.module} ({args.repo} {args.version}) - {pr}"
    text = read(TEMPLATE)
    mapping = {
        "title": title, "task": args.task, "mode": args.mode, "version": args.version, "repo": args.repo,
        "github": scope.get("github") or "?", "module": args.module, "pr": pr,
        "started": now.strftime("%Y-%m-%d %H:%M"), "finished": "{{finished}}", "status": status,
        "arguments": args.arguments or "-",
    }
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", str(value))
    write(path, text)
    print(path)


def cmd_log_finish(args, cfg):
    if not os.path.exists(args.path):
        sys.exit(f"log not found: {args.path}")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = read(args.path).replace("{{finished}}", now)
    text = re.sub(r"(?m)^\| status \| .* \|$", f"| status | {args.status} |", text)
    text = re.sub(r"(?m)^\| finished \| .* \|$", f"| finished | {now} |", text)
    write(args.path, text)
    print(args.path)


def cmd_log_move(args, cfg):
    log_root = root_path(cfg, "log_root", "logs")
    base = os.path.join(log_root, args.version, args.repo, args.module)
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


def cmd_finding(args, cfg):
    sev = args.severity.lower()
    if sev not in SEVERITY_RANK:
        sys.exit(f"unknown severity '{args.severity}' (info|low|medium|high|critical)")
    body = read(args.body_file) if args.body_file else args.body
    if not body:
        sys.exit("provide --body or --body-file")
    minimum = str(default(cfg, "security_min_severity", "medium")).lower()
    if SEVERITY_RANK[sev] < SEVERITY_RANK.get(minimum, 2):
        print(f"below threshold ({sev} < {minimum}): not recorded")
        return
    sec_root = root_path(cfg, "security_root", "security")
    folder = os.path.join(sec_root, args.version, args.repo, args.module)
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
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, *names):
        for n in names:
            p.add_argument(f"--{n}", required=True)

    sub.add_parser("config").set_defaults(func=cmd_config)
    p = sub.add_parser("list-scope"); p.add_argument("--version"); p.add_argument("--repo"); p.set_defaults(func=cmd_list_scope)
    p = sub.add_parser("check-scope"); common(p, "version", "repo", "module"); p.add_argument("--task"); p.set_defaults(func=cmd_check_scope)
    p = sub.add_parser("log-init"); common(p, "version", "repo", "module", "task", "mode")
    p.add_argument("--pr"); p.add_argument("--title"); p.add_argument("--arguments"); p.add_argument("--out-of-scope", action="store_true")
    p.set_defaults(func=cmd_log_init)
    p = sub.add_parser("log-finish"); common(p, "path", "status"); p.set_defaults(func=cmd_log_finish)
    p = sub.add_parser("log-move"); common(p, "version", "repo", "module", "from-pr", "to-pr"); p.set_defaults(func=cmd_log_move)
    p = sub.add_parser("finding"); common(p, "version", "repo", "module", "pr", "severity", "title")
    p.add_argument("--body"); p.add_argument("--body-file"); p.add_argument("--location"); p.add_argument("--cwe")
    p.set_defaults(func=cmd_finding)

    args = parser.parse_args()
    args.func(args, read_config(args.config))


if __name__ == "__main__":
    main()
