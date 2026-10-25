# task-reporting Specification

## Purpose

Reporting answers what was done on one day across every task, from the task files
alone: the agent lists the tasks alive on that day with the listing command, reads the
day's subsection of each one, and composes the report without inventing anything the
files do not say.

## Requirements

### Requirement: Candidates of a period
For a report of the period from F to T, one day when F equals T, the agent SHALL list
the candidates by running `gemba list --to T --updated-from F`, the tasks created on or
before T and updated on or after F, which are the tasks alive in the period, adding
`--include-archived` only when the user asks for archived tasks and no other filter.
The agent SHALL build one candidate list per period when several periods are
requested.

#### Scenario: Candidates listed by the command
- **WHEN** the user asks for the report of 2026-10-01
- **THEN** the agent runs `gemba list --to 2026-10-01 --updated-from 2026-10-01` and reads only the tasks it returns

#### Scenario: Candidates of a month
- **WHEN** the user asks for the report of September 2026
- **THEN** the agent runs `gemba list --to 2026-09-30 --updated-from 2026-09-01` and reads only the tasks it returns

#### Scenario: Task created after the date is not a candidate
- **WHEN** a task was created on 2026-10-02 and the report date is 2026-10-01
- **THEN** the listing leaves it out and the report does not mention it

### Requirement: Signals read from each candidate
For each candidate the agent SHALL open the file at the record's `path` and take as the
work of the period the bullets of every `### D` subsection under `## Updates` whose date
D lies in the period, SHALL take a record's `date` in the period as the task having been
created then, and a `done_at` in the period as the task having been finished then. A
candidate with none of the three SHALL be treated as having nothing recorded for the
period.

#### Scenario: Subsection read from the file
- **WHEN** a candidate's body holds `### 2026-10-01` with three bullets and the report is of 2026-10-01
- **THEN** the report shows that task with those three bullets condensed, under its workstream

#### Scenario: Subsections of a period
- **WHEN** the report is of 2026-09-28 to 2026-10-04 and a candidate holds `### 2026-09-25`, `### 2026-09-29` and `### 2026-10-02`
- **THEN** the report takes the bullets of 2026-09-29 and 2026-10-02 only

#### Scenario: Created or finished on the date
- **WHEN** a candidate's `date` lies in the period and its body has no subsection in it, or its `done_at` lies in the period
- **THEN** the report shows it as created, or as finished, in the period, without inventing bullets

### Requirement: Composition of the report
The agent SHALL compose the report in the language the user converses in, grouped by
workstream unless the user asks for another grouping, with one entry per task that has
a signal for the period: its title, ref and current status, then the bullets of the
period, condensed rather than transcribed. The candidates with nothing recorded for the
period SHALL be listed at the end, under a heading saying they were updated recently
with nothing recorded for that period, so the user can record what is missing. When no
candidate has a signal for the period, the report SHALL say so plainly. Several periods
SHALL give one report per period, oldest first. The layout is guidance: it adapts to
the question asked and no process depends on it.

#### Scenario: Report grouped by workstream
- **WHEN** two `support` tasks and one `development` task have a subsection in the period
- **THEN** the report has a `support` group with two entries and a `development` group with one, each entry with title, ref, status and bullets

#### Scenario: Gaps listed, not filled
- **WHEN** a candidate has no subsection in the period, was not created in it and was not finished in it
- **THEN** it appears only in the final list of tasks with nothing recorded for the period, with no bullets

#### Scenario: Day without activity
- **WHEN** no candidate has a signal for the period
- **THEN** the report says that nothing was recorded for the period and lists the candidates as having nothing recorded

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

#### Scenario: Problems relayed
- **WHEN** the listing or the report command returns a non-empty `problems` list
- **THEN** the agent tells the user each path and its problem alongside the report

#### Scenario: Gap pointed to recording
- **WHEN** a report lists a task with nothing recorded for the period
- **THEN** the agent says the gap is recorded with the `gemba-record` skill, inside the task's harness for the work of its run or from the tasks repo for work done outside one, and records nothing itself

### Requirement: Workstream customization of the report
The agent SHALL read the `report.context` of each workstream that has tasks in the
report and follow its `report.rules` when composing the entries of that workstream.

#### Scenario: Report rules applied
- **WHEN** workstream `support` declares `report.rules` containing "name the client before the title"
- **THEN** every `support` entry of the report names the client first

### Requirement: Skill contains no organization-specific value
The `gemba-report` skill SHALL contain only the process and SHALL NOT name any
workstream, prefix, metadata field or organization-specific rule.

#### Scenario: Config change without skill change
- **WHEN** a workstream or a metadata field is added to `gemba.yaml`
- **THEN** the skill needs no edit for the report to cover it

### Requirement: The report process owns gemba report
The report process SHALL be the `gemba-report` skill, scoped to the tasks repo, and the
`gemba report` subcommand. A report SHALL be the summary of a period of work, one day
or several consecutive days, across every task. The command SHALL compute every count
and sum over a selection of tasks and print it for the agent; the skill SHALL read the
task files for the work of the period and compose the report.

#### Scenario: Report subcommand exists
- **WHEN** `gemba report --help` runs
- **THEN** it exits 0 and names the selection filters, `--by` and `--sum`

### Requirement: Report inputs
`gemba report` SHALL take the selection filters of `gemba list`, with the same names,
values, validation and semantics, and MAY take groupings, `--by` (repeatable, each
`workstream`, `status` or a declared metadata key of type `text` or `boolean`), and
sums, `--sum` (repeatable, each a declared metadata key of type `number`). It SHALL
validate every filter, grouping and sum before scanning and, when any is invalid, SHALL
print nothing on standard output, exit with a non-zero status, and report every invalid
input in a single message. A key given twice to `--by`, or twice to `--sum`, is
invalid.

#### Scenario: Selection as in the listing
- **WHEN** `gemba report --done-from 2026-09-01 --done-to 2026-09-30 --where client=acme` runs over tasks done in August and September for `acme` and for `globex`
- **THEN** the total counts exactly the tasks `gemba list` returns with the same filters, the `acme` tasks done in September

#### Scenario: Invalid inputs reported together
- **WHEN** one call gives `--by hours` on a number field, `--sum client` on a text field, `--by ticket` with no such field declared, and `--status closed`
- **THEN** nothing is printed on standard output, the exit status is non-zero, and one message names the four problems

### Requirement: Report output document
On success the command SHALL print one JSON object with: `by`, the groupings in the
order given; `sum`, the summed keys in the order given; `groups`, one entry per
combination of grouping values found among the selected tasks, each with `key`, a map
from each grouping to its value, `tasks`, the number of selected tasks in the group,
`refs`, their refs in the order of the listing, and `sums`, a map from each summed key
to its `total` and to `missing`, the number of tasks of the group without a value to
add; `total`, with `tasks` and `sums` over every selected task, each task counted once;
and `problems`, the problems of the scan and the values of another type, as `gemba
list` reports them. Without `--by` there SHALL be one group, with an empty key, holding
every selected task; when no task is selected, `groups` SHALL be empty and every total
zero. The exit status SHALL be zero whenever the inputs and the config are valid, even
when problems were found or no task was selected.

#### Scenario: Sums by group
- **WHEN** `gemba report --by client --sum hours` runs over `SUP-1` (`client: acme`, `hours: 3`), `SUP-2` (`client: acme`, `hours: null`), `SUP-3` (`client: globex`, `hours: 2.5`) and `OPS-1` (`client: null`, `hours: 1`)
- **THEN** the groups are `acme` with 2 tasks, refs `SUP-1` and `SUP-2`, `hours` total 3 and missing 1; `globex` with 1 task, total 2.5 and missing 0; `null` with 1 task, total 1 and missing 0; and the total holds 4 tasks, `hours` total 6.5 and missing 1

#### Scenario: No grouping
- **WHEN** `gemba report --sum hours` runs over three selected tasks
- **THEN** `groups` holds one entry whose `key` is empty, with the three tasks and their refs, and the same numbers as the total

#### Scenario: Nothing selected
- **WHEN** no task matches the selection
- **THEN** `groups` is empty, the total holds 0 tasks and, per summed key, a total of 0 and 0 missing, and the exit status is zero

### Requirement: Grouping and sums
Every selected task SHALL belong to one group per combination of its grouping values.
The value of `workstream` and of `status` SHALL be the task's own. A metadata value of
`null`, a missing key and a value of another type than the key's declared type SHALL
group under `null`; a text list SHALL place the task in one group per distinct item,
and an empty list under `null`. Groups SHALL be ordered by their key, grouping after
grouping in the order given: workstreams in the order of the config, statuses as
`open`, `in-progress`, `blocked`, `done`, `false` before `true`, text by code point,
and `null` last. A sum SHALL add the values of its key exactly in decimal, writing a
total with no fractional part as an integer; a task whose value is `null`, missing or
of another type SHALL add nothing and SHALL be counted in `missing`.

#### Scenario: Several groupings
- **WHEN** `gemba report --by workstream --by status` runs over `support` and `operations` tasks with several statuses, `support` declared first in the config
- **THEN** each group's key holds a workstream and a status, the `support` groups come first, and within a workstream the statuses follow `open`, `in-progress`, `blocked`, `done`

#### Scenario: Task in several groups
- **WHEN** `gemba report --by project --sum hours` runs and one task carries `project: [checkout, landing]` and `hours: 2`
- **THEN** the task is counted, with its 2 hours, in the `checkout` group and in the `landing` group, and once in the total

#### Scenario: Tasks without a value counted
- **WHEN** `gemba report --by client --sum hours` runs over a task with `hours: null`, a task created before `hours` was declared, and a task with `hours: "two"` and `client: 7`
- **THEN** the three add nothing to `hours` and are counted in its `missing`, the task with `client: 7` is grouped under `null`, and `problems` names its two values of another type

#### Scenario: Sums are exact
- **WHEN** `gemba report --sum hours` runs over tasks with `hours` 0.1 and 0.2, and then over tasks with `hours` 1.5 and 0.5
- **THEN** the totals are 0.3 and 2

### Requirement: Numbers come from the command
Whenever the report states a count, a sum or a total, the agent SHALL run `gemba
report` and state the numbers it printed, never numbers it computed itself, together
with the count of tasks without a value when it is not zero. A number field holds one
total per task, so the agent SHALL select the tasks whose totals belong to the period
by their completion date, `--done-from F --done-to T`, unless the user asks for another
selection or the `report.rules` of the workstreams involved say otherwise, and SHALL
say which selection it used. It SHALL group with `--by` when the user asks for amounts
per workstream, per status or per field.

#### Scenario: Amount of a period
- **WHEN** the user asks how many hours went to each client in September 2026, `hours` being a number field and `client` a text field
- **THEN** the agent runs `gemba report --done-from 2026-09-01 --done-to 2026-09-30 --by client --sum hours`, states each total, the tasks without hours, and that the totals are those of the tasks finished in September

#### Scenario: No arithmetic by the agent
- **WHEN** the user asks for the total of two groups the command printed separately
- **THEN** the agent runs `gemba report` again with the selection or grouping that yields that total, instead of adding the two numbers
