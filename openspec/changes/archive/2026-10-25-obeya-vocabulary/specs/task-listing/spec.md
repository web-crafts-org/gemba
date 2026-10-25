# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Skill contains no organization-specific value`
- TO: `### Requirement: Skill contains no configured value`

## MODIFIED Requirements

### Requirement: Output document
On success the command SHALL print to standard output a single JSON object with two
keys: `tasks`, the list of matching task records, and `problems`, the list of problems
found while scanning. A task record SHALL carry exactly: `path` (relative to the
obeya root, POSIX separators), `workstream`, `archived` (boolean), `ref`, `date`
(the creation date from the filename), `title` (the display title derived from the
filename), `status`, `updated_at`, `done_at` (`null` when absent), `metadata` (the
frontmatter map as written, values uninterpreted) and `description` (the first
paragraph of the body, `null` when the body has none). Dates SHALL be ISO strings. A
problem SHALL carry `path` and `problem`, a sentence naming what is wrong. Records SHALL
be ordered by `date`, then `workstream`, then filename. The exit status SHALL be zero
whenever the filters and the config are valid, even when problems were found or no task
matched.

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

#### Scenario: Empty result
- **WHEN** no task matches the filters
- **THEN** the output is `{"tasks": [], "problems": []}` and the exit status is zero
- **Cases**: keeps `tests/cases/list/empty-result.yaml`

#### Scenario: Fixed order
- **WHEN** tasks exist with creation dates 2026-09-10 in `support`, 2026-09-05 in `operations` and 2026-09-10 in `operations`
- **THEN** the records appear in the order 2026-09-05 `operations`, 2026-09-10 `operations`, 2026-09-10 `support`
- **Cases**: keeps `tests/cases/list/fixed-order.yaml`

### Requirement: Skill contains no configured value
The `gemba-list` skill SHALL contain only the process and SHALL NOT name any workstream,
prefix, metadata field or configured rule.

#### Scenario: Config change without skill change
- **WHEN** a workstream or a metadata field is added to `gemba.yaml`
- **THEN** the skill needs no edit for the agent to filter by it
- **Cases**: keeps the entry `task-listing: Config change without skill change` of `tests/not-automated.yaml`
