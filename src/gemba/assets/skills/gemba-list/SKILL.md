---
name: gemba-list
description: List, find or count tasks in this obeya. Use whenever the user asks to list, show, find, count or filter tasks, or asks "what do I have open", "what am I working on" or what happened on a task, whatever the workstream.
---

# List tasks

Answer questions about the tasks in the obeya. The `gemba list` command scans the
task folders, validates every file and applies the filters. Your part is to turn the
request into filters, run the command, open task files only when the answer needs
their body, and present the result.

Every configured value (workstreams, prefixes, metadata fields, rules) lives in the
gemba config at the obeya root. Run `gemba config show` on every run and rely on nothing
else you know or remember about workstreams or fields: it prints the config resolved,
with the fields and the blocks shared by every workstream already joined to those of
each one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Do not run the package's
Python files directly and do not build the list by reading the task folders yourself.

## Process

1. **Locate the config.** Walk up from the current folder to the nearest `gemba.yaml`.
   That folder is the obeya root. If there is none, stop and tell the user that no
   gemba config was found.
2. **Choose the workstreams.** Run `gemba config show` from anywhere inside the obeya:
   it prints the config resolved as one JSON document, or the problem when the
   config is invalid, which you relay before stopping. When the request names an area
   of work, compare it with the `description` of every entry of `workstreams` in the
   document and pass one `--workstream` per entry that covers it. When the request
   names no area, or you cannot tell which entries cover it, pass no `--workstream`:
   every workstream is listed. Listing is read-only, so listing too much is cheaper
   than asking.
3. **Read the `list` block** of every chosen workstream (of every workstream when you
   pass none): `processes.list` of its entry in the document. Read its `context` as
   background and follow every entry of its `rules`, in order, when you run the command
   and present the result; when two rules contradict, follow the later one. A rule
   shared by every workstream appears in every entry: follow it once.
4. **Map the request to filters.** Resolve relative dates against today's date (read
   it from the environment if you are not sure of it: `date +%F` in a POSIX shell,
   `Get-Date -Format yyyy-MM-dd` in PowerShell); a week starts on Monday.

   | The user says | Filters |
   |---|---|
   | open, pending, active, "what do I have", "what am I working on" | `--status open --status in-progress --status blocked` |
   | one or more statuses by name (open, in progress, blocked) | one `--status` per named status |
   | done, finished, closed | `--status done --include-archived` |
   | a task ref, `<PREFIX>-<N>` | `--ref <PREFIX>-<N> --include-archived` and no other filter |
   | created on a day or in a period | `--from` and `--to` (the creation date) |
   | updated, touched or worked on in a period | `--updated-from` and `--updated-to` |
   | finished in a period | `--done-from` and `--done-to`, with `--include-archived` |
   | what could have been worked on on a past day D | `--to D --updated-from D` |
   | archived tasks, everything, including archived | `--include-archived` |
   | a value of a metadata field | `--where <field>=<value>` |
   | a span of a number or date field: at least, at most, between, in a period | `--where-from <field>=<low>`, `--where-to <field>=<high>`, or both |

   - A time word restricts dates only when it qualifies an event (created, updated,
     finished). "What do I have open today" is the open listing with no date filter.
   - Archived tasks are left out unless the request asks for them, for finished work or
     for a task by its ref.
   - For metadata, compare what the user said with the `name` and `description` of
     every field under `metadata` in the entries of the document, and use the declared
     name exactly. The command refuses a key that no workstream declares.
   - Write every metadata value in the form of the field's declared `type`: a `text`
     value exactly as it is stored, a `number` as a decimal (`3`, `2.5`, `-1`), a
     `boolean` as `true` or `false`, a `date` as `YYYY-MM-DD`. `<field>=null` finds the
     tasks where the field has no value, including those whose workstream declares the
     field and whose file lacks it.
   - Bounds apply to `number` and `date` fields only, and include their own value: a
     period such as a month is `--where-from <field>=<first day>` and
     `--where-to <field>=<last day>`. A task without a value never matches a bound. Give
     at most one `--where-from` and one `--where-to` per field.
   - Repeat an option to give alternatives: two `--status` values list tasks with
     either status, two `--where` values on the same field list tasks with either
     value. Different options must all match.
5. **Run the command** from anywhere inside the obeya root, every time, even when you
   listed the same tasks earlier in the conversation:

   ```bash
   gemba list [--workstream <id> ...] [--status <status> ...] [--ref <ref>] \
     [--from YYYY-MM-DD] [--to YYYY-MM-DD] \
     [--updated-from YYYY-MM-DD] [--updated-to YYYY-MM-DD] \
     [--done-from YYYY-MM-DD] [--done-to YYYY-MM-DD] \
     [--include-archived] [--where <field>=<value> ...] \
     [--where-from <field>=<value> ...] [--where-to <field>=<value> ...]
   ```

   - The command converts every metadata value by the declared type of its field; it
     never reads a value as YAML, so text is matched exactly as written. Quote the whole
     argument for the shell when it contains spaces.
   - If the command refuses, its message lists every invalid filter at once, with the
     valid workstreams, the allowed statuses or the declared fields. Fix the call and
     run it again, asking the user only when the request itself is unclear. If the
     config is missing or invalid, stop and report the message.
6. **Read the result.** The command prints one JSON object. `tasks` holds one record per
   matching task: `path` (relative to the obeya root), `workstream`, `archived`,
   `ref`, `date` (created), `title`, `status`, `updated_at`, `done_at`, `metadata` and
   `description`. `problems` holds the files that are not valid tasks and the metadata
   values that are not of the type their field declares, each with its `path` and the
   `problem`.
7. **Open a task file only when the answer needs its body**: what happened last, the
   history of the work, the links, what is left to do. Open it from the record's
   `path`. Progress is under `## Updates`, one `### YYYY-MM-DD` subsection per day in
   chronological order, so the last subsection is the latest activity.
8. **Present the result.** Adapt it to the question: a count gets the number, a
   question about one task gets a short answer, a request for refs gets the refs and
   titles. When a full listing is wanted, this layout reads well:

   ```
   <workstream>
     <ref>  <title>  <status>  updated <updated_at>
            <description, when it helps>

   Problems
     <path>: <problem>

   <N> tasks
   ```

   The layout is a suggestion, not a contract; nothing depends on it. When no task
   matches, say so plainly and name the filters you used.
9. **Relay every problem** the command returned, even when the question was about
   something else: give each path and its problem. Say that a file that is not a valid
   task is left out of the listing until it is fixed, and that a task whose value is of
   another type is still listed but matches no condition on that field until the value
   is set again with `gemba set`. Never fix a task file yourself.

## Rules

- Read, never write: do not edit, move or create any file, and do not commit.
- Commands own the frontmatter and the agent owns the body; if a frontmatter value
  looks wrong, tell the user instead of changing it.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream, field or rule is added, changed or removed.
