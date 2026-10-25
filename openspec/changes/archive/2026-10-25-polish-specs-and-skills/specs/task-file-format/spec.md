# Spec Delta

## MODIFIED Requirements

### Requirement: Task ref
Every task SHALL carry a ref `<PREFIX>-<N>`, `<PREFIX>` being the prefix of the
workstream it was created in and `<N>` a positive integer without leading zeros. The
ref SHALL be unique across the obeya, allocated by Gemba, never chosen by the user or
the agent, and internal: an external identifier, such as a ticket key or a merge
request number, belongs in metadata or as a link in the body. The ref in the
frontmatter SHALL equal the ref in the filename.

#### Scenario: Consecutive refs within a workstream
- **WHEN** the highest existing ref with prefix `CR` anywhere under `tasks/` (including archive folders) is `CR-12`
- **THEN** the next task created in the workstream with prefix `CR` receives `CR-13`
- **Cases**: keeps `tests/cases/create/consecutive-refs-within-workstream.yaml`

#### Scenario: First task of a prefix
- **WHEN** no task with prefix `EST` exists anywhere under `tasks/`
- **THEN** the first task created in the workstream with prefix `EST` receives `EST-1`
- **Cases**: keeps `tests/cases/create/first-task-of-a-prefix.yaml`

#### Scenario: Moved task keeps its ref
- **WHEN** a task with ref `CR-7` is moved into another workstream folder or into an archive folder
- **THEN** it keeps `CR-7`, and `CR-7` is never allocated again because allocation scans every task folder
- **Cases**: keeps `tests/cases/create/moved-task-keeps-its-ref.yaml`

#### Scenario: External key offered as ref
- **WHEN** the user asks for a task to be identified by a ticket key such as `PROD-16283`
- **THEN** Gemba still allocates an internal ref and records the ticket key in metadata or in the body, never as the ref
- **Cases**: keeps `tests/cases/create/external-key-offered-as-ref.yaml`

### Requirement: Built-in frontmatter fields
The frontmatter SHALL be a YAML block between `---` lines at the start of the file
holding exactly, in this order, `status`, `ref`, `updated_at`, `done_at` (only when
the status is `done`) and `metadata`. `status` SHALL be `open`, `in-progress`,
`blocked` or `done`. `updated_at` SHALL be an ISO date, the creation date at creation,
that only moves forward. `done_at` SHALL be the ISO date the task reached `done`,
removed when it leaves `done`, so it means "done since" and never "was once done".

#### Scenario: Frontmatter of a new task
- **WHEN** a task is created on 2026-09-30 in a workstream whose effective metadata schema declares `client` and `project`, with `client` supplied as `acme`
- **THEN** its frontmatter is exactly
  ```yaml
  ---
  status: open
  ref: SUP-1
  updated_at: 2026-09-30
  metadata:
    client: acme
    project: null
  ---
  ```
- **Cases**: keeps `tests/cases/create/frontmatter-of-a-new-task.yaml`

#### Scenario: Invalid status value
- **WHEN** a frontmatter `status` is anything other than `open`, `in-progress`, `blocked` or `done`
- **THEN** the file is not a valid task and processes report it instead of guessing
- **Cases**: keeps `tests/cases/create/invalid-status-value.yaml` and `tests/cases/list/invalid-status-value.yaml`

#### Scenario: Done at follows the status
- **WHEN** a task marked `done` on 2026-10-01 is marked `blocked` on 2026-10-02
- **THEN** its frontmatter reads `status: blocked`, `updated_at: 2026-10-02` and holds no `done_at` key, with every other key as it was
- **Cases**: keeps `tests/cases/mark/done-at-follows-the-status.yaml`

### Requirement: Metadata contract
`metadata` SHALL always be a flat map with snake_case keys. A gemba command that
writes it SHALL write every field of the effective schema of the task's workstream,
`null` when no value was given, admit no undeclared key in its input, and keep a key
the schema no longer declares. Each value SHALL be `null` or of its field's type: a
string for `text`, a number for `number`, `true` or `false` for `boolean`, an ISO date
for `date`; only a `text` field MAY hold a list, of strings.

#### Scenario: All declared keys present
- **WHEN** the effective schema declares `client`, `hours` and `billed` and only `client` is supplied
- **THEN** the frontmatter contains `client` with its value and `hours: null` and `billed: null`
- **Cases**: keeps `tests/cases/create/all-declared-keys-present.yaml`

#### Scenario: List value
- **WHEN** a text field receives more than one value, such as `project` receiving `checkout` and `landing`
- **THEN** it is written as a YAML list, `project: [checkout, landing]`
- **Cases**: keeps `tests/cases/create/list-value.yaml`

#### Scenario: Undeclared key
- **WHEN** a value is supplied for a key that is not in the effective schema
- **THEN** the task is not created and the undeclared key is reported
- **Cases**: keeps `tests/cases/create/undeclared-key-in-metadata.yaml`

#### Scenario: Nested value
- **WHEN** a task file holds a metadata value that is a map, or a list holding a map or a list
- **THEN** the file is not a valid task and is reported naming the key
- **Cases**: keeps `tests/cases/list/nested-value-reported.yaml`

### Requirement: Metadata meaning belongs to the user
The built-in processes and commands SHALL treat metadata as typed data, written,
preserved, converted, compared, filtered, grouped and summed by its field's declared
type, and SHALL NOT branch on the meaning of a key or give metadata to the agent as an
input to a process's flow. A built-in skill MAY branch on a field's type, never on its
name. Only the workstream config that declared a key MAY consume its value: meaning
belongs to the user who declared the field.

#### Scenario: Built-in process ignores meaning
- **WHEN** a task carries `metadata.billed: false`
- **THEN** no built-in process behaves differently because of that value; at most it is shown, filtered, grouped or counted on request
- **Cases**: keeps `tests/cases/create/built-in-process-ignores-meaning.yaml`

#### Scenario: Workstream customization consumes its own field
- **WHEN** workstream `code-reviews` declares `merge_url` and a future launch customization of that same workstream reads `merge_url`
- **THEN** that is allowed, because the consumer and the declarer are the same customization
- **Cases**: keeps the entry `task-file-format: Workstream customization consumes its own field` of `tests/not-automated.yaml`

### Requirement: Frontmatter ownership
Only gemba commands SHALL write the frontmatter, `metadata` and creation included;
agents SHALL edit the body only. After creation, `gemba mark` moves `status`,
`done_at` and `updated_at` through one rule table, which `gemba harness launch` also
applies to move `open` to `in-progress`; `gemba record` moves `updated_at` when a day
is recorded; and `gemba set` writes `metadata` alone. Only `gemba archive` SHALL move
a task file into `archive/`, changing no byte of it.

#### Scenario: Agent records progress
- **WHEN** an agent records work on a task
- **THEN** it drafts the bullets and relies on `gemba record` to write them and move `updated_at`; it edits neither the frontmatter nor the `## Updates` section by hand
- **Cases**: keeps the entry `task-file-format: Agent records progress` of `tests/not-automated.yaml`

#### Scenario: Metadata changes after creation
- **WHEN** a metadata value such as `hours` must change after the task exists
- **THEN** the change is made by `gemba set`, never by editing the frontmatter directly
- **Cases**: keeps `tests/cases/set/metadata-changes-after-creation.yaml`

#### Scenario: Launch rewrites only the frontmatter
- **WHEN** `gemba harness launch` starts an `open` task whose body holds a description, links and an empty `## Updates`
- **THEN** the frontmatter keeps its keys in order with the new `status` and `updated_at`, and the body is byte for byte what it was
- **Cases**: keeps `tests/cases/harness/open-task-started.yaml`

#### Scenario: Status changed by a command
- **WHEN** `gemba mark` moves a `blocked` task whose `metadata` holds a list value and whose body holds a description, a link line and two recorded days
- **THEN** only `status`, `updated_at` and, when it applies, `done_at` differ; the metadata is written as it was and the body is byte for byte what it was
- **Cases**: keeps `tests/cases/mark/only-the-frontmatter-changes.yaml`

### Requirement: Body structure
The body SHALL start with a short description of the task, optionally followed by
links to external references the user gave, and SHALL end with a `## Updates` section,
empty at creation, holding one `### YYYY-MM-DD` subsection per day with activity, in
chronological order. A command SHALL write a subsection as its heading, a blank line
and the bullets, one blank line apart from the `## Updates` heading and from its
neighbours.

#### Scenario: Body of a new task
- **WHEN** a task is created with the description "Login fails on Safari for the checkout app"
- **THEN** the body is that description, a blank line, and an empty `## Updates` section
- **Cases**: keeps `tests/cases/create/body-of-a-new-task.yaml`

#### Scenario: Task created without a description
- **WHEN** a task is created and no description was supplied to the command
- **THEN** the body contains only the empty `## Updates` section and the agent adds the description above it before reporting
- **Cases**: keeps `tests/cases/create/task-created-without-description.yaml`

#### Scenario: Subsection as written by a command
- **WHEN** a day is recorded on a task whose `## Updates` holds one earlier subsection
- **THEN** the body ends with `## Updates`, a blank line, the earlier subsection, a blank line, `### YYYY-MM-DD`, a blank line and the bullets, and the file ends with one newline
- **Cases**: keeps `tests/cases/record/subsection-as-written-by-a-command.yaml`

### Requirement: Updates section structure
A body SHALL hold exactly one `## Updates` line, no `## ` heading after it, and under
it only `### ` headings that are ISO dates in strictly increasing order. A command
that writes the section SHALL check this first and refuse, changing nothing, naming
the task path and the rule broken, when the heading is missing or repeated, when a
`## ` heading follows it, or when a date heading is invalid, repeated or out of order,
instead of guessing where to write. The lines under a date are not checked.

#### Scenario: Updates heading missing
- **WHEN** the body has no `## Updates` line and a day is recorded
- **THEN** the command exits 1, says the task has no `## Updates` section, and changes nothing
- **Cases**: keeps `tests/cases/record/updates-heading-missing.yaml`

#### Scenario: Updates not the last section
- **WHEN** the body holds `## Updates` twice, or a `## ` heading after `## Updates`
- **THEN** the command exits 1, names the offending heading, and changes nothing
- **Cases**: keeps `tests/cases/record/updates-not-the-last-section.yaml`

#### Scenario: Invalid subsection headings
- **WHEN** a `### ` heading under `## Updates` is not an ISO date, such as `### Monday`, or the dates read `### 2026-10-02` before `### 2026-10-01`, or a date appears twice
- **THEN** the command exits 1, names the offending heading, and changes nothing
- **Cases**: keeps `tests/cases/record/invalid-subsection-headings.yaml`

## REMOVED Requirements

### Requirement: Reading a task file
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "A file
read as a task", "Metadata read whatever the schema" and "The description of a task".

## ADDED Requirements

### Requirement: A file read as a task
A process that reads tasks SHALL accept a `.md` file as a task only when its filename
matches `YYYY-MM-DD-<ref>-<slug>.md` with a valid date, it starts with a YAML
frontmatter that parses to a map, `status` is allowed, `ref` is a string equal to the
filename's, `updated_at` and any `done_at` are ISO dates, and `metadata` is a map of
scalars or lists of scalars. A file that fails a check SHALL be reported with its path
and the rule, and never read as a task.

#### Scenario: Valid file read
- **WHEN** a file conforms to every rule above
- **THEN** the process reads its ref, status, dates, metadata and description
- **Cases**: keeps `tests/cases/list/complete-record.yaml`

#### Scenario: Missing or unparseable frontmatter
- **WHEN** a `.md` file in a workstream folder does not start with a frontmatter block, or the block is not valid YAML
- **THEN** the file is reported as invalid and is not read as a task
- **Cases**: keeps `tests/cases/list/missing-or-unparseable-frontmatter.yaml`

#### Scenario: Ref mismatch
- **WHEN** the filename says `SUP-3` and the frontmatter says `ref: SUP-4`
- **THEN** the file is reported as invalid, naming both refs
- **Cases**: keeps `tests/cases/list/ref-mismatch.yaml`

#### Scenario: Invalid date field
- **WHEN** `updated_at` is missing or is not an ISO date
- **THEN** the file is reported as invalid, naming the field
- **Cases**: keeps `tests/cases/list/invalid-date-field.yaml`

#### Scenario: Metadata not a map
- **WHEN** `metadata` is missing, or is a list or a scalar
- **THEN** the file is reported as invalid, naming `metadata`
- **Cases**: keeps `tests/cases/list/metadata-not-a-map.yaml`

### Requirement: Metadata read whatever the schema
The reader SHALL NOT check the metadata keys against the effective schema of the
workstream, nor the values against their declared types, so that a task written under
an earlier schema stays readable after the config changes; a value that does not match
its type is reported by the processes that operate on metadata, never by refusing the
task.

#### Scenario: Metadata keys outside the current schema
- **WHEN** a task carries `metadata.ticket_id` and the config no longer declares `ticket_id` for its workstream
- **THEN** the task is still read and listed with `ticket_id` in its metadata
- **Cases**: keeps `tests/cases/list/metadata-keys-outside-the-current-schema.yaml`

#### Scenario: Value of another type still read
- **WHEN** a task carries `hours: "3"` as a string and the config declares `hours` as a `number`
- **THEN** the task is read and listed with `hours: "3"` in its metadata, and the listing reports the value as a problem
- **Cases**: keeps `tests/cases/list/value-of-another-type-still-read.yaml`

### Requirement: The description of a task
The description SHALL be the first paragraph of the body, the text before the first
blank line after the frontmatter, or `null` when the body starts with the `## Updates`
heading.

#### Scenario: Description extracted
- **WHEN** the body is "Login fails on Safari for the checkout app", a blank line, a link line, a blank line and `## Updates`
- **THEN** the description is "Login fails on Safari for the checkout app"
- **Cases**: keeps `tests/cases/list/description-extracted.yaml`

#### Scenario: Description absent
- **WHEN** the body starts with `## Updates`
- **THEN** the description is `null`
- **Cases**: keeps `tests/cases/list/description-absent.yaml`
