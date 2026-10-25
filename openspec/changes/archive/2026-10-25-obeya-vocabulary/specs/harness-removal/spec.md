# Spec Delta

## MODIFIED Requirements

### Requirement: Remove deletes the harness of a task
`gemba harness remove <ref> [--yes] [--force]` SHALL run from the obeya: it SHALL
resolve the task with that ref anywhere under `tasks/`, archives included, and the
harness at `harnesses/<workstream>/<stem>/` under the obeya root. It SHALL
refuse, deleting nothing, when no task has that ref, when no folder exists at the
harness path, or when the folder holds no `harness.yaml`. It SHALL print a manifest of
the run: the harness path relative to the obeya root, then one line each for
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
left in a repository under the `repos_dir` of the personal config without a worktree,
then delete the harness folder and everything inside it, `task.md` whatever its form
and the uncommitted paths included and never the task file `task.md` links or names,
print `removed`, and exit 0. The remote of every repository SHALL NOT be touched. The
task file SHALL NOT be touched, whatever its status, and no git command SHALL run
against the obeya.

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
- **Cases**: modifies `tests/cases/harness/harness-removed-with-its-worktrees.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Orphan branch of the run deleted
- **WHEN** a repository under the `repos_dir` of the personal config holds `gemba/nakatomi/SUP-1` with no worktree and every commit of it on a remote branch, and `gemba harness remove SUP-1 --yes` runs
- **THEN** the branch no longer exists, the harness folder no longer exists and the exit code is 0
- **Cases**: modifies `tests/cases/harness/orphan-branch-of-the-run-deleted.yaml` (its config declares `obeya` in place of `organization`)

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

### Requirement: Remove refuses an unsafe deletion
Before deleting, and also when only showing the manifest, `remove` SHALL check that
the working directory is not inside the harness, that the state of the harness
repository can be read, that every worktree under `worktrees/` has no uncommitted path
and no commit that is not on any remote branch, that every branch of the run left in a
repository under the `repos_dir` of the personal config without a worktree has no
commit that is not on any remote branch, and that every folder under `worktrees/` is a
worktree. The uncommitted paths of the harness repository itself are not checked: the
manifest lists them and the removal deletes them. When a check fails, or when the
state of a worktree cannot be read, the command SHALL print the manifest, then
`harness not removed:` and one line per problem, naming each worktree with the number
of its uncommitted paths and of its unpushed commits, each orphan branch with its
repository and the number of its unpushed commits, and each folder that is not a
worktree, exit 1 and delete nothing, with or without `--yes`, so that the manifest
never promises a deletion the real run refuses. When the state of the harness
repository cannot be read, the manifest SHALL read `uncommitted: unknown`. With
`--force` the checks on worktrees, orphan branches and folders under `worktrees/`
SHALL NOT refuse, and with `--yes --force` the command SHALL discard what they
protect; the checks on the working directory and on the state of the harness
repository SHALL refuse regardless of `--force`.

#### Scenario: Working directory inside the harness refused
- **WHEN** `remove --yes` runs from a folder inside the harness it names
- **THEN** the command exits 1, says the working directory is inside the harness, and deletes nothing
- **Cases**: keeps `tests/cases/harness/working-directory-inside-the-harness-refused.yaml`

#### Scenario: Worktree with pending work refused
- **WHEN** `worktrees/nakatomi-web` holds an uncommitted file, or a commit not on any remote branch, and `remove SUP-1 --yes` runs
- **THEN** the output holds the manifest, `harness not removed:` and a line naming `worktrees/nakatomi-web` with the number of uncommitted paths or of unpushed commits, the exit code is 1, and the harness, the worktree and its branch still exist
- **Cases**: modifies `tests/cases/harness/worktree-with-pending-work-refused.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Orphan branch with pending work refused
- **WHEN** a repository under the `repos_dir` of the personal config holds `gemba/nakatomi/SUP-1` with no worktree and a commit not on any remote branch, and `remove SUP-1 --yes` runs
- **THEN** the output holds the manifest, `harness not removed:` and a line naming the branch, the repository and the number of unpushed commits, the exit code is 1, and the harness and the branch still exist
- **Cases**: modifies `tests/cases/harness/orphan-branch-with-pending-work-refused.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Folder that is not a worktree refused
- **WHEN** a plain folder with a file exists under `worktrees/` and `remove SUP-1 --yes` runs
- **THEN** the output holds the manifest, `harness not removed:` and a line saying the folder is not a worktree, the exit code is 1 and the tree is unchanged
- **Cases**: keeps `tests/cases/harness/folder-that-is-not-a-worktree-refused.yaml`

#### Scenario: Pending work discarded with force
- **WHEN** `worktrees/nakatomi-web` holds a commit not on any remote branch and `remove SUP-1 --yes --force` runs
- **THEN** the harness folder no longer exists, the base repository no longer holds `gemba/nakatomi/SUP-1`, the branches of `origin` are what they were, the output ends with `removed` and the exit code is 0
- **Cases**: modifies `tests/cases/harness/pending-work-discarded-with-force.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Force does not cover the working directory
- **WHEN** `remove SUP-1 --yes --force` runs from a folder inside the harness it names
- **THEN** the output holds `harness not removed:` and the line saying the working directory is inside the harness, the exit code is 1 and the tree is unchanged
- **Cases**: keeps `tests/cases/harness/force-does-not-cover-the-working-directory.yaml`

### Requirement: Removal confirmed by the agent
The `gemba-harness` skill SHALL have the agent, from the obeya, identify the task
by its ref, run `gemba harness remove <ref>` without `--yes` and without `--force`,
show the manifest to the user and ask for their confirmation in the chat, remind them
to close any IDE window open on that folder, and only after a yes run the command
again with `--yes` and relay the result. The confirmation in the chat is enough
because the harness is gemba's own data; an `external-action` note is not required.
When the manifest lists uncommitted paths of the harness, the skill SHALL have the
agent name them when asking for the confirmation, say that they will be deleted with
the harness, and say what would keep each one should the user want to (file a draft
note with `gemba harness note`, record an `update.md` with `gemba record`, from a
session inside the harness), and SHALL NOT have the agent file, commit or delete
anything in the harness itself. When the command refuses for a worktree, an orphan
branch or a folder under `worktrees/`, the skill SHALL have the agent relay every line,
say that a push from inside the harness saves unpushed commits and needs an approved
`external-action` note, and pass `--force` only after the user confirms, in the chat,
that everything the command listed is to be discarded; the agent SHALL NOT pass
`--force` on the first run, even when the user asks to force the removal. The skill
SHALL have the agent read the `harness.remove` block of the task's workstream and
follow its `rules` and `context`.

#### Scenario: Agent removes a harness
- **WHEN** the user asks to remove, clean up, delete or throw away the harness of a task
- **THEN** the agent shows the manifest, asks, and runs `remove --yes` only after the user says yes
- **Cases**: keeps the entry `harness-removal: Agent removes a harness` of `tests/not-automated.yaml`

#### Scenario: Agent names uncommitted paths before confirming
- **WHEN** the manifest lists uncommitted paths of the harness, such as a drafted note and an `update.md`
- **THEN** the agent names them when asking for the confirmation, says they will be deleted with the harness and how each could be kept, and files, commits or deletes nothing in the harness itself
- **Cases**: keeps the entry `harness-removal: Agent names uncommitted paths before confirming` of `tests/not-automated.yaml`

#### Scenario: Agent forces only after confirming the pending list
- **WHEN** the command refuses for a worktree with pending work and the user asks to force the removal
- **THEN** the agent relays the pending list, waits for the user to confirm that list, and only then runs `remove --yes --force`
- **Cases**: keeps the entry `harness-removal: Agent forces only after confirming the pending list` of `tests/not-automated.yaml`

#### Scenario: Agent follows the verb's rules
- **WHEN** workstream `support` declares `harness.remove.rules` containing "check the client report was sent before removing"
- **THEN** the agent follows that rule before showing the manifest for a `support` task
- **Cases**: keeps the entry `harness-removal: Agent follows the verb's rules` of `tests/not-automated.yaml`
