# Spec Delta

## MODIFIED Requirements

### Requirement: Where the record is made
`gemba record [<ref>] <file> [--date YYYY-MM-DD]`, or `gemba record [<ref>] --from
<task file>` as the migration mode requirement says, SHALL act on one task, from inside
a harness or from the tasks repo. The command runs inside a harness when `--harness`
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
the task is named by its ref, or when no task or several tasks hold the ref. The
requirements on the draft, its date and its subsection apply to a record made from a
draft.

#### Scenario: Harness resolved from the working directory
- **WHEN** `gemba record update.md --date 2026-10-01` runs from a folder inside a harness, without `--harness`
- **THEN** the task named by that harness's `harness.yaml` gains the update and the command exits 0
- **Cases**: keeps `tests/cases/record/harness-resolved-from-the-working-directory.yaml`

#### Scenario: No harness found
- **WHEN** `gemba record update.md --date 2026-10-01` runs, with no ref, from a folder of the tasks repo with no `harness.yaml` at or above it and without `--harness`
- **THEN** the command exits 1, says that no harness was found and that outside a harness the task is named by its ref, and changes nothing
- **Cases**: keeps `tests/cases/record/no-harness-found.yaml`

#### Scenario: Task file missing
- **WHEN** the `task` path of `harness.yaml` names a file that no longer exists under the tasks repo
- **THEN** the command exits 1, names the path, says the task file was not found there, and changes nothing
- **Cases**: keeps `tests/cases/record/task-file-missing.yaml`

#### Scenario: Task named by ref from the tasks repo
- **WHEN** `update.md` at the tasks repo root holds one bullet, `SUP-1` was created on `2026-09-30` with `updated_at: 2026-09-30` and has no harness, and `gemba record SUP-1 update.md --date 2026-10-01` runs from `tasks/support`
- **THEN** the task holds the bullet under `### 2026-10-01`, `updated_at` reads `2026-10-01`, `update.md` no longer exists, the output is the task path followed by `updated_at: 2026-09-30 -> 2026-10-01`, and the command exits 0
- **Cases**: keeps `tests/cases/record/task-named-by-ref-from-the-tasks-repo.yaml`

#### Scenario: Unknown ref refused
- **WHEN** `gemba record SUP-9 update.md` runs from the tasks repo and no task, archived or not, holds `SUP-9`
- **THEN** the command exits 1, says that no task has ref `SUP-9` under `tasks/`, archives included, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/unknown-ref-refused.yaml`

#### Scenario: Archived task recorded by ref
- **WHEN** `SUP-1` lies under `tasks/support/archive/` and `gemba record SUP-1 update.md --date 2026-10-01` runs from the tasks repo root
- **THEN** the archived task holds the bullets under `### 2026-10-01`, stays under `archive/`, and the command exits 0
- **Cases**: keeps `tests/cases/record/archived-task-recorded-by-ref.yaml`

#### Scenario: Ref of the harness's task accepted
- **WHEN** `update.md` at the root of the harness of `SUP-1` holds one bullet and `gemba record SUP-1 update.md --date 2026-10-01` runs inside that harness
- **THEN** the task gains the update exactly as without the ref, the draft of the harness root is deleted, and the command exits 0
- **Cases**: keeps `tests/cases/record/ref-of-the-harness-task-accepted.yaml`

#### Scenario: Another ref refused inside a harness
- **WHEN** `SUP-1` and `SUP-2` exist and `gemba record SUP-2 update.md --date 2026-10-01` runs inside the harness of `SUP-1`
- **THEN** the command exits 1, names `SUP-2` and `SUP-1`, says that `SUP-2` is recorded from the tasks repo or from its own harness, and changes nothing, the draft included
- **Cases**: keeps `tests/cases/record/another-ref-refused-inside-a-harness.yaml`

## ADDED Requirements

### Requirement: The migration mode copies a whole history
`gemba record [<ref>] --from <task file>` SHALL copy the dated history of another task
file, the source, into the task, in one call. The source path SHALL be relative to the
working directory or absolute, and the source SHALL only be read. `--from` SHALL NOT be
given with a draft or with `--date`, since the dates are those of the source; the
command SHALL refuse both, and a run given neither a draft nor `--from`.

#### Scenario: History copied into a new task
- **WHEN** `SUP-1` was created on `2026-09-30` with `updated_at: 2026-09-30`, a description and an empty `## Updates`, the source `old/tasks/support/2026-09-30-SUP-7-login-fails.md` holds `### 2026-09-30`, `### 2026-10-01` and `### 2026-10-02` with their bullets, and `gemba record SUP-1 --from old/tasks/support/2026-09-30-SUP-7-login-fails.md` runs from the tasks repo root
- **THEN** the body of `SUP-1` is its description, a blank line, `## Updates`, a blank line and the three subsections as the source holds them, `updated_at` reads `2026-10-02`, the source is byte for byte what it was, the output is the task path, `copied: 3 days, 2026-09-30 to 2026-10-02` and `updated_at: 2026-09-30 -> 2026-10-02`, and the command exits 0
- **Cases**: adds `tests/cases/record/history-copied-into-a-new-task.yaml`

#### Scenario: Draft, date or nothing given with the mode refused
- **WHEN** `gemba record SUP-1 update.md --from <source>` runs from the tasks repo root, or `gemba record SUP-1 --from <source> --date 2026-10-01`, or `gemba record` with no argument at all
- **THEN** the command exits 1, says that `--from` takes neither a draft nor `--date`, or that a draft or `--from` is needed, and changes nothing, the draft included
- **Cases**: adds `tests/cases/record/draft-or-date-with-from-refused.yaml`

### Requirement: The source is a task with a valid history
The source SHALL exist, hold UTF-8 text and read as a task under the reading rules of
the task file format; only then is its history checked. Its `## Updates` SHALL follow
the rules of the updates section structure, hold at least one `### YYYY-MM-DD`
subsection and no non-blank line before the first one, and every date SHALL fall on or
after the creation date of the task and not after today. Every broken rule SHALL be
reported, each naming the source and the heading or line, not only the first.

#### Scenario: Source not a task refused
- **WHEN** the source does not exist, or its frontmatter says `ref: SUP-8` while its filename says `SUP-7`
- **THEN** the command exits 1, names the source and says it does not exist or is not a valid task with the rule it breaks, and changes nothing
- **Cases**: adds `tests/cases/record/source-not-a-task-refused.yaml`

#### Scenario: History of the source refused
- **WHEN** the `## Updates` of the source holds a line of text before its first date heading, a `### Monday` heading, and `### 2026-10-02` before `### 2026-10-01`; or holds no date heading at all
- **THEN** the command exits 1 and names, in one message, the line before the first date, `### Monday` and the heading out of order; or says that the source holds no history to copy; and changes nothing
- **Cases**: adds `tests/cases/record/source-history-refused.yaml`

#### Scenario: Dates outside the life of the task refused
- **WHEN** the task was created on `2026-09-30` and the source holds `### 2026-09-01` and `### 2999-01-01`
- **THEN** the command exits 1, names both headings, says that the first is before the creation date of the task and the second after today, and changes nothing
- **Cases**: adds `tests/cases/record/history-dates-outside-the-task-refused.yaml`

### Requirement: Only a task with an empty Updates section receives a history
The `## Updates` section of the task SHALL follow the rules of the updates section
structure and hold no non-blank line, so that the mode fills a fresh task and a second
run never writes a history twice. The command SHALL report the problems of the task
and those of the source in one message and refuse, changing nothing, when there is
any.

#### Scenario: Task with updates refused
- **WHEN** `SUP-1` already holds `### 2026-10-01` and the source holds `### 2999-01-01`
- **THEN** the command exits 1, says in one message that the `## Updates` of `SUP-1` is not empty and that `### 2999-01-01` is after today, and changes nothing
- **Cases**: adds `tests/cases/record/task-with-updates-refused.yaml`

### Requirement: The history is written as it was
The command SHALL write the task file once: after its `## Updates` heading and one blank
line, the lines of the source from its first date heading to the end of its body, line
endings made LF and blank lines at the end dropped, with none of the rules of a draft
applied, the file ending with one newline. Every line before `## Updates` and every
frontmatter value other than `updated_at` SHALL be as it was, and the command SHALL run
no git command.

#### Scenario: Hand edits copied as they are
- **WHEN** the source, with CRLF line endings, holds `### 2026-09-30` followed with no blank line by a bullet, then a line that is neither a bullet nor a continuation, and a `#### Call` sub-heading
- **THEN** the `## Updates` of the task holds those lines exactly as the source does, with LF line endings, and the command exits 0
- **Cases**: adds `tests/cases/record/hand-edits-copied-as-they-are.yaml`

### Requirement: The migration moves updated_at and says what it copied
`updated_at` SHALL become the later of its value and the last date copied. On success
the command SHALL print the task path relative to the tasks repo root, then
`copied: <N> days, <first> to <last>`, or `copied: 1 day, <date>` for one, then the
`updated_at` line as a record from a draft prints it.

#### Scenario: Later updated_at kept
- **WHEN** `SUP-1` was created on `2026-09-30`, reads `updated_at: 2026-10-05`, and the source holds only `### 2026-10-01`
- **THEN** `updated_at` still reads `2026-10-05`, and the output is the task path, `copied: 1 day, 2026-10-01` and `updated_at: 2026-10-05 (unchanged)`
- **Cases**: adds `tests/cases/record/later-updated-at-kept.yaml`
