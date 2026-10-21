#!/usr/bin/env python3
"""Validate this list against the rules it states in CONTRIBUTING.md.

The list has three kinds of line and they are held to different rules:

  cases   entries under the case sections. These are the ones that make
          claims about other people, so a case must carry a tag, must state
          its license, and must have a row in docs/is-it-rea.md.
  tools   entries under the plugins, guides and related-tools sections.
          These are catalogues, not claims, so a tag is not required.
  records rows in docs/is-it-rea.md and docs/by-app.md. These are the
          evidence table and the index, so they are checked for parity and
          for broken anchors, not for tags.

Checks:

  1. tags       every case carries a tag from the documented set
  2. licenses   every case states its license, or says plainly that there is none
  3. coverage   every case tagged REA has a row in docs/is-it-rea.md
  4. parity     the English and Chinese files list the same projects
  5. anchors    every in-page link resolves to a heading in the same file
  6. mirrors    no mirror or pure fork of the upstream project is listed

Run with no arguments to check the working tree:

    python3 scripts/validate_list.py

Add --json for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EN_README, ZH_README = "README.md", "README.zh-CN.md"
EN_BY_APP, ZH_BY_APP = "docs/by-app.md", "docs/by-app.zh-CN.md"
EN_ISIT, ZH_ISIT = "docs/is-it-rea.md", "docs/is-it-rea.zh-CN.md"

# Sections whose entries are claims about other people's work.
CASE_SECTIONS = {
    "community cases built with rea",
    "the wider wave: without confirmed rea",
    "official showcases",
    "社区案例：用 rea 做出来的东西",
    "同一波浪潮：未写明使用 rea 的 ai 逆向项目",
    "官方案例",
}

# Tag vocabulary from CONTRIBUTING.md, including the Chinese forms.
TAGS = {
    "REA",
    "AI-RE",
    "AI 逆向",
    "Rebuild",
    "重写",
    "Claim?",
    "待核实",
    "Manual RE",
    "手工逆向",
}
# A tag may be qualified: `REA (showcase)`, `REA (partial)`, `REA (author's post)`.
TAG_RE = re.compile(r"`([^`]+)`")

LICENSE_PATTERNS = [
    re.compile(r"\bMIT\b", re.I),
    re.compile(r"Apache-2\.0", re.I),
    re.compile(r"GPL-?[23](?:\.0)?(?:-or-later)?", re.I),
    re.compile(r"CC0(?:-1\.0)?", re.I),
    re.compile(r"\bUnlicensed\b", re.I),
    re.compile(r"\bno license file\b", re.I),
    re.compile(r"source-available", re.I),
    re.compile(r"\bno license\b", re.I),
    re.compile(r"\bnone\b", re.I),
    # Chinese: "仓库未附许可证", "无许可证", "没有许可协议"
    re.compile(r"(未附|无|没有)[^，。；、]{0,4}(许可|授权|协议)"),
]

UPSTREAM = "morluto/rea"

# CONTRIBUTING rule 4: no mirrors, pure forks, or re-uploads of the upstream project.
MIRROR_NAME = re.compile(r"https-github(\.|-)com-morluto-rea", re.I)
MIRROR_NAME_EXACT = re.compile(
    r"^[^/]+/(npx-)?(rea|rea-agents|rea-agents-[\d.]+|morluto-rea|rea-backup"
    r"|morluto-rea-backup|rea-agents-setup|rea-independent|morluto-rea-explainer)$",
    re.I,
)
# The description has to say the project itself is a mirror, not that it
# mentions or warns about mirrors.
MIRROR_DESC = re.compile(
    r"\b(?:is|an?|the)\s+(?:independent\s+)?(?:git\s+)?(?:mirror|copy|backup|fork|clone)\b"
    r"|\bmirror(?:s|ed)?\s+(?:of|backup of|copy of)\b"
    r"|\bunofficial\s+(?:port|mirror|fork|clone)\b",
    re.I,
)
UPSTREAM_TAGLINE = re.compile(
    r"reverse engineer anything with agents, from app behavior down to native binaries", re.I
)

BULLET = re.compile(r"^\s*[-*]\s+(.*)$")
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def repo_of(url: str) -> str | None:
    """owner/name when the link points at a GitHub repository."""
    m = re.match(r"https?://github\.com/([^/#?]+)/([^/#?]+)", url)
    if not m:
        return None
    owner, name = m.group(1), m.group(2).split("#")[0]
    if name.endswith(".git"):
        name = name[:-4]
    return f"{owner}/{name}"


class Entry:
    def __init__(self, file: str, line_no: int, name: str, url: str, text: str, section: str):
        self.file = file
        self.line_no = line_no
        self.name = name
        self.url = url
        self.text = text
        self.section = section
        self.tags: list[str] = []
        self.has_license = False

    @property
    def repo(self) -> str | None:
        return repo_of(self.url)

    @property
    def tag(self) -> str | None:
        return self.tags[0] if self.tags else None

    @property
    def is_case(self) -> bool:
        return self.section.lower() in CASE_SECTIONS

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Entry {self.file}:{self.line_no} {self.repo or self.url} {self.tag}>"


def parse_file(path: Path) -> tuple[list[Entry], set[str]]:
    """Return the entries in a file and every GitHub repo it links to."""
    entries: list[Entry] = []
    all_repos: set[str] = set()
    section = "(top)"
    for line_no, raw in enumerate(read(path).splitlines(), start=1):
        heading = HEADING.match(raw)
        if heading:
            section = heading.group(2).strip()
            continue

        links = LINK.findall(raw)
        for _, url in links:
            repo = repo_of(url)
            if repo:
                all_repos.add(repo)

        # A bullet or a table row that starts with a link is an entry.
        first = links[0] if links else None
        if first is None:
            continue
        is_row = raw.lstrip().startswith("|")
        if is_row:
            if not BULLET.match(raw) and not raw.lstrip().startswith("|"):
                continue
        name, url = first
        text = raw
        entries.append(Entry(path.name, line_no, name, url, text, section))
    return entries, all_repos


def attach_metadata(entries: list[Entry]) -> None:
    for entry in entries:
        for match in TAG_RE.finditer(entry.text):
            candidate = match.group(1).strip()
            base = candidate.split("(")[0].strip()
            if candidate in TAGS or base in TAGS:
                entry.tags.append(candidate)
        entry.has_license = any(p.search(entry.text) for p in LICENSE_PATTERNS)


def anchor_of(heading: str) -> str:
    slug = heading.strip().lower()
    slug = re.sub(r"[^\w\s一-鿿-]", "", slug)
    return re.sub(r"\s+", "-", slug)


def check_anchors(path: Path) -> list[str]:
    text = read(path)
    anchors = set()
    for line in text.splitlines():
        heading = HEADING.match(line)
        if heading:
            anchors.add(anchor_of(heading.group(2)))
    problems = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for target in re.findall(r"\]\(#([^)]+)\)", line):
            if target not in anchors:
                problems.append(f"{path.name}:{line_no} broken anchor #{target}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    files = [EN_README, ZH_README, EN_BY_APP, ZH_BY_APP, EN_ISIT, ZH_ISIT]
    entries_by_file: dict[str, list[Entry]] = {}
    repos_by_file: dict[str, set[str]] = {}
    for name in files:
        path = ROOT / name
        if not path.exists():
            errors.append(f"missing file: {name}")
            continue
        entries, repos = parse_file(path)
        attach_metadata(entries)
        entries_by_file[name] = entries
        repos_by_file[name] = repos

    # 1. tags on cases
    for name in (EN_README, ZH_README):
        for entry in entries_by_file.get(name, []):
            if entry.repo is None or not entry.is_case:
                continue
            if not entry.tags:
                errors.append(
                    f"{name}:{entry.line_no} {entry.repo} is a case but carries no tag "
                    f"from the documented set"
                )

    # 2. licenses on cases
    for name in (EN_README, ZH_README):
        for entry in entries_by_file.get(name, []):
            if entry.repo is None or not entry.is_case:
                continue
            if entry.has_license:
                continue
            warnings.append(
                f"{name}:{entry.line_no} {entry.repo} does not state a license"
            )

    # 3. coverage: every REA case has a row in is-it-rea
    for readme, isit in ((EN_README, EN_ISIT), (ZH_README, ZH_ISIT)):
        isit_repos = repos_by_file.get(isit, set())
        for entry in entries_by_file.get(readme, []):
            if entry.repo is None or not entry.is_case or not entry.tags:
                continue
            if entry.tag.split("(")[0].strip() != "REA":
                continue
            if entry.repo == UPSTREAM:
                continue
            if entry.repo not in isit_repos:
                warnings.append(
                    f"{readme}:{entry.line_no} {entry.repo} is tagged REA but has no row "
                    f"in {isit}"
                )

    # 4. parity between the English and Chinese file of each pair
    for en_name, zh_name in ((EN_README, ZH_README), (EN_BY_APP, ZH_BY_APP), (EN_ISIT, ZH_ISIT)):
        en_repos = repos_by_file.get(en_name, set())
        zh_repos = repos_by_file.get(zh_name, set())
        for repo in sorted(en_repos - zh_repos):
            errors.append(f"{en_name} lists {repo} but {zh_name} does not")
        for repo in sorted(zh_repos - en_repos):
            errors.append(f"{zh_name} lists {repo} but {en_name} does not")

    # 5. anchors
    for name in files:
        path = ROOT / name
        if path.exists():
            errors.extend(check_anchors(path))

    # 6. mirrors
    for name in files:
        for entry in entries_by_file.get(name, []):
            repo = entry.repo
            if repo is None or repo == UPSTREAM:
                continue
            if MIRROR_NAME.search(repo) or MIRROR_NAME_EXACT.match(repo):
                errors.append(
                    f"{name}:{entry.line_no} {repo} looks like a mirror or re-upload of "
                    f"the upstream project, which rule 4 rejects"
                )
            elif MIRROR_DESC.search(entry.text) or UPSTREAM_TAGLINE.search(entry.text):
                errors.append(
                    f"{name}:{entry.line_no} {repo} reads like a mirror of the upstream project"
                )

    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, indent=2))
        return 1 if errors else 0

    for message in errors:
        print(f"ERROR   {message}")
    for message in warnings:
        print(f"WARNING {message}")
    print()
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
