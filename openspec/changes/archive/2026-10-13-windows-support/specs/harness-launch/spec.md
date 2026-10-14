# Spec Delta

## MODIFIED Requirements

### Requirement: The task is reachable from inside the harness
`launch` SHALL create `task.md` at the harness root as a relative symbolic link to the
task file when the system lets the command create one, and otherwise as a regular
file holding, on one line, the same relative path of the task file in POSIX form, so
that the task can be reached from inside the harness in both cases. The rule names no
operating system: the system decides. Commands SHALL resolve the task from
`harness.yaml`, never through `task.md`.

#### Scenario: Task linked
- **WHEN** `SUP-1` of workstream `support` is launched on a system that lets the command create symbolic links
- **THEN** `task.md` in the harness is a symbolic link whose target is `../../../tasks/support/2026-09-30-SUP-1-login-fails.md` and reading it yields the task file
- **Cases**: modifies `tests/cases/harness/task-linked.yaml` (the name says the link is made where the system allows it; the assertions are unchanged)

#### Scenario: Task path written when the system refuses links
- **WHEN** `SUP-1` of workstream `support` is launched and the system refuses to create a symbolic link
- **THEN** `task.md` in the harness is a regular file whose content is `../../../tasks/support/2026-09-30-SUP-1-login-fails.md` followed by a newline, and the launch completes as usual
- **Cases**: adds the entry `harness-launch: Task path written when the system refuses links` to `tests/not-automated.yaml` (no runner of the suite refuses links, the CI runners on Windows included; covered by a unit test in `tests/test_harness.py` that makes the link creation fail)

#### Scenario: Agent reads the task through the link
- **WHEN** the agent inside a harness needs the task
- **THEN** it reads `task.md`; when `task.md` is a file naming a path, it reads the file at that path, accepting the permission its tool may ask for a read above the harness, and in neither case browses `tasks/`
- **Cases**: keeps the entry `harness-launch: Agent reads the task through the link` of `tests/not-automated.yaml`

### Requirement: Launch opens the IDE
When the gemba config declares `ide`, `launch` SHALL take its command and its
arguments as the config defines them, resolve the command to an executable on PATH
the way the platform does (so that on Windows `code` finds `code.cmd`), append the
absolute harness path as the last argument, start it without waiting for it to finish
and without a console or standard streams of its own, and print the command line as
declared followed by the path. When the command resolves to nothing on PATH, `launch`
SHALL report that the harness is ready and that the IDE command could not be started,
naming the command, and exit 1. With `--no-open` it SHALL start nothing and print no
such line. Without `ide` in the config it SHALL start nothing and print the harness
path only.

#### Scenario: IDE opened
- **WHEN** the config declares `ide: "code -n"` and a task is launched without `--no-open`
- **THEN** the output holds a line with `code -n` followed by the absolute harness path
- **Cases**: modifies `tests/cases/harness/ide-opened.yaml` (the absolute path is no longer assumed to start with `/`)

#### Scenario: IDE command not found
- **WHEN** the config declares `ide: "no-such-ide -n"` and a task is launched without `--no-open`
- **THEN** the harness is created, the output says the harness is ready and that the IDE command `no-such-ide -n` could not be started, and the exit code is 1
- **Cases**: adds `tests/cases/harness/ide-command-not-found.yaml`

#### Scenario: Open skipped
- **WHEN** a task is launched with `--no-open`
- **THEN** no IDE command line appears in the output and the harness is created as usual
- **Cases**: keeps `tests/cases/harness/open-skipped.yaml`

#### Scenario: No IDE declared
- **WHEN** the config has no `ide` key and a task is launched without `--no-open`
- **THEN** no IDE command line appears in the output and the harness path is printed
- **Cases**: keeps `tests/cases/harness/no-ide-declared.yaml`
