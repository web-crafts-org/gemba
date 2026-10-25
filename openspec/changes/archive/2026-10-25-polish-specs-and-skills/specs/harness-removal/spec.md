# Spec Delta

## REMOVED Requirements

### Requirement: Remove deletes the harness of a task
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Remove
finds the harness of a task", "Remove shows the manifest of the run" and "Remove
deletes the run with yes".

### Requirement: Remove refuses an unsafe deletion
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "What
remove checks before deleting", "Remove reports every failed check" and "Force
discards the pending work".

### Requirement: Removal confirmed by the agent
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The agent
confirms a removal in the chat", "The agent names what the removal deletes" and "The
agent forces only after a confirmed list".

## ADDED Requirements

### Requirement: Remove finds the harness of a task
`gemba harness remove <ref> [--yes] [--force]` SHALL run from the obeya, resolve the
task with that ref anywhere under `tasks/`, archives included, and take its harness at
`harnesses/<workstream>/<stem>/` under the obeya root. It SHALL refuse, deleting
nothing, when no task has that ref, when no folder exists at the harness path, or when
the folder holds no `harness.yaml`.

#### Scenario: No harness to remove
- **WHEN** no task has the ref given, or the task exists but no folder exists at its harness path
- **THEN** the command exits 1, says which of the two it is, and deletes nothing
- **Cases**: keeps `tests/cases/harness/no-harness-to-remove.yaml`

#### Scenario: Folder without harness config refused
- **WHEN** a folder exists at the harness path but holds no `harness.yaml`
- **THEN** the command exits 1, says the folder is not a harness, and deletes nothing, with or without `--yes`
- **Cases**: keeps `tests/cases/harness/folder-without-harness-config-refused.yaml`

### Requirement: Remove shows the manifest of the run
`remove` SHALL print the harness path relative to the obeya root, then a line for each
of `task`, `launched_at`, `notes` and `assets` (their files), `commits` (of the
harness repository), `worktrees` and `uncommitted` (staged, unstaged or untracked
paths of the harness repository), then a `- <path>` line per such path, relative to
the harness root, in git's order. Without `--yes` it SHALL then print
`not removed: pass --yes to delete the harness` and exit 0, changing nothing.

#### Scenario: Manifest shown without deleting
- **WHEN** `gemba harness remove SUP-1` runs for a launched task whose harness holds two filed notes and one asset
- **THEN** the output holds the harness path, `task: tasks/support/2026-09-30-SUP-1-login-fails.md`, `launched_at: <date>`, `notes: 2`, `assets: 1`, `commits: 3`, `worktrees: 0`, `uncommitted: 0` and `not removed: pass --yes to delete the harness`, the tree is unchanged and the exit code is 0
- **Cases**: keeps `tests/cases/harness/manifest-shown-without-deleting.yaml`

#### Scenario: Uncommitted paths listed in the manifest
- **WHEN** the harness of `SUP-1` holds a drafted note `notes/draft.md` never filed and an `update.md` never recorded, and `gemba harness remove SUP-1` runs
- **THEN** the manifest reads `uncommitted: 2` followed by `- notes/draft.md` and `- update.md`, the output ends with `not removed: pass --yes to delete the harness`, the tree is unchanged and the exit code is 0
- **Cases**: keeps `tests/cases/harness/uncommitted-paths-listed-in-the-manifest.yaml`

### Requirement: Remove deletes the run with yes
With `--yes`, `remove` SHALL remove every worktree of the harness from its base
repository and delete the branch checked out in it, delete every branch of the run
left without a worktree in a repository under `repos_dir`, then delete the harness
folder, `task.md` and the uncommitted paths included, print `removed` and exit 0. An
uncommitted path of the harness SHALL NOT refuse the removal. The remotes, the task
file that `task.md` reaches and the obeya's git SHALL NOT be touched.

#### Scenario: Uncommitted paths deleted with the harness
- **WHEN** the harness of `SUP-1` holds a drafted note never filed, an `update.md` never recorded and a modified skill file, and `gemba harness remove SUP-1 --yes` runs
- **THEN** the manifest lists the three paths under `uncommitted: 3`, the harness folder no longer exists, the task file is byte for byte what it was, the output ends with `removed` and the exit code is 0
- **Cases**: keeps `tests/cases/harness/uncommitted-paths-deleted-with-the-harness.yaml`

#### Scenario: Harness removed
- **WHEN** `gemba harness remove SUP-1 --yes` runs for a launched task
- **THEN** the harness folder no longer exists, the task file is byte for byte what it was, the output ends with `removed` and the exit code is 0
- **Cases**: keeps `tests/cases/harness/harness-removed.yaml`

#### Scenario: Harness removed with its worktrees
- **WHEN** the harness of `SUP-1` holds worktrees of `nakatomi-web` and `nakatomi-api` with nothing pending and `gemba harness remove SUP-1 --yes` runs
- **THEN** the manifest reads `worktrees: 2` and `uncommitted: 0`, the harness folder no longer exists, neither base repository holds `gemba/nakatomi/SUP-1`, the branches of each `origin` are what they were, the output ends with `removed` and the exit code is 0
- **Cases**: keeps `tests/cases/harness/harness-removed-with-its-worktrees.yaml`

#### Scenario: Orphan branch of the run deleted
- **WHEN** a repository under the `repos_dir` of the personal config holds `gemba/nakatomi/SUP-1` with no worktree and every commit of it on a remote branch, and `gemba harness remove SUP-1 --yes` runs
- **THEN** the branch no longer exists, the harness folder no longer exists and the exit code is 0
- **Cases**: keeps `tests/cases/harness/orphan-branch-of-the-run-deleted.yaml`

#### Scenario: Removed harness relaunched
- **WHEN** a task's harness is removed with `--yes` and `gemba harness launch` runs again for it
- **THEN** a fresh harness is created with one commit, the status of the task is left as it was, and the exit code is 0
- **Cases**: keeps `tests/cases/harness/removed-harness-relaunched.yaml`

### Requirement: What remove checks before deleting
Before deleting, and also when only showing the manifest, `remove` SHALL check that
the working directory is not inside the harness, that the state of the harness
repository can be read, that every folder under `worktrees/` is a worktree with no
uncommitted path and no commit on no remote branch, and that every branch of the run
left without a worktree under `repos_dir` has no such commit. The uncommitted paths of
the harness repository itself are not checked.

#### Scenario: Working directory inside the harness refused
- **WHEN** `remove --yes` runs from a folder inside the harness it names
- **THEN** the command exits 1, says the working directory is inside the harness, and deletes nothing
- **Cases**: keeps `tests/cases/harness/working-directory-inside-the-harness-refused.yaml`

### Requirement: Remove reports every failed check
When a check fails, or the state of a worktree cannot be read, `remove` SHALL print
the manifest, then `harness not removed:` and one line per problem, naming each
worktree with its numbers of uncommitted paths and unpushed commits, each orphan
branch with its repository and unpushed commits, and each folder that is not a
worktree, and exit 1, deleting nothing, with or without `--yes`. When the state of the
harness repository cannot be read, the manifest SHALL read `uncommitted: unknown`.

#### Scenario: Worktree with pending work refused
- **WHEN** `worktrees/nakatomi-web` holds an uncommitted file, or a commit not on any remote branch, and `remove SUP-1 --yes` runs
- **THEN** the output holds the manifest, `harness not removed:` and a line naming `worktrees/nakatomi-web` with the number of uncommitted paths or of unpushed commits, the exit code is 1, and the harness, the worktree and its branch still exist
- **Cases**: keeps `tests/cases/harness/worktree-with-pending-work-refused.yaml`

#### Scenario: Orphan branch with pending work refused
- **WHEN** a repository under the `repos_dir` of the personal config holds `gemba/nakatomi/SUP-1` with no worktree and a commit not on any remote branch, and `remove SUP-1 --yes` runs
- **THEN** the output holds the manifest, `harness not removed:` and a line naming the branch, the repository and the number of unpushed commits, the exit code is 1, and the harness and the branch still exist
- **Cases**: keeps `tests/cases/harness/orphan-branch-with-pending-work-refused.yaml`

#### Scenario: Folder that is not a worktree refused
- **WHEN** a plain folder with a file exists under `worktrees/` and `remove SUP-1 --yes` runs
- **THEN** the output holds the manifest, `harness not removed:` and a line saying the folder is not a worktree, the exit code is 1 and the tree is unchanged
- **Cases**: keeps `tests/cases/harness/folder-that-is-not-a-worktree-refused.yaml`

### Requirement: Force discards the pending work
With `--force`, the checks on worktrees, orphan branches and folders under
`worktrees/` SHALL NOT refuse, and with `--yes --force` the command SHALL discard what
they protect. The checks on the working directory and on the state of the harness
repository SHALL refuse whatever `--force`.

#### Scenario: Pending work discarded with force
- **WHEN** `worktrees/nakatomi-web` holds a commit not on any remote branch and `remove SUP-1 --yes --force` runs
- **THEN** the harness folder no longer exists, the base repository no longer holds `gemba/nakatomi/SUP-1`, the branches of `origin` are what they were, the output ends with `removed` and the exit code is 0
- **Cases**: keeps `tests/cases/harness/pending-work-discarded-with-force.yaml`

#### Scenario: Force does not cover the working directory
- **WHEN** `remove SUP-1 --yes --force` runs from a folder inside the harness it names
- **THEN** the output holds `harness not removed:` and the line saying the working directory is inside the harness, the exit code is 1 and the tree is unchanged
- **Cases**: keeps `tests/cases/harness/force-does-not-cover-the-working-directory.yaml`

### Requirement: The agent confirms a removal in the chat
The `gemba-harness` skill SHALL have the agent, from the obeya, identify the task by
its ref, follow the `harness.remove` block of its workstream, run
`gemba harness remove <ref>` without `--yes` or `--force`, show the manifest, ask for
confirmation in the chat, remind the user to close any IDE window on the folder, and
only after a yes run it with `--yes` and relay the result. A yes in the chat is
enough: the harness is gemba's own data, so no `external-action` note is needed.

#### Scenario: Agent removes a harness
- **WHEN** the user asks to remove, clean up, delete or throw away the harness of a task
- **THEN** the agent shows the manifest, asks, and runs `remove --yes` only after the user says yes
- **Cases**: keeps the entry `harness-removal: Agent removes a harness` of `tests/not-automated.yaml`

#### Scenario: Agent follows the verb's rules
- **WHEN** workstream `support` declares `harness.remove.rules` containing "check the client report was sent before removing"
- **THEN** the agent follows that rule before showing the manifest for a `support` task
- **Cases**: keeps the entry `harness-removal: Agent follows the verb's rules` of `tests/not-automated.yaml`

### Requirement: The agent names what the removal deletes
When the manifest lists uncommitted paths of the harness, the agent SHALL name them
when asking, say they are deleted with the harness, and say what would keep each one,
from a session inside the harness: `gemba harness note` for a draft note,
`gemba record` for an `update.md`. It SHALL NOT file, commit or delete anything in the
harness itself.

#### Scenario: Agent names uncommitted paths before confirming
- **WHEN** the manifest lists uncommitted paths of the harness, such as a drafted note and an `update.md`
- **THEN** the agent names them when asking for the confirmation, says they will be deleted with the harness and how each could be kept, and files, commits or deletes nothing in the harness itself
- **Cases**: keeps the entry `harness-removal: Agent names uncommitted paths before confirming` of `tests/not-automated.yaml`

### Requirement: The agent forces only after a confirmed list
When the command refuses for a worktree, an orphan branch or a folder under
`worktrees/`, the agent SHALL relay every line and say that a push from inside the
harness, through an approved `external-action` note, saves unpushed commits. It SHALL
pass `--force` only after the user confirms, in the chat, that everything listed is to
be discarded, and never on the first run, even when the user asks to force the
removal.

#### Scenario: Agent forces only after confirming the pending list
- **WHEN** the command refuses for a worktree with pending work and the user asks to force the removal
- **THEN** the agent relays the pending list, waits for the user to confirm that list, and only then runs `remove --yes --force`
- **Cases**: keeps the entry `harness-removal: Agent forces only after confirming the pending list` of `tests/not-automated.yaml`
