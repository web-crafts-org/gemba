# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Skill contains no organization-specific value`
- TO: `### Requirement: Skill contains no configured value`
- FROM: `### Requirement: Recording from the tasks repo by the agent`
- TO: `### Requirement: Recording from the obeya by the agent`

## MODIFIED Requirements

### Requirement: Where the record is made
`gemba record [<ref>] <file> [--date YYYY-MM-DD]`, or `gemba record [<ref>] --from
<task file>` as the migration mode requirement says, SHALL act on one task, from inside
a harness or from the obeya. The command runs inside a harness when `--harness`
names one or when a folder at or above the working directory holds `harness.yaml`:
the harness root SHALL be that folder, the task SHALL be the one `harness.yaml`
names, resolved against the obeya root, which is `--root` or the nearest folder
above the harness that holds `gemba.yaml`, and `<ref>`, which is optional there, SHALL
be the ref of that task when given. Otherwise the command runs from the obeya:
the root SHALL be `--root` or the nearest folder at or above the working directory
that holds `gemba.yaml`, and the task SHALL be the one whose ref is `<ref>` under
`tasks/`, archives included. The command SHALL validate the gemba config as every
process does. It SHALL refuse, changing nothing, saying so and naming the path or the
ref: inside a harness, when the harness config is not one `launch` would have written,
when the task file it names does not exist or is not a valid task, or when `<ref>`
names another task, saying that task is recorded from the obeya or from its own
harness; from the obeya, when `<ref>` is missing, saying that outside a harness
the task is named by its ref, or when no task or several tasks hold the ref. The
requirements on the draft, its date and its subsection apply to a record made from a
draft.

#### Scenario: Harness resolved from the working directory
- **WHEN** `gemba record update.md --date 2026-10-01` runs from a folder inside a harness, without `--harness`
- **THEN** the task named by that harness's `harness.yaml` gains the update and the command exits 0
- **Cases**: keeps `tests/cases/record/harness-resolved-from-the-working-directory.yaml`

#### Scenario: No harness found
- **WHEN** `gemba record update.md --date 2026-10-01` runs, with no ref, from a folder of the obeya with no `harness.yaml` at or above it and without `--harness`
- **THEN** the command exits 1, says that no harness was found and that outside a harness the task is named by its ref, and changes nothing
- **Cases**: keeps `tests/cases/record/no-harness-found.yaml`

#### Scenario: Task file missing
- **WHEN** the `task` path of `harness.yaml` names a file that no longer exists under the obeya
- **THEN** the command exits 1, names the path, says the task file was not found there, and changes nothing
- **Cases**: keeps `tests/cases/record/task-file-missing.yaml`

#### Scenario: Task named by ref from the obeya
- **WHEN** `update.md` at the obeya root holds one bullet, `SUP-1` was created on `2026-09-30` with `updated_at: 2026-09-30` and has no harness, and `gemba record SUP-1 update.md --date 2026-10-01` runs from `tasks/support`
- **THEN** the task holds the bullet under `### 2026-10-01`, `updated_at` reads `2026-10-01`, `update.md` no longer exists, the output is the task path followed by `updated_at: 2026-09-30 -> 2026-10-01`, and the command exits 0
- **Cases**: modifies `tests/cases/record/task-named-by-ref-from-the-tasks-repo.yaml`, renamed `task-named-by-ref-from-the-obeya.yaml` (its name says obeya; it names its scenario by the new title)

#### Scenario: Unknown ref refused
- **WHEN** `gemba record SUP-9 update.md` runs from the obeya and no task, archived or not, holds `SUP-9`
- **THEN** the command exits 1, says that no task has ref `SUP-9` under `tasks/`, archives included, and changes nothing, the draft included
- **Cases**: modifies `tests/cases/record/unknown-ref-refused.yaml` (its name says obeya)

#### Scenario: Archived task recorded by ref
- **WHEN** `SUP-1` lies under `tasks/support/archive/` and `gemba record SUP-1 update.md --date 2026-10-01` runs from the obeya root
- **THEN** the archived task holds the bullets under `### 2026-10-01`, stays under `archive/`, and the command exits 0
- **Cases**: keeps `tests/cases/record/archived-task-recorded-by-ref.yaml`

#### Scenario: Ref of the harness's task accepted
- **WHEN** `update.md` at the root of the harness of `SUP-1` holds one bullet and `gemba record SUP-1 update.md --date 2026-10-01` runs inside that harness
- **THEN** the task gains the update exactly as without the ref, the draft of the harness root is deleted, and the command exits 0
- **Cases**: keeps `tests/cases/record/ref-of-the-harness-task-accepted.yaml`

#### Scenario: Another ref refused inside a harness
- **WHEN** `SUP-1` and `SUP-2` exist and `gemba record SUP-2 update.md --date 2026-10-01` runs inside the harness of `SUP-1`
- **THEN** the command exits 1, names `SUP-2` and `SUP-1`, says that `SUP-2` is recorded from the obeya or from its own harness, and changes nothing, the draft included
- **Cases**: modifies `tests/cases/record/another-ref-refused-inside-a-harness.yaml` (the message it expects names the obeya)

### Requirement: The draft is written by the agent and consumed by the command
The `<file>` argument SHALL be a path relative to the root of the place the record is
made: inside a harness, relative to the harness root and inside the harness; from the
obeya, relative to the obeya root and directly in that root, so that neither
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
- **Cases**: keeps `tests/cases/record/draft-consumed.yaml`

#### Scenario: Invalid draft refused
- **WHEN** the draft does not exist, or is outside the harness, or holds no bullet, or holds a non-blank line that is neither a bullet nor an indented continuation
- **THEN** the command exits 1, names the rule the draft breaks, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/invalid-draft-refused.yaml`

#### Scenario: Draft out of place refused in the obeya
- **WHEN** `gemba record SUP-1 <file>` runs from the obeya with a draft of valid bullets at `../outside.md`, outside the obeya, or at `tasks/support/update.md`, or at `harnesses/support/2026-09-30-SUP-1-login-fails/update.md`
- **THEN** the command exits 1, says that the draft does not lie directly in the root of the obeya, and changes nothing, the draft included
- **Cases**: modifies `tests/cases/record/draft-out-of-place-refused-in-the-tasks-repo.yaml`, renamed `draft-out-of-place-refused-in-the-obeya.yaml` (the message it expects names the obeya; its name says obeya; its comment says obeya; it names its scenario by the new title)

### Requirement: The subsection and updated_at are written in one step
The command SHALL write the task file once, with the `### D` subsection added under
`## Updates` in chronological position when the task has none for D, or the bullets
appended after the last line of the existing `### D` subsection, and with `updated_at`
set to the later of its current value and D. The frontmatter SHALL be written again in
its fixed key order with no other value changed, `status` included, and every line of
the body outside the written subsection SHALL be byte for byte what it was. The
command SHALL run no git command: the obeya is committed by a person and the
harness has nothing new to commit. On success it SHALL print the task path relative to
the obeya root, then `updated_at: <old> -> <new>` when the date moved, or
`updated_at: <value> (unchanged)` when it did not.

#### Scenario: First update of a task
- **WHEN** the task body ends with an empty `## Updates` and `gemba record update.md --date 2026-10-01` runs with a draft of two bullets, `updated_at` reading `2026-09-30`
- **THEN** the body ends with `## Updates`, a blank line, `### 2026-10-01`, a blank line and the two bullets, `updated_at` reads `2026-10-01`, and the output is the task path followed by `updated_at: 2026-09-30 -> 2026-10-01`
- **Cases**: keeps `tests/cases/record/first-update-of-a-task.yaml`

#### Scenario: Subsection inserted in chronological position
- **WHEN** the task holds `### 2026-09-30` and `### 2026-10-02` and the update is dated `2026-10-01`
- **THEN** `### 2026-10-01` appears between the two, separated from each by one blank line, and the existing subsections are unchanged
- **Cases**: keeps `tests/cases/record/subsection-inserted-in-order.yaml`

#### Scenario: Bullets merged into an existing subsection
- **WHEN** the task already holds `### 2026-10-01` with one bullet and the update is dated `2026-10-01`
- **THEN** the new bullets follow the existing one under the same heading and no second `### 2026-10-01` heading is written
- **Cases**: keeps `tests/cases/record/bullets-merged-into-existing-subsection.yaml`

#### Scenario: updated_at never moves backwards
- **WHEN** `updated_at` reads `2026-10-02` and the update is dated `2026-09-30`, or `updated_at` reads `2026-09-30` and the update is dated `2026-10-02`
- **THEN** the first leaves `updated_at` at `2026-10-02` and prints `updated_at: 2026-10-02 (unchanged)`, and the second moves it to `2026-10-02` and prints `updated_at: 2026-09-30 -> 2026-10-02`
- **Cases**: keeps `tests/cases/record/updated-at-never-moves-backwards.yaml`

#### Scenario: Only the section and updated_at change
- **WHEN** the task is `blocked`, carries `metadata` with a list value, and its body holds a description, a link line and `## Updates` with an earlier subsection
- **THEN** after recording, `status` still reads `blocked`, the metadata is written as it was, the description, the link line and the earlier subsection are byte for byte what they were, and only the new subsection and `updated_at` differ
- **Cases**: keeps `tests/cases/record/only-the-section-and-updated-at-change.yaml`

#### Scenario: Nothing is committed
- **WHEN** an update is recorded from a harness with one launch commit
- **THEN** the harness repository still has exactly that commit, and the task file in the obeya is modified on disk
- **Cases**: keeps `tests/cases/record/nothing-is-committed.yaml`

### Requirement: Skill contains no configured value
The `gemba-record` skill SHALL contain only the process and SHALL NOT name any
workstream, prefix, metadata field, language or configured rule; what the
bullets must say or how they must be written for one obeya belongs in
`record.rules` of the gemba config.

#### Scenario: Config change without skill change
- **WHEN** a workstream adds a `record.rules` entry such as "name the merge request in every bullet"
- **THEN** the skill needs no edit for the agent to follow it
- **Cases**: keeps the entry `task-recording: Config change without skill change` of `tests/not-automated.yaml`

### Requirement: Recording from the obeya by the agent
From the obeya, the `gemba-record` skill SHALL have the agent record what the
person tells it was done on a task, never the notes of a harness: identify the task by
its ref, distill one to five bullets under the `record` block of its workstream, write
them into `update.md` at the obeya root and run `gemba record <ref> update.md`,
with `--date` when the day is not today. When the task has a harness, the agent SHALL
say that the work of the run is recorded from inside it.

#### Scenario: Agent records work done outside a harness
- **WHEN** the user, in the obeya, tells the agent about a review held today on `SUP-1` and asks to record it
- **THEN** the agent writes `update.md` at the obeya root with bullets of what the user said, runs `gemba record SUP-1 update.md` and relays the result
- **Cases**: modifies the entry `task-recording: Agent records work done outside a harness` of `tests/not-automated.yaml` (its reason says obeya)

#### Scenario: Task with a harness recorded from the obeya
- **WHEN** the user asks, in the obeya, to record a day of a task that has a harness
- **THEN** the agent says that the work of the run is recorded from inside the harness, records only what the user told it, and reads no note of that harness
- **Cases**: modifies the entry `task-recording: Task with a harness recorded from the tasks repo` of `tests/not-automated.yaml` (now `task-recording: Task with a harness recorded from the obeya`)

#### Scenario: Nothing told, nothing recorded
- **WHEN** the user asks, in the obeya, to record a day on a task without saying what was done
- **THEN** the agent asks what was done, and records nothing the user did not tell it
- **Cases**: keeps the entry `task-recording: Nothing told, nothing recorded` of `tests/not-automated.yaml`

### Requirement: The migration mode copies a whole history
`gemba record [<ref>] --from <task file>` SHALL copy the dated history of another task
file, the source, into the task, in one call. The source path SHALL be relative to the
working directory or absolute, and the source SHALL only be read. `--from` SHALL NOT be
given with a draft or with `--date`, since the dates are those of the source; the
command SHALL refuse both, and a run given neither a draft nor `--from`.

#### Scenario: History copied into a new task
- **WHEN** `SUP-1` was created on `2026-09-30` with `updated_at: 2026-09-30`, a description and an empty `## Updates`, the source `old/tasks/support/2026-09-30-SUP-7-login-fails.md` holds `### 2026-09-30`, `### 2026-10-01` and `### 2026-10-02` with their bullets, and `gemba record SUP-1 --from old/tasks/support/2026-09-30-SUP-7-login-fails.md` runs from the obeya root
- **THEN** the body of `SUP-1` is its description, a blank line, `## Updates`, a blank line and the three subsections as the source holds them, `updated_at` reads `2026-10-02`, the source is byte for byte what it was, the output is the task path, `copied: 3 days, 2026-09-30 to 2026-10-02` and `updated_at: 2026-09-30 -> 2026-10-02`, and the command exits 0
- **Cases**: keeps `tests/cases/record/history-copied-into-a-new-task.yaml`

#### Scenario: Draft, date or nothing given with the mode refused
- **WHEN** `gemba record SUP-1 update.md --from <source>` runs from the obeya root, or `gemba record SUP-1 --from <source> --date 2026-10-01`, or `gemba record` with no argument at all
- **THEN** the command exits 1, says that `--from` takes neither a draft nor `--date`, or that a draft or `--from` is needed, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/draft-or-date-with-from-refused.yaml`

### Requirement: The migration moves updated_at and says what it copied
`updated_at` SHALL become the later of its value and the last date copied. On success
the command SHALL print the task path relative to the obeya root, then
`copied: <N> days, <first> to <last>`, or `copied: 1 day, <date>` for one, then the
`updated_at` line as a record from a draft prints it.

#### Scenario: Later updated_at kept
- **WHEN** `SUP-1` was created on `2026-09-30`, reads `updated_at: 2026-10-05`, and the source holds only `### 2026-10-01`
- **THEN** `updated_at` still reads `2026-10-05`, and the output is the task path, `copied: 1 day, 2026-10-01` and `updated_at: 2026-10-05 (unchanged)`
- **Cases**: keeps `tests/cases/record/later-updated-at-kept.yaml`
