# Proposal

## Why

`gemba record` only runs inside a harness, so work done outside one, such as a meeting
or a quick review, has no way into `## Updates`. To record it, a person launches a
harness only to record a day, or edits the task by hand, which breaks the rule that
commands write the updates. Recording a task by its ref from the tasks repo closes that
gap. The migration of tasks between two tasks repos builds on it, and so does team
mode, which points a person to that migration. So recording from the tasks repo goes
first.

## What Changes

- `gemba record [<ref>] <file> [--date YYYY-MM-DD]`: outside a harness, the task is
  named by its ref, as `gemba mark` and `gemba set` name it, archives included. Inside
  a harness the ref stays optional: when given, it must be the ref of the harness's
  task, and any other ref is refused, saying that task is recorded from the tasks repo
  or from its own harness. Outside a harness, a run without a ref is refused, saying
  the task is named by its ref there.
- The draft is relative to the root of the place the record is made, the harness root
  or the tasks repo root. Inside a harness it lies anywhere in it, as today. From the
  tasks repo it lies directly in the root, so that a task file or the draft of a run is
  never consumed as a draft. Every other rule of the command is the same in both
  places: the bullets, the date, the subsection, `updated_at`, the deleted draft, no
  git.
- `gemba init` adds `/update.md` to the lines of the `.gitignore` it writes and
  completes, so that a draft left at the tasks repo root by a refusal never reaches a
  commit. An earlier tasks repo gets the line by running `gemba init` again.
- The `gemba-record` skill is written into the tasks repo as well as into each harness.
  From the tasks repo, the agent records what the person tells it, such as a meeting or
  a review. It writes `update.md` at the tasks repo root and runs
  `gemba record <ref> update.md`. When the task has a harness, it says the work of the
  run is recorded from inside the harness, and it does not read the notes of that
  harness. Inside a harness nothing changes: the notes of the date stay the only source.
- The `gemba-report` skill points a gap to the `gemba-record` skill from either place:
  inside the task's harness for the work of its run, from the tasks repo for work done
  outside one. It no longer sends the person to launch a harness only to record.

Not in this change: the migration mode, `gemba record <ref> --from <task file>`, which
is the next change, `task-migration`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-recording`: the command runs from a harness or from the tasks repo, naming the
  task by ref there. The draft is relative to the root of the place, and from the
  tasks repo it lies directly in its root. The agent records from the tasks repo what
  the person says.
- `built-in-skills`: `gemba-record` belongs to both the tasks repo and the harness.
  Four scenarios name the cases whose list of tasks-repo skills gains `gemba-record`.
- `repo-initialization`: the `.gitignore` of the scaffold holds `/update.md` as a third
  line, and `gemba init` appends it to an earlier one.
- `task-reporting`: a gap is recorded with the `gemba-record` skill, inside the task's
  harness or from the tasks repo.
- `process-naming`: no rule changes. One scenario names the case whose list of written
  skills gains `gemba-record`.
- `gemba-config`: no rule changes. One scenario names the case whose list of written
  skills gains `gemba-record`.

## Impact

- `src/gemba/commands/record.py`: the optional ref, the choice between the harness and
  the tasks repo, and the draft checked against the root of the place. The rules about
  where the record is made and where the draft may lie move to a domain module,
  `tasks.py`.
- `src/gemba/skills.py` (`gemba-record` becomes `both`) and `src/gemba/repo.py` (a
  third ignored line).
- Skills `gemba-record` (a second path, from the tasks repo, and a new description) and
  `gemba-report` (where a gap is recorded).
- Tests: 6 new record cases (8 documents) and 1 new init case,
  `record/no-harness-found.yaml` modified, 11 init and skills cases whose output or
  `.gitignore` changes, `skills/every-registered-skill-is-written.yaml` gaining
  `gemba-record`, and 4 new entries in `tests/not-automated.yaml` for the agent's
  steps. The unit tests
  `GitignoreTest` of `tests/test_repo.py` and `test_scopes_and_providers` of
  `tests/test_skills.py` follow.
- `README.md` (recording from the tasks repo) and `CHANGELOG.md` (Added and Changed
  entries under `[Unreleased]`). Nothing breaks: every existing call of
  `gemba record <file>` inside a harness keeps its meaning. No new dependency.
