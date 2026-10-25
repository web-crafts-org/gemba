# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Skill contains no organization-specific value`
- TO: `### Requirement: Skill contains no configured value`

## MODIFIED Requirements

### Requirement: Setting touches nothing but the metadata
`set` SHALL write only the task file and only its `metadata`: `status`, `ref`,
`updated_at` and `done_at` SHALL be written as they were, the frontmatter SHALL keep its
fixed key order, and the body SHALL be kept byte for byte. `updated_at` SHALL NOT move:
metadata is data about the task, not activity on it. The command SHALL NOT touch the
harness of the task, if one exists, and SHALL run no git. It SHALL work from any folder
below the obeya root, a harness included.

#### Scenario: Only the metadata changes
- **WHEN** `gemba set SUP-1 hours+=2` runs on a `done` task with `done_at`, a description, a link line and two recorded days
- **THEN** only the value of `hours` differs: the other frontmatter lines, `updated_at` included, and the body are byte for byte what they were
- **Cases**: keeps `tests/cases/set/only-the-metadata-changes.yaml`

#### Scenario: Set from inside the harness
- **WHEN** `gemba set SUP-1 hours+=1` runs from inside the launched harness of `SUP-1`
- **THEN** the task file holds the new value, and the harness repository has the same commits as after the launch and a clean working tree
- **Cases**: keeps `tests/cases/set/set-from-inside-the-harness.yaml`

### Requirement: Setting by the agent
The `gemba-set` skill SHALL have the agent, from the obeya or from inside a
harness, identify the task by its ref, from `harness.yaml` when inside a harness and
asking when the request is ambiguous; map what the user says to declared fields by
their names and descriptions in the gemba config; write each value in the form of the
field's declared type; use `+=` whenever the user adds to an amount rather than stating
the new total, so that it never computes a sum itself; for a text field, look up the
values already in use with `gemba report --by <field>` and reuse their spelling when
the user means one of them; run `gemba set` once with every assignment; relay the
output; and stop. It SHALL have the agent read the `set` block of the task's workstream
in the gemba config and follow its `rules` and `context`, and SHALL forbid editing the
frontmatter by hand.

#### Scenario: Agent sets a value
- **WHEN** the user says a task took two more hours, or that it was invoiced today
- **THEN** the agent runs `gemba set` with `+=2` on the number field, or today's date on the date field, and relays the output
- **Cases**: keeps the entry `metadata-setting: Agent sets a value` of `tests/not-automated.yaml`

#### Scenario: Spelling in use reused
- **WHEN** the user says a task is for "ACME" and the text field `client` already holds `acme` on other tasks
- **THEN** the agent finds `acme` with `gemba report --by client` and sets `client=acme`, asking when it cannot tell whether the user means the value in use
- **Cases**: keeps the entry `metadata-setting: Spelling in use reused` of `tests/not-automated.yaml`

#### Scenario: Agent follows the verb's rules
- **WHEN** workstream `support` declares `set.rules` containing "set invoiced only when the task is done"
- **THEN** the agent follows that rule before running the command for a `support` task
- **Cases**: keeps the entry `metadata-setting: Agent follows the verb's rules` of `tests/not-automated.yaml`

### Requirement: Skill contains no configured value
The `gemba-set` skill SHALL contain only the process and SHALL NOT name any workstream,
prefix, metadata field or configured rule. It MAY branch on the declared type
of a field, never on its name or meaning.

#### Scenario: Config change without skill change
- **WHEN** a metadata field is added, retyped or removed in `gemba.yaml`
- **THEN** the skill needs no edit for the agent to set it
- **Cases**: keeps the entry `metadata-setting: Config change without skill change` of `tests/not-automated.yaml`
