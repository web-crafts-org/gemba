# Spec Delta

## MODIFIED Requirements

### Requirement: Remove deletes the harness of a task
`gemba harness remove <ref> [--yes] [--force]` SHALL run from the tasks repo: it SHALL
resolve the task with that ref anywhere under `tasks/`, archives included, and the
harness at `harnesses/<workstream>/<stem>/` under the tasks repo root. It SHALL
refuse, deleting nothing, when no task has that ref, when no folder exists at the
harness path, or when the folder holds no `harness.yaml`. It SHALL print a manifest of
the run: the harness path relative to the tasks repo root, then one line each for
`task`, `launched_at`, `notes` (the number of files under `notes/`), `assets` (the
number of files under `assets/`), `commits` (the number of commits of the harness
repository), `worktrees` (the number of worktrees under `worktrees/`) and
`uncommitted` (the number of uncommitted paths of the harness repository, staged,
unstaged or untracked), followed by one `- <path>` line per uncommitted path, relative
to the harness root, in the order git reports them. Nothing in the harness repository
is meant to outlive the run, so an uncommitted path SHALL NOT refuse the removal: it is
listed so that the confirmation is given knowing what will be lost, and it is deleted
with the folder. Without `--yes` it SHALL then print
`not removed: pass --yes to delete the harness` and exit 0, leaving the tree as it
was. With `--yes` it SHALL first remove every worktree of the harness from its base
repository and delete the branch checked out in it, delete every branch of the run
left in a repository under `repos_dir` without a worktree, then delete the harness
folder and everything inside it, `task.md` whatever its form and the uncommitted
paths included and never the task file `task.md` links or names, print `removed`,
and exit 0. The remote of every repository SHALL NOT be touched. The task file SHALL
NOT be touched, whatever its status, and no git command SHALL run against the tasks
repo.

#### Scenario: Manifest shown without deleting
- **WHEN** `gemba harness remove SUP-1` runs for a launched task whose harness holds two filed notes and one asset
- **THEN** the output holds the harness path, `task: tasks/support/2026-09-30-SUP-1-login-fails.md`, `launched_at: <date>`, `notes: 2`, `assets: 1`, `commits: 3`, `worktrees: 0`, `uncommitted: 0` and `not removed: pass --yes to delete the harness`, the tree is unchanged and the exit code is 0
- **Cases**: keeps `tests/cases/harness/manifest-shown-without-deleting.yaml`

#### Scenario: Uncommitted paths listed in the manifest
- **WHEN** the harness of `SUP-1` holds a drafted note `notes/draft.md` never filed and an `update.md` never recorded, and `gemba harness remove SUP-1` runs
- **THEN** the manifest reads `uncommitted: 2` followed by `- notes/draft.md` and `- update.md`, the output ends with `not removed: pass --yes to delete the harness`, the tree is unchanged and the exit code is 0
- **Cases**: keeps `tests/cases/harness/uncommitted-paths-listed-in-the-manifest.yaml`

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
- **WHEN** a repository under `repos_dir` holds `gemba/nakatomi/SUP-1` with no worktree and every commit of it on a remote branch, and `gemba harness remove SUP-1 --yes` runs
- **THEN** the branch no longer exists, the harness folder no longer exists and the exit code is 0
- **Cases**: keeps `tests/cases/harness/orphan-branch-of-the-run-deleted.yaml`

#### Scenario: Removed harness relaunched
- **WHEN** a task's harness is removed with `--yes` and `gemba harness launch` runs again for it
- **THEN** a fresh harness is created with one commit, the status of the task is left as it was, and the exit code is 0
- **Cases**: keeps `tests/cases/harness/removed-harness-relaunched.yaml`

#### Scenario: No harness to remove
- **WHEN** no task has the ref given, or the task exists but no folder exists at its harness path
- **THEN** the command exits 1, says which of the two it is, and deletes nothing
- **Cases**: keeps `tests/cases/harness/no-harness-to-remove.yaml`

#### Scenario: Folder without harness config refused
- **WHEN** a folder exists at the harness path but holds no `harness.yaml`
- **THEN** the command exits 1, says the folder is not a harness, and deletes nothing, with or without `--yes`
- **Cases**: keeps `tests/cases/harness/folder-without-harness-config-refused.yaml`

## ADDED Requirements

### Requirement: Removal finishes what the system allows
When deleting the harness folder, `remove --yes` SHALL delete a file the system
marks read-only, as git marks its objects on Windows, and SHALL retry briefly a path
another program holds open. When a path stays held, the command SHALL say the
harness was not removed completely, name what is left, say that an IDE window or a
terminal open on the harness is the likely cause, and say that running the removal
again with `--yes` finishes it, and SHALL exit 1.

#### Scenario: Read-only files deleted
- **WHEN** the harness repository holds read-only files under `.git/`, as git writes them on Windows, and `gemba harness remove SUP-1 --yes` runs
- **THEN** the harness folder no longer exists, the output ends with `removed` and the exit code is 0
- **Cases**: adds the entry `harness-removal: Read-only files deleted` to `tests/not-automated.yaml` (git marks its objects read-only on Windows only, where the `Harness removed` case exercises this deletion on the CI; on POSIX no file attribute blocks an unlink)

#### Scenario: Path held by another program reported
- **WHEN** a file of the harness stays held by another program while `gemba harness remove SUP-1 --yes` deletes the folder
- **THEN** the output says the harness was not removed completely, names the path left, names an IDE window or a terminal on the harness as the likely cause, says that `gemba harness remove SUP-1 --yes` again finishes, and the exit code is 1
- **Cases**: adds the entry `harness-removal: Path held by another program reported` to `tests/not-automated.yaml` (no case can hold a file open while the command runs; covered by a unit test of the deletion policy in `tests/test_harness.py` with a failure that persists)
