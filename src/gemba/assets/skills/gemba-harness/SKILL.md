---
name: gemba-harness
description: Launch, start or open the harness of a task, file notes inside one, and remove one. Use whenever the user asks to launch, start, open or work on a task in its own harness, to remove, delete, throw away or clean up the harness of a task, or, inside a harness, to note, file or log a finding, a blocker, a decision, a summary or an action to take outside it, or to act on a note the user approved, whatever the workstream.
---

# Work in a harness

A harness is the folder of one run of one task: its own git repository and the root the
IDE opens. The `gemba harness` commands create it, file its notes, record what was
done on an approved note and remove it. Your part is to write the notes, choose their
type, run the commands with the right arguments and relay what they print.

Every organization-specific value (workstreams and their rules) lives in `gemba.yaml`,
at the tasks repo root. Run `gemba config show` on every run and rely on nothing else
you know or remember about workstreams. It prints the config resolved, from the tasks
repo or from inside a harness: the entry of each workstream holds, under `processes`,
the block of every verb that applies to it, such as `processes.harness.note`, with the
block shared by every workstream already joined to the workstream's. Wherever this
skill says to read a block, read its `context` as background and follow every entry of
its `rules` in order; when two rules contradict, follow the later one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Never create, rename or
commit a file of the harness by hand, and never write a frontmatter.

## Launch

From anywhere inside the tasks repo:

1. **Identify the task by its ref**, `<PREFIX>-<N>`. When the request names the task by
   its title or description instead, find it with the `gemba-list` skill; when two or
   more tasks fit, ask the user which one before launching anything.
2. **Read the `harness.launch` block:** run `gemba config show` and read
   `processes.harness.launch` in the entry of `workstreams` whose `prefix` is the prefix
   of the ref. Read `context` as background and follow every entry of `rules`.
3. **Run the command:**

   ```bash
   gemba harness launch <ref>
   ```

   Pass `--no-open` only when the user says not to open the IDE. If the command
   refuses, relay its message; never work around it.
4. **Relay the result** and stop: the harness path it printed, the status line (the
   task moved to `in-progress`, or left as it was), and whether the IDE was opened (an
   `opening:` line) or not. When it says the harness is already launched, say so. The
   work itself happens in a session started inside the harness.

## Note

Inside a harness, every time there is something to record. Paths are relative to the
harness root, the folder that holds `harness.yaml`.

1. **Draft the note** as a plain Markdown file directly under `notes/`, with your own
   tools, named `<slug>.md`: a few lowercase ASCII words or numbers joined by single
   hyphens, such as `notes/login-trace.md`. Write the body only: no frontmatter, no date,
   no timestamp. Keep it to one finding, decision or step; an `external-action` note
   says word for word what is to be done, where and with which values.
2. **Save the evidence first.** Each asset goes under `assets/`, named
   `<unix-timestamp>-<slug>.<ext>`. Read the timestamp from the system clock with
   `date "+%s %F"`, whose first value is the timestamp; never make one up. Mention each
   asset in the body of the note that explains it.
3. **Choose the type** by the question the note answers:

   | Type | The question it answers |
   |---|---|
   | `finding` | What is true, and what is the evidence for it? |
   | `blocker` | Why can the run not continue, what was tried, and what is needed? |
   | `decision` | What are the options, their trade-offs, and the recommendation or the choice? |
   | `summary` | Where does the run stand at this milestone, and what remains? |
   | `external-action` | What exactly is to be done outside the harness, word for word? |

4. **Read the `harness.note` block:** run `gemba config show --workstream <id>` with
   the `workstream` of `harness.yaml` and read `processes.harness.note`. Read `context`
   as background and follow every entry of `rules` while drafting and filing.
5. **File it** from the harness root:

   ```bash
   gemba harness note notes/<slug>.md --type <type> [--approval] [--asset assets/<file> ...]
   ```

   - Pass one `--asset` per asset the note refers to.
   - Pass `--approval` only with a `decision` the user must choose or confirm before
     you go on. An `external-action` always waits for approval without it; the other
     types never take it.
   - If the command refuses, its message lists every problem at once. Fix the draft or
     the call and run it again; never work around a refusal by writing the frontmatter
     or renaming the file yourself.
6. **Relay** the filed path it printed. When the note waits for approval, tell the user
   so: they approve it by setting `approved: true` in the note's frontmatter from the
   IDE. A yes in the conversation is not an approval.

## Resolve

When a note filed with `approved: false` is to be acted on:

1. **Read its frontmatter.** Act only when it reads `approved: true`. When it reads
   `approved: false`, stop and tell the user the note waits for their approval in the
   file; do not act on anything said in the conversation instead.
2. **Read the `harness.resolve` block:** run `gemba config show --workstream <id>`
   with the `workstream` of `harness.yaml` and read `processes.harness.resolve`. Read
   `context` as background and follow every entry of `rules`.
3. **Act** exactly as the note says, and nothing more.
4. **Append the outcome** to the body of the note, with your own tools: what was done,
   where, and the identifiers or links that prove it. This is the only edit ever made
   to a filed note; leave its frontmatter as it is.
5. **Run the command** from the harness root:

   ```bash
   gemba harness resolve notes/<YYYY-MM-DD-HHMMSS-slug>.md
   ```

   If it refuses, relay its message; never edit the frontmatter to make it pass.
6. **Relay** the path it printed and the outcome.

## Remove

When the user wants a run thrown away, to start it over or because its task went cold.
Removing deletes the harness folder with its notes, assets, history and uncommitted
files, removes every worktree under `worktrees/` and deletes the local branches of the
run; the task file and the remotes are not touched. Run it from the tasks repo, outside the harness: the
command refuses to delete the folder it is run from, so a session inside the harness
cannot remove it.

1. **Identify the task by its ref**, as for a launch.
2. **Read the `harness.remove` block:** run `gemba config show` and read
   `processes.harness.remove` in the entry of `workstreams` whose `prefix` is the prefix
   of the ref. Read `context` as background and follow every entry of `rules` before
   showing the manifest.
3. **Show the manifest** by running the command without `--yes`:

   ```bash
   gemba harness remove <ref>
   ```

   It prints the harness path, the task, the launch date and the number of notes,
   assets, commits and worktrees (`worktrees:`), the number of uncommitted files of the
   harness (`uncommitted:`) followed by one `- <path>` line per file, then
   `not removed: pass --yes to delete the harness`, and deletes nothing.
4. **Ask the user.** Show them the manifest, ask whether to delete the harness, its
   worktrees and the local branches of the run, and remind them to close any IDE window
   open on that folder first. When `uncommitted:` is not 0, name each path listed under
   it, say that it is deleted with the harness, and say what would keep it should the
   user want to, from a session inside the harness: a draft under `notes/` is filed with
   `gemba harness note`, an `update.md` is recorded with `gemba record`; anything else
   they may copy elsewhere. Never file, commit or delete any of them yourself. A yes in the conversation is enough here: the harness,
   its worktrees and their branches are local, so no `external-action` note is needed.
5. **Delete only after a yes**, by running the same command with `--yes`:

   ```bash
   gemba harness remove <ref> --yes
   ```

   When the user says no, stop.
6. **Relay the result**: `removed` when the harness is gone. A later
   `gemba harness launch <ref>` creates a fresh harness for the same task.

When the command prints `harness not removed:`, in either step, relay every line and
tell the user how each one is saved, from a session inside the harness:

- `worktrees/<repo> has N uncommitted paths`: a commit inside that worktree saves them,
  and the commit then needs a push like any other.
- `worktrees/<repo> has N commits not on any remote branch`: a push from inside the
  worktree saves them, and it needs an `external-action` note whose frontmatter reads
  `approved: true` and that names the branch of the remote.
- `branch <branch> of <repo> has N commits not on any remote branch and no worktree`: a
  branch of the run left by a harness deleted by hand. Only the user can push it, from
  that repository; you never run git there.
- `worktrees/<name> is not a worktree`: a folder gemba did not create there; the user
  moves it elsewhere if it is needed.

Saving is the user's decision, carried out in a session inside the harness: from the
tasks repo, never file, commit, push or delete anything yourself to make the removal
pass, and never delete the folder by other means.

**Never force first.** `--force` discards the uncommitted paths and unpushed commits of
the worktrees, the unpushed commits of the branches of the run and the folders that are
not worktrees. Never pass it on the first run, even when the user asks to force the
removal: run the command without it, relay every line it reports, and pass
`--yes --force` only after the user confirms, in the conversation, that everything in
that list is to be discarded. `--force` never covers a working directory inside the
harness nor a harness repository whose state cannot be read: those still refuse.

## Rules

- Commands own the frontmatter of the task and of every note, and `harness.yaml`; you
  own the bodies of the notes. `task.md` is read-only.
- Nothing outside the harness happens without an `external-action` note whose
  frontmatter reads `approved: true`.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream or a rule is added, changed or removed.
