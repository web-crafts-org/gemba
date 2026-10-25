# Spec Delta

## MODIFIED Requirements

### Requirement: The repositories folder and the branch of a run
A repository a run may check out SHALL be a folder directly under the `repos_dir` of
the personal config that holds a git repository at its root, identified by its folder
name. `repos_dir` SHALL be absolute, start with `~`, which is expanded to the user's
home, or be relative to the obeya root. No verb SHALL search below that level or
clone anything. The remote of every operation SHALL be `origin`. Every worktree of a
run SHALL be on a local branch named `<branch_prefix>/<obeya>/<ref>`, with
`branch_prefix` from the personal config, `obeya` from the shared config and
`ref` from `harness.yaml`, created with no upstream, so that two runs on the same
repository never share a branch. No verb of the group SHALL push, delete or otherwise
change anything on the remote, whatever the flags.

#### Scenario: Repository resolved at the root of the folder
- **WHEN** `repos_dir` holds `nakatomi-web/` with a `.git` and `group/other/` with a `.git` below one more level, and `gemba worktree add nakatomi-web` and then `gemba worktree add other` run inside a harness
- **THEN** the first creates `worktrees/nakatomi-web` and exits 0, and the second exits 1, says that no repository named `other` is at the root of the folder, names `nakatomi-web` as the one found there, and creates no worktree and no branch
- **Cases**: modifies `tests/cases/worktree/repository-resolved-at-the-root.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Repositories folder relative to the obeya
- **WHEN** the personal config declares `repos_dir: repos` and `repos/nakatomi-web` is a git repository under the obeya root
- **THEN** `gemba worktree add nakatomi-web` finds it and creates the worktree
- **Cases**: modifies `tests/cases/worktree/repositories-folder-relative-to-the-tasks-repo.yaml`, renamed `repositories-folder-relative-to-the-obeya.yaml` (its config declares `obeya` in place of `organization`; its name says obeya; its comment says obeya; it names its scenario by the new title)

#### Scenario: Branch named after the run
- **WHEN** the shared config declares `obeya: nakatomi` and the personal config declares no `branch_prefix`, or `branch_prefix: nk`, and `gemba worktree add nakatomi-web` runs in the harness of `SUP-1`
- **THEN** the base repository holds the local branch `gemba/nakatomi/SUP-1`, or `nk/nakatomi/SUP-1`, checked out in `worktrees/nakatomi-web`, and `gemba worktree list` shows `upstream: none` for it
- **Cases**: modifies `tests/cases/worktree/branch-named-after-the-run.yaml` (its config declares `obeya` in place of `organization`; its name says obeya)

#### Scenario: Same repository in two runs
- **WHEN** `SUP-1` and `SUP-2` are launched and `gemba worktree add nakatomi-web` runs in each harness
- **THEN** both commands exit 0, the base repository holds `gemba/nakatomi/SUP-1` and `gemba/nakatomi/SUP-2`, and its own checked-out branch is the one it had before
- **Cases**: modifies `tests/cases/worktree/same-repository-in-two-runs.yaml` (its config declares `obeya` in place of `organization`)

### Requirement: Add creates the worktree of a repository
`gemba worktree add <repo> [--from <branch>] [--force]` SHALL run inside a harness,
resolved as the nearest `harness.yaml` at or above the working directory or as the
folder given with `--harness`. It SHALL refuse, creating nothing, when the shared
config declares no `obeya` or the personal config no `repos_dir`, naming the
missing key and the file it goes in; when no repository named `<repo>` is at the root
of `repos_dir`, naming the repositories that are; when `origin` has no branch
`<branch>` after the fetch; when `--from` is not given and the repository records no
default branch for `origin`, saying that `--from` names the base; when a folder exists
at `worktrees/<repo>` that is not a worktree of that repository; and when the base
repository already holds the branch of the run without a worktree, left by a harness
deleted by hand, unless `--force` is given, in which case that branch is deleted and
recreated. Otherwise it SHALL fetch `origin` with pruning, prune the stale worktree
records of the base repository, create the branch of the run at `origin/<branch>`, or
at the default branch of `origin` without `--from`, with no upstream, check it out as
a worktree at `worktrees/<repo>` in the harness, and print the worktree path relative
to the harness root, `branch:` and the branch, `from:` and the base, and `created`. A
failed fetch SHALL be a refusal that relays git's message. The harness repository
SHALL NOT be committed: `worktrees/` is excluded from it.

#### Scenario: Worktree added from the default branch
- **WHEN** `origin` of `nakatomi-web` has `main` as its default branch and `gemba worktree add nakatomi-web` runs in the harness of `SUP-1`
- **THEN** `worktrees/nakatomi-web` holds the files of `main`, its branch is `gemba/nakatomi/SUP-1`, the output is the path, `branch: gemba/nakatomi/SUP-1`, `from: origin/main` and `created`, the harness repository is clean with its commits unchanged, and the exit code is 0
- **Cases**: modifies `tests/cases/worktree/worktree-added-from-the-default-branch.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Worktree added from a named branch
- **WHEN** `gemba worktree add nakatomi-web --from feature/a` runs and `origin` has `feature/a`
- **THEN** `worktrees/nakatomi-web` holds the files of `feature/a`, the output reads `from: origin/feature/a`, and the exit code is 0
- **Cases**: modifies `tests/cases/worktree/worktree-added-from-a-named-branch.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Fresh base fetched
- **WHEN** `origin` received a commit on `main` that the base repository has not fetched, and `gemba worktree add nakatomi-web` runs
- **THEN** `worktrees/nakatomi-web` holds the file of that commit
- **Cases**: modifies `tests/cases/worktree/fresh-base-fetched.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Config without obeya or repositories folder refused
- **WHEN** the shared config declares no `obeya`, or the personal config no `repos_dir`, and `gemba worktree add nakatomi-web` runs
- **THEN** the command exits 1, names the missing key and the file it goes in, `gemba.yaml` or `gemba.local.yaml`, and creates no worktree and no branch
- **Cases**: modifies `tests/cases/worktree/config-without-organization-or-repos-dir-refused.yaml`, renamed `config-without-obeya-or-repos-dir-refused.yaml` (its config declares `obeya` in place of `organization`; the message it expects names the obeya; its name says obeya; it names its scenario by the new title)

#### Scenario: Missing remote branch refused
- **WHEN** `gemba worktree add nakatomi-web --from feature/none` runs and `origin` has no such branch
- **THEN** the command exits 1, says `origin` has no branch `feature/none`, and creates no worktree and no branch
- **Cases**: modifies `tests/cases/worktree/missing-remote-branch-refused.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: No default branch refused
- **WHEN** the base repository records no default branch for `origin` and `gemba worktree add nakatomi-web` runs without `--from`
- **THEN** the command exits 1, says that the repository has no default branch and that `--from` names the base, and creates no worktree and no branch
- **Cases**: modifies `tests/cases/worktree/no-default-branch-refused.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Folder that is not a worktree refused
- **WHEN** a plain folder with a file exists at `worktrees/nakatomi-web` and `gemba worktree add nakatomi-web` runs
- **THEN** the command exits 1, says the folder is not a worktree of `nakatomi-web`, creates no branch and leaves the folder as it was
- **Cases**: modifies `tests/cases/worktree/folder-that-is-not-a-worktree-refused.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Orphan branch refused and forced
- **WHEN** the base repository holds `gemba/nakatomi/SUP-1` with no worktree and `gemba worktree add nakatomi-web` runs without, then with, `--force`
- **THEN** the first run exits 1, names the branch and says `--force` deletes and recreates it, and creates no worktree; the second exits 0, creates the worktree, and the branch points at `origin/main`
- **Cases**: modifies `tests/cases/worktree/orphan-branch-refused-and-forced.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Run outside a harness refused
- **WHEN** `gemba worktree add nakatomi-web` runs outside any harness and without `--harness`
- **THEN** it exits 1, reports that no harness was found, and creates no worktree and no branch
- **Cases**: modifies `tests/cases/worktree/run-outside-a-harness-refused.yaml` (its config declares `obeya` in place of `organization`)

### Requirement: One worktree per repository per harness
When `worktrees/<repo>` is already a worktree of that repository, `gemba worktree add
<repo>` without `--from` SHALL print the path and `already attached, worktree
unchanged` and exit 0, changing nothing. With `--from <branch>` it SHALL fetch `origin`
with pruning, check that the worktree has no uncommitted path, staged, unstaged or
untracked, and no commit that is not on any remote branch, and then move the branch of
the worktree to `origin/<branch>`, discarding nothing, keeping the branch and its
name, and print the path, `branch:`, `from:` and `moved`. When a check fails it SHALL
refuse, changing nothing, naming each uncommitted path and the number of commits not
on any remote branch, unless `--force` is given, in which case it SHALL move the branch
and discard them. Moving the base is starting again from the base: carrying work from
one base onto another is a rebase inside the worktree and is not done by the command.

#### Scenario: Repository already attached
- **WHEN** `gemba worktree add nakatomi-web` runs twice without `--from`
- **THEN** the second run prints the path and `already attached, worktree unchanged`, exits 0, and the tree is identical to the one after the first run
- **Cases**: modifies `tests/cases/worktree/repository-already-attached.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Base changed on the same worktree
- **WHEN** `worktrees/nakatomi-web` was added from `main` with nothing pending and `gemba worktree add nakatomi-web --from feature/a` runs
- **THEN** `worktrees/nakatomi-web` holds the files of `feature/a`, its branch is still `gemba/nakatomi/SUP-1`, the output reads `from: origin/feature/a` and `moved`, and the exit code is 0
- **Cases**: modifies `tests/cases/worktree/base-changed-on-the-same-worktree.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Base change refused with pending work
- **WHEN** `worktrees/nakatomi-web` holds an uncommitted file, or a commit not on any remote branch, and `gemba worktree add nakatomi-web --from feature/a` runs
- **THEN** the command exits 1, names the uncommitted path or the number of unpushed commits, and the worktree still holds the files and the commit it had
- **Cases**: modifies `tests/cases/worktree/base-change-refused-with-pending-work.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Base change forced
- **WHEN** `worktrees/nakatomi-web` holds a commit not on any remote branch and `gemba worktree add nakatomi-web --from feature/a --force` runs
- **THEN** the command exits 0, the worktree holds the files of `feature/a`, and the commit is no longer in its history
- **Cases**: modifies `tests/cases/worktree/base-change-forced.yaml` (its config declares `obeya` in place of `organization`)

### Requirement: List reads the state of every worktree
`gemba worktree list` SHALL run inside a harness and print, for every worktree under
`worktrees/` in name order, the worktree path relative to the harness root, then
`branch:` and the branch checked out in it, `upstream:` and the upstream of that
branch or `none`, `uncommitted:` and the number of uncommitted paths, staged, unstaged
or untracked, and `unpushed:` and the number of commits of the branch that are not on
any remote branch, each block separated from the next by one empty line. Every value
SHALL be read from git when the command runs; nothing SHALL be stored for it. With no
worktree it SHALL print `no worktrees`. A folder under `worktrees/` that is not a
worktree SHALL be listed with `not a worktree` in place of the four lines.

#### Scenario: Worktrees listed
- **WHEN** `worktrees/nakatomi-api` was added with nothing pending and `worktrees/nakatomi-web` holds one untracked file and one commit not on any remote branch
- **THEN** the output is the block of `worktrees/nakatomi-api` with `upstream: none`, `uncommitted: 0` and `unpushed: 0`, an empty line, and the block of `worktrees/nakatomi-web` with `uncommitted: 1` and `unpushed: 1`, and the exit code is 0
- **Cases**: modifies `tests/cases/worktree/worktrees-listed.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Nothing to list
- **WHEN** `gemba worktree list` runs in a harness whose `worktrees/` is empty
- **THEN** the output is `no worktrees` and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/nothing-to-list.yaml`

#### Scenario: Upstream shown after a push
- **WHEN** the branch of `worktrees/nakatomi-web` was pushed with `git push -u origin HEAD:feature/login-fix`
- **THEN** `gemba worktree list` shows `upstream: origin/feature/login-fix` and `unpushed: 0`
- **Cases**: modifies `tests/cases/worktree/upstream-shown-after-a-push.yaml` (its config declares `obeya` in place of `organization`)

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
- **Cases**: modifies `tests/cases/worktree/state-shown-without-deleting.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Worktree removed
- **WHEN** `gemba worktree remove nakatomi-web --yes` runs for a worktree with nothing pending
- **THEN** `worktrees/nakatomi-web` no longer exists, the base repository no longer holds `gemba/nakatomi/SUP-1`, the branches of `origin` are what they were, the output ends with `removed` and the exit code is 0
- **Cases**: modifies `tests/cases/worktree/worktree-removed.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Removal refused with pending work
- **WHEN** `worktrees/nakatomi-web` holds an uncommitted file, or a commit not on any remote branch, and `gemba worktree remove nakatomi-web --yes` runs
- **THEN** the output holds the block, `worktree not removed:` and the problem, the exit code is 1, and the worktree and its branch still exist
- **Cases**: modifies `tests/cases/worktree/removal-refused-with-pending-work.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: Pending work discarded on request
- **WHEN** `worktrees/nakatomi-web` holds a commit not on any remote branch and `gemba worktree remove nakatomi-web --yes --force` runs
- **THEN** the worktree and its branch are gone, the branches of `origin` are what they were, and the exit code is 0
- **Cases**: modifies `tests/cases/worktree/pending-work-discarded-on-request.yaml` (its config declares `obeya` in place of `organization`)

#### Scenario: No worktree to remove
- **WHEN** `gemba worktree remove nakatomi-web` runs and nothing exists at `worktrees/nakatomi-web`, or a plain folder is there
- **THEN** the command exits 1, says which of the two it is, and deletes nothing
- **Cases**: keeps `tests/cases/worktree/no-worktree-to-remove.yaml`

#### Scenario: Worktree path held by another program reported
- **WHEN** a file of `worktrees/nakatomi-web` stays held by another program while `gemba worktree remove nakatomi-web --yes` runs
- **THEN** the output says the worktree was not removed, names the path left, names an IDE window or a terminal on the worktree as the likely cause, says that running the removal again finishes it, and the exit code is 1
- **Cases**: keeps the entry `harness-worktrees: Worktree path held by another program reported` of `tests/not-automated.yaml`
