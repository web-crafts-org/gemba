# Spec Delta

## ADDED Requirements

### Requirement: Scan scope of a team
When the shared config declares a team, the command SHALL scan
`tasks/<member>/<workstream>/` and its `archive/` by the rules of the scan scope, for
every member, active or not, or for those of the owner filter. When neither a
workstream nor an owner filter is given, a non-hidden entry directly under `tasks/`
that is not a member, or directly under a member's folder that is not a configured
workstream, SHALL be reported as a problem.

#### Scenario: Tasks of every member listed
- **WHEN** the team declares `manuel` and `ana`, `tasks/manuel/support/` holds `MR-SUP-1` created on 2026-10-20, `tasks/ana/operations/` holds `AG-OPS-1` created on 2026-10-21, and `tasks/ana/support/archive/` holds `AG-SUP-1`
- **THEN** `gemba list` lists `MR-SUP-1` then `AG-OPS-1`, and with the archived switch `AG-SUP-1` too, with `archived` `true`
- **Cases**: adds `tests/cases/list/tasks-of-every-member-listed.yaml`

#### Scenario: Folder that is not a member
- **WHEN** `tasks/bob/support/` holds a task file and `bob` is not a member of the team
- **THEN** its files are not listed and a problem names `tasks/bob` as a folder that is not a member of the team
- **Cases**: adds `tests/cases/list/folder-that-is-not-a-member.yaml`

#### Scenario: Folder of a member that is not a workstream
- **WHEN** `tasks/ana/legacy/` exists and `legacy` is not in the config
- **THEN** its files are not listed and a problem names `tasks/ana/legacy` as a folder that is not a workstream of the config
- **Cases**: adds `tests/cases/list/folder-of-a-member-that-is-not-a-workstream.yaml`

### Requirement: The owner filter
When the shared config declares a team, listing SHALL take an owner filter,
repeatable, each value a member of the team, whose values are alternatives and restrict
the scan to the folders of those members, as the workstream filter does. Without a
team, or for a value that is not a member, the filter SHALL be refused together with
every other invalid filter.

#### Scenario: Tasks of one member
- **WHEN** the owner filter is `manuel`, both `manuel` and `ana` have tasks, and `tasks/ana/support/` holds an invalid task file
- **THEN** only the tasks of `manuel` are listed and the invalid file of `ana` is not reported, because her folder was not scanned
- **Cases**: adds `tests/cases/list/tasks-of-one-member.yaml`

#### Scenario: Owner filter without a team refused
- **WHEN** the owner filter is given in an obeya whose shared config declares no team
- **THEN** nothing is listed, the exit status is non-zero, and the message says that the obeya declares no team
- **Cases**: adds `tests/cases/list/owner-filter-without-a-team-refused.yaml`

#### Scenario: Unknown owner refused
- **WHEN** the owner filter is `bob`, the team declares `manuel` and `ana`, and a status filter is `closed`
- **THEN** nothing is listed and one message names `bob`, lists `manuel` and `ana`, and names the invalid status
- **Cases**: adds `tests/cases/list/unknown-owner-refused.yaml`

### Requirement: The agent lists the user's tasks in a team
In an obeya with a team, the agent SHALL read a request about the user's own tasks,
such as "what do I have open", as the owner filter with `me`, read from `gemba config
show`; a request that names a member as that member's folder name; and a request about
the whole team as no owner filter.

#### Scenario: My open tasks in a team
- **WHEN** `me` is `manuel` and the user asks what they have open
- **THEN** the agent runs `gemba list --owner manuel` with the statuses `open`, `in-progress` and `blocked`
- **Cases**: adds the entry `task-listing: My open tasks in a team` of `tests/not-automated.yaml`

#### Scenario: Open tasks of the team
- **WHEN** the user asks what the team has open
- **THEN** the agent runs `gemba list` without an owner filter and shows each task with its owner
- **Cases**: adds the entry `task-listing: Open tasks of the team` of `tests/not-automated.yaml`

## MODIFIED Requirements

### Requirement: Scan scope
In an obeya without a team, the command SHALL scan only the folders under `tasks/` of
the workstreams of the config, those of the workstream filter when given: the `.md`
files directly under each, and those directly under its `archive/` only with the
archived switch, ignoring hidden entries and other files. A configured workstream
without a folder SHALL contribute nothing; a non-hidden entry directly under `tasks/`
that is not a configured workstream SHALL be reported as a problem.

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

### Requirement: A task record
A task record SHALL carry exactly `path` (relative to the obeya root, with POSIX
separators), `owner` (its owner's folder) only in an obeya with a team,
`workstream`, `archived` (a boolean), `ref`, `date` (the creation date of the
filename), `title` (the display title derived from the filename), `status`,
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

#### Scenario: Record of a member's task
- **WHEN** the shared config declares a team and `tasks/ana/support/2026-10-20-AG-SUP-1-export-times-out.md` is a valid task
- **THEN** its record carries `owner` `ana` right after `path`, followed by every other key of the record
- **Cases**: adds `tests/cases/list/record-of-a-members-task.yaml`
