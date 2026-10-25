# task-archiving Specification

## Purpose

Archiving moves a task that has gone cold into its workstream's `archive/` folder,
unchanged, so that listings stay small and the task stays findable on request; it is
independent of the task's status and of any run.

## Requirements

### Requirement: Archive moves the task file
`gemba archive <ref> [<ref> ...]` SHALL resolve each ref anywhere under `tasks/`,
archives included, move its task file from `tasks/<workstream>/` into
`tasks/<workstream>/archive/` with the same name and content, byte for byte,
`updated_at` included, since archiving is no activity on the task, and print
`archived: <new path>`. It SHALL archive a task whatever its status and run no git: a
person commits the obeya.

#### Scenario: Task archived
- **WHEN** `gemba archive SUP-1` runs for `tasks/support/2026-09-30-SUP-1-login-fails.md`, a `done` task with `updated_at: 2026-10-01`
- **THEN** `tasks/support/archive/2026-09-30-SUP-1-login-fails.md` holds exactly the former content, `updated_at` included, the former path no longer exists, the output is `archived: tasks/support/archive/2026-09-30-SUP-1-login-fails.md` and the exit code is 0

#### Scenario: Several tasks archived
- **WHEN** `gemba archive SUP-1 OPS-2` runs for a `done` task and a `blocked` task of two workstreams
- **THEN** both files are under their own workstream's `archive/`, one `archived:` line per ref is printed in the order given, and the exit code is 0

### Requirement: Archive refuses each ref on its own
Each ref SHALL be handled on its own: a ref SHALL be refused, the others still
archived, when no task has it, when its task is already archived, when a folder exists
at the harness path of its task, or when a file exists at the destination, with a line
`not archived: <ref> <reason>`. The command SHALL exit 0 when every ref was archived
and 1 otherwise.

#### Scenario: Task with a harness refused
- **WHEN** `gemba archive SUP-1 SUP-2` runs and a harness folder exists for `SUP-2`
- **THEN** `SUP-1` is archived, `SUP-2` is left where it is with a `not archived:` line naming the harness path and saying to remove the harness first, and the exit code is 1

#### Scenario: Already archived refused
- **WHEN** the task with the ref given is already under an `archive/` folder
- **THEN** the output says the task is already archived, nothing is written, and the exit code is 1

#### Scenario: Unknown ref refused
- **WHEN** no task under `tasks/` has one of the refs given
- **THEN** that ref gets a `not archived:` line saying no task has it, the other refs are archived, and the exit code is 1

### Requirement: The agent archives what went cold
The `gemba-archive` skill SHALL have the agent, from the obeya, archive the tasks the
user names by ref, or, asked to archive what went cold, list candidates with
`gemba list --updated-to <date>`, with `--status done` unless the user names other
statuses, show their ref, title, status and last update, let the user confirm or trim
them, and run `gemba archive` once with the confirmed refs. It SHALL relay every
`not archived:` line, saying that `gemba harness remove` clears a harness.

#### Scenario: Agent archives cold tasks
- **WHEN** the user asks to archive the tasks not touched since a date
- **THEN** the agent lists them with `gemba list --updated-to <date> --status done`, shows them, and after the user's confirmation runs `gemba archive` with their refs

### Requirement: The agent follows the archive block
The skill SHALL have the agent read the `archive` block of each workstream involved in
the gemba config and follow its `rules` and `context`, and SHALL forbid moving a task
file by hand.

#### Scenario: Agent follows the verb's rules
- **WHEN** workstream `support` declares `archive.rules` containing "never archive a task whose invoice is unpaid"
- **THEN** the agent follows that rule before proposing or running the command for a `support` task

#### Scenario: Config change without skill change
- **WHEN** an `archive` rule is added, changed or removed in the gemba config
- **THEN** the agent's behaviour changes accordingly without any change to the skill
