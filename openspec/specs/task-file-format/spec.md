# task-file-format Specification

## Purpose

A task file is the durable record of one unit of work: one Markdown file per task,
stored in its workstream folder, with a command-owned frontmatter that commands can trust
and an agent-owned body that carries the narrative. Every other process of Gemba
reads or writes this format.

## Requirements

### Requirement: Task location
A task SHALL be a single Markdown file stored directly under `tasks/<workstream>/` in
the obeya, where `<workstream>` is a workstream identifier from the gemba config, or
under `tasks/<member>/<workstream>/` when the shared config declares a team, where
`<member>` is the folder name of its owner. Each workstream folder SHALL contain an
`archive/` subfolder into which finished tasks are moved unchanged. Both folders SHALL
exist in version control even when empty, holding a `.gitkeep` file.

#### Scenario: Task placed in its workstream folder
- **WHEN** a task is created for workstream `support`
- **THEN** its file is written directly under `tasks/support/` and nowhere else

#### Scenario: Archived task
- **WHEN** a task file is moved from `tasks/support/` to `tasks/support/archive/`
- **THEN** its content is unchanged and processes that list active tasks skip it unless archived tasks are explicitly requested

#### Scenario: Task placed in its member's folder
- **WHEN** a task is created for workstream `support` in an obeya whose team declares `manuel`, and the personal config declares `me: manuel`
- **THEN** its file is written directly under `tasks/manuel/support/`, with `tasks/manuel/support/.gitkeep` and `tasks/manuel/support/archive/.gitkeep`, and nowhere else

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
Every task SHALL carry a ref `<PREFIX>-<N>`, or `<INITIALS>-<PREFIX>-<N>` in an obeya
with a team, with its owner's initials, `<PREFIX>` being the prefix of the workstream
it was created in and `<N>` a positive integer without leading zeros. The ref SHALL be unique across the obeya, allocated by Gemba, never chosen by
the user or the agent, and internal: an external identifier belongs in metadata or as a
link in the body. The ref in the frontmatter SHALL equal the ref in the filename.

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

#### Scenario: Ref of a member's task
- **WHEN** `manuel`, with initials `MR`, creates the first task of the workstream with prefix `SUP` on 2026-10-25 with slug `export-times-out`
- **THEN** the task receives `MR-SUP-1`, its filename is `2026-10-25-MR-SUP-1-export-times-out.md`, and `gemba list` reads it with that ref and the title `Export times out`

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

#### Scenario: Invalid status value
- **WHEN** a frontmatter `status` is anything other than `open`, `in-progress`, `blocked` or `done`
- **THEN** the file is not a valid task and processes report it instead of guessing

#### Scenario: Done at follows the status
- **WHEN** a task marked `done` on 2026-10-01 is marked `blocked` on 2026-10-02
- **THEN** its frontmatter reads `status: blocked`, `updated_at: 2026-10-02` and holds no `done_at` key, with every other key as it was

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
The built-in processes and commands SHALL treat metadata as typed data, written,
preserved, converted, compared, filtered, grouped and summed by its field's declared
type, and SHALL NOT branch on the meaning of a key or give metadata to the agent as an
input to a process's flow. A built-in skill MAY branch on a field's type, never on its
name. Only the workstream config that declared a key MAY consume its value: meaning
belongs to the user who declared the field.

#### Scenario: Built-in process ignores meaning
- **WHEN** a task carries `metadata.billed: false`
- **THEN** no built-in process behaves differently because of that value; at most it is shown, filtered, grouped or counted on request

#### Scenario: Workstream customization consumes its own field
- **WHEN** workstream `code-reviews` declares `merge_url` and a future launch customization of that same workstream reads `merge_url`
- **THEN** that is allowed, because the consumer and the declarer are the same customization

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
The body SHALL start with a short description of the task, optionally followed by
links to external references the user gave, and SHALL end with a `## Updates` section,
empty at creation, holding one `### YYYY-MM-DD` subsection per day with activity, in
chronological order. A command SHALL write a subsection as its heading, a blank line
and the bullets, one blank line apart from the `## Updates` heading and from its
neighbours.

#### Scenario: Body of a new task
- **WHEN** a task is created with the description "Login fails on Safari for the checkout app"
- **THEN** the body is that description, a blank line, and an empty `## Updates` section

#### Scenario: Task created without a description
- **WHEN** a task is created and no description was supplied to the command
- **THEN** the body contains only the empty `## Updates` section and the agent adds the description above it before reporting

#### Scenario: Subsection as written by a command
- **WHEN** a day is recorded on a task whose `## Updates` holds one earlier subsection
- **THEN** the body ends with `## Updates`, a blank line, the earlier subsection, a blank line, `### YYYY-MM-DD`, a blank line and the bullets, and the file ends with one newline

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

### Requirement: Metadata read whatever the schema
The reader SHALL NOT check the metadata keys against the effective schema of the
workstream, nor the values against their declared types, so that a task written under
an earlier schema stays readable after the config changes; a value that does not match
its type is reported by the processes that operate on metadata, never by refusing the
task.

#### Scenario: Metadata keys outside the current schema
- **WHEN** a task carries `metadata.ticket_id` and the config no longer declares `ticket_id` for its workstream
- **THEN** the task is still read and listed with `ticket_id` in its metadata

#### Scenario: Value of another type still read
- **WHEN** a task carries `hours: "3"` as a string and the config declares `hours` as a `number`
- **THEN** the task is read and listed with `hours: "3"` in its metadata, and the listing reports the value as a problem

### Requirement: The description of a task
The description SHALL be the first paragraph of the body, the text before the first
blank line after the frontmatter, or `null` when the body starts with the `## Updates`
heading.

#### Scenario: Description extracted
- **WHEN** the body is "Login fails on Safari for the checkout app", a blank line, a link line, a blank line and `## Updates`
- **THEN** the description is "Login fails on Safari for the checkout app"

#### Scenario: Description absent
- **WHEN** the body starts with `## Updates`
- **THEN** the description is `null`

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

#### Scenario: Updates not the last section
- **WHEN** the body holds `## Updates` twice, or a `## ` heading after `## Updates`
- **THEN** the command exits 1, names the offending heading, and changes nothing

#### Scenario: Invalid subsection headings
- **WHEN** a `### ` heading under `## Updates` is not an ISO date, such as `### Monday`, or the dates read `### 2026-10-02` before `### 2026-10-01`, or a date appears twice
- **THEN** the command exits 1, names the offending heading, and changes nothing
