# Spec Delta

## MODIFIED Requirements

### Requirement: The task is the implicit object of the command
A subcommand of `gemba` that acts on a task SHALL be a bare verb with no object noun.
The command SHALL NOT expose a `task` group or a `task` noun for those subcommands.
Initializing an obeya SHALL be the bare subcommand `init`, acting on the obeya itself; the config of the obeya, an object with verbs of its own, SHALL be
the group `gemba config`.

#### Scenario: Task subcommands take no noun
- **WHEN** a process registers, lists, updates, reports on or closes a task
- **THEN** its subcommand is the verb alone, as in `gemba create` and `gemba list`, and no form with a `task` noun exists
- **Cases**: keeps the entry `process-naming: Task subcommands take no noun` of `tests/not-automated.yaml`

#### Scenario: Harness initialization is plain
- **WHEN** a process initializes an obeya in a folder
- **THEN** its subcommand is `gemba init`, with no object noun, and its skill is `gemba-init`
- **Cases**: keeps the entry `process-naming: Harness initialization is plain` of `tests/not-automated.yaml`

#### Scenario: Config subcommands are grouped
- **WHEN** a process checks or shows the config of the obeya
- **THEN** its subcommands are `gemba config check` and `gemba config show`, and its skill is `gemba-config`
- **Cases**: keeps the entry `process-naming: Config subcommands are grouped` of `tests/not-automated.yaml`

### Requirement: Every other object is a group
A process whose steps act on an object other than a task or the obeya, such as
the harness of a launched task or the skills the CLI writes, SHALL expose its
subcommands under a group named after that object, as in `gemba harness <verb>` and
`gemba skills <verb>`. A verb SHALL NOT exist both bare and inside a group with
different meanings.

#### Scenario: Harness subcommands are grouped
- **WHEN** a process launches the harness of a task, files a note in it or resolves an approved note
- **THEN** its subcommands are `gemba harness launch`, `gemba harness note` and `gemba harness resolve`, and `gemba <verb>` keeps its meaning for tasks
- **Cases**: keeps the entry `process-naming: Harness subcommands are grouped` of `tests/not-automated.yaml`

#### Scenario: Skills subcommands are grouped
- **WHEN** the CLI writes or checks the skills of the obeya
- **THEN** its subcommands are `gemba skills <verb>`, as in `gemba skills update`
- **Cases**: keeps `tests/cases/skills/every-registered-skill-is-written.yaml`

### Requirement: One skill per process, named after its subcommand
Each process of Gemba SHALL be exactly one agent skill whose name is `gemba-` followed
by the subcommand or the group that process owns: `gemba-create`, `gemba-list`,
`gemba-init`, `gemba-harness`, `gemba-record`, `gemba-report`, `gemba-set`. A process
with several subcommands inside one group SHALL be one skill named after the group, not
one skill per verb. A process whose steps need no deterministic command of its own,
such as one that only composes the commands of other processes, SHALL be one skill
alone, named `gemba-` followed by the name of the process, which is the name its
subcommand would take, so that when a deterministic step appears the process gains
that subcommand and its skill keeps its name, as the report did; `gemba-migrate`,
which composes `gemba create`, `gemba record`, `gemba mark` and `gemba archive`, is
one. The skill's description, not its name, SHALL carry the phrases that make an agent
choose it. A subcommand or group that no process needs, because a person runs it to
maintain the obeya rather than an agent following steps, SHALL have no skill;
`gemba skills` is one.

#### Scenario: Existing skills follow the rule
- **WHEN** the obeya is at this change or later
- **THEN** the skills that drive `gemba create` and `gemba list` are `gemba-create` and `gemba-list`, and no skill named `task-creator` or `task-lister` exists
- **Cases**: keeps the entry `process-naming: Existing skills follow the rule` of `tests/not-automated.yaml`

#### Scenario: Grouped process is one skill
- **WHEN** a process owns the `gemba harness` group
- **THEN** it is the single skill `gemba-harness`, whatever the number of verbs in the group
- **Cases**: keeps the entry `process-naming: Grouped process is one skill` of `tests/not-automated.yaml`

#### Scenario: Skill-only process
- **WHEN** the migration process has no deterministic step of its own and composes the commands of other processes
- **THEN** it is the single skill `gemba-migrate`, with the name its subcommand would take, and no `gemba migrate` subcommand exists
- **Cases**: keeps the entry `process-naming: Skill-only process` of `tests/not-automated.yaml`

#### Scenario: Skill-only process gains its subcommand
- **WHEN** the report process gains a deterministic step, the arithmetic over the selected tasks
- **THEN** its subcommand is `gemba report` and its skill keeps the name `gemba-report`
- **Cases**: keeps the entry `process-naming: Skill-only process gains its subcommand` of `tests/not-automated.yaml`

#### Scenario: Maintenance group has no skill
- **WHEN** the skills are written with `gemba skills update`
- **THEN** no skill named `gemba-skills` exists in the package registry or in any skills folder the command writes
- **Cases**: keeps `tests/cases/skills/every-registered-skill-is-written.yaml`
