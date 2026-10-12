# Proposal

## Why

Gemba runs on Linux and macOS only: the harness links the task with a symbolic link
that Windows refuses without privileges, removing a harness fails on the read-only
objects of its git repository, the IDE command does not resolve `code.cmd`, a task
file checked out with CRLF breaks `gemba record`, and any non-ASCII character in a
title fails when the output goes to a pipe, which is how every agent runs the CLI.
Claude Code and Codex both run natively on Windows today, so the people Gemba is for
are there, and the product promise of the README, one install and every process
available, has to hold on the third desktop platform with the same guarantees as on
the other two.

## What Changes

- Windows becomes a supported platform, out of the box: Windows 10 or 11 with Git for
  Windows at its defaults, no administrator rights, no Developer Mode, any shell, with
  the same behaviour and the same guarantees as Linux and macOS, verified by CI on
  every push and pull request. A tasks repo and a harness created on one platform
  open on another.
- The text contract of the CLI is made explicit and the same everywhere: every file
  gemba writes ends its lines with LF, every file it reads accepts CRLF, and its
  standard output and standard error are UTF-8 whatever the console. `gemba init`
  pins LF for the files gemba owns through a `.gitattributes`.
- `task.md` in the harness is a symbolic link when the system can create one, and
  otherwise a file holding the relative path of the task, with the guide describing
  both and telling the agent to accept a permission prompt when its tool asks before
  reading the task. The rule names no operating system: the system decides.
- The `ide` command of the config gains a structured form, `command` plus `args`,
  with the string kept as its shorthand; the executable is resolved on PATH the way
  the platform does (so `code` finds `code.cmd`), the IDE starts detached on every
  platform, and the command line printed is the one declared. This is the seed of a
  later table of tools with a style per tool, as OpenSpec does, not that table.
- `gemba harness remove` and `gemba worktree remove` finish what the system lets
  them: read-only files are deleted, a path in use is retried briefly, and when it
  stays in use the command says what was left, that an IDE window or a terminal on
  the harness is the likely cause, and that running the removal again finishes it.
- Workstream identifiers and note slugs refuse the reserved device names of Windows
  on every platform, so that a tasks repo created on Linux clones on Windows. A git
  failure on a path too long for Windows gets a hint naming `core.longpaths`.
- The CI matrix runs the test suite on Windows and on macOS on the two extremes of
  the supported Python versions, with the git of the runner at its defaults, so that
  the CRLF contract is proven rather than neutralized. The package declares Windows
  in its classifiers; the README names git as a prerequisite on every platform and
  carries the Windows notes; SECURITY.md says that a `.cmd` IDE command runs through
  `cmd.exe`.

No change is breaking: every `gemba.yaml`, task file and harness that works today
keeps working, and the string form of `ide` is unchanged.

## Capabilities

### New Capabilities
- `platform-support`: the promises that belong to no single command: the supported
  platforms and their prerequisites, the text contract (LF written, CRLF read, UTF-8
  output), and the portability of what gemba names and writes across platforms.

### Modified Capabilities
- `harness-launch`: `task.md` is a symbolic link where the system allows one and a
  file holding the relative path of the task elsewhere; the IDE is started from a
  resolved executable and a list of arguments, detached on every platform.
- `gemba-config`: `ide` accepts a structured form, `{command, args}`, beside the
  string; workstream identifiers refuse the reserved device names of Windows.
- `harness-notes`: the slug of a draft refuses the reserved device names of Windows;
  the body of a filed note keeps its characters but takes LF line endings and loses
  a leading byte-order mark, so a note holds one convention whatever wrote the draft.
- `harness-removal`: a removal interrupted by the system reports what was left, the
  likely cause and that running it again finishes; `task.md` is deleted whatever its
  form.
- `harness-worktrees`: `worktree remove` and the removal of worktrees by
  `harness remove` apply the same resilience to a worktree in use.
- `repo-initialization`: the scaffold holds a `.gitattributes` that pins LF for the
  files gemba owns, written when missing and kept when present, like the
  `.gitignore` line.
- `harness-guide`: the guide describes `task.md` in both forms and the permission
  prompt the agent may get when reading the task.
- `package-release`: the classifiers name Windows beside POSIX and macOS, and the CI
  runs the suite on the three platforms, on the two extremes of the Python versions
  on macOS and Windows.

## Impact

- `src/gemba/cli.py`: standard output and error reconfigured to UTF-8 at start.
- `src/gemba/commands/create.py`, `record.py`, `commands/harness.py`: LF on every
  write, CRLF normalized at every read boundary.
- `src/gemba/commands/harness.py`: the link with its fallback, the IDE launch
  (executable resolution, detached start per platform), the resilient deletion;
  `src/gemba/commands/worktree.py`: the resilient worktree removal.
- `src/gemba/config.py`: the structured `ide`, the reserved-name rule for workstream
  identifiers; `src/gemba/harness.py`: the same rule for draft slugs, the `task.md`
  forms; a new domain module for the platform rules (reserved names, the text
  contract helpers, the deletion policy) so that no adapter carries them twice.
- `src/gemba/repo.py`, `commands/init.py`: the `.gitattributes` of the scaffold.
- `src/gemba/assets/harness/guide.md` and the `gemba-harness` skill: `task.md` in
  both forms; the `gemba-config` and `gemba-init` skills: the structured `ide`.
- `tests/test_cases.py`: a `code.cmd` stub beside the shell stub, the IDE case no
  longer assuming an absolute path starts with `/`; unit tests for the link
  fallback, since CI runners on Windows can create links.
- `.github/workflows/ci.yml`: Windows jobs; macOS on two Python versions.
- `pyproject.toml`, `README.md`, `SECURITY.md`, `CHANGELOG.md`.
- No new dependency: everything comes from the standard library.
