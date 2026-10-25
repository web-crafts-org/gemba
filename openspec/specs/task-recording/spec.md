# task-recording Specification

## Purpose

Recording writes one day of work into its task file. Inside the harness of the task,
the agent distills the day's notes of the run into bullets; from the tasks repo, for
work done outside a run, it drafts what the person tells it. One command writes them as
the dated subsection of `## Updates` and moves `updated_at` in the same step, so that
the task file stays the durable record and no update is ever invisible to date-filtered
listings.

## Requirements

### Requirement: Where the record is made
`gemba record [<ref>] <file> [--date YYYY-MM-DD]` SHALL act on one task, from inside a
harness or from the tasks repo. The command runs inside a harness when `--harness`
names one or when a folder at or above the working directory holds `harness.yaml`:
the harness root SHALL be that folder, the task SHALL be the one `harness.yaml`
names, resolved against the tasks repo root, which is `--root` or the nearest folder
above the harness that holds `gemba.yaml`, and `<ref>`, which is optional there, SHALL
be the ref of that task when given. Otherwise the command runs from the tasks repo:
the root SHALL be `--root` or the nearest folder at or above the working directory
that holds `gemba.yaml`, and the task SHALL be the one whose ref is `<ref>` under
`tasks/`, archives included. The command SHALL validate the gemba config as every
process does. It SHALL refuse, changing nothing, saying so and naming the path or the
ref: inside a harness, when the harness config is not one `launch` would have written,
when the task file it names does not exist or is not a valid task, or when `<ref>`
names another task, saying that task is recorded from the tasks repo or from its own
harness; from the tasks repo, when `<ref>` is missing, saying that outside a harness
the task is named by its ref, or when no task or several tasks hold the ref.

#### Scenario: Harness resolved from the working directory
- **WHEN** `gemba record update.md --date 2026-10-01` runs from a folder inside a harness, without `--harness`
- **THEN** the task named by that harness's `harness.yaml` gains the update and the command exits 0

#### Scenario: No harness found
- **WHEN** `gemba record update.md --date 2026-10-01` runs, with no ref, from a folder of the tasks repo with no `harness.yaml` at or above it and without `--harness`
- **THEN** the command exits 1, says that no harness was found and that outside a harness the task is named by its ref, and changes nothing

#### Scenario: Task file missing
- **WHEN** the `task` path of `harness.yaml` names a file that no longer exists under the tasks repo
- **THEN** the command exits 1, names the path, says the task file was not found there, and changes nothing

#### Scenario: Task named by ref from the tasks repo
- **WHEN** `update.md` at the tasks repo root holds one bullet, `SUP-1` was created on `2026-09-30` with `updated_at: 2026-09-30` and has no harness, and `gemba record SUP-1 update.md --date 2026-10-01` runs from `tasks/support`
- **THEN** the task holds the bullet under `### 2026-10-01`, `updated_at` reads `2026-10-01`, `update.md` no longer exists, the output is the task path followed by `updated_at: 2026-09-30 -> 2026-10-01`, and the command exits 0

#### Scenario: Unknown ref refused
- **WHEN** `gemba record SUP-9 update.md` runs from the tasks repo and no task, archived or not, holds `SUP-9`
- **THEN** the command exits 1, says that no task has ref `SUP-9` under `tasks/`, archives included, and changes nothing, the draft included

#### Scenario: Archived task recorded by ref
- **WHEN** `SUP-1` lies under `tasks/support/archive/` and `gemba record SUP-1 update.md --date 2026-10-01` runs from the tasks repo root
- **THEN** the archived task holds the bullets under `### 2026-10-01`, stays under `archive/`, and the command exits 0

#### Scenario: Ref of the harness's task accepted
- **WHEN** `update.md` at the root of the harness of `SUP-1` holds one bullet and `gemba record SUP-1 update.md --date 2026-10-01` runs inside that harness
- **THEN** the task gains the update exactly as without the ref, the draft of the harness root is deleted, and the command exits 0

#### Scenario: Another ref refused inside a harness
- **WHEN** `SUP-1` and `SUP-2` exist and `gemba record SUP-2 update.md --date 2026-10-01` runs inside the harness of `SUP-1`
- **THEN** the command exits 1, names `SUP-2` and `SUP-1`, says that `SUP-2` is recorded from the tasks repo or from its own harness, and changes nothing, the draft included

### Requirement: The draft is written by the agent and consumed by the command
The `<file>` argument SHALL be a path relative to the root of the place the record is
made: inside a harness, relative to the harness root and inside the harness; from the
tasks repo, relative to the tasks repo root and directly in that root, so that neither
a task file nor the draft of a run is consumed. The draft SHALL exist, hold UTF-8
text, and its non-blank lines SHALL each start with `- `
or, continuing the previous bullet, with at least two spaces; at least one bullet
SHALL be present. The command SHALL report every problem of the draft in one message
and refuse, changing nothing, when there is any. After writing the task, the command
SHALL delete the draft, so the place is left as it was before the agent wrote it. The
bullets SHALL be written into the task as they are in the draft, leading and trailing
blank lines dropped, with no rewording or reformatting.

#### Scenario: Draft consumed
- **WHEN** `update.md` at the harness root holds two bullets and `gemba record update.md --date 2026-10-01` runs
- **THEN** the task holds the two bullets under `### 2026-10-01` and `update.md` no longer exists

#### Scenario: Invalid draft refused
- **WHEN** the draft does not exist, or is outside the harness, or holds no bullet, or holds a non-blank line that is neither a bullet nor an indented continuation
- **THEN** the command exits 1, names the rule the draft breaks, and changes nothing, the draft included

#### Scenario: Draft out of place refused in the tasks repo
- **WHEN** `gemba record SUP-1 <file>` runs from the tasks repo with a draft of valid bullets at `../outside.md`, outside the tasks repo, or at `tasks/support/update.md`, or at `harnesses/support/2026-09-30-SUP-1-login-fails/update.md`
- **THEN** the command exits 1, says that the draft does not lie directly in the root of the tasks repo, and changes nothing, the draft included

### Requirement: The date of the update
The update SHALL be dated by `--date`, an ISO `YYYY-MM-DD`, or by the current date when
`--date` is absent. The command SHALL refuse, changing nothing, a date that is not a
valid ISO date, a date after the current date, or a date before the creation date of
the task, which is the date of its filename, so that an update never falls outside the
life of its task.

#### Scenario: Default date is today
- **WHEN** `gemba record update.md` runs without `--date`
- **THEN** the subsection written is `### <today>` and `updated_at` reads today

#### Scenario: Invalid date refused
- **WHEN** `--date` is `2026-13-01`, or `2999-01-01`, or a date before the creation date in the task's filename
- **THEN** the command exits 1, names the date and the rule it breaks, and changes nothing

### Requirement: The subsection and updated_at are written in one step
The command SHALL write the task file once, with the `### D` subsection added under
`## Updates` in chronological position when the task has none for D, or the bullets
appended after the last line of the existing `### D` subsection, and with `updated_at`
set to the later of its current value and D. The frontmatter SHALL be written again in
its fixed key order with no other value changed, `status` included, and every line of
the body outside the written subsection SHALL be byte for byte what it was. The
command SHALL run no git command: the tasks repo is committed by a person and the
harness has nothing new to commit. On success it SHALL print the task path relative to
the tasks repo root, then `updated_at: <old> -> <new>` when the date moved, or
`updated_at: <value> (unchanged)` when it did not.

#### Scenario: First update of a task
- **WHEN** the task body ends with an empty `## Updates` and `gemba record update.md --date 2026-10-01` runs with a draft of two bullets, `updated_at` reading `2026-09-30`
- **THEN** the body ends with `## Updates`, a blank line, `### 2026-10-01`, a blank line and the two bullets, `updated_at` reads `2026-10-01`, and the output is the task path followed by `updated_at: 2026-09-30 -> 2026-10-01`

#### Scenario: Subsection inserted in chronological position
- **WHEN** the task holds `### 2026-09-30` and `### 2026-10-02` and the update is dated `2026-10-01`
- **THEN** `### 2026-10-01` appears between the two, separated from each by one blank line, and the existing subsections are unchanged

#### Scenario: Bullets merged into an existing subsection
- **WHEN** the task already holds `### 2026-10-01` with one bullet and the update is dated `2026-10-01`
- **THEN** the new bullets follow the existing one under the same heading and no second `### 2026-10-01` heading is written

#### Scenario: updated_at never moves backwards
- **WHEN** `updated_at` reads `2026-10-02` and the update is dated `2026-09-30`, or `updated_at` reads `2026-09-30` and the update is dated `2026-10-02`
- **THEN** the first leaves `updated_at` at `2026-10-02` and prints `updated_at: 2026-10-02 (unchanged)`, and the second moves it to `2026-10-02` and prints `updated_at: 2026-09-30 -> 2026-10-02`

#### Scenario: Only the section and updated_at change
- **WHEN** the task is `blocked`, carries `metadata` with a list value, and its body holds a description, a link line and `## Updates` with an earlier subsection
- **THEN** after recording, `status` still reads `blocked`, the metadata is written as it was, the description, the link line and the earlier subsection are byte for byte what they were, and only the new subsection and `updated_at` differ

#### Scenario: Nothing is committed
- **WHEN** an update is recorded from a harness with one launch commit
- **THEN** the harness repository still has exactly that commit, and the task file in the tasks repo is modified on disk

### Requirement: Recording by the agent
The `gemba-record` skill SHALL have the agent, from inside a harness, read `task.md`
and every note under `notes/` whose name carries the date to record, in the order of
their names and whatever their type, distill them into one to five bullets of what
moved that day, each understandable without the harness, skipping process noise, and
write the bullets with its own tools into `update.md` at the harness root with no
heading, date or frontmatter. The agent SHALL read the `record` block of the task's
workstream in the gemba config, follow its `rules`, run `gemba record update.md`,
with `--date` when the day is not today, and relay the printed path and `updated_at`
movement. When no note carries the date and nothing was done in the session on that
date, the agent SHALL say so and stop, recording nothing. The agent SHALL never edit
`task.md`, write a `### YYYY-MM-DD` heading by hand, or record a date the notes do not
support. When several dates are to be recorded, the agent SHALL record each one with
its own draft and its own command run, oldest first.

#### Scenario: Agent records the day
- **WHEN** the user asks, inside a harness, to record what was done today on the task
- **THEN** the agent reads the notes dated today, writes `update.md` with the distilled bullets, runs `gemba record update.md` and relays the result

#### Scenario: Nothing to record
- **WHEN** no note under `notes/` carries the requested date and the session did nothing on that date
- **THEN** the agent says there is nothing to record for that date and runs no command

#### Scenario: Agent follows the verb's rules
- **WHEN** the task's workstream declares `record.rules`
- **THEN** the agent follows them while distilling and drafting the bullets

### Requirement: Skill contains no organization-specific value
The `gemba-record` skill SHALL contain only the process and SHALL NOT name any
workstream, prefix, metadata field, language or organization-specific rule; what the
bullets must say or how they must be written for one organization belongs in
`record.rules` of the gemba config.

#### Scenario: Config change without skill change
- **WHEN** a workstream adds a `record.rules` entry such as "name the merge request in every bullet"
- **THEN** the skill needs no edit for the agent to follow it

### Requirement: Recording from the tasks repo by the agent
From the tasks repo, the `gemba-record` skill SHALL have the agent record what the
person tells it was done on a task, never the notes of a harness: identify the task by
its ref, distill one to five bullets under the `record` block of its workstream, write
them into `update.md` at the tasks repo root and run `gemba record <ref> update.md`,
with `--date` when the day is not today. When the task has a harness, the agent SHALL
say that the work of the run is recorded from inside it.

#### Scenario: Agent records work done outside a harness
- **WHEN** the user, in the tasks repo, tells the agent about a review held today on `SUP-1` and asks to record it
- **THEN** the agent writes `update.md` at the tasks repo root with bullets of what the user said, runs `gemba record SUP-1 update.md` and relays the result

#### Scenario: Task with a harness recorded from the tasks repo
- **WHEN** the user asks, in the tasks repo, to record a day of a task that has a harness
- **THEN** the agent says that the work of the run is recorded from inside the harness, records only what the user told it, and reads no note of that harness

#### Scenario: Nothing told, nothing recorded
- **WHEN** the user asks, in the tasks repo, to record a day on a task without saying what was done
- **THEN** the agent asks what was done, and records nothing the user did not tell it
