# Spec Delta

## MODIFIED Requirements

### Requirement: The task is the implicit object of the command
A subcommand of `gemba` that acts on a task SHALL be a bare verb with no object noun.
The command SHALL NOT expose a `task` group or a `task` noun for those subcommands.
Initializing an obeya and checking it before a pull and a push SHALL be the bare
subcommands `init` and `sync`, acting on the obeya itself; the config of the obeya, an
object with verbs of its own, SHALL be the group `gemba config`.

#### Scenario: Task subcommands take no noun
- **WHEN** a process registers, lists, updates, reports on or closes a task
- **THEN** its subcommand is the verb alone, as in `gemba create` and `gemba list`, and no form with a `task` noun exists
- **Cases**: keeps the entry `process-naming: Task subcommands take no noun` of `tests/not-automated.yaml`

#### Scenario: Harness initialization is plain
- **WHEN** a process initializes an obeya in a folder
- **THEN** its subcommand is `gemba init`, with no object noun, and its skill is `gemba-init`
- **Cases**: keeps the entry `process-naming: Harness initialization is plain` of `tests/not-automated.yaml`

#### Scenario: Sync is plain
- **WHEN** a process checks an obeya before a pull and a push
- **THEN** its subcommand is `gemba sync`, with no object noun, and its skill is `gemba-sync`
- **Cases**: adds the entry `process-naming: Sync is plain` to `tests/not-automated.yaml`

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
- **Cases**: modifies `tests/cases/skills/every-registered-skill-is-written.yaml` (the output of its second document lists `gemba-sync`)

### Requirement: A maintenance command has no skill
A subcommand or group that no process needs, because a person runs it to maintain the
obeya or git runs it from a hook, rather than an agent following steps, SHALL have no
skill; `gemba skills` and `gemba hook` are such groups.

#### Scenario: Maintenance group has no skill
- **WHEN** the skills are written with `gemba skills update`
- **THEN** no skill named `gemba-skills` exists in the package registry or in any skills folder the command writes
- **Cases**: keeps `tests/cases/skills/every-registered-skill-is-written.yaml` (its third document)

#### Scenario: Hook group has no skill
- **WHEN** the skills are written with `gemba skills update`
- **THEN** no skill named `gemba-hook` exists in the package registry or in any skills folder the command writes
- **Cases**: adds `tests/cases/skills/hook-group-has-no-skill.yaml`
