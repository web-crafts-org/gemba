# task-file-format Specification

## Purpose

A task file is the durable record of one unit of work: one Markdown file per task,
stored in its workstream folder, with a command-owned frontmatter that commands can trust
and an agent-owned body that carries the narrative. Every other process of Gemba
reads or writes this format.

## Requirements

### Requirement: Task location
A task SHALL be a single Markdown file stored directly under `tasks/<workstream>/` in
the tasks repo, where `<workstream>` is a workstream identifier from the
gemba config. Each workstream folder SHALL contain an `archive/` subfolder into which
finished tasks are moved unchanged. Both folders SHALL exist in version control even
when empty, holding a `.gitkeep` file.

#### Scenario: Task placed in its workstream folder
- **WHEN** a task is created for workstream `support`
- **THEN** its file is written directly under `tasks/support/` and nowhere else

#### Scenario: Archived task
- **WHEN** a task file is moved from `tasks/support/` to `tasks/support/archive/`
- **THEN** its content is unchanged and processes that list active tasks skip it unless archived tasks are explicitly requested

### Requirement: Filename
A task filename SHALL be `YYYY-MM-DD-<ref>-<slug>.md`. `YYYY-MM-DD` is the creation date
(the day the task is registered, unless the user states another date). `<ref>` is the
task ref defined below. `<slug>` is one or more lowercase words of ASCII letters and
digits joined by single hyphens, derived from what the user said; it is the task's
title and no separate title field exists.

#### Scenario: Filename with a valid slug
- **WHEN** a task with ref `SUP-1` and slug `login-fails-on-safari` is created on 2026-09-30
- **THEN** its filename is `2026-09-30-SUP-1-login-fails-on-safari.md`

#### Scenario: Invalid slug
- **WHEN** a slug contains uppercase letters, spaces, accented characters, consecutive hyphens or a leading or trailing hyphen
- **THEN** the task is not created and the slug is reported as invalid

#### Scenario: Display title derived from the filename
- **WHEN** a process needs a human-readable title for `2026-09-30-SUP-1-login-fails-on-safari.md` whose frontmatter ref is `SUP-1`
- **THEN** it strips the date, the known ref and the extension, replaces hyphens with spaces and capitalizes the first letter, yielding `Login fails on safari`

### Requirement: Task ref
Every task SHALL carry a ref of the form `<PREFIX>-<N>`, where `<PREFIX>` is the prefix
of the workstream the task was created in and `<N>` is a positive integer without
leading zeros. The ref SHALL be unique across the whole repository, SHALL be allocated
by Gemba (never chosen by the user or the agent), and SHALL be internal: it is
never an external identifier such as a ticket key or merge request number. External
identifiers, when they exist, belong in metadata or as links in the body. The ref
written in the frontmatter SHALL equal the ref in the filename.

#### Scenario: Consecutive refs within a workstream
- **WHEN** the highest existing ref with prefix `CR` anywhere under `tasks/` (including archive folders) is `CR-12`
- **THEN** the next task created in the workstream with prefix `CR` receives `CR-13`

#### Scenario: First task of a prefix
- **WHEN** no task with prefix `EST` exists anywhere under `tasks/`
- **THEN** the first task created in the workstream with prefix `EST` receives `EST-1`

#### Scenario: Moved task keeps its ref
- **WHEN** a task with ref `CR-7` is moved into another workstream folder or into an archive folder
- **THEN** it keeps `CR-7`, and `CR-7` is never allocated again because allocation scans every task folder

#### Scenario: External key offered as ref
- **WHEN** the user asks for a task to be identified by a ticket key such as `PROD-16283`
- **THEN** Gemba still allocates an internal ref and records the ticket key in metadata or in the body, never as the ref

### Requirement: Built-in frontmatter fields
The frontmatter SHALL be a YAML block delimited by `---` lines at the start of the file
containing exactly these top-level keys, in this order: `status`, `ref`, `updated_at`,
`done_at` (present only when status is `done`), and `metadata`. `status` SHALL be one
of `open`, `in-progress`, `blocked`, `done`. `updated_at` SHALL be an ISO date equal to
the creation date at creation and SHALL only ever move forward afterwards. `done_at`
SHALL be the ISO date the task reached `done`, and SHALL be removed when the task
leaves `done`, so that it always means "done since this date" and never "was once
done".

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

#### Scenario: Invalid status value
- **WHEN** a frontmatter `status` is anything other than `open`, `in-progress`, `blocked` or `done`
- **THEN** the file is not a valid task and processes report it instead of guessing

#### Scenario: Done at follows the status
- **WHEN** a task marked `done` on 2026-10-01 is marked `blocked` on 2026-10-02
- **THEN** its frontmatter reads `status: blocked`, `updated_at: 2026-10-02` and holds no `done_at` key, with every other key as it was

### Requirement: Metadata contract
`metadata` SHALL always be present as a flat map. A gemba command that writes it SHALL
write every field name of the effective metadata schema of the task's workstream, with
`null` when no value was given, SHALL admit no undeclared key in its input, and SHALL
keep as it was a key the schema no longer declares. Each value SHALL be `null` or a
value of the declared type of its field: a string for `text`, a number for `number`,
`true` or `false` for `boolean`, an ISO date for `date`. Only a `text` field MAY hold a
list, of strings. Nested maps are not allowed. Keys are snake_case.

#### Scenario: All declared keys present
- **WHEN** the effective schema declares `client`, `hours` and `billed` and only `client` is supplied
- **THEN** the frontmatter contains `client` with its value and `hours: null` and `billed: null`

#### Scenario: List value
- **WHEN** a text field receives more than one value, such as `project` receiving `checkout` and `landing`
- **THEN** it is written as a YAML list, `project: [checkout, landing]`

#### Scenario: Undeclared key
- **WHEN** a value is supplied for a key that is not in the effective schema
- **THEN** the task is not created and the undeclared key is reported

#### Scenario: Nested value
- **WHEN** a task file holds a metadata value that is a map, or a list holding a map or a list
- **THEN** the file is not a valid task and is reported naming the key

### Requirement: Metadata meaning belongs to the user
The built-in processes and commands of Gemba SHALL treat metadata as typed data: they
write it, preserve it, convert it, compare it, filter it, group it and sum it by the
declared type of its field, and SHALL NOT branch on the meaning of any key or present
metadata to the agent as an input for deciding a process's flow. A built-in skill MAY
branch on the declared type of a field, never on its name. Only the customization
(workstream config) that declared a key MAY consume its value. Meaning belongs to the
user who declared the field.

#### Scenario: Built-in process ignores meaning
- **WHEN** a task carries `metadata.billed: false`
- **THEN** no built-in process behaves differently because of that value; at most it is shown, filtered, grouped or counted on request

#### Scenario: Workstream customization consumes its own field
- **WHEN** workstream `code-reviews` declares `merge_url` and a future launch customization of that same workstream reads `merge_url`
- **THEN** that is allowed, because the consumer and the declarer are the same customization

### Requirement: Frontmatter ownership
Only gemba commands SHALL write the frontmatter, including at creation and including
`metadata`. Agents SHALL edit the body only and SHALL NOT modify the frontmatter by
hand. Any change to a frontmatter field after creation SHALL go through a gemba
command: `gemba mark` moves `status`, `done_at` and `updated_at` through one rule
table, `gemba harness launch` moves `open` to `in-progress` through that same table
when work starts, `gemba record` moves `updated_at` when a day is recorded, `gemba set`
writes `metadata` and nothing else, and the commands of later sprints move the fields
their process owns. Only `gemba archive` SHALL move a task file into `archive/`, and it
SHALL change no byte of it.

#### Scenario: Agent records progress
- **WHEN** an agent records work on a task
- **THEN** it drafts the bullets and relies on `gemba record` to write them and move `updated_at`; it edits neither the frontmatter nor the `## Updates` section by hand

#### Scenario: Metadata changes after creation
- **WHEN** a metadata value such as `hours` must change after the task exists
- **THEN** the change is made by `gemba set`, never by editing the frontmatter directly

#### Scenario: Launch rewrites only the frontmatter
- **WHEN** `gemba harness launch` starts an `open` task whose body holds a description, links and an empty `## Updates`
- **THEN** the frontmatter keeps its keys in order with the new `status` and `updated_at`, and the body is byte for byte what it was

#### Scenario: Status changed by a command
- **WHEN** `gemba mark` moves a `blocked` task whose `metadata` holds a list value and whose body holds a description, a link line and two recorded days
- **THEN** only `status`, `updated_at` and, when it applies, `done_at` differ; the metadata is written as it was and the body is byte for byte what it was

### Requirement: Body structure
The body SHALL start with a short description of the task, optionally followed by links
to external references the user provided, and SHALL end with a `## Updates` section.
`## Updates` SHALL contain one `### YYYY-MM-DD` subsection per day with activity, in
chronological order, with bullets inside, and SHALL be empty at creation. A subsection
as a gemba command writes it SHALL be the `### YYYY-MM-DD` heading, a blank line and
the bullets, separated from the `## Updates` heading and from the neighbouring
subsections by one blank line.

#### Scenario: Body of a new task
- **WHEN** a task is created with the description "Login fails on Safari for the checkout app"
- **THEN** the body is that description, a blank line, and an empty `## Updates` section

#### Scenario: Task created without a description
- **WHEN** a task is created and no description was supplied to the command
- **THEN** the body contains only the empty `## Updates` section and the agent adds the description above it before reporting

#### Scenario: Subsection as written by a command
- **WHEN** a day is recorded on a task whose `## Updates` holds one earlier subsection
- **THEN** the body ends with `## Updates`, a blank line, the earlier subsection, a blank line, `### YYYY-MM-DD`, a blank line and the bullets, and the file ends with one newline

### Requirement: Reading a task file
A process that reads tasks SHALL accept a `.md` file as a task only when: its filename
matches `YYYY-MM-DD-<ref>-<slug>.md` with a valid date; it starts with a YAML
frontmatter block that parses to a map; `status` is one of the allowed values; `ref` is
a string equal to the ref in the filename; `updated_at` is an ISO date; `done_at`,
when present, is an ISO date; and `metadata` is present as a map whose values are
scalars or lists of scalars. The reader SHALL NOT check the metadata keys against the
effective schema of the workstream, nor the values against the declared types of their
fields, so a task written under an earlier schema stays readable after the config
changes; a value that does not match its type is reported by the processes that
operate on metadata, never by refusing the task. The description SHALL be the first
paragraph of the body, that is the text before the first blank line after the
frontmatter, or `null` when the body starts with the `## Updates` heading. A file that
fails any check SHALL be reported with its path and the failing rule and SHALL never be
read as a task.

#### Scenario: Valid file read
- **WHEN** a file conforms to every rule above
- **THEN** the process reads its ref, status, dates, metadata and description

#### Scenario: Missing or unparseable frontmatter
- **WHEN** a `.md` file in a workstream folder does not start with a frontmatter block, or the block is not valid YAML
- **THEN** the file is reported as invalid and is not read as a task

#### Scenario: Ref mismatch
- **WHEN** the filename says `SUP-3` and the frontmatter says `ref: SUP-4`
- **THEN** the file is reported as invalid, naming both refs

#### Scenario: Invalid date field
- **WHEN** `updated_at` is missing or is not an ISO date
- **THEN** the file is reported as invalid, naming the field

#### Scenario: Metadata not a map
- **WHEN** `metadata` is missing, or is a list or a scalar
- **THEN** the file is reported as invalid, naming `metadata`

#### Scenario: Metadata keys outside the current schema
- **WHEN** a task carries `metadata.ticket_id` and the config no longer declares `ticket_id` for its workstream
- **THEN** the task is still read and listed with `ticket_id` in its metadata

#### Scenario: Value of another type still read
- **WHEN** a task carries `hours: "3"` as a string and the config declares `hours` as a `number`
- **THEN** the task is read and listed with `hours: "3"` in its metadata, and the listing reports the value as a problem

#### Scenario: Description extracted
- **WHEN** the body is "Login fails on Safari for the checkout app", a blank line, a link line, a blank line and `## Updates`
- **THEN** the description is "Login fails on Safari for the checkout app"

#### Scenario: Description absent
- **WHEN** the body starts with `## Updates`
- **THEN** the description is `null`

### Requirement: Updates section structure
A body SHALL hold exactly one line equal to `## Updates`, no `## ` heading after it,
and under it only `### ` headings that are valid ISO dates, in strictly increasing
order. A command that writes the section SHALL check these rules first and SHALL
refuse, changing nothing, when the heading is missing or repeated, when another `## `
heading follows it, when a `### ` heading under it is not an ISO date, or when the
dates repeat or are out of order, naming the task path and the rule broken, instead of
guessing where to write. Lines under a date heading are not checked: they are the
agent's and the command's bullets as written over time.

#### Scenario: Updates heading missing
- **WHEN** the body has no `## Updates` line and a day is recorded
- **THEN** the command exits 1, says the task has no `## Updates` section, and changes nothing

#### Scenario: Updates not the last section
- **WHEN** the body holds `## Updates` twice, or a `## ` heading after `## Updates`
- **THEN** the command exits 1, names the offending heading, and changes nothing

#### Scenario: Invalid subsection headings
- **WHEN** a `### ` heading under `## Updates` is not an ISO date, such as `### Monday`, or the dates read `### 2026-10-02` before `### 2026-10-01`, or a date appears twice
- **THEN** the command exits 1, names the offending heading, and changes nothing
