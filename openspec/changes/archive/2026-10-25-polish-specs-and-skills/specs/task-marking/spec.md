# Spec Delta

## REMOVED Requirements

### Requirement: Mark moves the status of a task
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Mark
moves the status through one rule table", "Mark reports the transition" and "Mark
refuses what it cannot mark".

### Requirement: Marking by the agent
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The agent
marks the task through the command", "The user's words for each status" and "The agent
offers to record before done".

## ADDED Requirements

### Requirement: Mark moves the status through one rule table
`gemba mark <ref> <status> [--date YYYY-MM-DD]` SHALL set the task's `status` to one
of `open`, `in-progress`, `blocked` and `done` through one rule table: a move to
`done` sets `done_at` to the date of the transition, leaving `done` removes it, and
`updated_at` moves to the later of its value and that date. When the status is already
the one given, the command SHALL write nothing, say the status was left as it was, and
exit 0. The frontmatter SHALL keep its key order and the body every byte.

#### Scenario: Task leaves done
- **WHEN** a `done` task with `done_at: 2026-10-01` is marked `open`, or marked `in-progress`
- **THEN** its frontmatter has no `done_at` key, `status` reads the destination, the output holds `done_at: removed`, and the body is unchanged
- **Cases**: keeps `tests/cases/mark/task-leaves-done.yaml`

#### Scenario: Task marked blocked and back
- **WHEN** an `in-progress` task is marked `blocked`, and then marked `in-progress` again
- **THEN** each run rewrites `status` to the destination, `done_at` never appears, and `updated_at` moves to the date of each transition
- **Cases**: keeps `tests/cases/mark/task-marked-blocked.yaml`

#### Scenario: Same status left as it was
- **WHEN** a `blocked` task is marked `blocked`
- **THEN** the command exits 0, the output says `status: blocked, left as it was`, and the tree is unchanged
- **Cases**: keeps `tests/cases/mark/same-status-left-as-it-was.yaml`

### Requirement: Mark reports the transition
`gemba mark` SHALL resolve the task with that ref anywhere under `tasks/`, archives
included, and on success print the task path relative to the obeya root,
`status: <old> -> <new>`, `done_at: <date>` or `done_at: removed` when `done_at`
changed, and `updated_at: <old> -> <new>` or `updated_at: <value> (unchanged)`.

#### Scenario: Task marked done
- **WHEN** `gemba mark SUP-1 done --date 2026-10-03` runs on an `in-progress` task with `updated_at: 2026-10-01`
- **THEN** its frontmatter reads `status: done`, `updated_at: 2026-10-03` and `done_at: 2026-10-03` in that order before `metadata`, the body is unchanged, and the output holds the path, `status: in-progress -> done`, `done_at: 2026-10-03` and `updated_at: 2026-10-01 -> 2026-10-03`
- **Cases**: keeps `tests/cases/mark/task-marked-done.yaml`

### Requirement: Mark refuses what it cannot mark
The command SHALL refuse, writing nothing, when no task has that ref, when the status
is not one of the four, or when the task is archived, saying then that the file must
be moved out of `archive/` first, reporting every problem in one message and exiting
1.

#### Scenario: Invalid status refused
- **WHEN** the status given is `closed`
- **THEN** the command exits 1, names `closed` and the four allowed values, and writes nothing
- **Cases**: keeps `tests/cases/mark/invalid-status-refused.yaml`

#### Scenario: Unknown ref refused
- **WHEN** no task under `tasks/` has the ref given
- **THEN** the command exits 1, reports that no task has that ref, and writes nothing
- **Cases**: keeps `tests/cases/mark/unknown-ref-refused.yaml`

#### Scenario: Archived task refused
- **WHEN** the task with that ref is under an `archive/` folder
- **THEN** the command exits 1, says the task is archived and that it must be moved out of `archive/` before it is marked, and writes nothing
- **Cases**: keeps `tests/cases/mark/archived-task-refused.yaml`

### Requirement: The agent marks the task through the command
The `gemba-mark` skill SHALL have the agent, from the obeya or a harness, identify the
task by its ref, asking when the request is ambiguous, read the `mark` block of its
workstream and follow its `rules` and `context`, run `gemba mark <ref> <status>`, with
`--date` only when the user names a past day, relay the output and stop. It SHALL
forbid editing the frontmatter by hand.

#### Scenario: Agent follows the verb's rules
- **WHEN** workstream `support` declares `mark.rules` containing "before done, confirm the client was told"
- **THEN** the agent follows that rule before running the command for a `support` task
- **Cases**: keeps the entry `task-marking: Agent follows the verb's rules` of `tests/not-automated.yaml`

#### Scenario: Config change without skill change
- **WHEN** a `mark` rule is added, changed or removed in the gemba config
- **THEN** the agent's behaviour changes accordingly without any change to the skill
- **Cases**: keeps the entry `task-marking: Config change without skill change` of `tests/not-automated.yaml`

### Requirement: The user's words for each status
The skill SHALL map the user's words to one status: finished, completed, closed or
done is `done`; stuck, waiting or blocked is `blocked`; reopen, or any request to
bring back a `done` task that does not say the work resumes now, is `open`;
continuing, resuming or working on it now is `in-progress`.

#### Scenario: Agent marks a task
- **WHEN** the user says a task is finished, blocked or back on
- **THEN** the agent runs `gemba mark` with the ref and the mapped status and relays the status, `done_at` and `updated_at` lines
- **Cases**: keeps the entry `task-marking: Agent marks a task` of `tests/not-automated.yaml`

#### Scenario: Reopen defaults to open
- **WHEN** the user asks to reopen a `done` task and does not say the work resumes now
- **THEN** the agent marks it `open`; when the user says they continue now, the agent marks it `in-progress`
- **Cases**: keeps the entry `task-marking: Reopen defaults to open` of `tests/not-automated.yaml`

### Requirement: The agent offers to record before done
From inside a harness, before marking a task `done`, the skill SHALL have the agent
check whether the current day is recorded in the task and offer to record it first,
marking the task whatever the user answers.

#### Scenario: Record before done
- **WHEN** inside a harness the user asks to mark the task done and the day has notes that are not recorded in the task
- **THEN** the agent offers to record the day first and marks the task done whatever the answer
- **Cases**: keeps the entry `task-marking: Record before done` of `tests/not-automated.yaml`
