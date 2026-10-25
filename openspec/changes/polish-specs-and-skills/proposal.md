# Proposal

## Why

Delivering the first four changes of the team plan exposed three frictions. The first
is that `openspec validate --specs` reports 76 warnings, all of them "requirement text
is very long". That noise hides a new warning (obeya-vocabulary added the 76th
unnoticed until the archive) and makes `--strict` unusable on the main specs. The
second is that the `gemba-harness` skill relays a filed note as a plain path, so the
user has to find the file to read it or to set `approved`. The third is that the
`gemba-worktree` skill forbids any look at `repos_dir`, so when a request names a
repository loosely, the agent can only ask for its exact folder name.
`team-mode` comes next, the largest spec change of the plan, and it edits several of
those long requirements, so they are best fixed before it.

## What Changes

- **Requirements under the limit**: each of the 76 requirements longer than 500
  characters, in 19 main specs, is rewritten to 500 or fewer without changing what it
  requires. A requirement that states one behavior is condensed in place, keeping its
  name and its scenarios. One that states several is split into one requirement per
  behavior, its scenarios shared out among them by title. No scenario changes its
  title, so no case changes, except the scenarios the two items below change.
  `openspec validate --specs` then reports no warning, and a new rule in
  `rules.specs` of `openspec/config.yaml` keeps every new or modified requirement
  under the limit.
- **Notes as links**: the `gemba-harness` skill has the agent relay a note it filed or
  resolved as a Markdown link to the file. The link uses the final name the command
  printed, relative to the harness root, which is the folder the IDE opens. The user
  opens the note from the chat, to read it or to set `approved: true`.
- **`gemba worktree list --available`**: a new flag that prints, one per line in name
  order, the repositories `gemba worktree add` accepts: the folders directly under
  `repos_dir` that hold a git repository. It refuses as `add` does when `repos_dir`
  is not declared or is not a folder, prints `no repositories` when none is there,
  and writes nothing.
- **The agent looks the repository up**: the `gemba-worktree` skill has the agent
  take the repositories from the request, `task.md` and the notes, then compare them
  with `gemba worktree list --available`. A name equal to a folder name is used as
  it is. Otherwise the agent asks the user to choose among the repositories that may
  fit, as the options of its question tool (a panel) when it has one, and never
  guesses. The agent still never reads `repos_dir` itself: the command does.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

Requirements shortened, with no change of behavior: `built-in-skills`,
`config-maintenance`, `gemba-config`, `harness-guide`, `harness-launch`,
`harness-removal`, `metadata-setting`, `package-release`, `process-naming`,
`repo-initialization`, `task-archiving`, `task-creation`, `task-file-format`,
`task-listing`, `task-marking`, `task-recording` and `task-reporting`.

Requirements shortened, and behavior that changes:

- `harness-notes`: the agent relays a filed or resolved note as a link, under its
  final name.
- `harness-worktrees`: `gemba worktree list --available` lists the repositories of
  `repos_dir`; the agent looks a repository up through it and asks the user to choose
  when no name matches exactly.

## Impact

- `src/gemba/commands/worktree.py`: the `--available` flag of `list`, over the
  existing `repositories()`; its messages in `src/gemba/worktree.py`.
- Skills `gemba-harness` and `gemba-worktree` (`src/gemba/assets/skills/`); obeyas get
  them with `gemba skills update`.
- `tests/cases/worktree/`: new cases for `--available`; `tests/not-automated.yaml`:
  entries for the new agent scenarios. No existing case changes.
- `openspec/specs/`: 19 specs, through the archive; `openspec/config.yaml`: one rule
  under `rules.specs`.
- `README.md` (the worktree section) and the `[Unreleased]` section of
  `CHANGELOG.md`.
- No breaking change. No new dependency.
