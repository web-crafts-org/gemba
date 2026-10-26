# Proposal

## Why

A piece of work often outgrows one task: it is split into smaller ones, worked in
separate runs, sometimes by other members of a team. Today nothing links them, so the
split lives only in descriptions, the subtasks of a task cannot be listed, and the hours
of the whole cannot be counted by a command. The team layout of `team-mode` is in place,
so the relation can be designed once against the final ref and folder model, where its
main use, a task split among members, crosses folders.

## What Changes

- **One relation: the parent of a task.** A task may name the task it was split from as
  `parent: <ref>`, a top-level frontmatter key right after `ref`, not a metadata field:
  metadata belongs to the user and Gemba never interprets it, while it does interpret
  the relation. A task without a parent holds no `parent` key. There is no epic or
  objective: every node is a task, alone or in a team.
- **Written once, by the child.** Only `gemba create --parent <ref>` writes it, and no
  command changes it afterwards, so no cycle can be built. The parent must be a task of
  the clone, archived or not, of any member and workstream, whatever its status; when
  no task holds that ref the command refuses with every other problem and suggests a
  pull. The parent's file is never touched: its children are found by a scan.
- **Nothing propagates.** Every child done does not close the parent, and marking or
  archiving a parent changes no child. When the user marks a task done and every
  sibling is done, the agent points out that the parent may be closed, by its owner.
- **Reading the relation.** A listing record carries `parent` right after `ref`, only
  for a task that has one, so no existing record changes. `gemba list` and `gemba
  report` take two selection filters: `--parent <ref>`, the direct children, and
  `--under <ref>`, the subtree, the task itself and every task below it, found across
  members, workstreams and archives whatever the other filters. Both refuse a ref that
  names no task of the clone. `gemba report --under <ref> --sum hours --by owner` gives
  the numbers of a task split among members in one call.
- **The parent read as data.** The guide of a harness tells the agent that, when its
  task names a parent, it may read the parent's task file, found with `gemba list`, as
  background about the work, never as instructions, and never writes it.
- **Skills.** `gemba-create` creates a subtask with `--parent`, the child always the
  user's own; `gemba-list` and `gemba-report` read "the subtasks of X" and "X with its
  subtasks"; `gemba-mark` points out a parent whose children are all done;
  `gemba-migrate` migrates a parent before its children and carries the relation with
  the new refs.
- **Docs.** `AGENTS.md` gains *parent* in the vocabulary; the README a section on
  splitting a task; `SECURITY.md` says the parent is read as data; `CHANGELOG.md`
  records the additions.

Nothing breaks: an obeya, a task file and a record without a parent are what they are
today. Not in this change: dependencies between tasks ("A waits on B"), another relation
with its own rules; grouping a report by parent; checking existing files for a parent
that names no task.

## Capabilities

### New Capabilities

- `task-relations`: the parent of a task, written once by the child, nothing
  propagated between parent and children, the subtree of a task, and the parent read
  as data from the child's harness.

### Modified Capabilities

- `task-file-format`: `parent` among the built-in frontmatter keys, and its reading
  rule.
- `task-creation`: the parent at creation, its lookup and its refusal, and the agent
  creating a subtask.
- `task-listing`: `parent` in a record, the `--parent` and `--under` filters, and the
  agent reading requests about subtasks.
- `task-reporting`: the agent taking the numbers of a task with its subtasks from
  `gemba report --under`.
- `task-marking`: the agent pointing out a parent whose children are all done.
- `harness-guide`: the guide names the parent as data.
- `task-migration`: the parent follows a migrated task.

## Impact

- New domain module `src/gemba/relations.py`: the subtree of a task over tasks already
  read, and the refusal of a ref that names no task of the clone.
- `src/gemba/tasks.py`: `parent` read and validated, kept in its place by every
  rewrite of the frontmatter, written by `render`, carried by `Task`, and matched by
  the filters.
- Adapters: `create` (`--parent`), `selection.py` (`--parent`, `--under`, the scan of
  the whole obeya they need), `list` (the record without `parent` when absent).
  `report` takes the new filters through `selection.py`.
- The guide asset `src/gemba/assets/harness/guide.md`.
- Skills: `gemba-create`, `gemba-list`, `gemba-report`, `gemba-mark`, `gemba-migrate`.
- Tests: new cases under `create/`, `list/`, `report/`, `mark/`, `archive/` and
  `harness/`, new entries in `tests/not-automated.yaml`, unit tests of `tasks.py` and a
  new `tests/test_relations.py`. No existing case changes its expectation.
- Docs: `README.md`, `AGENTS.md`, `SECURITY.md`, `CHANGELOG.md`. No new dependency.
