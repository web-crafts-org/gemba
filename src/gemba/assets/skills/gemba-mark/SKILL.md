---
name: gemba-mark
description: Mark a task done, blocked, open or in progress. Use whenever the user says a task is finished, completed, closed or done, that it is stuck, waiting or blocked, or asks to mark, finish, close, complete, block, unblock, reopen or resume a task, from the obeya or inside its harness, whatever the workstream.
---

# Mark a task

A task moves between four statuses after its creation: `open`, `in-progress`, `blocked`
and `done`. The `gemba mark` command is the one writer of that move: it sets `status`,
writes `done_at` when the task reaches `done` and removes it when the task leaves
`done`, moves `updated_at` forward, and rewrites nothing but the frontmatter. Your part
is to find the task, turn the user's words into one status, run the command and relay
what it prints.

Every configured value (workstreams and their rules) lives in the gemba config at the
obeya root. Run `gemba config show` on every run and rely on nothing else
you know or remember about workstreams: it prints the config resolved, with the blocks
shared by every workstream already joined to those of each one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Never edit the
frontmatter of a task by hand.

## Process

From the obeya or from inside the harness of the task. Inside a harness, the
folder that holds `harness.yaml` is the harness root.

1. **Identify the task by its ref**, `<PREFIX>-<N>`. Inside a harness, the task is the
   one named by `ref` in `harness.yaml`, unless the user names another. From the obeya,
   take the ref the user gives; when they name the task by its title or
   description instead, find it with the `gemba-list` skill. When two or more tasks
   fit, ask the user which one before marking anything.
2. **Choose the status** from the user's words:

   | The user says | Status |
   |---|---|
   | finished, completed, closed, done | `done` |
   | stuck, waiting, blocked | `blocked` |
   | reopen, or bring back a `done` task, without saying the work resumes now | `open` |
   | continue, resume, unblock, working on it now | `in-progress` |

   When the words fit none of these rows, or fit two, ask the user which status they
   mean.
3. **Offer to record the day first.** Only inside a harness and only when the status is
   `done`: read today's date from the environment (`date +%F` in a POSIX shell,
   `Get-Date -Format yyyy-MM-dd` in PowerShell), then read `task.md`. When its
   `## Updates` section has no `### <today>` subsection and `notes/` holds notes of
   today (`notes/<today>-*.md`), tell the user the day is not recorded yet and offer to
   record it with the `gemba-record` skill before marking. If they accept, record the
   day, then go on. If they decline, go on and mark the task anyway.
4. **Read the `mark` block** of the task's workstream: run `gemba config show` and
   take the entry of `workstreams` whose `prefix` is the prefix of the ref; for the task
   of the harness, `gemba config show --workstream <id>` with the `workstream` of
   `harness.yaml` prints that entry alone. Read `processes.mark` of that entry: `context`
   as background, and every entry of `rules` to follow, in order, before running the
   command; when two rules contradict, follow the later one.
5. **Run the command:**

   ```bash
   gemba mark <ref> <status> [--date YYYY-MM-DD]
   ```

   - Pass `--date` only when the user says the change happened on a past day, such as
     "I finished it yesterday"; resolve that day against today's date, read from the
     environment (`date +%F` in a POSIX shell, `Get-Date -Format yyyy-MM-dd` in
     PowerShell). Without it the change is dated today.
   - If the command refuses, its message lists every problem at once. Fix the call
     when the problem is yours (the ref, the status, the date) and run it again. When
     it says the task is archived, relay the message and stop: whether to move the
     file out of `archive/` is the user's decision, not yours.
6. **Relay the result** and stop: the task path, the `status:` line, the `done_at:` line
   when there is one (the date written, or `removed`) and the `updated_at:` line. When
   the command says the status was left as it was, say the task already had that
   status.

## Rules

- Commands own the frontmatter: never write `status`, `done_at` or `updated_at` by
  hand, in `task.md` or in the task file.
- Marking writes no update. What was done belongs under `## Updates`, through the
  `gemba-record` skill; marking never replaces recording.
- Marking does not touch the harness. A task reopened to `open` moves to `in-progress`
  by itself the next time its harness is launched; a `done` task cannot be launched
  until it is marked `open` or `in-progress`.
- In an obeya with a team, only the owner of a task marks it. When the command refuses a
  task because it belongs to another member, relay the refusal, suggest asking its
  owner, and never edit the task file to get around it.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream or a rule is added, changed or removed.
