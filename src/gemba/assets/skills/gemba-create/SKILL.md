---
name: gemba-create
description: Register a new task in this tasks repo. Use whenever the user asks to register, create, track or add a task, TODO or work item, whatever the workstream.
---

# Create a task

Register one unit of work as a task file. The `gemba create` command validates the
request, allocates the ref and writes the file. Your part is to choose the workstream,
gather what the config requires, run the command and complete the body.

Every organization-specific value (workstreams, prefixes, metadata fields, rules) lives
in `gemba.yaml`. Run `gemba config show` on every run and rely on nothing else you know
or remember about workstreams or fields: it prints the config resolved, with the fields
and the blocks shared by every workstream already joined to those of each one.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command. Do not run the package's
Python files directly and do not write the task file by hand.

## Process

1. **Locate the config.** Walk up from the current folder to the nearest `gemba.yaml`.
   That folder is the tasks repo root. If there is none, stop and tell the user that no
   gemba config was found.
2. **Choose the workstream.** Run `gemba config show` from anywhere inside the tasks
   repo: it prints the config resolved as one JSON document, or the problem when the
   config is invalid, which you relay before stopping. Compare the request with the
   `description` of every entry of `workstreams` in the document:
   - one description clearly covers the work: use that workstream without asking;
   - no description covers it: use `default_workstream`;
   - two or more cover it equally well: ask the user which one before creating anything.
3. **Read the fields of the chosen workstream.** The `metadata` of its entry lists every
   field the task may hold, each with its `name`, `type`, `required` and `description`.
4. **Read the `create` block** of the chosen workstream, `processes.create` of its entry.
   Read its `context` as background and follow every entry of its `rules` in order,
   including any question a rule tells you to ask; when two rules contradict, follow
   the later one.
5. **Gather required fields.** For every field with `required: true` whose value the user
   has not given, ask for it, phrasing the question with the field's `description` when
   it has one. Ask for all of them in one message. Never ask for optional fields; pass
   an optional field only when the user mentioned its value.
6. **Write each value by its type.** Every field declares a `type`, and the command
   converts the value by it:
   - `text`: the value exactly as it should read; a field of this type alone holds a
     list, given by repeating the key;
   - `number`: a decimal such as `3`, `2.5` or `-1`;
   - `boolean`: `true` or `false`;
   - `date`: `YYYY-MM-DD`.

   For a `text` field, look up the values already in use before writing one:

   ```bash
   gemba report --by <field> --include-archived
   ```

   The `key` of each group is a value in use. When the user means one of them, written
   another way (another case, an abbreviation), pass it with the spelling in use; when
   you cannot tell whether the user means a value in use or a new one, ask.
7. **Build the slug** from what the user said. It is the task's title: a few lowercase
   ASCII words or numbers joined by single hyphens, matching `^[a-z0-9]+(-[a-z0-9]+)*$`.
   Transliterate accented letters and drop punctuation.
8. **Run the command** from anywhere inside the tasks repo root:

   ```bash
   gemba create --workstream <id> --slug <slug> \
     [--date YYYY-MM-DD] [--status in-progress|blocked] \
     [--description "<short description>"] [--set <key>=<value> ...]
   ```

   - Pass `--date` only when the user states a creation date other than today.
   - Pass `--status` only when the user says the work is already in progress or blocked.
     New tasks are `open` by default and `done` is refused.
   - Pass `--set` once per value, written as step 6 says; repeat the key of a `text`
     field to give a list. Values are never read as YAML: text is kept exactly as
     written. Quote the argument for the shell when it contains spaces.
   - Never choose a ref: the command allocates it. An external identifier such as a
     ticket key or a link goes into a declared metadata field or into the body, never
     into the slug.

   If the command refuses, its message lists every problem at once, including every
   missing and every undeclared key and every value that is not of its field's type. Fix the call, asking the user when a value is
   missing, and run it again. Never work around a refusal by writing or editing the
   file yourself.
9. **Complete the body.** The command prints the created path, relative to the tasks
   repo root, and the ref. If you did not pass `--description`, write a short description
   above `## Updates` now. Add links to any external references the user gave below
   the description. Edit only the body and leave `## Updates` empty.
10. **Report** the path, the ref and a one-line summary to the user. Do not commit.

## Rules

- Commands own the frontmatter, including `metadata`; you own the body. Never edit the
  frontmatter by hand, not even to fix a value; tell the user what is wrong instead.
- When `gemba.yaml` changes, follow the new content. This skill never needs an edit when
  a workstream, field or rule is added, changed or removed.
