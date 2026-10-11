# process-naming Specification

## Purpose

How a process of Gemba is named, as an agent skill and as a subcommand of the
`gemba` command, so that every process added by a later sprint gets its name from one
rule instead of from a case-by-case choice.

## Requirements

### Requirement: The task is the implicit object of the command
A subcommand of `gemba` that acts on a task SHALL be a bare verb with no object noun.
The command SHALL NOT expose a `task` group or a `task` noun for those subcommands.
Initializing a tasks repo SHALL be the bare subcommand `init`, acting on the tasks
repo itself; the config of the tasks repo, an object with verbs of its own, SHALL be
the group `gemba config`.

#### Scenario: Task subcommands take no noun
- **WHEN** a process registers, lists, updates, reports on or closes a task
- **THEN** its subcommand is the verb alone, as in `gemba create` and `gemba list`, and no form with a `task` noun exists

#### Scenario: Harness initialization is plain
- **WHEN** a process initializes a tasks repo in a folder
- **THEN** its subcommand is `gemba init`, with no object noun, and its skill is `gemba-init`

#### Scenario: Config subcommands are grouped
- **WHEN** a process checks or shows the config of the tasks repo
- **THEN** its subcommands are `gemba config check` and `gemba config show`, and its skill is `gemba-config`

### Requirement: Every other object is a group
A process whose steps act on an object other than a task or the tasks repo, such as
the harness of a launched task or the skills the CLI writes, SHALL expose its
subcommands under a group named after that object, as in `gemba harness <verb>` and
`gemba skills <verb>`. A verb SHALL NOT exist both bare and inside a group with
different meanings.

#### Scenario: Harness subcommands are grouped
- **WHEN** a process launches the harness of a task, files a note in it or resolves an approved note
- **THEN** its subcommands are `gemba harness launch`, `gemba harness note` and `gemba harness resolve`, and `gemba <verb>` keeps its meaning for tasks

#### Scenario: Skills subcommands are grouped
- **WHEN** the CLI writes or checks the skills of the tasks repo
- **THEN** its subcommands are `gemba skills <verb>`, as in `gemba skills update`

### Requirement: One skill per process, named after its subcommand
Each process of Gemba SHALL be exactly one agent skill whose name is `gemba-` followed
by the subcommand or the group that process owns: `gemba-create`, `gemba-list`,
`gemba-init`, `gemba-harness`, `gemba-record`, `gemba-report`, `gemba-set`. A process
with several subcommands inside one group SHALL be one skill named after the group, not
one skill per verb. A process whose steps need no deterministic command SHALL be one
skill alone, named `gemba-` followed by the name of the process, which is the name its
subcommand would take, so that when a deterministic step appears the process gains
that subcommand and its skill keeps its name, as the report did. The skill's
description, not its name, SHALL carry the phrases that make an agent choose it. A
subcommand or group that no process needs, because a person runs it to maintain the
tasks repo rather than an agent following steps, SHALL have no skill; `gemba skills` is
one.

#### Scenario: Existing skills follow the rule
- **WHEN** the tasks repo is at this change or later
- **THEN** the skills that drive `gemba create` and `gemba list` are `gemba-create` and `gemba-list`, and no skill named `task-creator` or `task-lister` exists

#### Scenario: Grouped process is one skill
- **WHEN** a process owns the `gemba harness` group
- **THEN** it is the single skill `gemba-harness`, whatever the number of verbs in the group

#### Scenario: Skill-only process
- **WHEN** a process has no deterministic step and so owns no subcommand
- **THEN** it is the single skill named after the process, with the name its subcommand would take, and no subcommand of that name exists

#### Scenario: Skill-only process gains its subcommand
- **WHEN** the report process gains a deterministic step, the arithmetic over the selected tasks
- **THEN** its subcommand is `gemba report` and its skill keeps the name `gemba-report`

#### Scenario: Maintenance group has no skill
- **WHEN** the skills are written with `gemba skills update`
- **THEN** no skill named `gemba-skills` exists in the package registry or in any skills folder the command writes
