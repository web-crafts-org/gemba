# AGENTS.md

This file provides guidance to AI agents (Claude Code, Codex and others) when working
with code in this repository. `CLAUDE.md` is a link to it.

## What this repository is

This is the product repository of Gemba, a task-based system for working with AI
agents. It holds the gemba CLI (`src/gemba/`), the skills that drive each process
(assets of the package under `src/gemba/assets/`), the specification of what the CLI
does (`openspec/specs/`) and its tests (`tests/`). It holds no `gemba.yaml` and no
tasks: a tasks repo is what `gemba init` creates somewhere else, and the README
describes Gemba from that side.

## Vocabulary

One word for one thing, in the specs, the skills, the code and the chat.

- **Gemba** is the product. The **gemba CLI** is the package we publish (distribution
  `gemba-cli`, command `gemba`).
- The **tasks repo** is the repository that holds `gemba.yaml`, `tasks/` and
  `harnesses/`; `gemba init` creates one. It is the personal traceability layer of
  someone who works for an organization.
- The **gemba config** is `gemba.yaml`, the organization's customization.
- A **task** is one unit of work, recorded in one **task file** under
  `tasks/<workstream>/`, identified by its **ref** (`PREFIX-N`). A **workstream** is a
  folder under `tasks/` plus its block in the gemba config. An **update** is one dated
  entry under `## Updates`; recording it is the process, `record`.
- A **run** is the execution of a task, from launch to removal. A **harness** is the
  folder of one run under `harnesses/<workstream>/<stem>/`: its own local git
  repository, where the agent executes, and the root the IDE opens. The **harness
  config** is `harness.yaml`, the identity of the run. To **launch** a task is to
  create its harness and open it in the IDE.
- Inside a harness: the **guide** (`AGENTS.md`, `CLAUDE.md`, one per agent provider),
  **notes** (filed and dated by gemba), **assets** (raw artifacts), **worktrees** (git
  worktrees of the repositories under the `repos_dir` of the gemba config, each on the
  local **branch of the run**, `<branch_prefix>/<organization>/<ref>`, never pushed
  under its own name).
- An **agent provider** is the agent tool (Claude Code, Codex...) that decides the
  skills folder and the guide filename. The **IDE** is the editor that opens the
  harness. Both are declared in the gemba config.
- A **process** is one capability of Gemba: one skill plus one subcommand or group. A
  **skill** is the agent-facing instructions of a process, a package asset written by
  the CLI into the tasks repo and into each harness.
- A **report** is the summary of a period of work across every task, read from the
  task files, every count and sum computed by `gemba report`.
- Rejected words: *sandbox* and *workspace* for the harness, *ledger* for the tasks
  repo, *task type*, *daily status* for the report, and *harness* for the tasks repo.

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
  steps in the skills), customization (`gemba.yaml`) and data (`tasks/`,
  `harnesses/`). No module and no skill contains a value of one organization;
  everything organization-specific is read from the gemba config at run time.
- **Commands own the frontmatter, agents own the body.** Only commands write
  `status`, `ref`, the dates and `metadata` of a task; the skills are forbidden from
  writing frontmatter by hand. Refs are never reused, archives included.
- **Domain modules and adapters.** The modules of `src/gemba/` hold the rules and have
  no side effects beyond reading files; `commands/*.py` are the adapters, one per
  process, each exposing `register(subparsers)` and returning an exit code, owning the
  writes, the git commands, the clock and the output. `cli.py` only dispatches. New
  logic goes into a domain module; every public function is fully type-annotated, and
  each module's docstring says what it owns.
- **Every problem at once, nothing written on refusal.** Validation problems are
  accumulated and reported in one message so the agent fixes a call in one round.
  Every error path exits 1, argparse usage errors included, and writes no file.
- **Config and skills share one contract.** `config.py` is the only entry point that
  validates `gemba.yaml`, including the `context` and `rules` blocks that only the
  agent consumes; `gemba config show` prints the effective config and the skills read
  it there, never combining the levels of the file themselves.
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
  A maintenance group a person runs, such as `gemba skills`, has no skill. The rule is
  `openspec/specs/process-naming/spec.md`.
- **Adding a process:** a spec under `openspec/specs/`, its cases, a domain module or
  functions in one, an adapter in `commands/`, its entry in `COMMANDS` of `cli.py`, a
  skill asset at `src/gemba/assets/skills/<name>/SKILL.md` and its entry in `SKILLS` of
  `skills.py`, with its scope (`repo`, `harness` or `both`).
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
