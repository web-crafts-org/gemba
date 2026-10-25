# task-ownership Specification

## Purpose

In an obeya shared by a team, every task belongs to one member, its owner, and each
clone knows its member through `me`. The commands that write a task write only the
tasks of that member, so that each member's folder has one writer; the guard stops
accidents, not a determined person.

## Requirements

### Requirement: The owner of a task
When the shared config declares a team, the owner of a task SHALL be the member whose
folder under `tasks/` holds its file, archived or not. The tasks of every member,
active or not, SHALL be read, listed, reported and found by ref as any task is,
whether or not the personal config declares `me`.

#### Scenario: Tasks of an inactive member read
- **WHEN** the team declares `manuel` and `ana`, `ana` with `active: false`, and `tasks/ana/support/` holds `AG-SUP-1`
- **THEN** `gemba list` lists `AG-SUP-1` with `owner` `ana`, and the exit code is 0

#### Scenario: Tasks read without a member
- **WHEN** the shared config declares a team, the personal config declares no `me`, and `gemba list` and `gemba report --by owner` run
- **THEN** both commands read every member's tasks as they would with `me` declared, and exit 0

### Requirement: Writes need an active member
When the shared config declares a team, `gemba create`, `gemba record`, `gemba mark`,
`gemba set`, `gemba archive` and `gemba harness launch` SHALL refuse to write when the
personal config declares no `me`, saying to add it to `gemba.local.yaml` and naming the
members, or when `me` names an inactive member, together with every other problem of
the call.

#### Scenario: Write without a member refused
- **WHEN** `gemba create --workstream support --slug export-times-out` runs in an obeya whose team declares `manuel` and `ana` and whose personal config declares no `me`
- **THEN** the command exits 1, says that `me` goes in `gemba.local.yaml`, names `manuel` and `ana`, and writes nothing

#### Scenario: Inactive member writes nothing
- **WHEN** the personal config declares `me: ana`, `ana` has `active: false`, and `gemba mark AG-SUP-1 done` runs
- **THEN** the command exits 1, says that `ana` is an inactive member, and the task file is unchanged

### Requirement: Only the owner writes a task
When the shared config declares a team, `gemba record`, `gemba mark`, `gemba set`,
`gemba archive` and `gemba harness launch` SHALL refuse a task whose owner is not
`me`, naming the task and its owner, together with every other problem of the call,
and write nothing for it. The guard prevents accidents and is not access control,
which belongs to the git host.

#### Scenario: Own task launched
- **WHEN** `me` is `manuel` and `gemba harness launch MR-SUP-1 --no-open` runs, `MR-SUP-1` being a task of `manuel` under `tasks/manuel/support/`
- **THEN** the harness is created under `harnesses/support/`, its `task.md` reaches the task file under `tasks/manuel/support/`, the task moves to `in-progress`, and the exit code is 0

#### Scenario: Another member's task not marked
- **WHEN** `me` is `manuel` and `gemba mark AG-SUP-1 done` runs, `AG-SUP-1` being a task of `ana`
- **THEN** the command exits 1, names `AG-SUP-1` and its owner `ana`, and the task file is unchanged

#### Scenario: Another member's task not set
- **WHEN** `me` is `manuel` and `gemba set AG-SUP-1 hours=2` runs, `AG-SUP-1` being a task of `ana`
- **THEN** the command exits 1, names `AG-SUP-1` and its owner `ana`, and the task file is unchanged

#### Scenario: Another member's task not recorded
- **WHEN** `me` is `manuel` and `gemba record AG-SUP-1 update.md` runs from the obeya, `AG-SUP-1` being a task of `ana`
- **THEN** the command exits 1, names `AG-SUP-1` and its owner `ana`, and neither the task file nor the draft changes

#### Scenario: Another member's task not archived
- **WHEN** `me` is `manuel` and `gemba archive MR-SUP-1 AG-SUP-1` runs, `MR-SUP-1` being a task of `manuel` and `AG-SUP-1` a task of `ana`
- **THEN** `MR-SUP-1` is archived, a `not archived:` line names `AG-SUP-1` and its owner `ana`, its file stays where it was, and the exit code is 1

#### Scenario: Another member's task not launched
- **WHEN** `me` is `manuel` and `gemba harness launch AG-SUP-1` runs, `AG-SUP-1` being a task of `ana`
- **THEN** the command exits 1, names `AG-SUP-1` and its owner `ana`, and neither a harness folder nor a change to the task file is left

### Requirement: The agent writes only the user's tasks
Following the skills that write a task, the agent SHALL never create a task for another
member nor write a task another member owns. When a command refuses a task of another
member, the agent SHALL relay the refusal and suggest asking its owner, and SHALL never
edit the task file by hand to get around it.

#### Scenario: Task asked for another member
- **WHEN** the user asks the agent to create a task for `ana`, another member of the team
- **THEN** the agent says that each member creates their own tasks, offers to create one for the user or to draft what `ana` needs to create hers, and runs no command on `ana`'s behalf

#### Scenario: Refusal of another member's task relayed
- **WHEN** `gemba mark` refuses `AG-SUP-1` because its owner is `ana`
- **THEN** the agent relays the refusal, suggests asking `ana`, and leaves the task file as it is
