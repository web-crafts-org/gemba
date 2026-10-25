# Spec Delta

## MODIFIED Requirements

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
- **Cases**: keeps `tests/cases/list/unknown-workstream-filter.yaml`

#### Scenario: Invalid status filter
- **WHEN** a status filter is anything other than `open`, `in-progress`, `blocked` or `done`
- **THEN** nothing is listed and the message names the invalid status and the allowed values
- **Cases**: keeps `tests/cases/list/invalid-status-filter.yaml`

#### Scenario: Invalid date filter
- **WHEN** a date filter is not a valid ISO date
- **THEN** nothing is listed and the message names the invalid value
- **Cases**: keeps `tests/cases/list/invalid-date-filter.yaml`

#### Scenario: Invalid filters reported together
- **WHEN** a workstream filter is unknown and a status filter is invalid in the same call
- **THEN** nothing is listed and one message names both problems
- **Cases**: keeps `tests/cases/list/invalid-filters-reported-together.yaml`

#### Scenario: Invalid config stops the listing
- **WHEN** `gemba.yaml` is missing or invalid
- **THEN** nothing is listed, the exit status is non-zero and the config problem is reported
- **Cases**: keeps `tests/cases/list/invalid-config-stops-the-listing.yaml`

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
- **Cases**: keeps `tests/cases/list/archived-tasks-excluded-by-default.yaml`

#### Scenario: Archived tasks included on request
- **WHEN** the archived switch is on
- **THEN** the archived task is listed too, with `archived` set to `true`, and the active task with `archived` set to `false`
- **Cases**: keeps `tests/cases/list/archived-tasks-included-on-request.yaml`

#### Scenario: Workstream filter restricts the scan
- **WHEN** the workstream filter names `support` and `tasks/operations/` holds an invalid task file
- **THEN** only `support` tasks are listed and the invalid `operations` file is not reported, because its folder was not scanned
- **Cases**: keeps `tests/cases/list/workstream-filter-restricts-the-scan.yaml`

#### Scenario: Configured workstream without a folder
- **WHEN** the config declares `estimates` and `tasks/estimates/` does not exist
- **THEN** the listing succeeds with no `estimates` task and no problem
- **Cases**: keeps `tests/cases/list/configured-workstream-without-a-folder.yaml`

#### Scenario: Folder that is not a configured workstream
- **WHEN** `tasks/legacy/` exists and `legacy` is not in the config
- **THEN** its files are not listed and a problem names `tasks/legacy` as a folder that is not a workstream of the config
- **Cases**: keeps `tests/cases/list/folder-that-is-not-a-configured-workstream.yaml`

#### Scenario: Non-task entries ignored
- **WHEN** a workstream folder holds `.gitkeep`, a hidden file and a `notes.txt` beside a task file
- **THEN** only the task file is listed and none of the others is reported
- **Cases**: keeps `tests/cases/list/non-task-entries-ignored.yaml`

### Requirement: Filter semantics
Values of the same filter SHALL combine as alternatives, a task matching any of them;
different filters SHALL combine as conditions, a task matching all of them. The
creation range SHALL compare the filename date, the update range `updated_at`, and the
completion range `done_at`, which a task without `done_at` never matches; every range
end SHALL be inclusive. The ref filter SHALL match the frontmatter ref exactly.

#### Scenario: Several statuses
- **WHEN** the status filter is given as `open` and as `blocked`
- **THEN** tasks with either status are listed and tasks with `in-progress` or `done` are not
- **Cases**: keeps `tests/cases/list/several-statuses.yaml`

#### Scenario: Several workstreams
- **WHEN** the workstream filter is given as `support` and as `deployments`
- **THEN** tasks of both workstreams are listed and no other
- **Cases**: keeps `tests/cases/list/several-workstreams.yaml`

#### Scenario: Filters combine as conditions
- **WHEN** the workstream filter is `support` and the status filter is `open`
- **THEN** only `support` tasks with status `open` are listed
- **Cases**: keeps `tests/cases/list/filters-combine-as-conditions.yaml`

#### Scenario: Task by ref
- **WHEN** the ref filter is `CR-7`
- **THEN** the task whose frontmatter ref is `CR-7` is the only record, whatever its workstream or status
- **Cases**: keeps `tests/cases/list/task-by-ref.yaml`

#### Scenario: Creation date range
- **WHEN** the creation range is 2026-09-08 to 2026-09-12 and tasks were created on 2026-09-07, 2026-09-08, 2026-09-12 and 2026-09-13
- **THEN** only the tasks created on 2026-09-08 and 2026-09-12 are listed
- **Cases**: keeps `tests/cases/list/creation-date-range.yaml`

#### Scenario: Update date range
- **WHEN** the update range is 2026-09-15 to 2026-09-15 and tasks have `updated_at` 2026-09-14, 2026-09-15 and 2026-09-16
- **THEN** only the task updated on 2026-09-15 is listed
- **Cases**: keeps `tests/cases/list/update-date-range.yaml`

#### Scenario: Completion date range
- **WHEN** the completion range is 2026-09-20 to 2026-09-25 and tasks have `done_at` 2026-09-19 and 2026-09-22 while a third task is still open
- **THEN** only the task completed on 2026-09-22 is listed
- **Cases**: keeps `tests/cases/list/completion-date-range.yaml`

#### Scenario: Candidates for a past day
- **WHEN** the creation range ends on 2026-09-15 and the update range starts on 2026-09-15
- **THEN** every task created on or before 2026-09-15 and updated on or after 2026-09-15 is listed, which is the superset of tasks that can hold an update for that day
- **Cases**: keeps `tests/cases/list/candidates-for-a-past-day.yaml`

## REMOVED Requirements

### Requirement: Output document
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The
listing document" and "A task record".

### Requirement: Metadata conditions
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "A
metadata condition and its value", "How an equality matches" and "How a bound
matches".

### Requirement: Listing by the agent
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The agent
lists through the command" and "The agent turns a request into filters".

## ADDED Requirements

### Requirement: The listing document
On success the command SHALL print one JSON object with two keys: `tasks`, the
matching task records ordered by `date`, then `workstream`, then filename, and
`problems`, those found while scanning, each with `path` and `problem`, a sentence
naming what is wrong. The exit status SHALL be zero whenever the filters and the
config are valid, even when problems were found or no task matched.

#### Scenario: Empty result
- **WHEN** no task matches the filters
- **THEN** the output is `{"tasks": [], "problems": []}` and the exit status is zero
- **Cases**: keeps `tests/cases/list/empty-result.yaml`

#### Scenario: Fixed order
- **WHEN** tasks exist with creation dates 2026-09-10 in `support`, 2026-09-05 in `operations` and 2026-09-10 in `operations`
- **THEN** the records appear in the order 2026-09-05 `operations`, 2026-09-10 `operations`, 2026-09-10 `support`
- **Cases**: keeps `tests/cases/list/fixed-order.yaml`

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
- **Cases**: keeps `tests/cases/list/complete-record.yaml`

#### Scenario: Done task record
- **WHEN** a task has `status: done` and `done_at: 2026-09-20`
- **THEN** its record carries `status` `done` and `done_at` `2026-09-20`
- **Cases**: keeps `tests/cases/list/done-task-record.yaml`

#### Scenario: Metadata values keep their type
- **WHEN** a task's frontmatter has `hours: 3`, `billed: false` and `project: [checkout, landing]`
- **THEN** the record's `metadata` carries the number `3`, the boolean `false` and the two-item list
- **Cases**: keeps `tests/cases/list/metadata-values-keep-their-type.yaml`

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
- **Cases**: keeps `tests/cases/list/undeclared-key-refused.yaml`

#### Scenario: Invalid metadata conditions reported together
- **WHEN** one call gives `hours=three` on a number field, `where-from client=a` on a text field, and `where-from hours=1` twice
- **THEN** nothing is listed and one message names the three problems
- **Cases**: keeps `tests/cases/list/invalid-metadata-conditions-refused.yaml`

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
- **Cases**: keeps `tests/cases/list/scalar-equality.yaml`

#### Scenario: Typed value
- **WHEN** the condition is `hours=3` on a number field and one task carries `hours: 3` as a number while another carries `hours: "3"` as a string
- **THEN** only the task with the number is listed, and the string is reported as a value of another type
- **Cases**: keeps `tests/cases/list/typed-value.yaml`

#### Scenario: List membership
- **WHEN** the condition is `project=landing` and a task carries `project: [checkout, landing]`
- **THEN** that task is listed
- **Cases**: keeps `tests/cases/list/list-membership.yaml`

#### Scenario: Unset value
- **WHEN** the condition is `client=null`
- **THEN** tasks whose `client` is `null` are listed and tasks with a value are not
- **Cases**: keeps `tests/cases/list/unset-value.yaml`

#### Scenario: Missing key reads as null
- **WHEN** `support` declares `invoiced`, a `support` task created before the field existed lacks the key, an `operations` task's workstream does not declare `invoiced`, and the condition is `invoiced=null`
- **THEN** the `support` task is listed and the `operations` task is not
- **Cases**: keeps `tests/cases/list/missing-key-reads-as-null.yaml`

#### Scenario: Key declared in one workstream only
- **WHEN** `merge_url` is declared only by `code-reviews` and the condition is `merge_url=https://example.com/mr/1` without a workstream filter
- **THEN** the matching `code-reviews` task is listed and tasks of other workstreams, which lack the key, are not
- **Cases**: keeps `tests/cases/list/key-declared-in-one-workstream-only.yaml`

#### Scenario: Same key as alternatives
- **WHEN** the conditions are `client=acme` and `client=globex`
- **THEN** tasks with either client are listed
- **Cases**: keeps `tests/cases/list/same-key-as-alternatives.yaml`

### Requirement: How a bound matches
A bound SHALL match a value of the key's type on its side of it, the bound included,
and never a `null` value. A key SHALL take at most one `where-from` and one
`where-to`.

#### Scenario: Range on a number
- **WHEN** the bounds are `where-from hours=2` and `where-to hours=5` and tasks carry `hours` 1, 2, 5, 6 and `null`
- **THEN** only the tasks with 2 and 5 are listed
- **Cases**: keeps `tests/cases/list/range-on-a-number.yaml`

#### Scenario: Range on a date
- **WHEN** the bounds are `where-from invoiced=2026-09-01` and `where-to invoiced=2026-09-30` and tasks carry `invoiced` 2026-08-31, 2026-09-01, 2026-09-30, 2026-10-01 and `null`
- **THEN** only the tasks invoiced on 2026-09-01 and 2026-09-30 are listed
- **Cases**: keeps `tests/cases/list/range-on-a-date.yaml`

### Requirement: The agent lists through the command
The agent SHALL list by running the command, never by reading task files to build the
list, open a listed file only when the user wants detail the record does not carry,
report every problem the command returned, and edit and commit nothing. It SHALL read
the chosen workstreams' `list.context` and follow their `list.rules` when present.

#### Scenario: Detail beyond the record
- **WHEN** the user asks what happened last on a listed task
- **THEN** the agent opens that task's file from the record's `path` and answers from its `## Updates` section
- **Cases**: keeps the entry `task-listing: Detail beyond the record` of `tests/not-automated.yaml`

#### Scenario: Problems relayed
- **WHEN** the command returns a non-empty `problems` list
- **THEN** the agent tells the user each path and its problem alongside the listing
- **Cases**: keeps the entry `task-listing: Problems relayed` of `tests/not-automated.yaml`

### Requirement: The agent turns a request into filters
The agent SHALL turn the user's request into filters: workstreams chosen by their
config descriptions; a conversational "open" or "pending" as every status other than
`done` unless the user names a status; and metadata mentions as conditions on declared
fields, equalities for a value and bounds for a span of numbers or dates, each value
written in the form of its field's declared type.

#### Scenario: Conversational open
- **WHEN** the user asks what they have open
- **THEN** the agent lists tasks with status `open`, `in-progress` and `blocked`, archives excluded
- **Cases**: keeps the entry `task-listing: Conversational open` of `tests/not-automated.yaml`

#### Scenario: Span of a field asked in words
- **WHEN** the user asks for the tasks invoiced in September and `invoiced` is a date field
- **THEN** the agent runs `gemba list` with `--where-from invoiced=<first day>` and `--where-to invoiced=<last day>` of that September
- **Cases**: keeps the entry `task-listing: Span of a field asked in words` of `tests/not-automated.yaml`
