# Spec Delta

## MODIFIED Requirements

### Requirement: Remove deletes one worktree and its branch
`gemba worktree remove <repo> [--yes] [--force]` SHALL run inside a harness and
refuse, deleting nothing, when nothing exists at `worktrees/<repo>` or when the folder
there is not a worktree. It SHALL print the block `list` prints for that worktree,
then, when the worktree has an uncommitted path or a commit not on any remote branch
and `--force` is not given, `worktree not removed:` and one line per problem, exit 1
and delete nothing, with or without `--yes`. Otherwise without `--yes` it SHALL print
`not removed: pass --yes to delete the worktree` and exit 0, and with `--yes` it SHALL
remove the worktree from the base repository, delete the folder, delete the branch
that was checked out in it from the base repository, print `removed` and exit 0. The
remote SHALL NOT be touched: its branches are what they were. When git cannot delete
the folder because another program holds a path in it, the command SHALL retry
briefly and, when the path stays held, say the worktree was not removed, name the
path, name an IDE window or a terminal on the worktree as the likely cause, and say
that running the removal again finishes it, with the branch left for that run.

#### Scenario: State shown without deleting
- **WHEN** `gemba worktree remove nakatomi-web` runs for a worktree with nothing pending
- **THEN** the output is the block of the worktree and `not removed: pass --yes to delete the worktree`, the tree is unchanged and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/state-shown-without-deleting.yaml`

#### Scenario: Worktree removed
- **WHEN** `gemba worktree remove nakatomi-web --yes` runs for a worktree with nothing pending
- **THEN** `worktrees/nakatomi-web` no longer exists, the base repository no longer holds `gemba/nakatomi/SUP-1`, the branches of `origin` are what they were, the output ends with `removed` and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/worktree-removed.yaml`

#### Scenario: Removal refused with pending work
- **WHEN** `worktrees/nakatomi-web` holds an uncommitted file, or a commit not on any remote branch, and `gemba worktree remove nakatomi-web --yes` runs
- **THEN** the output holds the block, `worktree not removed:` and the problem, the exit code is 1, and the worktree and its branch still exist
- **Cases**: keeps `tests/cases/worktree/removal-refused-with-pending-work.yaml`

#### Scenario: Pending work discarded on request
- **WHEN** `worktrees/nakatomi-web` holds a commit not on any remote branch and `gemba worktree remove nakatomi-web --yes --force` runs
- **THEN** the worktree and its branch are gone, the branches of `origin` are what they were, and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/pending-work-discarded-on-request.yaml`

#### Scenario: No worktree to remove
- **WHEN** `gemba worktree remove nakatomi-web` runs and nothing exists at `worktrees/nakatomi-web`, or a plain folder is there
- **THEN** the command exits 1, says which of the two it is, and deletes nothing
- **Cases**: keeps `tests/cases/worktree/no-worktree-to-remove.yaml`

#### Scenario: Worktree path held by another program reported
- **WHEN** a file of `worktrees/nakatomi-web` stays held by another program while `gemba worktree remove nakatomi-web --yes` runs
- **THEN** the output says the worktree was not removed, names the path left, names an IDE window or a terminal on the worktree as the likely cause, says that running the removal again finishes it, and the exit code is 1
- **Cases**: adds the entry `harness-worktrees: Worktree path held by another program reported` to `tests/not-automated.yaml` (no case can hold a file open while the command runs; covered by the unit test of the deletion policy in `tests/test_harness.py`, which both removals share)
