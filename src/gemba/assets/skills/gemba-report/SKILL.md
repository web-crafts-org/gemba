---
name: gemba-report
description: Report what was done in a period, a day, a week or a month, across every task of this obeya, with every count and total taken from gemba report. Use whenever the user asks for the daily report, a standup, an end-of-day, weekly or monthly summary, "what did I do today", "yesterday", "this week" or "in September", what the team did, or how much of an amount went to each workstream, member, status or value of a field in a period, whatever the workstream.
---

# Report a period

The report answers what was done in a period, one day or several consecutive days,
across every task, and how much of each amount went where. `gemba list` finds the tasks
alive in the period, each task file records its work under `## Updates`, one
`### YYYY-MM-DD` subsection per day, and `gemba report` computes every count and every
sum over a selection of tasks. Your part is to list the candidates, read the
subsections of the period, take every number from `gemba report`, and compose the
report without adding anything the files and the commands do not say.

Every configured value (workstreams, prefixes, metadata fields, rules) lives in the
gemba config at the obeya root. Run `gemba config show` on every run and rely on nothing
else you know or remember about workstreams or fields: it prints the config resolved,
with the fields and the blocks shared by every workstream already joined to those of
each one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Do not build the list of
candidates by reading the task folders yourself, and do not compute a number yourself.

## Process

1. **Locate the config.** Walk up from the current folder to the nearest `gemba.yaml`.
   That folder is the obeya root. If there is none, stop and tell the user that no
   gemba config was found.
2. **Choose the period**, from F to T, both included. Today, unless the user names
   another day or period. Read today's date from the environment (`date +%F` in a
   POSIX shell, `Get-Date -Format yyyy-MM-dd` in PowerShell) and resolve "yesterday",
   a weekday, "this week", "last week", a month or "this month" against it; a week
   starts on Monday, and a period never ends after today. A day is F equal to T. Several
   periods give one report each, oldest first, and steps 3 to 9 run once per period.
3. **List the candidates** of the period with exactly this command, from anywhere
   inside the obeya:

   ```bash
   gemba list --to T --updated-from F
   ```

   It returns the tasks created on or before T and updated on or after F, which are
   exactly the tasks alive in the period. Add `--include-archived` only when the user
   asks for archived tasks too, and no other filter but the owner below: the report
   covers every workstream. Read only the tasks it returns. If the command refuses,
   relay its message and stop.

   Run `gemba config show` first. When it holds `team`, the obeya is shared by a team,
   and the report covers the user's own work: add `--owner <me>`, with `me` read from
   that document, to this command and to every `gemba report` of step 6. When the user
   asks about another member, use `--owner` with that member's folder name, the key of
   their entry under `team`. When they ask about the whole team, pass no `--owner` and
   group the numbers of step 6 `--by owner`, so that each member's total and the team's
   come from the command. When `me` is `null` and the user asks about their own work,
   ask which member they are.
4. **Read the signals of each candidate.** Open the file at the record's `path` and
   take:
   - the bullets of every `### D` subsection under `## Updates` whose date D lies from F
     to T: the work of the period, day by day;
   - the record's `date` from F to T: the task was created in the period;
   - the record's `done_at` from F to T: the task was finished in the period.

   A candidate with none of the three has nothing recorded for the period.
5. **Read the `report` block** of every workstream that has candidates: run
   `gemba config show` and read `processes.report` of each of their entries. Read
   `context` as background and follow every entry of `rules`, in order, when composing
   the entries of that workstream and when choosing a selection for its numbers; when
   two rules contradict, follow the later one. A rule shared by every workstream
   appears in every entry: follow it once.
6. **Take the numbers from `gemba report`** whenever the report states a count, a sum or
   a total, and whenever the user asks how much of something went where. The command
   takes the filters of `gemba list` and prints one JSON object:

   ```bash
   gemba report --done-from F --done-to T [--owner <member>] \
     [--by <grouping> ...] [--sum <field> ...]
   ```

   - **Selection.** A number field holds one total per task, so the totals of a period
     are those of the tasks finished in it: select with `--done-from F --done-to T`
     unless the user asks for another selection (created in the period is
     `--from F --to T`; a date field in the period is `--where-from <field>=F
     --where-to <field>=T`) or the `report.rules` of the workstreams involved say
     otherwise. Add `--include-archived` when the user asks for archived tasks too.
     Narrow it with `--workstream`, `--status` or `--where` when the question does.
   - **Groupings.** `--by workstream`, `--by status`, `--by owner` in an obeya with a
     team, or `--by <field>` for a field whose declared `type` is `text` or `boolean`,
     when the user asks for amounts per workstream, per member, per status or per value
     of a field. Repeat `--by` to group within
     groups. Map the user's words to fields by the `name` and `description` of every
     field under `metadata` in the entries of the document of step 5, and write every
     value by its field's declared type, as `gemba list` takes them.
   - **Sums.** `--sum <field>` for a field whose declared `type` is `number`.
   - **Reading.** `groups` holds one entry per combination of grouping values: `key`
     (each grouping and its value, `null` for tasks without one), `tasks`, `refs` and,
     per summed field, `total` and `missing`, the tasks without a number to add.
     `total` holds the same over every selected task, each counted once. A task whose
     text field holds a list is counted in the group of each item, so the groups may add
     up to more than the total: say so when you report both.
   - If the command refuses, its message lists every invalid filter, grouping and sum at
     once. Fix the call and run it again, asking the user only when the request itself
     is unclear.

   State only the numbers the command printed: each total, each count, and the tasks
   without a value whenever `missing` is not zero. Never add, subtract, average or
   compare numbers yourself; when the user wants a total the command did not print,
   such as two groups together, run `gemba report` again with the selection or the
   grouping that yields it. Say which selection the numbers come from, such as "tasks
   finished from F to T".
7. **Compose the report** in the language the user converses in, grouped by
   workstream unless the user asks for another grouping, with one entry per task that
   has a signal for the period: its title, ref and current status, with its owner when
   the report covers more than one member, then the bullets of the period, condensed
   rather than transcribed. A task created or finished in the
   period says so, without bullets made up for it. When no candidate has a signal for
   the period, say plainly that nothing was recorded for it. This layout reads well:

   ```
   Report for <F> to <T>

   <workstream>
     <ref>  <title>  <status>
       - <condensed bullet>
       - created on <date> | finished on <done_at>

   Numbers (<the selection used>)
     <group>  <count> tasks  <field>: <total> (<missing> without a value)

   Updated recently, nothing recorded from <F> to <T>
     <ref>  <title>  <status>  updated <updated_at>
   ```

   The layout is guidance, not a contract: adapt it to the question asked; nothing
   depends on it. A question about amounts alone gets the numbers alone.
8. **List the gaps at the end:** every candidate with nothing recorded for the period,
   under a heading saying they were updated recently with nothing recorded for that
   period, with no bullets, so the user can record what is missing.
9. **Relay every problem** that `gemba list` or `gemba report` returned, alongside the
   report: give each path and its problem. A file that is not a valid task is left out
   until it is fixed; a value that is not of its field's type is grouped under `null`
   and counted as missing until it is set again with `gemba set`.

## Filling a gap

The report never fills a gap. To record what a task is missing, point the user to the
`gemba-record` skill, used in one of two places: inside the harness of that task,
`harnesses/<workstream>/<task file name without .md>/`, for the work of its run, from
its notes; or from the obeya, for work done outside a run, such as a meeting or a
review, from what the user tells it. A metadata value that is missing or wrong is set
with the `gemba-set` skill.

## Rules

- Read, never write: do not edit, move or create any file, and do not commit.
- State no activity that a subsection of the period, a creation date or a `done_at`
  does not support, and no number that `gemba report` did not print. A task with
  nothing recorded is a gap to show, not one to fill from memory.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream, field or rule is added, changed or removed.
