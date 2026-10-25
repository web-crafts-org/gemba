# Spec Delta

## REMOVED Requirements

### Requirement: One skill per process, named after its subcommand
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "One skill
per process", "A process with no command of its own" and "A maintenance command has no
skill".

## ADDED Requirements

### Requirement: One skill per process
Each process of Gemba SHALL be exactly one agent skill named `gemba-` followed by the
subcommand or the group it owns, such as `gemba-create`, `gemba-list`, `gemba-init`,
`gemba-harness`, `gemba-record`, `gemba-report` and `gemba-set`. A process of several
subcommands in one group SHALL be one skill named after the group, not one per verb.
The skill's description, not its name, SHALL carry the phrases that make an agent
choose it.

#### Scenario: Existing skills follow the rule
- **WHEN** the obeya is at this change or later
- **THEN** the skills that drive `gemba create` and `gemba list` are `gemba-create` and `gemba-list`, and no skill named `task-creator` or `task-lister` exists
- **Cases**: keeps the entry `process-naming: Existing skills follow the rule` of `tests/not-automated.yaml`

#### Scenario: Grouped process is one skill
- **WHEN** a process owns the `gemba harness` group
- **THEN** it is the single skill `gemba-harness`, whatever the number of verbs in the group
- **Cases**: keeps the entry `process-naming: Grouped process is one skill` of `tests/not-automated.yaml`

### Requirement: A process with no command of its own
A process whose steps need no deterministic command of its own, such as one that only
composes the commands of others, SHALL be one skill alone, named `gemba-` followed by
the name its subcommand would take, so that when a deterministic step appears the
process gains that subcommand and its skill keeps its name, as the report did.
`gemba-migrate`, which composes `gemba create`, `gemba record`, `gemba mark` and
`gemba archive`, is one.

#### Scenario: Skill-only process
- **WHEN** the migration process has no deterministic step of its own and composes the commands of other processes
- **THEN** it is the single skill `gemba-migrate`, with the name its subcommand would take, and no `gemba migrate` subcommand exists
- **Cases**: keeps the entry `process-naming: Skill-only process` of `tests/not-automated.yaml`

#### Scenario: Skill-only process gains its subcommand
- **WHEN** the report process gains a deterministic step, the arithmetic over the selected tasks
- **THEN** its subcommand is `gemba report` and its skill keeps the name `gemba-report`
- **Cases**: keeps the entry `process-naming: Skill-only process gains its subcommand` of `tests/not-automated.yaml`

### Requirement: A maintenance command has no skill
A subcommand or group that no process needs, because a person runs it to maintain the
obeya rather than an agent following steps, SHALL have no skill; `gemba skills` is
one.

#### Scenario: Maintenance group has no skill
- **WHEN** the skills are written with `gemba skills update`
- **THEN** no skill named `gemba-skills` exists in the package registry or in any skills folder the command writes
- **Cases**: keeps `tests/cases/skills/every-registered-skill-is-written.yaml`
