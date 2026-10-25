# Spec Delta

## MODIFIED Requirements

### Requirement: Composition of the report
The agent SHALL write the report in the user's language, by workstream unless asked
otherwise, with one entry per task that has a signal for the period: its title, ref
and status, then the period's bullets, condensed rather than transcribed. The
candidates with nothing recorded for the period SHALL be listed at the end, under a
heading that says so; with no signal at all, the report SHALL say so plainly. Several
periods SHALL give one report each, oldest first. The layout is guidance only.

#### Scenario: Report grouped by workstream
- **WHEN** two `support` tasks and one `development` task have a subsection in the period
- **THEN** the report has a `support` group with two entries and a `development` group with one, each entry with title, ref, status and bullets
- **Cases**: keeps the entry `task-reporting: Report grouped by workstream` of `tests/not-automated.yaml`

#### Scenario: Gaps listed, not filled
- **WHEN** a candidate has no subsection in the period, was not created in it and was not finished in it
- **THEN** it appears only in the final list of tasks with nothing recorded for the period, with no bullets
- **Cases**: keeps the entry `task-reporting: Gaps listed, not filled` of `tests/not-automated.yaml`

#### Scenario: Day without activity
- **WHEN** no candidate has a signal for the period
- **THEN** the report says that nothing was recorded for the period and lists the candidates as having nothing recorded
- **Cases**: keeps the entry `task-reporting: Day without activity` of `tests/not-automated.yaml`

### Requirement: The report is read-only and invents nothing
While reporting, the agent SHALL NOT edit a task file, write any file or commit, nor
state any activity that no subsection of the period, creation date or `done_at`
supports, nor any number `gemba report` did not print. It SHALL report every problem
the listing or the report returned. For what is missing it SHALL point to the
`gemba-record` skill, inside the task's harness for the work of its run or from the
obeya for work outside one, recording nothing itself.

#### Scenario: Nothing written
- **WHEN** a report is produced
- **THEN** the obeya working tree is as it was before
- **Cases**: keeps `tests/cases/report/nothing-written.yaml`

#### Scenario: Problems relayed
- **WHEN** the listing or the report command returns a non-empty `problems` list
- **THEN** the agent tells the user each path and its problem alongside the report
- **Cases**: keeps the entry `task-reporting: Problems relayed` of `tests/not-automated.yaml`

#### Scenario: Gap pointed to recording
- **WHEN** a report lists a task with nothing recorded for the period
- **THEN** the agent says the gap is recorded with the `gemba-record` skill, inside the task's harness for the work of its run or from the obeya for work done outside one, and records nothing itself
- **Cases**: keeps the entry `task-reporting: Gap pointed to recording` of `tests/not-automated.yaml`

### Requirement: Report inputs
`gemba report` SHALL take the selection filters of `gemba list`, with the same names,
values, validation and semantics, and MAY take groupings, `--by`, each `workstream`,
`status` or a declared `text` or `boolean` metadata key, and sums, `--sum`, each a
declared `number` key, both repeatable, a key given twice to either being invalid. It
SHALL validate every input before scanning and, when any is invalid, print nothing,
exit non-zero and report every invalid input in one message.

#### Scenario: Selection as in the listing
- **WHEN** `gemba report --done-from 2026-09-01 --done-to 2026-09-30 --where client=acme` runs over tasks done in August and September for `acme` and for `globex`
- **THEN** the total counts exactly the tasks `gemba list` returns with the same filters, the `acme` tasks done in September
- **Cases**: keeps `tests/cases/report/selection-as-in-the-listing.yaml`

#### Scenario: Invalid inputs reported together
- **WHEN** one call gives `--by hours` on a number field, `--sum client` on a text field, `--by ticket` with no such field declared, and `--status closed`
- **THEN** nothing is printed on standard output, the exit status is non-zero, and one message names the four problems
- **Cases**: keeps `tests/cases/report/invalid-inputs-reported-together.yaml`

### Requirement: Numbers come from the command
Whenever the report states a count, a sum or a total, the agent SHALL run
`gemba report` and state the numbers it printed, never its own, with the count of
tasks without a value when not zero. A number field holds one total per task, so the
agent SHALL select the tasks of a period by completion date,
`--done-from F --done-to T`, unless the user or the workstreams' `report.rules` say
otherwise, and say which selection it used, grouping with `--by` for amounts per
workstream, status or field.

#### Scenario: Amount of a period
- **WHEN** the user asks how many hours went to each client in September 2026, `hours` being a number field and `client` a text field
- **THEN** the agent runs `gemba report --done-from 2026-09-01 --done-to 2026-09-30 --by client --sum hours`, states each total, the tasks without hours, and that the totals are those of the tasks finished in September
- **Cases**: keeps the entry `task-reporting: Amount of a period` of `tests/not-automated.yaml`

#### Scenario: No arithmetic by the agent
- **WHEN** the user asks for the total of two groups the command printed separately
- **THEN** the agent runs `gemba report` again with the selection or grouping that yields that total, instead of adding the two numbers
- **Cases**: keeps the entry `task-reporting: No arithmetic by the agent` of `tests/not-automated.yaml`

## REMOVED Requirements

### Requirement: Report output document
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The
report document" and "A report with no grouping or no task".

### Requirement: Grouping and sums
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "How tasks
are grouped" and "How values are summed".

## ADDED Requirements

### Requirement: The report document
On success the command SHALL print one JSON object with `by` and `sum`, the groupings
and summed keys in the order given; `groups`, one per combination of grouping values
found, each with `key`, a map of each grouping to its value, `tasks`, their number,
`refs`, in listing order, and `sums`, each summed key's `total` and `missing`, the
tasks with no value to add; `total`, with `tasks` and `sums` over every selected task,
counted once; and `problems`, as `gemba list` reports them.

#### Scenario: Sums by group
- **WHEN** `gemba report --by client --sum hours` runs over `SUP-1` (`client: acme`, `hours: 3`), `SUP-2` (`client: acme`, `hours: null`), `SUP-3` (`client: globex`, `hours: 2.5`) and `OPS-1` (`client: null`, `hours: 1`)
- **THEN** the groups are `acme` with 2 tasks, refs `SUP-1` and `SUP-2`, `hours` total 3 and missing 1; `globex` with 1 task, total 2.5 and missing 0; `null` with 1 task, total 1 and missing 0; and the total holds 4 tasks, `hours` total 6.5 and missing 1
- **Cases**: keeps `tests/cases/report/sums-by-group.yaml`

### Requirement: A report with no grouping or no task
Without `--by` there SHALL be one group, with an empty key, holding every selected
task; when no task is selected, `groups` SHALL be empty and every total zero. The exit
status SHALL be zero whenever the inputs and the config are valid, even when problems
were found or no task was selected.

#### Scenario: No grouping
- **WHEN** `gemba report --sum hours` runs over three selected tasks
- **THEN** `groups` holds one entry whose `key` is empty, with the three tasks and their refs, and the same numbers as the total
- **Cases**: keeps `tests/cases/report/no-grouping.yaml`

#### Scenario: Nothing selected
- **WHEN** no task matches the selection
- **THEN** `groups` is empty, the total holds 0 tasks and, per summed key, a total of 0 and 0 missing, and the exit status is zero
- **Cases**: keeps `tests/cases/report/nothing-selected.yaml`

### Requirement: How tasks are grouped
Every selected task SHALL belong to one group per combination of its grouping values:
its own `workstream` and `status`; for a metadata key, `null` for a `null`, missing or
mistyped value, and one group per distinct item of a text list, `null` for an empty
one. Groups SHALL be ordered by key, grouping after grouping as given: workstreams in
config order, statuses as `open`, `in-progress`, `blocked`, `done`, `false` before
`true`, text by code point, `null` last.

#### Scenario: Several groupings
- **WHEN** `gemba report --by workstream --by status` runs over `support` and `operations` tasks with several statuses, `support` declared first in the config
- **THEN** each group's key holds a workstream and a status, the `support` groups come first, and within a workstream the statuses follow `open`, `in-progress`, `blocked`, `done`
- **Cases**: keeps `tests/cases/report/several-groupings.yaml`

#### Scenario: Task in several groups
- **WHEN** `gemba report --by project --sum hours` runs and one task carries `project: [checkout, landing]` and `hours: 2`
- **THEN** the task is counted, with its 2 hours, in the `checkout` group and in the `landing` group, and once in the total
- **Cases**: keeps `tests/cases/report/task-in-several-groups.yaml`

### Requirement: How values are summed
A sum SHALL add the values of its key exactly in decimal, a total with no fractional
part written as an integer; a task whose value is `null`, missing or of another type
SHALL add nothing and SHALL be counted in `missing`.

#### Scenario: Tasks without a value counted
- **WHEN** `gemba report --by client --sum hours` runs over a task with `hours: null`, a task created before `hours` was declared, and a task with `hours: "two"` and `client: 7`
- **THEN** the three add nothing to `hours` and are counted in its `missing`, the task with `client: 7` is grouped under `null`, and `problems` names its two values of another type
- **Cases**: keeps `tests/cases/report/tasks-without-a-value-counted.yaml`

#### Scenario: Sums are exact
- **WHEN** `gemba report --sum hours` runs over tasks with `hours` 0.1 and 0.2, and then over tasks with `hours` 1.5 and 0.5
- **THEN** the totals are 0.3 and 2
- **Cases**: keeps `tests/cases/report/sums-are-exact.yaml`
