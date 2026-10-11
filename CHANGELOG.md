# Changelog

All notable changes to the gemba CLI are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): while the major version is
0, a minor version may change a command or a file format, and the entry says so.

## [Unreleased]

## [0.1.0] - 2026-10-09

The first release: the whole cycle of a task, from a tasks repo that `gemba init`
creates to the report of a period.

### Added

- `gemba init`, which makes a folder a tasks repo, and the `gemba-init` skill, the
  guided first configuration.
- `gemba.yaml`, the gemba config: workstreams with their prefixes, typed metadata
  fields (`text`, `number`, `boolean`, `date`), agent providers, the IDE command, the
  organization, the repositories folder, and `context` and `rules` per process, at the
  top level and per workstream; `gemba config check` and `gemba config show`, and the
  `gemba-config` skill that holds the reference of every key.
- `gemba create`, `gemba list`, `gemba set`, `gemba mark` and `gemba archive`, each with
  its skill: the frontmatter of a task is written by commands only, refs are never
  reused, and listings and reports read every task file and report the invalid ones.
- `gemba harness launch`, `note`, `resolve` and `remove`: the harness of a run, its own
  git repository with the guide of the agent, the filed notes and their approval gate
  for actions outside the harness.
- `gemba worktree add`, `list` and `remove`: git worktrees of the organization's
  repositories inside a harness, each on the local branch of the run, never pushed
  under its own name.
- `gemba record` and the `gemba-report` skill: the update of a day written into the
  task from a draft, and the report of a day, a week or a month, with every count and
  sum taken from `gemba report`.
- `gemba skills update`: the skills ship with the package and are written into the
  tasks repo and into each harness for every agent provider declared, with their
  provenance, so an upgrade refreshes them and a hand edit is kept.

[Unreleased]: https://github.com/web-crafts-org/gemba/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/web-crafts-org/gemba/releases/tag/v0.1.0
