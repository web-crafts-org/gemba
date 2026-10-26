# AGENTS.md

This file provides guidance to AI agents (Claude Code, Codex and others) when working
with code in this repository. `CLAUDE.md` is a link to it.

## What this repository is

This is the product repository of Gemba, a task-based system for working with AI
agents, made for developers to organize their own work, alone or with a team, beside
the way their company organizes its tasks rather than in its place. It holds the gemba
CLI (`src/gemba/`), the skills that drive each process (assets of the package under
`src/gemba/assets/`), the specification of what the CLI does (`openspec/specs/`) and
its tests (`tests/`). It holds no `gemba.yaml` and no tasks: an obeya is what
`gemba init` creates somewhere else, and the README describes Gemba from that side.

## Vocabulary

One word for one thing, in the specs, the skills, the code and the chat.

- **Gemba** is the product. The **gemba CLI** is the package we publish (distribution
  `gemba-cli`, command `gemba`).
- The **obeya** (大部屋, "big room": in lean, the room where a program, a team or a
  project keeps all of its work in sight) is the repository that holds `gemba.yaml`,
  `tasks/` and `harnesses/`; `gemba init` creates one. Whoever creates it draws its
  boundary: the organization they work for, a project, a team inside a company, or a
  whole startup. One person may keep it alone, or a team may share it. Its name, the
  `obeya` of the shared config, is a segment of the branch of every run. Plural
  *obeyas*, article *an obeya*.
- The **gemba config** is the customization of the obeya, in two files at its root:
  the **shared config**, `gemba.yaml`, committed, what everyone who uses the obeya
  agrees on; and the **personal config**, `gemba.local.yaml`, optional, private to the
  clone and ignored by git, what belongs to one person on one machine. `config.py` says
  which file each key belongs in.
- A **team** is the members the `team` of the shared config declares, who share one
  obeya. A **member** is one person of the team, with a folder under `tasks/` and
  initials; the personal config of each clone names its member as `me`. A member who
  leaves is marked inactive, never removed, so their initials are never reused. The
  **owner** of a task is the one member it belongs to, the one whose folder holds it.
- A **task** is one unit of work, recorded in one **task file** under
  `tasks/<workstream>/`, or `tasks/<member>/<workstream>/` in an obeya with a team,
  identified by its **ref** (`PREFIX-N`, or `INITIALS-PREFIX-N` with a team, such as
  `MR-SUP-3`). The **parent** of a task is the task it was split from, which the child
  names when it is created, and never the reverse: the children of a task are found by
  a scan. A **workstream** is a folder under `tasks/` plus its block in the gemba
  config. An **update** is one dated entry under `## Updates`; recording it is the
  process, `record`.
- A **run** is the execution of a task, from launch to removal. A **harness** is the
  folder of one run under `harnesses/<workstream>/<stem>/`: its own local git
  repository, where the agent executes, and the root the IDE opens. The **harness
  config** is `harness.yaml`, the identity of the run. To **launch** a task is to
  create its harness and open it in the IDE.
- Inside a harness: the **guide** (`AGENTS.md`, `CLAUDE.md`, one per agent provider),
  **notes** (filed and dated by gemba), **assets** (raw artifacts), **worktrees** (git
  worktrees of the repositories under the `repos_dir` of the personal config, each on
  the local **branch of the run**, `<branch_prefix>/<obeya>/<ref>`, never pushed under
  its own name). *Repo* alone always means one of those repositories under `repos_dir`,
  never the obeya.
- An **agent provider** is the agent tool (Claude Code, Codex...) that decides the
  skills folder and the guide filename, declared in the shared config, which the
  personal config may replace for the harnesses of its clone. The **IDE** is the editor
  that opens the harness, declared in the personal config.
- A **process** is one capability of Gemba: one skill plus one subcommand or group. A
  **skill** is the agent-facing instructions of a process, a package asset written by
  the CLI into the obeya and into each harness.
- A **report** is the summary of a period of work across every task, read from the
  task files, every count and sum computed by `gemba report`.
- Rejected words: *sandbox* and *workspace* for the harness; *ledger*, *tasks repo* and
  *harness* for the obeya; *organization* for the obeya or its name; *task type*;
  *daily status* for the report.

## Commands

```bash
uv sync                                          # environment, lock file, editable install
uv run python -m unittest discover -s tests      # full suite: cases, unit tests, traceability
uv run python -m unittest discover -s tests -p test_config.py   # one module
uv run python -m unittest discover -s tests -k test_create_invalid_slug   # one case file
GEMBA_CHANGE=<change> uv run python -m unittest discover -s tests -p test_scenarios.py
uv run ruff format .  &&  uv run ruff check .  &&  uv run pyright
uv run pre-commit install --hook-type pre-commit --hook-type pre-push   # lint on commit, suite on push
uv tool install -e .                             # the gemba command from this tree, for development
uv build                                         # the distributions, under dist/
```

The black-box cases run the `gemba` executable found on PATH: under `uv run` that is
the one of `.venv`, which always reflects the working tree. Harness and worktree cases
need `git`; the runner ignores the user's git config, fixes the identity and puts a
stub `code` first on PATH, so no case opens an IDE. `gemba --help` lists every
subcommand; the README explains each process.

## Principles

- **Three piles, kept physically separate.** Built-in behaviour (`src/gemba/` and the
  steps in the skills), customization (`gemba.yaml`, `gemba.local.yaml`) and data
  (`tasks/`, `harnesses/`). No module and no skill contains a configured value; every
  one is read from the gemba config at run time.
- **Commands own the frontmatter, agents own the body.** Only commands write
  `status`, `ref`, `parent`, the dates and `metadata` of a task; the skills are
  forbidden from writing frontmatter by hand. Refs are never reused, archives included.
- **Domain modules and adapters.** The modules of `src/gemba/` hold the rules and have
  no side effects beyond reading files; `commands/*.py` are the adapters, one per
  process, each exposing `register(subparsers)` and returning an exit code, owning the
  writes, the git commands, the clock and the output. `cli.py` only dispatches. New
  logic goes into a domain module; every public function is fully type-annotated, and
  each module's docstring says what it owns.
- **One writer per folder.** In an obeya with a team, the commands that write a task
  write only the tasks of `me`, under `tasks/<me>/`, and every member reads every task,
  so the obeya needs no backend: git carries it, and a pull almost never conflicts. The
  guard stops accidents, not a determined person: access control belongs to the git
  host.
- **Every problem at once, nothing written on refusal.** Validation problems are
  accumulated and reported in one message so the agent fixes a call in one round.
  Every error path exits 1, argparse usage errors included, and writes no file.
- **Config and skills share one contract.** `config.py` is the only entry point that
  validates `gemba.yaml` and `gemba.local.yaml`, including the `context` and `rules`
  blocks that only the agent consumes; `gemba config show` prints the effective config
  and the skills read it there, never combining the levels of the files themselves.
- **The cases are the executable specification.** `tests/cases/<process>/*.yaml` hold
  one black-box case per spec scenario, each naming its scenario
  (`<capability>: <scenario title>`); `test_scenarios.py` enforces the link in both
  directions, with `tests/not-automated.yaml` as the only exemption, each entry with
  its reason. It reads the main specs with the delta specs of every active change
  applied, so the suite passes as soon as a change is implemented; `GEMBA_CHANGE`
  narrows it to one. Cases, exemptions and specs change together, through a change,
  never to make a failing test pass.

## Naming and adding

- A process is one skill named `gemba-` plus the subcommand or group it owns:
  `gemba-create` drives `gemba create`. The task is the implicit object, so a
  subcommand that acts on a task is a bare verb; any other object with verbs of its
  own is a group (`gemba harness <verb>`, `gemba config <verb>`) driven by one skill.
  A group that a person runs to maintain the obeya, such as `gemba skills`, or that git
  runs from a hook, such as `gemba hook`, has no skill. The rule is
  `openspec/specs/process-naming/spec.md`.
- **Adding a process:** a spec under `openspec/specs/`, its cases, a domain module or
  functions in one, an adapter in `commands/`, its entry in `COMMANDS` of `cli.py`, a
  skill asset at `src/gemba/assets/skills/<name>/SKILL.md` and its entry in `SKILLS` of
  `skills.py`, with its scope (`obeya`, `harness` or `both`).
- **Adding an agent provider:** one row in `PROVIDERS` of `skills.py`.
- **Editing a skill:** edit the asset, never a written copy. `gemba skills update`
  writes the copies with their provenance and tells a generation from a hand edit.

## Workflow

Work is organized as OpenSpec changes: `openspec new change <name>` scaffolds one,
`openspec status` and `openspec instructions` say what to write next, and
`openspec archive` lands it and syncs the specs; the OpenSpec skills of an agent run
the same commands. `openspec/config.yaml` carries the per-artifact rules and the apply
guidance: case first, then implementation; formatter, linter, type checker and suite
before a task is done. Follow it rather than re-deriving the rules here. Releasing is described in
`CONTRIBUTING.md`; `CHANGELOG.md` records every version.

Type annotations are evaluated at import time; use `from __future__ import annotations`
when a module needs a typeshed-only generic such as `argparse._SubParsersAction[...]`.
Dependency resolution has a 30-day release quarantine (`exclude-newer` in
`pyproject.toml`); a "newer version available" notice from a tool is expected.
