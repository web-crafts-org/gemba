---
name: gemba-worktree
description: Check out the repositories of a task as git worktrees inside its harness, list them and remove them. Use whenever, inside a harness, the user asks to check out, attach, add or open a repository of the task, to start a repository from another branch, to list or show the worktrees, their branches or what is not pushed, or to detach, drop or remove a worktree, whatever the workstream.
---

# Work on repositories in worktrees

A worktree is a checkout of another repository under `worktrees/` of the harness, on
one local branch of the run that gemba names after the task. The `gemba worktree`
commands create, move, list and remove the worktrees and their branches; every git
command against the repository a worktree comes from is theirs. Your part is to choose
the repositories and the base branch, run the commands, relay what they print, and do
the work of the task inside the worktrees.

Every organization-specific value (the repositories folder, the workstreams and their
rules) lives in `gemba.yaml`, at the tasks repo root. Run
`gemba config show --workstream <id>`, with the `workstream` of `harness.yaml`, on every
run and rely on nothing else you know or remember about repositories, branches or
workstreams. It prints the config resolved, from anywhere inside the harness:
`repos_dir` at the top level, and in the entry of the workstream, under
`processes.worktree`, the block of every verb, such as `processes.worktree.add`, with
the block shared by every workstream already joined to the workstream's. Wherever this
skill says to read a block, read its `context` as background and follow every entry of
its `rules` in order; when two rules contradict, follow the later one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Every verb runs inside a
harness, from its root or any folder below it. Never run `git worktree` or
`git branch`, and never run any git command in the repository a worktree comes from.

## Add

1. **Find the repositories the task needs** in `task.md` and in the notes of the run.
   Name each one by its folder name under the `repos_dir` that `gemba config show`
   prints, such as `nakatomi-web`. When a name is not clear from them, ask the user; never
   browse `repos_dir` or any folder above the harness to guess it.
2. **Read the `worktree.add` block**, `processes.worktree.add` of the document. Read
   `context` as background and follow every entry of `rules`: they say which branch each
   repository starts from.
3. **Choose the base.** Without `--from`, the worktree starts at the default branch of
   `origin`. Pass `--from <branch>` when the rules, the task or the user name another
   branch of `origin`. Only a branch is a base: never pass a tag or a commit.
4. **Run the command** once per repository:

   ```bash
   gemba worktree add <repo> [--from <branch>]
   ```

5. **Relay** what it printed: the worktree path, `branch:`, `from:` and `created`, or
   `already attached, worktree unchanged` when the repository is already checked out in
   this harness. When it refuses, relay every line, the repositories it names as found
   at the root of `repos_dir` included, and ask the user how to go on; never work
   around a refusal.

## Branches

- The branch of a worktree is local: gemba names it after the run, it exists only on
  this machine and it is never pushed under its own name.
- It starts with no upstream. Inside the worktree, commit, fetch and pull freely; a
  pull needs the upstream that the first push sets.
- A push reaches the remote, so it needs an `external-action` note whose frontmatter
  reads `approved: true` and that names the branch of the remote. The push always names
  its target, `git push -u origin HEAD:<the branch the note names>`; the first one sets
  the upstream, which `gemba worktree list` then shows. Never run `git push` alone or
  `git push origin HEAD`.
- To start again from another base, run `gemba worktree add <repo> --from <branch>` on
  the repository already attached: it moves the branch of the run to that base and
  keeps its name. It is not a rebase: it refuses while anything is uncommitted or on no
  remote branch, and even after a push it discards the local tree. To carry your
  commits onto another base instead, rebase inside the worktree with
  `git rebase --onto origin/<new base> origin/<old base>`.

## List

Read the `worktree.list` block, `processes.worktree.list` of the document, and run:

```bash
gemba worktree list
```

For each worktree it prints its path, `branch:`, `upstream:` (`none` until a push sets
it), `uncommitted:`, the number of paths not committed, and `unpushed:`, the number of
commits on no remote branch. Every value is read from git when it runs. Relay them; a
folder listed as `not a worktree` was not created by gemba, so tell the user. With no
worktree it prints `no worktrees`.

## Remove

1. **Read the `worktree.remove` block**, `processes.worktree.remove` of the document.
   Read `context` as background and follow every entry of `rules` before showing the
   state.
2. **Show the state** by running the command without `--yes`:

   ```bash
   gemba worktree remove <repo>
   ```

   It prints the block `list` prints for that worktree, then
   `not removed: pass --yes to delete the worktree`, and deletes nothing.
3. **Ask the user.** Show them the state, ask whether to remove the worktree and its
   local branch, and remind them to close any editor window open on that folder first.
   A yes in the conversation is enough: the worktree and its branch are local.
4. **Remove only after a yes**, by running the same command with `--yes`:

   ```bash
   gemba worktree remove <repo> --yes
   ```

   When the user says no, stop. Relay `removed`: the worktree and its local branch are
   gone, and the remote is what it was.

## When work is pending

`gemba worktree add --from` prints `worktree not moved:` and `gemba worktree remove`
prints `worktree not removed:` while the worktree holds uncommitted paths or commits on
no remote branch. Relay every line and say how each is saved: uncommitted paths by a
commit inside the worktree; commits on no remote branch by a push through an approved
`external-action` note. Never commit, push or delete anything to make the command pass.

**Never force first.** `--force` discards work. Never pass it on the first run of
`add --from` or `remove`, even when the user asks to force it: run the command without
it, relay what it reports as pending, and pass `--force` only after the user confirms,
in the conversation, that everything in that list is to be discarded. The same holds
for `add --force` without `--from`, which deletes and recreates a branch of the run
left without a worktree, discarding its commits.

## Rules

- The commands own the worktrees and the branches of the run. Never run `git worktree`
  or `git branch`, and never run git in the repository a worktree comes from.
- Nothing reaches the remote without an `external-action` note whose frontmatter reads
  `approved: true`.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream, a rule or the repositories folder is added, changed or removed.
