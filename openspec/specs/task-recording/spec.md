# task-recording Specification

## Purpose

Recording promotes one day of a run into its task file: the agent distills the day's
notes into bullets inside the harness, and one command writes them as the dated
subsection of `## Updates` and moves `updated_at` in the same step, so that the task
file stays the durable record and no update is ever invisible to date-filtered
listings.

## Requirements

### Requirement: Record runs inside a harness
`gemba record <file> [--date YYYY-MM-DD]` SHALL act on the task of the harness it runs
in: the harness root SHALL be the folder named by `--harness` or the nearest folder at
or above the working directory that holds `harness.yaml`, and the task SHALL be the
one `harness.yaml` names, resolved against the tasks repo root, which is `--root` or
the nearest folder above the harness that holds `gemba.yaml`. The command SHALL
validate the gemba config as every process does. It SHALL refuse, changing nothing,
when no harness is found, when the harness config is not one `launch` would have
written, or when the task file named by the harness config does not exist or is not a
valid task, saying so and naming the path. There is no way to name a task by ref: a
task without a harness is not recorded by this command.

#### Scenario: Harness resolved from the working directory
- **WHEN** `gemba record update.md --date 2026-10-01` runs from a folder inside a harness, without `--harness`
- **THEN** the task named by that harness's `harness.yaml` gains the update and the command exits 0

#### Scenario: No harness found
- **WHEN** the command runs from a folder with no `harness.yaml` at or above it and without `--harness`
- **THEN** the command exits 1, says no harness was found, and changes nothing

#### Scenario: Task file missing
- **WHEN** the `task` path of `harness.yaml` names a file that no longer exists under the tasks repo
- **THEN** the command exits 1, names the path, says the task file was not found there, and changes nothing

### Requirement: The draft is written by the agent and consumed by the command
The `<file>` argument SHALL be a path relative to the harness root, inside the
harness, that exists, holds UTF-8 text, and whose non-blank lines each start with `- `
or, continuing the previous bullet, with at least two spaces; at least one bullet
SHALL be present. The command SHALL report every problem of the draft in one message
and refuse, changing nothing, when there is any. After writing the task, the command
SHALL delete the draft, so the harness is left as it was before the agent wrote it.
The bullets SHALL be written into the task as they are in the draft, leading and
trailing blank lines dropped, with no rewording or reformatting.

#### Scenario: Draft consumed
- **WHEN** `update.md` at the harness root holds two bullets and `gemba record update.md --date 2026-10-01` runs
- **THEN** the task holds the two bullets under `### 2026-10-01` and `update.md` no longer exists

#### Scenario: Invalid draft refused
- **WHEN** the draft does not exist, or is outside the harness, or holds no bullet, or holds a non-blank line that is neither a bullet nor an indented continuation
- **THEN** the command exits 1, names the rule the draft breaks, and changes nothing, the draft included

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
