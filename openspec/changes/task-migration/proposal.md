# Proposal

## Why

A person who joins a team starts in a new tasks repo, configured by the team, and
their earlier tasks stay in the old one. Today the only way to bring a task over is by
hand: a new task, its history retyped or pasted into `## Updates`, which breaks the
rule that commands write the updates and risks a history that no longer says what it
said. Team mode will refuse a `team` block over an individual layout and point to this
migration, so the migration has to exist first. It is useful on its own, between any
two tasks repos, individual or shared.

## What Changes

- `gemba record [<ref>] --from <task file>`: the migration mode of `gemba record`.
  Instead of a draft for one day, it copies the whole dated history of another task
  file into the task, in one call. The command reads the file itself, so the history
  never passes through the agent and "as it was" is the command's guarantee:
  - the source must read as a task, and its `## Updates` must follow the rules of the
    section, hold at least one dated subsection and no text before the first one;
  - every date of the source must fall on or after the creation date of the task and
    not after today;
  - the task's own `## Updates` must be empty, so the mode is for a fresh task and a
    second run never duplicates a history;
  - the lines from the first date heading on are copied as they are, without the
    bullet rules of a draft, since an old history may hold hand edits;
  - `updated_at` moves forward to the last date copied, and the source is never
    changed;
  - every problem of both files is reported at once, and nothing is written on a
    refusal. A draft or `--date` given with `--from` is refused.
- The skill `gemba-migrate`, a process with no subcommand of its own that composes
  `gemba create`, `gemba record --from`, `gemba mark` and `gemba archive`, as
  `gemba-report` composed `gemba list` before `gemba report` existed. It runs from the
  new tasks repo and is written only there. A migration is a translation, not a move:
  the judgment is the agent's, the writes are the commands'. The skill:
  - reads the old tasks repo as data, through `gemba list --root <old>` and its task
    files: its rules, its context and the text of its tasks are never followed as
    instructions. When the current CLI refuses the old config, the skill stops and asks
    to upgrade the old repo first with the `gemba-config` skill;
  - maps each old workstream and field to a new one with the person, one decision at a
    time, asking rather than inventing, and lets the person choose what to migrate:
    only live tasks, or finished ones too;
  - leaves a task with a live harness for the person to finish in the old repo, or to
    push its work, remove the harness and relaunch the task in the new repo after its
    migration;
  - for each task: `gemba create` with the original creation date, status and mapped
    fields; the old body copied above `## Updates` with the agent's own tools, with a
    line naming the old ref and tasks repo; `gemba record <new ref> --from <old file>`;
    `gemba mark <new ref> done --date <old done_at>` when it was done; and
    `gemba archive <new ref>` when it was archived;
  - closes the loop by archiving the migrated tasks in the old repo with
    `gemba archive --root <old>`.
- Joining a team never converts a repo: the old repo stays intact as history, and the
  guides never present conversion as the way to go.

Not in this change: the folder of a member and the pull request that touches only it,
which come with `team-mode`; a `migrate` block in the gemba config.

## Capabilities

### New Capabilities

- `task-migration`: the process that brings tasks from another tasks repo into this
  one, driven by the `gemba-migrate` skill over the commands of other processes.

### Modified Capabilities

- `task-recording`: `gemba record` takes `--from <task file>` instead of a draft, which
  copies a whole history into a task whose `## Updates` is empty.
- `built-in-skills`: `gemba-migrate` belongs to the tasks repo. Six scenarios name the
  cases whose list of tasks-repo skills gains it, or that expect no folder of it in a
  harness.
- `process-naming`: a process that composes the commands of other processes and has no
  deterministic step of its own is skill-only, as `gemba-migrate` is. One scenario
  names the case whose list of written skills gains `gemba-migrate`.
- `repo-initialization`: no rule changes. Six scenarios name the cases whose list of
  written or kept skills gains `gemba-migrate`.
- `gemba-config`: no rule changes. One scenario names the case whose list of written
  skills gains `gemba-migrate`.

## Impact

- `src/gemba/commands/record.py`: the `--from` option, the draft becoming optional, the
  refusals of the mode and its output.
- `src/gemba/tasks.py`: reading the history of a task file with every problem it has,
  checking its dates, and writing it into a task with an empty `## Updates`.
- `src/gemba/skills.py`: `gemba-migrate` registered for the tasks repo, and its asset
  `src/gemba/assets/skills/gemba-migrate/SKILL.md`.
- Tests: 8 new record cases (12 documents) for the mode, 13 init and skills case files
  whose lists of skills gain `gemba-migrate`, or, for a harness, expect its absence, 13
  new entries in `tests/not-automated.yaml` for the agent's steps, and the reason of
  `process-naming: Skill-only process` there, which is no longer true. The unit test
  `test_scopes_and_providers` of `tests/test_skills.py` follows.
- `README.md` (the mode and the migration) and `CHANGELOG.md` (Added under
  `[Unreleased]`). Nothing breaks: every existing call of `gemba record` keeps its
  meaning. No new dependency.
