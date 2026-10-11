---
name: gemba-record
description: Record the day's work on the task of this harness, distilled from its notes. Use whenever, inside a harness, the user asks to record, log or backfill what was done on the task today, yesterday or on a given date, or to update the task from the notes, whatever the workstream.
---

# Record the day

The notes of a harness are the memory of the run; the task file is the durable record,
with one `### YYYY-MM-DD` subsection per day under `## Updates`. Recording promotes one
day of the run into the task: you distill the notes of that day into a few bullets in a
draft, and `gemba record` writes them into the task and moves its `updated_at` in the
same step. Your part is to decide what the bullets say; the command decides where they
go.

Every organization-specific value (workstreams and their rules) lives in `gemba.yaml`,
at the tasks repo root. Run `gemba config show` on every run and rely on nothing else
you know or remember about workstreams: it prints the config resolved, with the blocks
shared by every workstream already joined to those of each one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Never edit `task.md`.

## Process

Inside the harness of the task. Paths are relative to the harness root, the folder that
holds `harness.yaml`.

1. **Choose the date.** Today, unless the user names another day. Read today's date
   with `date +%F` and resolve "yesterday" or a weekday against it. When several dates
   are to be recorded, take them oldest first and go through steps 2 to 8 once per
   date, each with its own draft and its own run.
2. **Read the task and the notes of the date.** Read `task.md` for what the task is and
   what is already recorded. Then read every note under `notes/` whose name starts with
   the date, `notes/<YYYY-MM-DD>-*.md`, in the order of their names, whatever their
   type. Notes of other dates are context, not content for this date.
3. **Stop when there is nothing to record.** When no note carries the date and this
   session did nothing on the task that day, tell the user there is nothing to record
   for that date and stop: write no draft and run no command. When this session did
   work that day that no note holds yet, file that note first with the `gemba-harness`
   skill, so that the notes stay the only source of the update.
4. **Read the `record` block** of the task's workstream: run
   `gemba config show --workstream <id>` with the `workstream` of `harness.yaml`, from
   anywhere inside the harness, and read `processes.record`. Read `context` as
   background and follow every entry of `rules`, in order, while distilling and
   drafting; when two rules contradict, follow the later one.
5. **Distill one to five bullets** of what moved that day: what was found, decided,
   changed or delivered, what is blocked and on whom. Each bullet must make sense to
   someone who never opens the harness: name the system, the file, the merge request or
   the person, never a note or an asset of the harness. Leave out process noise: notes
   filed, files read, commands that changed nothing, attempts that led nowhere unless
   their failure is the news. Say nothing the notes do not support.
6. **Write the draft** at the harness root, `update.md`, with your own tools: bullets
   only, each starting with `- `, and a bullet that runs over several lines continued
   by lines indented by two spaces. No heading, no date, no frontmatter, no other text.
   Never write it under `notes/` or `assets/`.
7. **Run the command** from the harness root:

   ```bash
   gemba record update.md [--date YYYY-MM-DD]
   ```

   - Pass `--date` whenever the date is not today.
   - The command writes the bullets under `### <date>` in the task, after any bullets
     already recorded for that date, moves `updated_at` to the date when it is later,
     deletes `update.md` and commits nothing.
   - If it refuses, its message lists every problem at once. For a problem with the
     draft or the date, fix the draft or the call and run it again. For a problem with
     the `## Updates` section of the task, tell the user what the message says: the
     task file is theirs to fix, and the draft stays for the retry. Never work around a
     refusal by editing `task.md`.
   - If it says the task is recorded but the draft could not be deleted, delete
     `update.md` yourself and do not run the command again: a second run would write
     the same bullets twice.
8. **Relay the result:** the task path and the `updated_at` line the command printed,
   which says whether the date moved or was left unchanged because the task was
   already updated later, and the bullets you recorded. The user reviews and commits
   the change in the tasks repo.

## Rules

- `task.md` is read-only: never edit it, and never write a `### YYYY-MM-DD` heading or a
  frontmatter value by hand. The command is the only writer of the update.
- Record only what the notes of the date support; when in doubt, leave it out.
- One draft and one run per date, oldest date first.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream or a rule is added, changed or removed.
