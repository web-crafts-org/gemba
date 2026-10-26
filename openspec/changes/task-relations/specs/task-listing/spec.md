# Spec Delta

## ADDED Requirements

### Requirement: The parent filter
Listing SHALL take a parent filter, one ref, matching the tasks whose `parent` is that
ref: its direct children. The ref SHALL name a task of the obeya, archives and every
member's folder included; otherwise the filter SHALL be refused with every other
invalid filter, saying that the ref is not a task of this clone, to be pulled first
when it was created in another clone.

#### Scenario: Direct children
- **WHEN** `SUP-2` and `OPS-1` name `SUP-1` as parent, `SUP-3` names `SUP-2`, and `SUP-4` names none
- **THEN** `gemba list --parent SUP-1` lists `SUP-2` and `OPS-1`, and no other task
- **Cases**: adds `tests/cases/list/direct-children.yaml`

#### Scenario: Unknown parent refused
- **WHEN** `gemba list --parent SUP-9 --status closed` runs and no task has the ref `SUP-9`
- **THEN** nothing is listed, the exit status is non-zero, and one message says that `SUP-9` is not a task of this clone, suggests a pull, and names the invalid status
- **Cases**: adds `tests/cases/list/unknown-parent-refused.yaml`

### Requirement: The subtree filter
Listing SHALL take a subtree filter, one ref, matching the tasks of the subtree of that
task, the task itself included. Its ref SHALL be refused as the parent filter's is. The
subtree SHALL be found whatever the other filters, which, the scan scope and the
archived switch included, still decide which of its tasks are listed.

#### Scenario: Subtree within a workstream filter
- **WHEN** `SUP-1` has the child `OPS-1`, which has the child `SUP-2`, and `gemba list --under SUP-1 --workstream support` runs
- **THEN** `SUP-1` and `SUP-2` are listed, and `OPS-1`, which links them, is not
- **Cases**: adds `tests/cases/list/subtree-within-a-workstream-filter.yaml`

#### Scenario: Unknown subtree root refused
- **WHEN** `gemba list --under SUP-9` runs and no task has the ref `SUP-9`
- **THEN** nothing is listed, the exit status is non-zero, and the message says that `SUP-9` is not a task of this clone and suggests a pull
- **Cases**: adds `tests/cases/list/unknown-subtree-root-refused.yaml`

### Requirement: The agent reads a request about subtasks
The agent SHALL read a request about the subtasks of a task as the parent filter, and
one about a task with everything split from it as the subtree filter, adding the
archived switch unless the user asks only for live work, and SHALL show the parent of
each task when the listing holds tasks of several parents.

#### Scenario: Subtasks asked
- **WHEN** the user asks what the subtasks of `SUP-1` are
- **THEN** the agent runs `gemba list --parent SUP-1 --include-archived`
- **Cases**: adds the entry `task-listing: Subtasks asked` of `tests/not-automated.yaml`

#### Scenario: Open work under a task asked
- **WHEN** the user asks what is still open under `SUP-1`
- **THEN** the agent runs `gemba list --under SUP-1` with the statuses `open`, `in-progress` and `blocked`
- **Cases**: adds the entry `task-listing: Open work under a task asked` of `tests/not-automated.yaml`

## MODIFIED Requirements

### Requirement: A task record
A task record SHALL carry exactly `path` (relative to the obeya root, with POSIX
separators), `owner` (its owner's folder) only in an obeya with a team,
`workstream`, `archived` (a boolean), `ref`, `parent` only for a task with a parent,
`date` (the filename's date), `title` (its display title), `status`, `updated_at`,
`done_at` (`null` when absent), `metadata` (the frontmatter map as written,
uninterpreted) and `description` (the first paragraph of the body, or `null`), dates as
ISO strings.

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

#### Scenario: Record of a member's task
- **WHEN** the shared config declares a team and `tasks/ana/support/2026-10-20-AG-SUP-1-export-times-out.md` is a valid task
- **THEN** its record carries `owner` `ana` right after `path`, followed by every other key of the record
- **Cases**: keeps `tests/cases/list/record-of-a-members-task.yaml`

#### Scenario: Record of a child task
- **WHEN** `tasks/support/2026-10-02-SUP-2-safari-css.md` holds `parent: SUP-1`, and `SUP-1` names no parent
- **THEN** the record of `SUP-2` carries `parent` `SUP-1` right after `ref`, and the record of `SUP-1` carries no `parent` key
- **Cases**: adds `tests/cases/list/record-of-a-child-task.yaml`
