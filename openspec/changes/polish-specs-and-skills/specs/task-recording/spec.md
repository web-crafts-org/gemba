# Spec Delta

## REMOVED Requirements

### Requirement: Where the record is made
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "A record
made inside a harness" and "A record made from the obeya".

### Requirement: The draft is written by the agent and consumed by the command
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Where the
draft lies" and "What a draft holds".

### Requirement: The subsection and updated_at are written in one step
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The task
is written once" and "Record reports updated_at and commits nothing".

### Requirement: Recording by the agent
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The agent
distills the notes of a day" and "The agent records only what the notes support".

## ADDED Requirements

### Requirement: A record made inside a harness
`gemba record` SHALL run inside a harness when `--harness` names one or a folder at or
above the working directory holds `harness.yaml`. There the task SHALL be the one
`harness.yaml` names, under the obeya root (`--root` or the nearest folder above
holding `gemba.yaml`), and an optional `<ref>` SHALL be its ref. It SHALL refuse,
changing nothing, a harness config `launch` would not write, a task file missing or
invalid, and a `<ref>` of another task, saying where that task is recorded.

#### Scenario: Harness resolved from the working directory
- **WHEN** `gemba record update.md --date 2026-10-01` runs from a folder inside a harness, without `--harness`
- **THEN** the task named by that harness's `harness.yaml` gains the update and the command exits 0
- **Cases**: keeps `tests/cases/record/harness-resolved-from-the-working-directory.yaml`

#### Scenario: Task file missing
- **WHEN** the `task` path of `harness.yaml` names a file that no longer exists under the obeya
- **THEN** the command exits 1, names the path, says the task file was not found there, and changes nothing
- **Cases**: keeps `tests/cases/record/task-file-missing.yaml`

#### Scenario: Ref of the harness's task accepted
- **WHEN** `update.md` at the root of the harness of `SUP-1` holds one bullet and `gemba record SUP-1 update.md --date 2026-10-01` runs inside that harness
- **THEN** the task gains the update exactly as without the ref, the draft of the harness root is deleted, and the command exits 0
- **Cases**: keeps `tests/cases/record/ref-of-the-harness-task-accepted.yaml`

#### Scenario: Another ref refused inside a harness
- **WHEN** `SUP-1` and `SUP-2` exist and `gemba record SUP-2 update.md --date 2026-10-01` runs inside the harness of `SUP-1`
- **THEN** the command exits 1, names `SUP-2` and `SUP-1`, says that `SUP-2` is recorded from the obeya or from its own harness, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/another-ref-refused-inside-a-harness.yaml`

### Requirement: A record made from the obeya
Otherwise `gemba record <ref> <file> [--date YYYY-MM-DD]`, or
`gemba record <ref> --from <task file>` in migration mode, runs from the obeya, whose
root is `--root` or the nearest folder at or above the working directory holding
`gemba.yaml`, on the task whose ref is `<ref>` under `tasks/`, archives included. It
SHALL refuse, changing nothing, when `<ref>` is missing, saying that outside a harness
a task is named by its ref, or when no task or several hold it.

#### Scenario: No harness found
- **WHEN** `gemba record update.md --date 2026-10-01` runs, with no ref, from a folder of the obeya with no `harness.yaml` at or above it and without `--harness`
- **THEN** the command exits 1, says that no harness was found and that outside a harness the task is named by its ref, and changes nothing
- **Cases**: keeps `tests/cases/record/no-harness-found.yaml`

#### Scenario: Task named by ref from the obeya
- **WHEN** `update.md` at the obeya root holds one bullet, `SUP-1` was created on `2026-09-30` with `updated_at: 2026-09-30` and has no harness, and `gemba record SUP-1 update.md --date 2026-10-01` runs from `tasks/support`
- **THEN** the task holds the bullet under `### 2026-10-01`, `updated_at` reads `2026-10-01`, `update.md` no longer exists, the output is the task path followed by `updated_at: 2026-09-30 -> 2026-10-01`, and the command exits 0
- **Cases**: keeps `tests/cases/record/task-named-by-ref-from-the-obeya.yaml`

#### Scenario: Unknown ref refused
- **WHEN** `gemba record SUP-9 update.md` runs from the obeya and no task, archived or not, holds `SUP-9`
- **THEN** the command exits 1, says that no task has ref `SUP-9` under `tasks/`, archives included, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/unknown-ref-refused.yaml`

#### Scenario: Archived task recorded by ref
- **WHEN** `SUP-1` lies under `tasks/support/archive/` and `gemba record SUP-1 update.md --date 2026-10-01` runs from the obeya root
- **THEN** the archived task holds the bullets under `### 2026-10-01`, stays under `archive/`, and the command exits 0
- **Cases**: keeps `tests/cases/record/archived-task-recorded-by-ref.yaml`

### Requirement: Where the draft lies
The `<file>` argument SHALL be a path relative to the root of the place the record is
made: inside a harness, a file inside the harness; from the obeya, a file directly in
the obeya root, so that neither a task file nor the draft of a run is consumed.

#### Scenario: Draft out of place refused in the obeya
- **WHEN** `gemba record SUP-1 <file>` runs from the obeya with a draft of valid bullets at `../outside.md`, outside the obeya, or at `tasks/support/update.md`, or at `harnesses/support/2026-09-30-SUP-1-login-fails/update.md`
- **THEN** the command exits 1, says that the draft does not lie directly in the root of the obeya, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/draft-out-of-place-refused-in-the-obeya.yaml`

### Requirement: What a draft holds
The draft SHALL exist and hold UTF-8 text whose non-blank lines each start with `- `
or, continuing the previous bullet, with at least two spaces, with at least one
bullet; any problem SHALL refuse the record, changing nothing, every problem in one
message. The bullets SHALL be written as they are, leading and trailing blank lines
dropped, never reworded or reformatted, and the draft then deleted, leaving the place
as it was before the agent wrote it.

#### Scenario: Draft consumed
- **WHEN** `update.md` at the harness root holds two bullets and `gemba record update.md --date 2026-10-01` runs
- **THEN** the task holds the two bullets under `### 2026-10-01` and `update.md` no longer exists
- **Cases**: keeps `tests/cases/record/draft-consumed.yaml`

#### Scenario: Invalid draft refused
- **WHEN** the draft does not exist, or is outside the harness, or holds no bullet, or holds a non-blank line that is neither a bullet nor an indented continuation
- **THEN** the command exits 1, names the rule the draft breaks, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/invalid-draft-refused.yaml`

### Requirement: The task is written once
The command SHALL write the task file once: under `## Updates`, a `### D` subsection
in chronological position when the task has none for D, or else the bullets after the
last line of `### D`; and `updated_at` set to the later of its value and D. The
frontmatter SHALL be written again in its fixed key order with no other value changed,
`status` included, and every line of the body outside the written subsection SHALL be
byte for byte what it was.

#### Scenario: Subsection inserted in chronological position
- **WHEN** the task holds `### 2026-09-30` and `### 2026-10-02` and the update is dated `2026-10-01`
- **THEN** `### 2026-10-01` appears between the two, separated from each by one blank line, and the existing subsections are unchanged
- **Cases**: keeps `tests/cases/record/subsection-inserted-in-order.yaml`

#### Scenario: Bullets merged into an existing subsection
- **WHEN** the task already holds `### 2026-10-01` with one bullet and the update is dated `2026-10-01`
- **THEN** the new bullets follow the existing one under the same heading and no second `### 2026-10-01` heading is written
- **Cases**: keeps `tests/cases/record/bullets-merged-into-existing-subsection.yaml`

#### Scenario: Only the section and updated_at change
- **WHEN** the task is `blocked`, carries `metadata` with a list value, and its body holds a description, a link line and `## Updates` with an earlier subsection
- **THEN** after recording, `status` still reads `blocked`, the metadata is written as it was, the description, the link line and the earlier subsection are byte for byte what they were, and only the new subsection and `updated_at` differ
- **Cases**: keeps `tests/cases/record/only-the-section-and-updated-at-change.yaml`

### Requirement: Record reports updated_at and commits nothing
The command SHALL run no git: a person commits the obeya, and the harness has nothing
new to commit. On success it SHALL print the task path relative to the obeya root,
then `updated_at: <old> -> <new>` when the date moved, or
`updated_at: <value> (unchanged)` when it did not.

#### Scenario: First update of a task
- **WHEN** the task body ends with an empty `## Updates` and `gemba record update.md --date 2026-10-01` runs with a draft of two bullets, `updated_at` reading `2026-09-30`
- **THEN** the body ends with `## Updates`, a blank line, `### 2026-10-01`, a blank line and the two bullets, `updated_at` reads `2026-10-01`, and the output is the task path followed by `updated_at: 2026-09-30 -> 2026-10-01`
- **Cases**: keeps `tests/cases/record/first-update-of-a-task.yaml`

#### Scenario: updated_at never moves backwards
- **WHEN** `updated_at` reads `2026-10-02` and the update is dated `2026-09-30`, or `updated_at` reads `2026-09-30` and the update is dated `2026-10-02`
- **THEN** the first leaves `updated_at` at `2026-10-02` and prints `updated_at: 2026-10-02 (unchanged)`, and the second moves it to `2026-10-02` and prints `updated_at: 2026-09-30 -> 2026-10-02`
- **Cases**: keeps `tests/cases/record/updated-at-never-moves-backwards.yaml`

#### Scenario: Nothing is committed
- **WHEN** an update is recorded from a harness with one launch commit
- **THEN** the harness repository still has exactly that commit, and the task file in the obeya is modified on disk
- **Cases**: keeps `tests/cases/record/nothing-is-committed.yaml`

### Requirement: The agent distills the notes of a day
The `gemba-record` skill SHALL have the agent, inside a harness, read `task.md` and
every note whose name carries the date to record, in name order, whatever their type,
distill them into one to five bullets of what moved that day, each clear without the
harness, and write them into `update.md` at the harness root, with no heading, date or
frontmatter. Following the `record` block of the workstream, it SHALL run
`gemba record update.md`, with `--date` for another day, and relay what it prints.

#### Scenario: Agent records the day
- **WHEN** the user asks, inside a harness, to record what was done today on the task
- **THEN** the agent reads the notes dated today, writes `update.md` with the distilled bullets, runs `gemba record update.md` and relays the result
- **Cases**: keeps the entry `task-recording: Agent records the day` of `tests/not-automated.yaml`

#### Scenario: Agent follows the verb's rules
- **WHEN** the task's workstream declares `record.rules`
- **THEN** the agent follows them while distilling and drafting the bullets
- **Cases**: keeps the entry `task-recording: Agent follows the verb's rules` of `tests/not-automated.yaml`

### Requirement: The agent records only what the notes support
When no note carries the date and nothing was done in the session on it, the agent
SHALL say so and record nothing. It SHALL never edit `task.md`, write a
`### YYYY-MM-DD` heading by hand or record a date the notes do not support, and SHALL
record several dates oldest first, each with its own draft and command run.

#### Scenario: Nothing to record
- **WHEN** no note under `notes/` carries the requested date and the session did nothing on that date
- **THEN** the agent says there is nothing to record for that date and runs no command
- **Cases**: keeps the entry `task-recording: Nothing to record` of `tests/not-automated.yaml`
