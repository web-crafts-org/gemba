# task-listing Specification

## Purpose

Task listing answers what tasks exist, where they are and in what state: a gemba
command scans the workstream folders, validates each file against the task file format,
applies typed filters and prints one machine-readable document for the agent, which
renders it for the user and opens the listed files when more detail is needed.

## Requirements

### Requirement: Listing inputs
Listing SHALL take zero or more filters and validate them all before scanning:
workstreams of the config; statuses of `open`, `in-progress`, `blocked` and `done`; an
exact ref; inclusive ISO date ranges of creation (`from`, `to`), update
(`updated-from`, `updated-to`) and completion (`done-from`, `done-to`); an archived
switch; and metadata equalities and bounds (`where-from`, `where-to`). On any invalid
filter it SHALL print nothing, exit non-zero and report every invalid filter in one
message.

#### Scenario: Unknown workstream filter
- **WHEN** a workstream filter names an identifier that is not in the config
- **THEN** nothing is listed and the message names the unknown identifier and lists the valid identifiers

#### Scenario: Invalid status filter
- **WHEN** a status filter is anything other than `open`, `in-progress`, `blocked` or `done`
- **THEN** nothing is listed and the message names the invalid status and the allowed values

#### Scenario: Invalid date filter
- **WHEN** a date filter is not a valid ISO date
- **THEN** nothing is listed and the message names the invalid value

#### Scenario: Invalid filters reported together
- **WHEN** a workstream filter is unknown and a status filter is invalid in the same call
- **THEN** nothing is listed and one message names both problems

#### Scenario: Invalid config stops the listing
- **WHEN** `gemba.yaml` is missing or invalid
- **THEN** nothing is listed, the exit status is non-zero and the config problem is reported

### Requirement: Scan scope
The command SHALL scan only the folders under `tasks/` of the workstreams of the
config, those of the workstream filter when given: the `.md` files directly under
each, and those directly under its `archive/` only with the archived switch, ignoring
hidden entries and other files. A configured workstream without a folder SHALL
contribute nothing; a non-hidden entry directly under `tasks/` that is not a
configured workstream SHALL be reported as a problem, so that no task disappears
silently.

#### Scenario: Archived tasks excluded by default
- **WHEN** `tasks/support/` holds one task and `tasks/support/archive/` holds another, and the listing is run without the archived switch
- **THEN** only the active task is listed

#### Scenario: Archived tasks included on request
- **WHEN** the archived switch is on
- **THEN** the archived task is listed too, with `archived` set to `true`, and the active task with `archived` set to `false`

#### Scenario: Workstream filter restricts the scan
- **WHEN** the workstream filter names `support` and `tasks/operations/` holds an invalid task file
- **THEN** only `support` tasks are listed and the invalid `operations` file is not reported, because its folder was not scanned

#### Scenario: Configured workstream without a folder
- **WHEN** the config declares `estimates` and `tasks/estimates/` does not exist
- **THEN** the listing succeeds with no `estimates` task and no problem

#### Scenario: Folder that is not a configured workstream
- **WHEN** `tasks/legacy/` exists and `legacy` is not in the config
- **THEN** its files are not listed and a problem names `tasks/legacy` as a folder that is not a workstream of the config

#### Scenario: Non-task entries ignored
- **WHEN** a workstream folder holds `.gitkeep`, a hidden file and a `notes.txt` beside a task file
- **THEN** only the task file is listed and none of the others is reported

### Requirement: The listing document
On success the command SHALL print one JSON object with two keys: `tasks`, the
matching task records ordered by `date`, then `workstream`, then filename, and
`problems`, those found while scanning, each with `path` and `problem`, a sentence
naming what is wrong. The exit status SHALL be zero whenever the filters and the
config are valid, even when problems were found or no task matched.

#### Scenario: Empty result
- **WHEN** no task matches the filters
- **THEN** the output is `{"tasks": [], "problems": []}` and the exit status is zero

#### Scenario: Fixed order
- **WHEN** tasks exist with creation dates 2026-09-10 in `support`, 2026-09-05 in `operations` and 2026-09-10 in `operations`
- **THEN** the records appear in the order 2026-09-05 `operations`, 2026-09-10 `operations`, 2026-09-10 `support`

### Requirement: A task record
A task record SHALL carry exactly `path` (relative to the obeya root, with POSIX
separators), `workstream`, `archived` (a boolean), `ref`, `date` (the creation date of
the filename), `title` (the display title derived from the filename), `status`,
`updated_at`, `done_at` (`null` when absent), `metadata` (the frontmatter map as
written, uninterpreted) and `description` (the first paragraph of the body, or
`null`), dates as ISO strings.

#### Scenario: Complete record
- **WHEN** `tasks/support/2026-09-30-SUP-1-login-fails-on-safari.md` has `status: open`, `ref: SUP-1`, `updated_at: 2026-09-30`, `metadata` with `client: acme` and `project: null`, and the body "Login fails on Safari for the checkout app" above `## Updates`
- **THEN** the output holds one record with `path` `tasks/support/2026-09-30-SUP-1-login-fails-on-safari.md`, `workstream` `support`, `archived` `false`, `ref` `SUP-1`, `date` `2026-09-30`, `title` `Login fails on safari`, `status` `open`, `updated_at` `2026-09-30`, `done_at` `null`, `metadata` `{client: acme, project: null}` and `description` `Login fails on Safari for the checkout app`, and an empty `problems` list

#### Scenario: Done task record
- **WHEN** a task has `status: done` and `done_at: 2026-09-20`
- **THEN** its record carries `status` `done` and `done_at` `2026-09-20`

#### Scenario: Metadata values keep their type
- **WHEN** a task's frontmatter has `hours: 3`, `billed: false` and `project: [checkout, landing]`
- **THEN** the record's `metadata` carries the number `3`, the boolean `false` and the two-item list

### Requirement: Invalid task files are reported and skipped
A `.md` file in a scanned folder that is not a valid task under the task file format
SHALL appear in `problems` with its path and the reason, SHALL NOT appear in `tasks`,
and SHALL NOT stop the listing of the valid files. Problems SHALL be reported for every
scanned folder regardless of the status, ref, date and metadata filters.

#### Scenario: Invalid file does not stop the listing
- **WHEN** a workstream folder holds a valid task and a file whose frontmatter has `status: closed`
- **THEN** the valid task is listed, the invalid file appears in `problems` with a reason naming `closed`, and the exit status is zero

#### Scenario: Problems reported despite filters
- **WHEN** the status filter is `open` and a scanned folder holds a file with no frontmatter
- **THEN** that file appears in `problems` even though it could not have matched the filter

### Requirement: Filter semantics
Values of the same filter SHALL combine as alternatives, a task matching any of them;
different filters SHALL combine as conditions, a task matching all of them. The
creation range SHALL compare the filename date, the update range `updated_at`, and the
completion range `done_at`, which a task without `done_at` never matches; every range
end SHALL be inclusive. The ref filter SHALL match the frontmatter ref exactly.

#### Scenario: Several statuses
- **WHEN** the status filter is given as `open` and as `blocked`
- **THEN** tasks with either status are listed and tasks with `in-progress` or `done` are not

#### Scenario: Several workstreams
- **WHEN** the workstream filter is given as `support` and as `deployments`
- **THEN** tasks of both workstreams are listed and no other

#### Scenario: Filters combine as conditions
- **WHEN** the workstream filter is `support` and the status filter is `open`
- **THEN** only `support` tasks with status `open` are listed

#### Scenario: Task by ref
- **WHEN** the ref filter is `CR-7`
- **THEN** the task whose frontmatter ref is `CR-7` is the only record, whatever its workstream or status

#### Scenario: Creation date range
- **WHEN** the creation range is 2026-09-08 to 2026-09-12 and tasks were created on 2026-09-07, 2026-09-08, 2026-09-12 and 2026-09-13
- **THEN** only the tasks created on 2026-09-08 and 2026-09-12 are listed

#### Scenario: Update date range
- **WHEN** the update range is 2026-09-15 to 2026-09-15 and tasks have `updated_at` 2026-09-14, 2026-09-15 and 2026-09-16
- **THEN** only the task updated on 2026-09-15 is listed

#### Scenario: Completion date range
- **WHEN** the completion range is 2026-09-20 to 2026-09-25 and tasks have `done_at` 2026-09-19 and 2026-09-22 while a third task is still open
- **THEN** only the task completed on 2026-09-22 is listed

#### Scenario: Candidates for a past day
- **WHEN** the creation range ends on 2026-09-15 and the update range starts on 2026-09-15
- **THEN** every task created on or before 2026-09-15 and updated on or after 2026-09-15 is listed, which is the superset of tasks that can hold an update for that day

### Requirement: A metadata condition and its value
A metadata condition SHALL name a key declared in some metadata schema of the config
and be an equality, `key=value`, or an inclusive bound, `key=value` given as
`where-from` or `where-to`. Its value SHALL be converted by the key's declared type,
as creation converts it, `null` standing for no value. A condition whose key no schema
declares, whose value does not convert, that bounds a key of a type other than
`number` or `date`, or that repeats a bound SHALL be refused as an invalid filter.

#### Scenario: Undeclared key refused
- **WHEN** the condition names a key that no metadata schema of the config declares
- **THEN** nothing is listed and the message names the key as undeclared

#### Scenario: Invalid metadata conditions reported together
- **WHEN** one call gives `hours=three` on a number field, `where-from client=a` on a text field, and `where-from hours=1` twice
- **THEN** nothing is listed and one message names the three problems

### Requirement: How an equality matches
An equality SHALL match when the task value equals the converted value or is a list
that holds it, and `key=null` a `null` value, a key of the task's schema missing from
its `metadata` reading as `null`. A task whose workstream's schema does not declare
the key, or whose value does not match the key's type, SHALL never match. Equalities
on the same key SHALL combine as alternatives, and every other combination of
conditions as conditions.

#### Scenario: Scalar equality
- **WHEN** the condition is `client=acme` and tasks carry `client: acme`, `client: globex` and `client: null`
- **THEN** only the task with `client: acme` is listed

#### Scenario: Typed value
- **WHEN** the condition is `hours=3` on a number field and one task carries `hours: 3` as a number while another carries `hours: "3"` as a string
- **THEN** only the task with the number is listed, and the string is reported as a value of another type

#### Scenario: List membership
- **WHEN** the condition is `project=landing` and a task carries `project: [checkout, landing]`
- **THEN** that task is listed

#### Scenario: Unset value
- **WHEN** the condition is `client=null`
- **THEN** tasks whose `client` is `null` are listed and tasks with a value are not

#### Scenario: Missing key reads as null
- **WHEN** `support` declares `invoiced`, a `support` task created before the field existed lacks the key, an `operations` task's workstream does not declare `invoiced`, and the condition is `invoiced=null`
- **THEN** the `support` task is listed and the `operations` task is not

#### Scenario: Key declared in one workstream only
- **WHEN** `merge_url` is declared only by `code-reviews` and the condition is `merge_url=https://example.com/mr/1` without a workstream filter
- **THEN** the matching `code-reviews` task is listed and tasks of other workstreams, which lack the key, are not

#### Scenario: Same key as alternatives
- **WHEN** the conditions are `client=acme` and `client=globex`
- **THEN** tasks with either client are listed

### Requirement: How a bound matches
A bound SHALL match a value of the key's type on its side of it, the bound included,
and never a `null` value. A key SHALL take at most one `where-from` and one
`where-to`.

#### Scenario: Range on a number
- **WHEN** the bounds are `where-from hours=2` and `where-to hours=5` and tasks carry `hours` 1, 2, 5, 6 and `null`
- **THEN** only the tasks with 2 and 5 are listed

#### Scenario: Range on a date
- **WHEN** the bounds are `where-from invoiced=2026-09-01` and `where-to invoiced=2026-09-30` and tasks carry `invoiced` 2026-08-31, 2026-09-01, 2026-09-30, 2026-10-01 and `null`
- **THEN** only the tasks invoiced on 2026-09-01 and 2026-09-30 are listed

### Requirement: The agent lists through the command
The agent SHALL list by running the command, never by reading task files to build the
list, open a listed file only when the user wants detail the record does not carry,
report every problem the command returned, and edit and commit nothing. It SHALL read
the chosen workstreams' `list.context` and follow their `list.rules` when present.

#### Scenario: Detail beyond the record
- **WHEN** the user asks what happened last on a listed task
- **THEN** the agent opens that task's file from the record's `path` and answers from its `## Updates` section

#### Scenario: Problems relayed
- **WHEN** the command returns a non-empty `problems` list
- **THEN** the agent tells the user each path and its problem alongside the listing

### Requirement: The agent turns a request into filters
The agent SHALL turn the user's request into filters: workstreams chosen by their
config descriptions; a conversational "open" or "pending" as every status other than
`done` unless the user names a status; and metadata mentions as conditions on declared
fields, equalities for a value and bounds for a span of numbers or dates, each value
written in the form of its field's declared type.

#### Scenario: Conversational open
- **WHEN** the user asks what they have open
- **THEN** the agent lists tasks with status `open`, `in-progress` and `blocked`, archives excluded

#### Scenario: Span of a field asked in words
- **WHEN** the user asks for the tasks invoiced in September and `invoiced` is a date field
- **THEN** the agent runs `gemba list` with `--where-from invoiced=<first day>` and `--where-to invoiced=<last day>` of that September

### Requirement: Human rendering is guidance
The skill SHALL suggest a readable rendering of the output (grouped by workstream, one
line per task with ref, title, status and last update, description when it helps,
problems and a count at the end) and SHALL state that the rendering adapts to the
question asked. The rendering SHALL NOT be a contract: no command, test or other
process depends on it.

#### Scenario: Rendering adapts to the question
- **WHEN** the user asks only for the refs of blocked tasks
- **THEN** the agent answers with the refs and titles, without the full suggested layout

### Requirement: Skill contains no configured value
The `gemba-list` skill SHALL contain only the process and SHALL NOT name any workstream,
prefix, metadata field or configured rule.

#### Scenario: Config change without skill change
- **WHEN** a workstream or a metadata field is added to `gemba.yaml`
- **THEN** the skill needs no edit for the agent to filter by it

### Requirement: Values of another type are reported
For every scanned task, each metadata value whose key is declared in the config and that
does not match the declared type of the key SHALL appear in `problems`, with the task
path and a sentence naming the key, its type and the value, whatever the filters. The
task itself SHALL still be listed when it matches the filters.

#### Scenario: Value of another type reported
- **WHEN** the status filter is `open`, an `open` task carries `hours: "3"` with `hours` declared as a `number`, and a `done` task carries `billed: "yes"` with `billed` declared as a `boolean`
- **THEN** the `open` task is listed, and `problems` names both paths, each with its key and type
