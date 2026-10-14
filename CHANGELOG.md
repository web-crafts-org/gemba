# Changelog

All notable changes to the gemba CLI are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): while the major version is
0, a minor version may change a command or a file format, and the entry says so.

## [Unreleased]

## [0.2.0] - 2026-10-13

Windows joins Linux and macOS as a supported platform, with the same behaviour and the
same guarantees. One change refuses a `gemba.yaml` that 0.1 accepted: a workstream
named after a device Windows reserves, listed under Changed.

### Added

- Windows is a supported platform, beside Linux and macOS: Windows 10 or later with
  Git for Windows at its defaults, no administrator rights and no Developer Mode, from
  PowerShell, the command prompt or Git Bash. The README has a section on it.
- Python 3.14 is supported. The CI runs the suite on every pull request and every push
  to `main`: on Linux with every supported Python, 3.11 to 3.14, and on macOS and
  Windows with 3.11 and 3.14.
- The `ide` command of `gemba.yaml` takes a structured form, `{ command, args }`,
  beside the string, which is split as a POSIX shell splits it; the command is
  resolved on PATH the way the platform does, so `code` finds `code.cmd` on Windows,
  and an `ide` command found nowhere on PATH is reported with its name.
- `gemba init` writes a `.gitattributes` that keeps LF line endings in the files
  Gemba owns, and completes an existing one like the `.gitignore`: running it again on
  a tasks repo made before this version adds it.
- A git failure on a path too long for Windows gets a hint naming `core.longpaths`.
- `SECURITY.md`: how to report a vulnerability privately, the threat model of the CLI,
  what is in scope and what is not, and the automated checks of the repository. The
  workflows that test, build and publish the package pin every action to a commit and
  run with read-only permissions.

### Changed

- Workstream identifiers and note slugs refuse the device names Windows reserves
  (`con`, `nul`, `aux`, `com1`...) on every platform, so that a tasks repo moves
  between platforms: a `gemba.yaml` that declares a workstream with one of those names,
  accepted by 0.1, is refused, and the workstream has to be renamed.
- Every file Gemba writes ends its lines with LF, every file it reads accepts CRLF,
  and its output is UTF-8 whatever the console: a task file checked out with CRLF
  records and launches like any other, and a draft filed as a note takes LF line
  endings and loses a leading byte-order mark.
- `task.md` in a harness is a symbolic link where the system lets Gemba create one
  and otherwise a file holding the relative path of the task; the guide describes
  both forms.
- `gemba harness remove` and `gemba worktree remove` delete read-only files, retry a
  path another program holds open, and when it stays held say what is left, that an
  IDE window or a terminal on the folder is the likely cause, and that running the
  removal again finishes it.
- The skills read today's date from the environment, naming the command for a POSIX
  shell and for PowerShell.

### Fixed

- The help of `gemba harness remove` says that the uncommitted paths of the harness
  repository are listed and deleted with it, as the command does, instead of saying
  that they stop the removal.

## [0.1.1] - 2026-10-11

### Added

- The release workflow creates the GitHub Release page of each version with the
  notes of its changelog section, and refuses a tag whose version has no section.

## [0.1.0] - 2026-10-11

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

[Unreleased]: https://github.com/web-crafts-org/gemba/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/web-crafts-org/gemba/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/web-crafts-org/gemba/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/web-crafts-org/gemba/releases/tag/v0.1.0
