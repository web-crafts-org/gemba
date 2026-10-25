# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Record runs inside a harness`
- TO: `### Requirement: Where the record is made`

## MODIFIED Requirements

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
- **Cases**: keeps `tests/cases/record/harness-resolved-from-the-working-directory.yaml`

#### Scenario: No harness found
- **WHEN** `gemba record update.md --date 2026-10-01` runs, with no ref, from a folder of the tasks repo with no `harness.yaml` at or above it and without `--harness`
- **THEN** the command exits 1, says that no harness was found and that outside a harness the task is named by its ref, and changes nothing
- **Cases**: modifies `tests/cases/record/no-harness-found.yaml` (the message it expects)

#### Scenario: Task file missing
- **WHEN** the `task` path of `harness.yaml` names a file that no longer exists under the tasks repo
- **THEN** the command exits 1, names the path, says the task file was not found there, and changes nothing
- **Cases**: keeps `tests/cases/record/task-file-missing.yaml`

#### Scenario: Task named by ref from the tasks repo
- **WHEN** `update.md` at the tasks repo root holds one bullet, `SUP-1` was created on `2026-09-30` with `updated_at: 2026-09-30` and has no harness, and `gemba record SUP-1 update.md --date 2026-10-01` runs from `tasks/support`
- **THEN** the task holds the bullet under `### 2026-10-01`, `updated_at` reads `2026-10-01`, `update.md` no longer exists, the output is the task path followed by `updated_at: 2026-09-30 -> 2026-10-01`, and the command exits 0
- **Cases**: adds `tests/cases/record/task-named-by-ref-from-the-tasks-repo.yaml`

#### Scenario: Unknown ref refused
- **WHEN** `gemba record SUP-9 update.md` runs from the tasks repo and no task, archived or not, holds `SUP-9`
- **THEN** the command exits 1, says that no task has ref `SUP-9` under `tasks/`, archives included, and changes nothing, the draft included
- **Cases**: adds `tests/cases/record/unknown-ref-refused.yaml`

#### Scenario: Archived task recorded by ref
- **WHEN** `SUP-1` lies under `tasks/support/archive/` and `gemba record SUP-1 update.md --date 2026-10-01` runs from the tasks repo root
- **THEN** the archived task holds the bullets under `### 2026-10-01`, stays under `archive/`, and the command exits 0
- **Cases**: adds `tests/cases/record/archived-task-recorded-by-ref.yaml`

#### Scenario: Ref of the harness's task accepted
- **WHEN** `update.md` at the root of the harness of `SUP-1` holds one bullet and `gemba record SUP-1 update.md --date 2026-10-01` runs inside that harness
- **THEN** the task gains the update exactly as without the ref, the draft of the harness root is deleted, and the command exits 0
- **Cases**: adds `tests/cases/record/ref-of-the-harness-task-accepted.yaml`

#### Scenario: Another ref refused inside a harness
- **WHEN** `SUP-1` and `SUP-2` exist and `gemba record SUP-2 update.md --date 2026-10-01` runs inside the harness of `SUP-1`
- **THEN** the command exits 1, names `SUP-2` and `SUP-1`, says that `SUP-2` is recorded from the tasks repo or from its own harness, and changes nothing, the draft included
- **Cases**: adds `tests/cases/record/another-ref-refused-inside-a-harness.yaml`

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
- **Cases**: keeps `tests/cases/record/draft-consumed.yaml`

#### Scenario: Invalid draft refused
- **WHEN** the draft does not exist, or is outside the harness, or holds no bullet, or holds a non-blank line that is neither a bullet nor an indented continuation
- **THEN** the command exits 1, names the rule the draft breaks, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/invalid-draft-refused.yaml`

#### Scenario: Draft out of place refused in the tasks repo
- **WHEN** `gemba record SUP-1 <file>` runs from the tasks repo with a draft of valid bullets at `../outside.md`, outside the tasks repo, or at `tasks/support/update.md`, or at `harnesses/support/2026-09-30-SUP-1-login-fails/update.md`
- **THEN** the command exits 1, says that the draft does not lie directly in the root of the tasks repo, and changes nothing, the draft included
- **Cases**: adds `tests/cases/record/draft-out-of-place-refused-in-the-tasks-repo.yaml`, one document per path

## ADDED Requirements

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
- **Cases**: adds the entry `task-recording: Agent records work done outside a harness` of `tests/not-automated.yaml`

#### Scenario: Task with a harness recorded from the tasks repo
- **WHEN** the user asks, in the tasks repo, to record a day of a task that has a harness
- **THEN** the agent says that the work of the run is recorded from inside the harness, records only what the user told it, and reads no note of that harness
- **Cases**: adds the entry `task-recording: Task with a harness recorded from the tasks repo` of `tests/not-automated.yaml`

#### Scenario: Nothing told, nothing recorded
- **WHEN** the user asks, in the tasks repo, to record a day on a task without saying what was done
- **THEN** the agent asks what was done, and records nothing the user did not tell it
- **Cases**: adds the entry `task-recording: Nothing told, nothing recorded` of `tests/not-automated.yaml`
