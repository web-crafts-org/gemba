# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Skill contains no organization-specific value`
- TO: `### Requirement: Skill contains no configured value`

## MODIFIED Requirements

### Requirement: The report is read-only and invents nothing
The agent SHALL NOT edit any task file, write any file or commit while reporting, and
SHALL NOT state any activity that a subsection of the period, a creation date or a
`done_at` does not support, nor any number that `gemba report` did not print. It SHALL
report every problem returned by the listing or by the report command alongside the
report. To record what is missing, it SHALL point the user to the `gemba-record`
skill, used inside the harness of the task for the work of its run, or from the obeya for work done outside one, rather than editing the task itself.

#### Scenario: Nothing written
- **WHEN** a report is produced
- **THEN** the obeya working tree is as it was before
- **Cases**: modifies `tests/cases/report/nothing-written.yaml` (its name says obeya)

#### Scenario: Problems relayed
- **WHEN** the listing or the report command returns a non-empty `problems` list
- **THEN** the agent tells the user each path and its problem alongside the report
- **Cases**: keeps the entry `task-reporting: Problems relayed` of `tests/not-automated.yaml`

#### Scenario: Gap pointed to recording
- **WHEN** a report lists a task with nothing recorded for the period
- **THEN** the agent says the gap is recorded with the `gemba-record` skill, inside the task's harness for the work of its run or from the obeya for work done outside one, and records nothing itself
- **Cases**: modifies the entry `task-reporting: Gap pointed to recording` of `tests/not-automated.yaml` (its reason says obeya)

### Requirement: Skill contains no configured value
The `gemba-report` skill SHALL contain only the process and SHALL NOT name any
workstream, prefix, metadata field or configured rule.

#### Scenario: Config change without skill change
- **WHEN** a workstream or a metadata field is added to `gemba.yaml`
- **THEN** the skill needs no edit for the report to cover it
- **Cases**: keeps the entry `task-reporting: Config change without skill change` of `tests/not-automated.yaml`

### Requirement: The report process owns gemba report
The report process SHALL be the `gemba-report` skill, scoped to the obeya, and the
`gemba report` subcommand. A report SHALL be the summary of a period of work, one day
or several consecutive days, across every task. The command SHALL compute every count
and sum over a selection of tasks and print it for the agent; the skill SHALL read the
task files for the work of the period and compose the report.

#### Scenario: Report subcommand exists
- **WHEN** `gemba report --help` runs
- **THEN** it exits 0 and names the selection filters, `--by` and `--sum`
- **Cases**: keeps `tests/cases/report/report-subcommand-exists.yaml`
