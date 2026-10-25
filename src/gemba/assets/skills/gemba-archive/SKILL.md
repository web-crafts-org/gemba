---
name: gemba-archive
description: Archive tasks of this obeya that went cold, so that they leave the listings. Use whenever the user asks to archive tasks, to put away cold, old or inactive tasks, or to clean up the task list, whatever the workstream.
---

# Archive tasks

A task that went cold moves, unchanged, into the `archive/` folder of its workstream:
it leaves the listings and stays findable on request. The `gemba archive` command moves
the files, one or many in one call, whatever their status, and refuses the ones it
cannot move. Your part is to find the tasks with the user, get their confirmation, run
the command once and relay every line it prints.

Every configured value (workstreams and their rules) lives in the gemba config at the
obeya root. Run `gemba config show` on every run and rely on nothing else
you know or remember about workstreams: it prints the config resolved, with the blocks
shared by every workstream already joined to those of each one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Never move a task file
yourself, with `mv`, `git mv` or any other tool.

## Process

From anywhere inside the obeya.

1. **Take the refs the user names.** When the user names the tasks by ref, go to
   step 4 with those refs. When they name them by title or description, find their
   refs with the `gemba-list` skill.
2. **Find the candidates** when the user asks to archive what went cold. Settle the
   date first: tasks not updated since that date are cold. Use the date the user
   names; when they name none, propose one, such as a month before today (read
   today's date from the environment: `date +%F` in a POSIX shell,
   `Get-Date -Format yyyy-MM-dd` in PowerShell), and wait for them to confirm or change
   it. Then run:

   ```bash
   gemba list --updated-to <date> --status done
   ```

   Pass one `--status` per status the user names instead of `done` when they want
   other statuses archived too, such as blocked tasks nobody came back to.
3. **Show the candidates and confirm.** Show them as a short table, one row per task
   with its ref, title, status and last update, and ask the user which to archive. Let
   them confirm all, drop some or stop. When there are none, say so with the date and
   statuses you used, and stop.
4. **Read the `archive` block** of every workstream involved: run `gemba config show`
   and read `processes.archive` of each of their entries. Read `context` as background
   and follow every entry of `rules`, in order, before proposing and before running the
   command; when two rules contradict, follow the later one, and follow a rule shared by
   every workstream once. When a rule excludes a task, tell the user why and leave it
   out.
5. **Run the command once** with every confirmed ref:

   ```bash
   gemba archive <ref> [<ref> ...]
   ```

   Each ref is handled on its own: the command prints `archived: <new path>` for each
   task it moved and `not archived: <ref> <reason>` for each one it refused, and exits
   1 when it refused any.
6. **Relay every line.** Give the paths that were archived and every `not archived:`
   line with its reason. When a task was refused because its harness still exists, say
   that `gemba harness remove <ref>` clears it, through the `gemba-harness` skill, and
   that the task can be archived once its harness is gone. The user reviews and
   commits the moves in the obeya.

## Rules

- The command is the only way a task file moves into `archive/`. Never move, rename or
  edit a task file yourself.
- Archiving changes no byte of the task: its status and `updated_at` stay as they were.
- An archived task is left out of `gemba list` unless `--include-archived` is given.
  Bringing one back out of `archive/` is the user's own move, made by hand; tell them
  so when they ask, and do not do it for them.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream or a rule is added, changed or removed.
