# Spec Delta

## MODIFIED Requirements

### Requirement: List reads the state of every worktree
`gemba worktree list` SHALL run inside a harness and print, for each folder under
`worktrees/` in name order, one empty line apart, its path relative to the harness
root, then `branch:` with its branch, `upstream:` with its upstream or `none`,
`uncommitted:` with the number of staged, unstaged or untracked paths, and `unpushed:`
with the number of commits on no remote branch, read from git as it runs, or
`not a worktree` in place of the four lines. With no worktree it SHALL print
`no worktrees`.

#### Scenario: Worktrees listed
- **WHEN** `worktrees/nakatomi-api` was added with nothing pending and `worktrees/nakatomi-web` holds one untracked file and one commit not on any remote branch
- **THEN** the output is the block of `worktrees/nakatomi-api` with `upstream: none`, `uncommitted: 0` and `unpushed: 0`, an empty line, and the block of `worktrees/nakatomi-web` with `uncommitted: 1` and `unpushed: 1`, and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/worktrees-listed.yaml`

#### Scenario: Nothing to list
- **WHEN** `gemba worktree list` runs in a harness whose `worktrees/` is empty
- **THEN** the output is `no worktrees` and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/nothing-to-list.yaml`

#### Scenario: Upstream shown after a push
- **WHEN** the branch of `worktrees/nakatomi-web` was pushed with `git push -u origin HEAD:feature/login-fix`
- **THEN** `gemba worktree list` shows `upstream: origin/feature/login-fix` and `unpushed: 0`
- **Cases**: keeps `tests/cases/worktree/upstream-shown-after-a-push.yaml`

## REMOVED Requirements

### Requirement: The repositories folder and the branch of a run
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "A
repository is a folder at the root of repos_dir" and "The branch of a run".

### Requirement: Add creates the worktree of a repository
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Add
refuses a config or a repository it cannot use", "Add refuses a base it cannot start
from" and "Add checks out the branch of the run".

### Requirement: One worktree per repository per harness
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "A
repository is attached once per harness" and "Add moves the base of an attached
worktree".

### Requirement: Remove deletes one worktree and its branch
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Remove
shows the state of a worktree", "Remove deletes the worktree with yes" and "A held
worktree path is reported".

### Requirement: Worktrees by the agent
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The agent
looks up the repositories of the task", "The agent adds the worktrees of the task",
"The agent keeps git inside the worktree" and "The agent never forces first".

## ADDED Requirements

### Requirement: A repository is a folder at the root of repos_dir
A repository a run may check out SHALL be a folder directly under the `repos_dir` of
the personal config that holds a git repository at its root, identified by its folder
name. `repos_dir` SHALL be absolute, start with `~`, expanded to the user's home, or
be relative to the obeya root. No verb SHALL search below that level or clone
anything.

#### Scenario: Repository resolved at the root of the folder
- **WHEN** `repos_dir` holds `nakatomi-web/` with a `.git` and `group/other/` with a `.git` below one more level, and `gemba worktree add nakatomi-web` and then `gemba worktree add other` run inside a harness
- **THEN** the first creates `worktrees/nakatomi-web` and exits 0, and the second exits 1, says that no repository named `other` is at the root of the folder, names `nakatomi-web` as the one found there, and creates no worktree and no branch
- **Cases**: keeps `tests/cases/worktree/repository-resolved-at-the-root.yaml`

#### Scenario: Repositories folder relative to the obeya
- **WHEN** the personal config declares `repos_dir: repos` and `repos/nakatomi-web` is a git repository under the obeya root
- **THEN** `gemba worktree add nakatomi-web` finds it and creates the worktree
- **Cases**: keeps `tests/cases/worktree/repositories-folder-relative-to-the-obeya.yaml`

### Requirement: The branch of a run
Every worktree of a run SHALL be on a local branch named
`<branch_prefix>/<obeya>/<ref>`, with `branch_prefix` from the personal config,
`obeya` from the shared config and `ref` from `harness.yaml`, created with no
upstream, so that two runs on the same repository never share a branch. The remote of
every operation SHALL be `origin`, and no verb of the group SHALL push, delete or
otherwise change anything on it, whatever the flags.

#### Scenario: Branch named after the run
- **WHEN** the shared config declares `obeya: nakatomi` and the personal config declares no `branch_prefix`, or `branch_prefix: nk`, and `gemba worktree add nakatomi-web` runs in the harness of `SUP-1`
- **THEN** the base repository holds the local branch `gemba/nakatomi/SUP-1`, or `nk/nakatomi/SUP-1`, checked out in `worktrees/nakatomi-web`, and `gemba worktree list` shows `upstream: none` for it
- **Cases**: keeps `tests/cases/worktree/branch-named-after-the-run.yaml`

#### Scenario: Same repository in two runs
- **WHEN** `SUP-1` and `SUP-2` are launched and `gemba worktree add nakatomi-web` runs in each harness
- **THEN** both commands exit 0, the base repository holds `gemba/nakatomi/SUP-1` and `gemba/nakatomi/SUP-2`, and its own checked-out branch is the one it had before
- **Cases**: keeps `tests/cases/worktree/same-repository-in-two-runs.yaml`

### Requirement: Add refuses a config or a repository it cannot use
`gemba worktree add <repo> [--from <branch>] [--force]` SHALL run inside a harness,
the nearest `harness.yaml` at or above the working directory or the folder given with
`--harness`. It SHALL refuse, creating nothing, when the shared config declares no
`obeya` or the personal config no `repos_dir`, naming the key and its file; when no
repository named `<repo>` is at the root of `repos_dir`, naming those that are; and
when a folder at `worktrees/<repo>` is not a worktree of that repository.

#### Scenario: Config without obeya or repositories folder refused
- **WHEN** the shared config declares no `obeya`, or the personal config no `repos_dir`, and `gemba worktree add nakatomi-web` runs
- **THEN** the command exits 1, names the missing key and the file it goes in, `gemba.yaml` or `gemba.local.yaml`, and creates no worktree and no branch
- **Cases**: keeps `tests/cases/worktree/config-without-obeya-or-repos-dir-refused.yaml`

#### Scenario: Folder that is not a worktree refused
- **WHEN** a plain folder with a file exists at `worktrees/nakatomi-web` and `gemba worktree add nakatomi-web` runs
- **THEN** the command exits 1, says the folder is not a worktree of `nakatomi-web`, creates no branch and leaves the folder as it was
- **Cases**: keeps `tests/cases/worktree/folder-that-is-not-a-worktree-refused.yaml`

#### Scenario: Run outside a harness refused
- **WHEN** `gemba worktree add nakatomi-web` runs outside any harness and without `--harness`
- **THEN** it exits 1, reports that no harness was found, and creates no worktree and no branch
- **Cases**: keeps `tests/cases/worktree/run-outside-a-harness-refused.yaml`

### Requirement: Add refuses a base it cannot start from
`add` SHALL also refuse, creating nothing, when the fetch fails, relaying git's
message; when `origin` has no branch `<branch>` after the fetch; when `--from` is not
given and the repository records no default branch for `origin`, saying that `--from`
names the base; and when the base repository holds the branch of the run without a
worktree, left by a harness deleted by hand, unless `--force` is given, which deletes
and recreates that branch.

#### Scenario: Missing remote branch refused
- **WHEN** `gemba worktree add nakatomi-web --from feature/none` runs and `origin` has no such branch
- **THEN** the command exits 1, says `origin` has no branch `feature/none`, and creates no worktree and no branch
- **Cases**: keeps `tests/cases/worktree/missing-remote-branch-refused.yaml`

#### Scenario: No default branch refused
- **WHEN** the base repository records no default branch for `origin` and `gemba worktree add nakatomi-web` runs without `--from`
- **THEN** the command exits 1, says that the repository has no default branch and that `--from` names the base, and creates no worktree and no branch
- **Cases**: keeps `tests/cases/worktree/no-default-branch-refused.yaml`

#### Scenario: Orphan branch refused and forced
- **WHEN** the base repository holds `gemba/nakatomi/SUP-1` with no worktree and `gemba worktree add nakatomi-web` runs without, then with, `--force`
- **THEN** the first run exits 1, names the branch and says `--force` deletes and recreates it, and creates no worktree; the second exits 0, creates the worktree, and the branch points at `origin/main`
- **Cases**: keeps `tests/cases/worktree/orphan-branch-refused-and-forced.yaml`

### Requirement: Add checks out the branch of the run
Otherwise `add` SHALL fetch `origin` with pruning, prune the stale worktree records of
the base repository, create the branch of the run at `origin/<branch>`, or at the
default branch of `origin` without `--from`, with no upstream, check it out at
`worktrees/<repo>`, and print the worktree path relative to the harness root,
`branch:` and the branch, `from:` and the base, and `created`. The harness repository
SHALL NOT be committed: `worktrees/` is excluded from it.

#### Scenario: Worktree added from the default branch
- **WHEN** `origin` of `nakatomi-web` has `main` as its default branch and `gemba worktree add nakatomi-web` runs in the harness of `SUP-1`
- **THEN** `worktrees/nakatomi-web` holds the files of `main`, its branch is `gemba/nakatomi/SUP-1`, the output is the path, `branch: gemba/nakatomi/SUP-1`, `from: origin/main` and `created`, the harness repository is clean with its commits unchanged, and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/worktree-added-from-the-default-branch.yaml`

#### Scenario: Worktree added from a named branch
- **WHEN** `gemba worktree add nakatomi-web --from feature/a` runs and `origin` has `feature/a`
- **THEN** `worktrees/nakatomi-web` holds the files of `feature/a`, the output reads `from: origin/feature/a`, and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/worktree-added-from-a-named-branch.yaml`

#### Scenario: Fresh base fetched
- **WHEN** `origin` received a commit on `main` that the base repository has not fetched, and `gemba worktree add nakatomi-web` runs
- **THEN** `worktrees/nakatomi-web` holds the file of that commit
- **Cases**: keeps `tests/cases/worktree/fresh-base-fetched.yaml`

### Requirement: A repository is attached once per harness
When `worktrees/<repo>` is already a worktree of that repository,
`gemba worktree add <repo>` without `--from` SHALL print the path and
`already attached, worktree unchanged` and exit 0, changing nothing.

#### Scenario: Repository already attached
- **WHEN** `gemba worktree add nakatomi-web` runs twice without `--from`
- **THEN** the second run prints the path and `already attached, worktree unchanged`, exits 0, and the tree is identical to the one after the first run
- **Cases**: keeps `tests/cases/worktree/repository-already-attached.yaml`

### Requirement: Add moves the base of an attached worktree
With `--from <branch>` on an attached repository, `add` SHALL fetch `origin` with
pruning and, when the worktree has no uncommitted path and no commit on no remote
branch, move its branch to `origin/<branch>`, keeping its name, and print the path,
`branch:`, `from:` and `moved`. Otherwise it SHALL refuse, changing nothing, naming
each uncommitted path and the number of unpushed commits, unless `--force` is given,
which moves the branch and discards them. It never rebases.

#### Scenario: Base changed on the same worktree
- **WHEN** `worktrees/nakatomi-web` was added from `main` with nothing pending and `gemba worktree add nakatomi-web --from feature/a` runs
- **THEN** `worktrees/nakatomi-web` holds the files of `feature/a`, its branch is still `gemba/nakatomi/SUP-1`, the output reads `from: origin/feature/a` and `moved`, and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/base-changed-on-the-same-worktree.yaml`

#### Scenario: Base change refused with pending work
- **WHEN** `worktrees/nakatomi-web` holds an uncommitted file, or a commit not on any remote branch, and `gemba worktree add nakatomi-web --from feature/a` runs
- **THEN** the command exits 1, names the uncommitted path or the number of unpushed commits, and the worktree still holds the files and the commit it had
- **Cases**: keeps `tests/cases/worktree/base-change-refused-with-pending-work.yaml`

#### Scenario: Base change forced
- **WHEN** `worktrees/nakatomi-web` holds a commit not on any remote branch and `gemba worktree add nakatomi-web --from feature/a --force` runs
- **THEN** the command exits 0, the worktree holds the files of `feature/a`, and the commit is no longer in its history
- **Cases**: keeps `tests/cases/worktree/base-change-forced.yaml`

### Requirement: List shows the repositories that can be added
`gemba worktree list --available` SHALL run inside a harness and print the name of
every repository at the root of `repos_dir`, the ones `gemba worktree add` accepts,
attached or not, one per line in name order, or `no repositories` when there is none,
and exit 0. It SHALL refuse as `add` does when the personal config declares no
`repos_dir` or when `repos_dir` is not a folder, and SHALL write nothing.

#### Scenario: Repositories listed
- **WHEN** `repos_dir` holds `nakatomi-web/` and `nakatomi-api/` with a `.git`, `notes/` without one and `group/other/` with a `.git` one level below, and `gemba worktree list --available` runs inside a harness where `nakatomi-web` is attached
- **THEN** the output is `nakatomi-api` and `nakatomi-web`, one per line in that order, the tree is unchanged and the exit code is 0
- **Cases**: adds `tests/cases/worktree/repositories-listed.yaml`

#### Scenario: No repository to list
- **WHEN** `repos_dir` is a folder that holds no git repository at the root of a subfolder, and `gemba worktree list --available` runs inside a harness
- **THEN** the output is `no repositories` and the exit code is 0
- **Cases**: adds `tests/cases/worktree/no-repository-to-list.yaml`

#### Scenario: Repositories folder missing for the list refused
- **WHEN** the personal config declares no `repos_dir`, or one that names no folder, and `gemba worktree list --available` runs inside a harness
- **THEN** the command exits 1, names `repos_dir` and `gemba.local.yaml`, or says that `repos_dir` is not a folder, and writes nothing
- **Cases**: adds `tests/cases/worktree/repositories-folder-missing-for-the-list-refused.yaml`

### Requirement: Remove shows the state of a worktree
`gemba worktree remove <repo> [--yes] [--force]` SHALL run inside a harness and
refuse, deleting nothing, when nothing exists at `worktrees/<repo>` or the folder
there is not a worktree. It SHALL print the block `list` prints for it, then, when it
holds an uncommitted path or a commit on no remote branch and `--force` is not given,
`worktree not removed:` and one line per problem, and exit 1. Otherwise, without
`--yes`, it SHALL print `not removed: pass --yes to delete the worktree` and exit 0.

#### Scenario: State shown without deleting
- **WHEN** `gemba worktree remove nakatomi-web` runs for a worktree with nothing pending
- **THEN** the output is the block of the worktree and `not removed: pass --yes to delete the worktree`, the tree is unchanged and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/state-shown-without-deleting.yaml`

#### Scenario: Removal refused with pending work
- **WHEN** `worktrees/nakatomi-web` holds an uncommitted file, or a commit not on any remote branch, and `gemba worktree remove nakatomi-web --yes` runs
- **THEN** the output holds the block, `worktree not removed:` and the problem, the exit code is 1, and the worktree and its branch still exist
- **Cases**: keeps `tests/cases/worktree/removal-refused-with-pending-work.yaml`

#### Scenario: No worktree to remove
- **WHEN** `gemba worktree remove nakatomi-web` runs and nothing exists at `worktrees/nakatomi-web`, or a plain folder is there
- **THEN** the command exits 1, says which of the two it is, and deletes nothing
- **Cases**: keeps `tests/cases/worktree/no-worktree-to-remove.yaml`

### Requirement: Remove deletes the worktree with yes
With `--yes`, and with nothing pending or `--force`, `remove` SHALL remove the
worktree from the base repository, delete its folder and the branch that was checked
out in it, print `removed` and exit 0. The remote SHALL NOT be touched: its branches
are what they were.

#### Scenario: Worktree removed
- **WHEN** `gemba worktree remove nakatomi-web --yes` runs for a worktree with nothing pending
- **THEN** `worktrees/nakatomi-web` no longer exists, the base repository no longer holds `gemba/nakatomi/SUP-1`, the branches of `origin` are what they were, the output ends with `removed` and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/worktree-removed.yaml`

#### Scenario: Pending work discarded on request
- **WHEN** `worktrees/nakatomi-web` holds a commit not on any remote branch and `gemba worktree remove nakatomi-web --yes --force` runs
- **THEN** the worktree and its branch are gone, the branches of `origin` are what they were, and the exit code is 0
- **Cases**: keeps `tests/cases/worktree/pending-work-discarded-on-request.yaml`

### Requirement: A held worktree path is reported
When another program holds a path in the folder, `remove` SHALL retry briefly and,
when the path stays held, say the worktree was not removed, name the path, name an IDE
window or a terminal on the worktree as the likely cause, and say that running the
removal again finishes it, leaving the branch for that run.

#### Scenario: Worktree path held by another program reported
- **WHEN** a file of `worktrees/nakatomi-web` stays held by another program while `gemba worktree remove nakatomi-web --yes` runs
- **THEN** the output says the worktree was not removed, names the path left, names an IDE window or a terminal on the worktree as the likely cause, says that running the removal again finishes it, and the exit code is 1
- **Cases**: keeps the entry `harness-worktrees: Worktree path held by another program reported` of `tests/not-automated.yaml`

### Requirement: The agent looks up the repositories of the task
The `gemba-worktree` skill SHALL have the agent take the repositories the task needs
from the request, `task.md` and the notes, and look each one up in the output of
`gemba worktree list --available`. A name equal to a listed one SHALL be used as it
is; otherwise the agent SHALL ask the user to choose among the listed repositories the
request may mean, as the options of its question tool when it has one, and never
guess. The agent SHALL NOT read `repos_dir` itself.

#### Scenario: Repository found by its exact name
- **WHEN** the user asks to check out `nakatomi-web` and `gemba worktree list --available` prints `nakatomi-api` and `nakatomi-web`
- **THEN** the agent runs `gemba worktree add nakatomi-web` without asking which repository is meant
- **Cases**: adds the entry `harness-worktrees: Repository found by its exact name` to `tests/not-automated.yaml`

#### Scenario: Repository chosen by the user
- **WHEN** the user asks to check out "the web app" and `gemba worktree list --available` prints `nakatomi-api`, `nakatomi-web` and `nakatomi-web-legacy`
- **THEN** the agent asks the user to choose between `nakatomi-web` and `nakatomi-web-legacy`, as the options of its question tool when it has one, without listing `repos_dir` itself, and runs `gemba worktree add` only for the repository the user chooses
- **Cases**: adds the entry `harness-worktrees: Repository chosen by the user` to `tests/not-automated.yaml`

### Requirement: The agent adds the worktrees of the task
Following the `gemba-worktree` skill, the agent SHALL read the `worktree.add` block of
the task's workstream and follow its `rules` and `context` to choose `--from`, run
`gemba worktree add` once per repository, and relay what it prints. When the command
refuses, the agent SHALL relay the message, the repositories it names included, and
ask the user how to go on.

#### Scenario: Agent adds the repositories of the task
- **WHEN** the user asks, inside a harness, to check out, attach or add the repositories of the task
- **THEN** the agent names each repository by its folder name, chooses `--from` by the workstream's rules, runs the command once per repository and relays its output
- **Cases**: keeps the entry `harness-worktrees: Agent adds the repositories of the task` of `tests/not-automated.yaml`

#### Scenario: Agent follows the verb's rules
- **WHEN** workstream `code-reviews` declares `worktree.add.rules` containing "pass --from with the source branch of each merge request of the task"
- **THEN** the agent reads the source branch of each merge request and passes it with `--from` for a `code-reviews` task
- **Cases**: keeps the entry `harness-worktrees: Agent follows the verb's rules` of `tests/not-automated.yaml`

#### Scenario: Config change without skill change
- **WHEN** a workstream adds or changes its `worktree` block in the gemba config
- **THEN** the agent follows the new content without any edit to the `gemba-worktree` skill
- **Cases**: keeps the entry `harness-worktrees: Config change without skill change` of `tests/not-automated.yaml`

### Requirement: The agent keeps git inside the worktree
The skill and the guide SHALL have the agent never run `git worktree`, `git branch` or
any git command in the base repository, never push the local branch under its own
name, and push only to the branch an approved `external-action` note names, with
`git push -u origin HEAD:<branch>`, while it commits, fetches and pulls freely inside
a worktree.

#### Scenario: Agent never runs git against the base repository
- **WHEN** the agent needs a worktree created, moved or removed, or a branch created or deleted
- **THEN** it runs the `gemba worktree` verbs and never `git worktree` or `git branch`, and never runs git in `repos_dir`
- **Cases**: keeps the entry `harness-worktrees: Agent never runs git against the base repository` of `tests/not-automated.yaml`

#### Scenario: Agent pushes only to the branch a note names
- **WHEN** an approved `external-action` note says to push the work of a worktree to a branch of the remote
- **THEN** the agent runs `git push -u origin HEAD:<that branch>` and never `git push` alone or `git push origin HEAD`
- **Cases**: keeps the entry `harness-worktrees: Agent pushes only to the branch a note names` of `tests/not-automated.yaml`

### Requirement: The agent never forces first
The skill SHALL have the agent never pass `--force` on the first run of `add --from`
or `remove`, even when the user asks for it: it runs without the flag, relays what the
command reports as pending, and passes `--force` only after the user confirms that
list. Removing with `--yes` SHALL follow a yes from the user in the chat, as the
removal of a harness does.

#### Scenario: Agent never forces first
- **WHEN** the user asks to move the base or remove a worktree and says to force it
- **THEN** the agent runs the command without `--force`, relays what it reports as pending, and passes `--force` only after the user confirms that list
- **Cases**: keeps the entry `harness-worktrees: Agent never forces first` of `tests/not-automated.yaml`
