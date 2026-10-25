# Spec Delta

## MODIFIED Requirements

### Requirement: The report is read-only and invents nothing
The agent SHALL NOT edit any task file, write any file or commit while reporting, and
SHALL NOT state any activity that a subsection of the period, a creation date or a
`done_at` does not support, nor any number that `gemba report` did not print. It SHALL
report every problem returned by the listing or by the report command alongside the
report. To record what is missing, it SHALL point the user to the `gemba-record`
skill, used inside the harness of the task for the work of its run, or from the tasks
repo for work done outside one, rather than editing the task itself.

#### Scenario: Nothing written
- **WHEN** a report is produced
- **THEN** the tasks repo working tree is as it was before
- **Cases**: keeps `tests/cases/report/nothing-written.yaml`

#### Scenario: Problems relayed
- **WHEN** the listing or the report command returns a non-empty `problems` list
- **THEN** the agent tells the user each path and its problem alongside the report
- **Cases**: keeps the entry `task-reporting: Problems relayed` of `tests/not-automated.yaml`

#### Scenario: Gap pointed to recording
- **WHEN** a report lists a task with nothing recorded for the period
- **THEN** the agent says the gap is recorded with the `gemba-record` skill, inside the task's harness for the work of its run or from the tasks repo for work done outside one, and records nothing itself
- **Cases**: adds the entry `task-reporting: Gap pointed to recording` of `tests/not-automated.yaml`
