---
name: gemba-config
description: Explain, check, show and edit gemba.yaml, the config of this tasks repo. Use whenever the user asks to add, change or remove a workstream, a field, a provider, the IDE command, the repositories folder or the context and rules of a process, or asks what the config can hold.
---

# Maintain the gemba config

`gemba.yaml`, at the root of the tasks repo, is the customization of the organization:
its workstreams, the fields a task records, the agent providers, and the context and
rules of every process. Every command reads it; no command writes it after `gemba init`
created it. Every change is an edit of the file by hand, by the user or by you on their
behalf. `gemba config check` validates the file and `gemba config show` prints it
resolved. Your part is to know what the file can hold, to edit it keeping everything
else as it was, and to prove the edit valid with `gemba config check`.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command.

## Reference

Every example below is only an example: the names of this tasks repo are in its own
`gemba.yaml`, which `gemba config show` prints.

### Top level

| Key | Holds | When absent |
|---|---|---|
| `default_workstream` | the identifier of a workstream of the catalogue, where a task goes when no description covers it | refused: it is required |
| `workstreams` | a non-empty map of workstreams, keyed by identifier; its order is the order reports group by | refused: it is required |
| `metadata` | the list of field declarations shared by every workstream | no shared field |
| `agent_providers` | a non-empty list of the agent providers whose skills folders gemba writes, each listed once: `claude` (`.claude/skills/`, guide `CLAUDE.md`) or `agents` (`.agents/skills/`, guide `AGENTS.md`) | `gemba skills update`, `gemba harness launch` and `gemba init` refuse to run |
| `ide` | the command that opens a folder in the IDE, as a string split the way a POSIX shell splits it, such as `code -n`, where a path holding spaces or backslashes goes between double quotes, or as a map `{ command: code, args: [-n] }`, which means the same and needs no quoting; the command is resolved on PATH and launch appends the harness path | launch opens nothing |
| `organization` | a kebab-case name, the middle segment of the branch of a run, `<branch_prefix>/<organization>/<ref>` | `gemba worktree add` refuses to run |
| `repos_dir` | the folder of the repositories a run may check out as worktrees: absolute, starting with `~`, or relative to the tasks repo root | `gemba worktree add` refuses to run |
| `branch_prefix` | a kebab-case name, the first segment of the branch of a run | `gemba` |

The top level may also hold the process blocks described below, `create`, `list`,
`record`, `report`, `mark`, `archive`, `set`, `harness` and `worktree`: the base
blocks, shared by every workstream. No other process key is read.

### A workstream

```yaml
workstreams:
  support:
    prefix: SUP
    description: Investigate a client-reported problem
    metadata:
      - name: client
        type: text
        required: true
```

- The identifier, the key of the entry, is kebab-case (lowercase letters, digits and
  single hyphens). It names the folder of its tasks, `tasks/<identifier>/`.
- `prefix` is required: one or more uppercase ASCII letters, used by no other
  workstream. Refs are `<prefix>-<N>`. Quote it, as in `prefix: "ON"`, when YAML would
  read it as a boolean.
- `description` is required and not empty. Agents choose the workstream of a new task
  by it, so it says which work belongs there and which does not.
- `metadata` lists the fields of this workstream.
- Any process block, with the same shape as at the top level.

### A field

```yaml
metadata:
  - name: client
    type: text
    description: Client the work is done for
```

- `name` is required: snake_case (lowercase letters, digits and single underscores),
  declared once per list. `workstream` and `status` are reserved: every report groups
  tasks by them.
- `type` is required, one of four, and tells every process how to read and operate on
  a value, never what it means: `text` (the one type that may hold a list), `number`
  (a decimal), `boolean` (`true` or `false`) or `date` (`YYYY-MM-DD`). A name keeps one
  type across the whole file, in every list that declares it.
- `required` is `true` or `false`, `false` when absent: `gemba create` refuses a task
  without a value for a required field.
- `description` is optional and not empty: agents map the user's words to the field
  by its name and description, and ask for a required value with it.
- A declaration takes no other key.

The fields of a workstream are the shared ones and its own, joined by name: a field the
workstream declares with the name of a shared one replaces that declaration entirely.

### Process blocks

```yaml
create:
  context: Every task is billed to one client.
  rules:
    - ask who requested the work if not stated
worktree:
  add:
    rules:
      - start from the default branch of origin
```

- A block holds `context`, a string the agent reads as background, and `rules`, a list
  of non-empty strings the agent follows. Both are optional.
- `create`, `list`, `record`, `report`, `mark`, `archive` and `set` are one verb each:
  the block sits directly under the process name.
- `harness` and `worktree` are groups: the block sits under each verb, `harness.launch`,
  `harness.note`, `harness.resolve`, `harness.remove`, `worktree.add`, `worktree.list`
  and `worktree.remove`. A group takes no other key, except `harness.guide`.
- `harness.guide` is a non-empty string written into the guide of every harness
  launched afterwards: the top-level text under `## Your organization` and the
  workstream's under `## Your workstream`. A harness already launched keeps its guide.
- The block that applies to a workstream joins the top level and the workstream: the
  top-level context then the workstream's, every top-level rule then every rule of the workstream, the rule of
  the workstream winning a contradiction. `gemba config show` prints it joined, under
  `processes` of each workstream.

## Process

1. **Locate the config.** Walk up from the current folder to the first folder that holds
   `gemba.yaml`: it is the tasks repo root. If there is none, stop and tell the user
   that a tasks repo is started with `gemba init` and configured the first time through
   the `gemba-init` skill.
2. **Read the current state** with `gemba config show`, and read `gemba.yaml` itself,
   since the edit is made there. When the command refuses, the file is already invalid:
   tell the user and go to step 5 with the problem it names.
3. **Ask for what the edit needs and the user did not say**, one question at a time,
   proposing a value from what they said: for a workstream, its identifier, prefix and
   description; for a field, its name, type, whether it is required, its description,
   and whether every workstream shares it or one workstream holds it; for a rule or a
   context, the process or verb and whether it is shared or belongs to one workstream.
   Check each value against the reference and the current state: an identifier or a
   prefix already in use, or a field name declared with another type, is refused. Do
   not ask for what the user did not raise and has a default, such as `branch_prefix`.
4. **Edit `gemba.yaml`** with your own tools, changing only what the edit needs: keep
   every other line, comment, key and their order as they were, and write new keys in
   the style of the file. Never rewrite the file from the output of `gemba config show`:
   it holds defaults and joined blocks that the file does not.
5. **Check the file:**

   ```bash
   gemba config check
   ```

   It exits 0 with a summary when the config is valid; otherwise it exits 1 naming the
   file and the first problem. Fix that problem and run it again until it exits 0: it
   reports one problem at a time. Never leave an invalid config behind, since every
   command refuses to run while it is.
6. **Refresh the skills when `agent_providers` changed**, from the tasks repo root:

   ```bash
   gemba skills update
   ```

   It writes the skills of a provider added. A provider removed keeps its skills
   folder: tell the user that `.claude/skills/` or `.agents/skills/` is left for them to
   delete. A harness keeps the providers it was launched with.
7. **Report** what changed in the file, the summary `gemba config check` printed and
   what follows from the edit: the skills written, a folder left to delete, tasks whose
   values no longer match a field. Do not commit: the user reviews and commits the
   tasks repo.

## Rules

- The CLI never writes `gemba.yaml`. Edit it by hand, and run `gemba config check`
  after every edit.
- Never move, rename or edit a task file because the config changed. A workstream
  renamed or removed leaves its folder under `tasks/` as it is, and `gemba list`
  reports that folder as a problem until the user moves it; a prefix changed leaves
  every ref already allocated as it is; a field changed leaves every value already
  written as it is, and a value no longer of its field's type is reported until
  `gemba set` writes it again. Tell the user so.
- No organization's names belong in a skill or in the CLI: every workstream, field and
  rule of the tasks repo lives in its `gemba.yaml`.
