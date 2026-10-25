# Changelog

All notable changes to the gemba CLI are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): while the major version is
0, a minor version may change a command or a file format, and the entry says so.

## [Unreleased]

The gemba config becomes two files, so that an obeya can be shared: `gemba.yaml`,
committed, and `gemba.local.yaml`, private to the clone. The obeya is what earlier
versions called the tasks repo. Two changes refuse a `gemba.yaml` that 0.2 accepted,
both listed under Changed: the keys that moved to the personal config, and
`organization`, renamed `obeya`.

### Added

- `gemba.local.yaml`, the personal config, beside `gemba.yaml` at the obeya root:
  optional, ignored by git, never written by a command. It holds `ide`, `repos_dir`
  and `branch_prefix`; it may declare `agent_providers`, which replace the shared ones
  for the harnesses launched from that clone and for nothing else; and it may add
  `context`, `rules` and `harness.guide` at its top level and under `workstreams`, for
  workstreams of the shared catalogue. The personal blocks come after the shared ones
  in every effective block, so a personal rule wins a contradiction.
- The guide of a harness ends with a `Your user` section holding the `harness.guide`
  texts of the personal config.
- `gemba config check` reports `gemba.local.yaml is valid` and a `harness providers:`
  line when there is a personal config; `gemba config show` prints `harness_providers`
  and `guide.user`.
- `gemba init` writes `gemba.local.yaml` into the `.gitignore` and appends it to an
  existing one: running it again on an obeya made before this version adds it.
- `gemba record <ref> <file>` records a task from the obeya, for work done outside a
  harness, such as a meeting or a review: the task is named by its ref, archives
  included, and the draft lies directly in the obeya root. Inside a harness the ref is
  optional and, when given, must be the ref of its task, so `gemba record update.md`
  keeps its meaning.
- The `gemba-record` skill is written into the obeya too: from there the agent records
  what you tell it was done on a task, such as a meeting or a review, and never the
  notes of a harness, whose run is recorded from inside it.
- `gemba record <ref> --from <task file>` copies the whole dated history of another
  task file, such as a task of an earlier obeya, into a task whose `## Updates` is
  empty, in one call. The command reads that file itself and copies its subsections as
  they are, moves `updated_at` to the last date copied, and never changes the file. It
  refuses with every problem of both files at once: a history that breaks the rules of
  the section, text before its first date, a date before the creation of the task or
  after today, or a task that already holds an update.
- The `gemba-migrate` skill, written into the obeya: ask the agent to migrate tasks
  from another obeya, such as your earlier tasks into a team's obeya. It reads the old
  obeya as data, asks which tasks to bring and how its workstreams and fields map to
  this config, one decision at a time, and writes every task through `gemba create`,
  `gemba record --from`, `gemba mark` and `gemba archive`. The old obeya is never
  converted: it stays as it was, its migrated tasks archived. An obeya made before this
  version gets the skill with `gemba init` or `gemba skills update`.
- `gemba worktree list --available` prints the repositories `gemba worktree add`
  accepts, one per line in name order: the folders directly under `repos_dir` that hold
  a git repository, attached or not, or `no repositories` when there is none. It
  refuses as `add` does when `repos_dir` is not declared or is not a folder, and writes
  nothing.

### Changed

- **Breaking:** `ide`, `repos_dir` and `branch_prefix` are read from
  `gemba.local.yaml` only. Every command refuses a `gemba.yaml` that declares them,
  naming each key and the file it goes in. Move them by hand, or ask the agent to fix
  the config (the `gemba-config` skill moves them), then run `gemba init` once and
  commit `gemba.yaml` and `.gitignore`. No command rewrites the config.
- **Breaking:** the `organization` key of `gemba.yaml` is now `obeya`, the name of the
  obeya, with the same shape: optional, kebab-case, in the shared config only, and the
  middle segment of the branch of a run, `<branch_prefix>/<obeya>/<ref>`. Every command
  refuses `organization` in either file, saying that it was renamed `obeya`, which
  belongs in `gemba.yaml`, together with every other problem. With the same value the
  branches keep their names, so no run loses its branches. Rename it by hand, or ask the
  agent to fix the config: the `gemba-config` skill renames it in the same pass that
  moves `ide`, `repos_dir` and `branch_prefix`.
- The tasks repo is now called the obeya (大部屋, "big room": in lean, the room where a
  team keeps all of its work in sight) everywhere: the help and the messages of every
  command, the skills, the document of `gemba config show`, which prints `obeya` and
  `harness.guide.obeya` instead of `organization` and `harness.guide.organization`, and
  the guide of a harness, whose top-level section of the shared config is titled
  `Your obeya`; a harness launched earlier keeps its guide. Run `gemba skills update`,
  or `gemba init`, to refresh the skills of an obeya made by an earlier version.
- A config refusal reports every problem of both files at once, each on its own line
  with the path of its file, instead of the first one; a check that needs another
  value runs only when that value is valid, so one mistake is reported once.
- The `gemba-init` skill writes the IDE command and the repositories folder into
  `gemba.local.yaml`, and the `gemba-config` skill holds the reference of both files,
  moves the keys of an earlier `gemba.yaml` and renames its `organization`:
  `gemba skills update` refreshes them.
- `gemba init` writes `/update.md` into the `.gitignore`, so that a draft left at the
  obeya root by a refused `gemba record` never reaches a commit. Running `gemba init`
  again on an obeya made before this version appends the line and writes the
  `gemba-record` skill; `gemba skills update` writes the skill alone.
- The `gemba-harness` skill gives a note it filed or resolved as a Markdown link to the
  path the command printed, relative to the harness root, so that you open the note
  from the chat to read it or to set `approved: true`. A harness launched earlier gets
  the new skill with `gemba skills update` run inside it.
- The `gemba-worktree` skill looks up the repositories a task needs in
  `gemba worktree list --available`: a name spelled as a listed one is used as it is;
  otherwise the agent asks you to choose among the repositories the request may mean,
  with its question panel when it has one, and never guesses. It still never reads
  `repos_dir` itself. A harness launched earlier gets the new skill with
  `gemba skills update` run inside it.

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
