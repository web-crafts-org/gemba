---
name: gemba-set
description: Set, change, correct or clear a metadata value of a task, or add to an amount it holds, such as the time it took, from the tasks repo or inside its harness. Use whenever the user gives a value of a task's field after its creation, says a task took more time or more of any amount than recorded, says something happened to a task on a date a field records, or asks to set, change, fix, clear, log or add to a value of a task, whatever the workstream. Recording the day's work is gemba-record and the status of a task is gemba-mark.
---

# Set metadata of a task

The metadata of a task is the map of values its workstream declares in `gemba.yaml`,
each field with a `type`: `text`, `number`, `boolean` or `date`. The `gemba set` command
is the one writer of those values after creation: it converts every value by the type
of its field, adds to a number without anyone doing the sum, completes the map with the
keys of the current schema, and rewrites nothing but `metadata`; `updated_at` does not
move. Your part is to find the task, turn the user's words into assignments of declared
fields, run the command once and relay what it prints.

Every organization-specific value (workstreams, prefixes, metadata fields, rules) lives
in `gemba.yaml`, at the tasks repo root. Run `gemba config show` on every run and rely
on nothing else you know or remember about workstreams or fields: it prints the config
resolved, with the fields and the blocks shared by every workstream already joined to
those of each one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Never edit the
frontmatter of a task by hand.

## Process

From the tasks repo or from inside the harness of the task. Inside a harness, the
folder that holds `harness.yaml` is the harness root.

1. **Identify the task by its ref**, `<PREFIX>-<N>`. Inside a harness, the task is the
   one named by `ref` in `harness.yaml`, unless the user names another. From the tasks
   repo, take the ref the user gives; when they name the task by its title or
   description instead, find it with the `gemba-list` skill. When two or more tasks
   fit, ask the user which one before setting anything.
2. **Read the schema of the task.** Its workstream is the one whose `prefix` is the
   prefix of the ref: run `gemba config show` and take the entry of `workstreams` with
   that `prefix`; for the task of the harness, `gemba config show --workstream <id>`
   with the `workstream` of `harness.yaml` prints that entry alone. The `metadata` of
   that entry lists every field the task may hold, each with its `name`, `type`,
   `required` and `description`. Read its `processes.set` too: `context` as background,
   and every entry of `rules` to follow, in order, before running the command; when two
   rules contradict, follow the later one.
3. **Map the user's words to declared fields** by their names and descriptions. Use the
   declared name exactly. When nothing in the schema fits what the user said, tell them
   which fields are declared and stop: a new field is an edit of `gemba.yaml`, not a
   value to invent.
4. **Write each assignment by the field's `type`:**

   | Type | The user says | Assignment |
   |---|---|---|
   | `number` | a new total | `<field>=<decimal>`, such as `3` or `2.5` |
   | `number` | more of an amount, "another", "two more" | `<field>+=<decimal>` |
   | `boolean` | yes or no | `<field>=true` or `<field>=false` |
   | `date` | a day | `<field>=YYYY-MM-DD` |
   | `text` | a value | `<field>=<value>`, exactly as it should read |
   | `text` | several values | `<field>=<one> <field>=<two>`, the whole list |
   | any | remove, clear, unset | `<field>=null` |

   - Resolve "today", "yesterday" or a weekday against `date +%F`.
   - Use `+=` whenever the user adds to an amount instead of stating the new total, and
     never add, subtract or convert numbers yourself. When the user gives an amount in
     another unit than the one the field's name or description implies, ask for it in
     the field's unit.
   - A text list replaces the whole value: to add one item, give every item.
   - For a `text` field, look up the values already in use before writing one:

     ```bash
     gemba report --by <field> --include-archived
     ```

     The `key` of each group is a value in use. When the user means one of them,
     written another way (another case, an abbreviation), use the spelling in use; when
     you cannot tell whether the user means a value in use or a new one, ask.
5. **Run the command once,** with every assignment, from anywhere inside the tasks repo
   or the harness:

   ```bash
   gemba set <ref> <field>=<value> [<field>+=<number> ...]
   ```

   Quote an assignment for the shell when it contains spaces. If the command refuses,
   its message lists every problem at once. Fix the call when the problem is yours
   (a field name, the form of a value) and run it again. When it says a required field
   would be left null, ask the user for that value and pass it in the same call. When it
   cannot add to a value that is not a number, tell the user and ask for the total to
   set with `=`.
6. **Relay the result** and stop: the task path and one line per field, `old -> new`,
   `(unchanged)` when the value was already there, or `added as null` for a field the
   task lacked because it was declared after the task was created.

## Rules

- Commands own the frontmatter: never write `metadata`, or any other frontmatter key,
  by hand, in `task.md` or in the task file.
- Setting records no work and moves no status. What was done belongs under
  `## Updates`, through the `gemba-record` skill; the status belongs to the `gemba-mark`
  skill.
- Choose the assignment by the declared `type` of a field, never by its name.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream, field or rule is added, changed or removed.
