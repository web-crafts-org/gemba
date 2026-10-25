# Proposal

## Why

An obeya can be kept by one person or shared by a team, but today every task of an
obeya sits in one folder per workstream, with one counter per prefix and no notion of
who a task belongs to. Two people sharing one would compete for the same ref numbers
and could write each other's tasks by accident, and git would see the same files
change on both sides. The shared and personal configs (`personal-config-layer`), the
migration of tasks into a new obeya (`task-migration`) and the word *obeya*
(`obeya-vocabulary`) are in place, so team mode can now be added without touching
individual use.

## What Changes

- **A team in the shared config.** `gemba.yaml` may declare `team`, a map keyed by the
  folder name of each member, each with `initials` (uppercase letters, unique across
  the team) and `active` (`true` when absent). A member who leaves is marked
  `active: false`, never removed, so their initials and refs are never reused. Without
  `team`, an obeya works exactly as today.
- **The member of a clone.** `gemba.local.yaml` may declare `me`, the member the clone
  belongs to, which must name a member of the team. `team` lives only in the shared
  config and `me` only in the personal one.
- **One writer per folder.** With a team, every task lives under
  `tasks/<member>/<workstream>/`, archives included, and its owner is the member whose
  folder holds it. Refs read `<INITIALS>-<PREFIX>-<N>`, such as `MR-SUP-3`, with one
  counter per member and prefix, so two members never compete for a number. `gemba
  create` writes into the folder of `me`.
- **The write guard.** With a team, `gemba create`, `record`, `mark`, `set`, `archive`
  and `harness launch` refuse when the clone declares no `me` or names an inactive
  member, and `record`, `mark`, `set`, `archive` and `harness launch` refuse a task
  whose owner is not `me`, naming its owner, with every other problem of the call.
  Every member's tasks can still be read, listed, reported and found by ref. The guard
  stops accidents, not a determined person: access control belongs to the git host.
- **Listing and reporting by owner.** With a team, a listing record carries `owner`
  after `path`, `gemba list` and `gemba report` take a repeatable `--owner <member>`
  filter that restricts the scan to those folders, and `gemba report --by owner`
  groups by member in the order of the team. Without a team, a record keeps its current
  keys, and `--owner` and `--by owner` are refused, saying the obeya declares no team.
- **A team starts in a new obeya.** When the shared config declares a team while
  `tasks/` holds the workstream folders of an obeya without one, every command refuses,
  naming those folders and pointing to the `gemba-migrate` skill. No obeya is converted
  in place.
- **Config commands.** `gemba config check` prints a `team:` line and, when declared,
  a `me:` line; `gemba config show` prints `team` and `me` in an obeya with a team.
- **BREAKING**: `owner` becomes a reserved metadata field name, beside `workstream` and
  `status`, since a report groups by it. A config that declares a field named `owner`
  is refused. It lands in the unreleased 0.3.0 that already breaks `gemba.yaml`.
- **Skills.** `gemba-init` asks, after the obeya's name, whether a team shares it, and
  then its members and who the person is; in an obeya with a team and a clone without
  `gemba.local.yaml`, it configures that clone only (`me`, the IDE, the repositories
  folder). `gemba-config` documents `team` and `me` and maintains the members.
  `gemba-list` and `gemba-report` read "my tasks" and "what did I do" as the tasks of
  `me` in an obeya with a team. `gemba-create` never creates a task for another
  member, and the write skills relay a refusal of another member's task without
  editing its file.
- **Docs.** `AGENTS.md` gains *team*, *member* and *owner*; the README a section on
  sharing an obeya; `SECURITY.md` says the write guard is not access control;
  `CHANGELOG.md` records the additions and the break.

Not in this change: the parent of a task (`task-relations`), and the commits, pushes,
hooks and `gemba sync` of `git-control`, with the git preferences the `gemba-init`
interview will ask then.

## Capabilities

### New Capabilities

- `task-ownership`: the owner of a task in an obeya with a team, the member of a
  clone, and the guard that lets only the owner write a task.

### Modified Capabilities

- `gemba-config`: the `team` key of the shared config and `me` of the personal one,
  their layers, the refusal of a team over the layout of an obeya without one, and
  `owner` as a reserved field name.
- `config-maintenance`: `check` summarizes the team and `show` prints it; the
  `gemba-config` skill maintains the members.
- `task-file-format`: the location of a task and the form of its ref in an obeya with a
  team.
- `task-creation`: the ref is allocated per member and prefix, in the folder of `me`.
- `task-listing`: the scan of the members' folders, `owner` in a record, the `--owner`
  filter, and "my tasks" read by the agent.
- `task-reporting`: grouping by `owner`, and a member's report covering `me` by
  default.
- `repo-initialization`: the `gemba-init` interview asks about the team, and
  configures the clone of a member joining an obeya with a team.

## Impact

- New domain module `src/gemba/team.py`: the members, who may write a task, and the
  layout check.
- `src/gemba/config.py`: parsing and validating `team` and `me`, their layers, the
  layout refusal. `src/gemba/metadata.py`: `owner` reserved.
- `src/gemba/tasks.py`: the filename pattern, the owner of a task, the scan of
  member folders, allocation per member, the archive destination.
- Adapters: `create`, `record`, `mark`, `set`, `archive`, `harness` (launch), `list`,
  `report`, `config`, and `selection.py`; `src/gemba/report.py` for the owner grouping.
- Skills: `gemba-init`, `gemba-config`, `gemba-list`, `gemba-report`, `gemba-create`,
  `gemba-record`, `gemba-mark`, `gemba-set`, `gemba-archive`, `gemba-harness`.
- Tests: new cases under `config/`, `create/`, `list/`, `report/`, `mark/`, `set/`,
  `record/`, `archive/` and `harness/`, one changed case for the reserved names, new
  entries in `tests/not-automated.yaml`, and unit tests of `team.py`, `config.py` and
  `tasks.py`. No existing case changes its expectation: an obeya without a team behaves
  as before.
- Docs: `README.md`, `AGENTS.md`, `SECURITY.md`, `CHANGELOG.md`. No new dependency.
