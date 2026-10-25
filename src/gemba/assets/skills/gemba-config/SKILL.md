---
name: gemba-config
description: Explain, check, show and edit the config of this obeya, gemba.yaml, shared by everyone who uses it, and gemba.local.yaml, private to this clone. Use whenever the user asks to add, change or remove a workstream, a field, a member of the team, a provider, the IDE command, the repositories folder, the branch prefix or the context and rules of a process, for everyone who uses the obeya or for themselves alone, asks to share the obeya with a team, or asks what the config can hold.
---

# Maintain the gemba config

The gemba config is two files at the root of the obeya. `gemba.yaml`, the shared
config, is committed with the obeya: its workstreams, the fields a task records,
the name of the obeya, the team that shares it, the agent providers and the context and
rules of every process. `gemba.local.yaml`, the personal config, is optional, private to
this clone and ignored by git: the command that opens the IDE, where the repositories
are, how the local branches are named, the member of the team the clone belongs to, and
what the person adds for themselves alone. Every command reads both; no command writes
either after `gemba init` created `gemba.yaml`. Every change is an edit of a file by
hand, by the user or by you on their behalf. `gemba config check` validates both files
and `gemba config show` prints the config resolved. Your part is to know what each file
can hold, to edit the right one keeping everything else as it was, and to prove the edit
valid with `gemba config check`.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command.

## Reference

Every example below is only an example: the names of this obeya are in its own
files, which `gemba config show` prints resolved.

### Top level

Each key belongs in one file, or may be in both. A key in the wrong file is refused,
naming the file it belongs in; a key gemba does not know is ignored in both.

| Key | File | Holds | When absent |
|---|---|---|---|
| `default_workstream` | `gemba.yaml` | the identifier of a workstream of the catalogue, where a task goes when no description covers it | refused: it is required |
| `workstreams` | `gemba.yaml`; process blocks only in `gemba.local.yaml` | a non-empty map of workstreams, keyed by identifier; its order is the order reports group by | refused: it is required |
| `metadata` | `gemba.yaml` | the list of field declarations shared by every workstream | no shared field |
| `obeya` | `gemba.yaml` | the name of the obeya, the repository that holds `gemba.yaml`, `tasks/` and `harnesses/`, where one person or a team keeps a part of their work in sight, drawn as whoever created it chose: a kebab-case name, the middle segment of the branch of a run, `<branch_prefix>/<obeya>/<ref>` | `gemba worktree add` refuses to run |
| `team` | `gemba.yaml` | the members of the team that shares the obeya, described in "The team" below: a non-empty map keyed by the folder name of each member, kebab-case and not the identifier of a workstream, each with `initials`, one or more uppercase ASCII letters no other member uses, and `active`, `true` or `false`, `true` when absent | the obeya has no team: tasks live under `tasks/<workstream>/` and refs read `<prefix>-<N>` |
| `agent_providers` | both | a non-empty list of agent providers, each listed once: `claude` (`.claude/skills/`, guide `CLAUDE.md`) or `agents` (`.agents/skills/`, guide `AGENTS.md`). In `gemba.yaml`, the providers whose skills the obeya holds, and those of every harness; in `gemba.local.yaml`, the providers of the harnesses launched from this clone, in place of the shared list | in `gemba.yaml`: `gemba skills update` and `gemba init` refuse to run, and so does `gemba harness launch` unless `gemba.local.yaml` declares a list; in `gemba.local.yaml`: harnesses use the shared list |
| `ide` | `gemba.local.yaml` | the command that opens a folder in the IDE, as a string split the way a POSIX shell splits it, such as `code -n`, where a path holding spaces or backslashes goes between double quotes, or as a map `{ command: code, args: [-n] }`, which means the same and needs no quoting; the command is resolved on PATH and launch appends the harness path | launch opens nothing |
| `repos_dir` | `gemba.local.yaml` | the folder of the repositories a run may check out as worktrees: absolute, starting with `~`, or relative to the obeya root | `gemba worktree add` refuses to run |
| `branch_prefix` | `gemba.local.yaml` | a kebab-case name, the first segment of the branch of a run | `gemba` |
| `me` | `gemba.local.yaml` | the folder name of the member of the team this clone belongs to, active or not; refused when `gemba.yaml` declares no team or no such member | with a team, the commands that write a task refuse to run; every task can still be read |

The top level of either file may also hold the process blocks described below,
`create`, `list`, `record`, `report`, `mark`, `archive`, `set`, `harness` and
`worktree`: the base blocks, which apply to every workstream. No other process key is
read.

`ide`, `repos_dir` and `branch_prefix` live only in the personal config because they
run something or name paths and branches of one machine: no command a teammate commits
runs on another person's machine.

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

A workstream is declared in `gemba.yaml`:

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

Fields are declared in `gemba.yaml` only, at the top level or in a workstream:

- `name` is required: snake_case (lowercase letters, digits and single underscores),
  declared once per list. `workstream`, `status` and `owner` are reserved: a report
  groups tasks by them.
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
  launched afterwards: the top-level text of `gemba.yaml` under `## Your obeya`,
  the workstream's under `## Your workstream`, and the texts of `gemba.local.yaml`
  under `## Your user`, last. A harness already launched keeps its guide.
- The block that applies to a workstream joins four levels in this order: the top level
  of `gemba.yaml`, the workstream in `gemba.yaml`, the top level of `gemba.local.yaml`
  and the workstream in `gemba.local.yaml`. Contexts follow one another in that order
  and so do rules, a later rule winning a contradiction: the workstream's over the top
  level's of the same file, and any personal rule over any shared one. `gemba config
  show` prints it joined, under `processes` of each workstream.

### The personal config

```yaml
ide: code -n
repos_dir: ~/projects
agent_providers: [claude]
harness:
  guide: Answer me in Spanish.
workstreams:
  support:
    create:
      rules:
        - name the client in the title
```

`gemba.local.yaml` sits beside `gemba.yaml` and is read only there: a folder that holds
it without `gemba.yaml` is not an obeya. It is never committed (`gemba init` adds
it to the `.gitignore`), so nobody else sees it. An empty file declares nothing.

- `ide`, `repos_dir` and `branch_prefix` go here and nowhere else.
- `agent_providers`, when declared, replaces the shared list for the harnesses launched
  from this clone, and for nothing else: the skills of the obeya stay those of the
  shared list, since they are committed for everyone.
- Process blocks at its top level apply to every workstream, after the shared ones.
- `workstreams` gives process blocks to workstreams of the shared catalogue: each key is
  an identifier declared in `gemba.yaml`, and each entry holds process blocks only. A
  `prefix`, `description` or `metadata` there is refused: what defines a workstream is
  shared.
- The personal layer only adds: it never removes or replaces a shared rule, and wins a
  contradiction by coming last.

### The team

```yaml
team:
  manuel:
    initials: MR
  ana:
    initials: AG
    active: false
```

An obeya shared by a team declares it in `gemba.yaml`, and the clone of each member
names that member in its own `gemba.local.yaml`, as `me: manuel`. With a team, the tasks
of each member live under `tasks/<member>/<workstream>/`, archives included, and their
refs start with the member's initials, such as `MR-SUP-3`. The owner of a task is the
member whose folder holds it: only a clone whose `me` is the owner writes it, and every
member reads every task.

- A new member gets a folder name and initials no member, active or not, ever used:
  propose initials from their name and check them against every member.
- A member who leaves is marked `active: false` and stays in `team`, their tasks where
  they are. Never remove a member and never give their initials to another: refs are
  never reused.
- Each member declares their own `me`, in the personal config of their own clone. Never
  write `me` for another person.
- A team starts in a new obeya. Never add `team` to an obeya whose `tasks/` holds tasks:
  every command refuses a team while `tasks/` holds the workstream folders of an obeya
  without one. Explain this, leave `gemba.yaml` as it is, and offer the `gemba-migrate`
  skill, run from a new obeya configured for the team, which brings earlier tasks into
  it.

## Process

1. **Locate the config.** Walk up from the current folder to the first folder that holds
   `gemba.yaml`: it is the obeya root, and `gemba.local.yaml`, when there is one,
   is beside it. If there is none, stop and tell the user that an obeya is started
   with `gemba init` and configured the first time through the `gemba-init` skill.
2. **Read the current state** with `gemba config show`, and read `gemba.yaml` and
   `gemba.local.yaml` themselves, since the edit is made there. When the command
   refuses, the config is already invalid: tell the user and go to step 5 with the
   problems it names.
3. **Ask for what the edit needs and the user did not say**, one question at a time,
   proposing a value from what they said: for a workstream, its identifier, prefix and
   description; for a field, its name, type, whether it is required, its description,
   and whether every workstream shares it or one workstream holds it; for a member of
   the team, their folder name and initials; for a rule or a context, the process or
   verb and whether it applies to every workstream or to one.
   For a key both files may hold, `agent_providers`, a context, a rule or a
   `harness.guide`, ask whether it is for everyone who uses the obeya, in
   `gemba.yaml`, or for the user alone, in `gemba.local.yaml`, unless they said so.
   Check each value against the reference and the current state: an identifier or a
   prefix already in use, a field name declared with another type, or a personal block
   for a workstream the catalogue does not hold, is refused. Do not ask for what the
   user did not raise and has a default, such as `branch_prefix`.
4. **Edit the file the key belongs in** with your own tools, changing only what the edit
   needs: keep every other line, comment, key and their order as they were, and write
   new keys in the style of the file. When a key of the personal config is set and
   `gemba.local.yaml` does not exist, create it at the obeya root holding that key
   alone. Never rewrite a file from the output of `gemba config show`: it holds defaults
   and joined blocks that the files do not.
5. **Check the config:**

   ```bash
   gemba config check
   ```

   It exits 0 with a summary when the config is valid; otherwise it exits 1 and lists
   every problem of both files, each with the path of its file. Fix every problem it
   lists, then run it again until it exits 0. A key reported as belonging in the other
   file is moved there, as the next section says. Never leave an invalid config behind,
   since every command refuses to run while it is.
6. **Refresh the skills when the `agent_providers` of `gemba.yaml` changed**, from the
   obeya root:

   ```bash
   gemba skills update
   ```

   It writes the skills of a provider added. A provider removed keeps its skills
   folder: tell the user that `.claude/skills/` or `.agents/skills/` is left for them to
   delete. A change to the `agent_providers` of `gemba.local.yaml` needs no refresh: it
   applies to the next harness launched. A harness keeps the providers it was launched
   with.
7. **Report** what changed in each file, the summary `gemba config check` printed and
   what follows from the edit: the skills written, a folder left to delete, tasks whose
   values no longer match a field, and, for a member added, that they declare `me` in
   the personal config of their own clone. Do not commit: the user reviews and commits
   the obeya, which never holds `gemba.local.yaml`.

## Keys of an earlier config

A config written for an earlier version of gemba declares `ide`, `repos_dir` or
`branch_prefix` in `gemba.yaml`, and every command refuses it, saying that each belongs
in `gemba.local.yaml`. It may also declare `organization`, which every command refuses,
saying that it was renamed `obeya`, which belongs in `gemba.yaml`. When
`gemba config check` reports them:

1. Move each of `ide`, `repos_dir` and `branch_prefix` to `gemba.local.yaml`, creating
   the file when it is missing, with its value exactly as written and any comment that
   belongs to it, and remove it from `gemba.yaml`. Leave every other key where it is.
2. Rename `organization` to `obeya` in `gemba.yaml`, with its value and any comment
   that belongs to it exactly as written, leaving every other line where it is. Its
   value names the branches of the runs, which keep their names. When
   `gemba.local.yaml` declares `organization`, remove it there and give its value to
   `obeya` in `gemba.yaml`, asking the user which value to keep when both files declare
   one and they differ.
3. Run `gemba config check` until it exits 0, fixing every other problem it lists.
4. When the `.gitignore` at the obeya root does not list `gemba.local.yaml`, tell
   the user that running `gemba init` once appends that line and changes nothing else,
   so the personal config never reaches the history.
5. Report the move and the rename without committing.

## Rules

- The CLI never writes `gemba.yaml` after `gemba init` created it, and never writes
  `gemba.local.yaml`. Edit them by hand, and run `gemba config check` after every edit.
- Never commit `gemba.local.yaml`, and never copy its keys into `gemba.yaml`: they belong
  to one person on one machine.
- Never move, rename or edit a task file because the config changed. A workstream
  renamed or removed leaves its folder under `tasks/` as it is, and `gemba list`
  reports that folder as a problem until the user moves it; a prefix changed leaves
  every ref already allocated as it is; a field changed leaves every value already
  written as it is, and a value no longer of its field's type is reported until
  `gemba set` writes it again. Tell the user so.
- No configured value belongs in a skill or in the CLI: every workstream, field and
  rule of the obeya lives in its config files.
