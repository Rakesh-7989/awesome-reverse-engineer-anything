# AGENTS.md

Instructions for coding agents and AI assistants contributing to this list.

This repository is a **curated list**, not a software project. Every entry is a
claim about someone else's work, and the value of the list depends entirely on
those claims being checkable. Read this before adding anything.

## What this list is for

It records what AI agents have reverse-engineered and rebuilt, and it says
**what each case actually used**. A case that used Claude Code and Ghidra is
not the same as a case that used REA, and the list says which.

## The one rule that matters

**Do not tag a case `REA` unless the project's own README, the author's post,
or the official showcase says `morluto/rea` was used.** Read the source. Do
not infer it from the project being adjacent to the REA ecosystem.

`REA` is a claim *that the author made*. `Confirmed` in `docs/is-it-rea.md`
means *we found the statement*. Neither means the case is good, and neither
means the reconstruction is legally clean. Say so when it is not.

## Tags

| Tag | Means | Evidence to look for |
|---|---|---|
| `REA` | morluto/rea was used | README, author's post, or the official showcase |
| `AI-RE` | other or unstated AI tools | README or post naming a different tool |
| `Rebuild` | clean-room rewrite, no reverse-engineering evidence | README stating a clean-room approach |
| `Claim?` | not yet verified | nothing conclusive found |
| `Manual RE` | reverse-engineered by hand, no AI stated | README with no AI mention |

A tag may be qualified: `REA (showcase)`, `REA (partial)`, `REA (author's post)`.

Chinese tags: `REA`, `AI 逆向`, `重写`, `待核实`, `手工逆向`.

## Where an entry goes

| Section | What belongs there |
|---|---|
| Official showcases | cases on `rea.tools/showcase/` |
| Community cases built with REA | cases whose source says REA was used |
| The wider wave | AI work that says nothing about REA, or uses other tools |
| Plugins and integrations | adapters, plugins, skills, packaging |
| Guides and research | write-ups, labs, deep research |
| Related MCP reverse-engineering tools | tools in the same category as REA |
| Other lists | other curated lists |

A case that only says "AI" belongs in **The wider wave**, not in the REA
section, even when the project is clearly in the same space.

## Format

One line per entry:

```
- [Name](link) - what it does, and its tag.
```

Rules that the validator in `scripts/validate_list.py` enforces:

1. **Every case carries a tag** from the table above.
2. **Every case states its license**, or says plainly that there is none.
   `MIT`, `Apache-2.0`, `GPL-3.0`, `CC0-1.0`, `No license file`, `none`,
   or `source-available, not open source` for a non-open license.
3. **Both READMEs change together.** The English and Chinese lists carry the
   same projects. The validator fails if one side has an entry the other
   lacks.
4. **Every `REA` case has a row in `docs/is-it-rea.md`** and its Chinese
   counterpart. That table is where the evidence link lives.
5. **No mirrors, pure forks, or re-uploads** of the upstream project, and no
   projects whose main purpose is bypassing licensing or distributing
   copyrighted assets.

## Numbers and dates

Anything countable goes stale weekly. When you write one:

- give it a date, and put that date next to it;
- prefer a link to the source over a number you copied;
- write "no license file" rather than leaving the license out.

## Before you open a pull request

```bash
python3 scripts/validate_list.py
```

It reports tags, licenses, English/Chinese parity, broken anchors, and
mirrors. Zero errors is the bar. Warnings are worth fixing too.

Then check, by hand:

- every link works;
- the evidence link shows REA use, if you claim REA;
- the license is stated and correct;
- you updated **both** `README.md` and `README.zh-CN.md`.

Use the **Case** issue form for suggestions, and the pull request template
for changes.

## Takedowns

If you are the author of a listed project and want it removed, open an issue
with the project name and the reason. The entry is removed and the evidence
is archived.

## Do not

- add a project whose README does not mention REA to the REA section;
- add a mirror of `morluto/rea`;
- add a project whose main purpose is bypassing licensing;
- edit one language and leave the other behind;
- write a number without a date.
