# Working in this repository

## Pull requests: open one by default

**Push work as a pull request, without being asked each time.** The default in
Claude Code is the opposite — no PR unless explicitly requested — and this file
overrides it for this repository, at the maintainer's instruction (5 Sep 2026).

* Open a PR when a coherent piece of work is finished, pushed and green.
* Keep it on the session's designated branch; never push to `main`.
* If a PR for that branch is already open, push to it rather than opening a
  second one.
* If the open PR has been **merged**, start the follow-up from the latest
  `main` on the same branch name and open a new PR — a merged PR cannot track
  new work.

The body follows the same standard as the commit messages: say what changed and
what it cost, name the defects found, and state what is *not* done rather than
letting a green tick imply it is.

## Where the rules actually live

`specs/` is authoritative — code is written from it, not the other way round.
Before changing behaviour, read the specification that governs it and amend that
in the same change. [`specs/README.md`](specs/README.md) is the map;
[`specs/ROADMAP.md`](specs/ROADMAP.md) says which phase is current and what its
exit criteria are.

## Verification before pushing

`ruff check . && python3 -m pytest -q` must be clean. Tier 3 needs a real QGIS
and tier 4 needs engine binaries; both skip with a reason rather than failing,
so a green local run does **not** mean CI is green. Check every workflow after
pushing — `test`, `build`, `reference`, and `engine` — not just the first one
that reports.
