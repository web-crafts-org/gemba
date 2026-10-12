---
name: gemba-init
description: Configure gemba for the first time in a tasks repo that gemba init just created, through a guided interview, one question at a time. Use whenever the user asks to configure gemba, set up gemba, do the first configuration, or customize this tasks repo for their work, right after gemba init.
---

# Configure a new tasks repo

`gemba init` writes a tasks repo that every command accepts, with a minimal
`gemba.yaml`: one workstream, `default`, and every agent provider the CLI knows. This
skill turns that scaffold into the config of the person's own work, once, by asking
what only they know. Your part is to ask one question at a time, propose the values
from the answers, and hand the edit over to the `gemba-config` skill, which holds the
reference of every key and the process to edit, check and refresh.

## Prerequisite

The `gemba` command must be on the PATH. It is installed once from PyPI with
`uv tool install gemba-cli` and checked with `gemba --version`. If `gemba` is not
found, stop and tell the user to install it with that command.

Run `gemba config show`. This skill is for a tasks repo whose config still holds the
`default` workstream of the scaffold. When the command finds no config, tell the user
to run `gemba init` first. When the config holds no `default` workstream, it has been
configured already: follow the `gemba-config` skill instead.

## Process

Ask the questions below in this order, one per message, and skip any the user already
answered. Propose a value from each answer and let the user confirm or change it; never
fill a value the user did not give or confirm.

1. **The organization.** Ask for the name of the organization the work is done for or
   in. Propose `organization` from it: kebab-case, lowercase letters, digits and single
   hyphens. It names the branches of the runs.
2. **The kinds of work.** Ask what kinds of work the person does. Propose one workstream
   per kind, each with:
   - an identifier, kebab-case;
   - a prefix of uppercase ASCII letters, short and used by no other workstream: the
     refs of its tasks read `<prefix>-<N>`;
   - a description that lets an agent tell which work belongs there and which does not,
     since agents choose the workstream of a new task by it.
3. **The default workstream.** Ask which workstream takes a task that fits no other.
   The `default` workstream of the scaffold is replaced by the ones the person named,
   unless they want a catch-all, which then keeps or renames it with a description of
   its own.
4. **What to record per task.** Ask what the person needs to know of every task, such
   as who it is for, the time it took or whether it was billed. Propose one field per
   answer, each with a snake_case name, one of the four types (`text`, `number`,
   `boolean`, `date`), whether it is required, and a description. Propose whether every
   workstream shares the field or only some hold it.
5. **The agent providers.** The scaffold declares every known provider in
   `agent_providers`. Ask which agents the person uses and propose the list trimmed to
   them.
6. **The IDE.** Ask for the command that opens a folder in their editor, such as
   `code -n`; it becomes `ide`, run on every harness at launch. Write it as a string
   when it is a bare command with its arguments; when the path holds spaces or
   backslashes, as on Windows, either put it between double quotes inside the string
   or use the map form, `{ command: 'C:\Program Files\Code\code.cmd', args: [-n] }`,
   where the path is written as YAML writes any string, with no quoting rule of its own.
7. **The repositories folder.** Only when the work involves code: ask for the folder
   that holds the repositories the runs check out as worktrees; it becomes `repos_dir`,
   absolute, starting with `~`, or relative to the tasks repo root.

Do not ask for what has a default or comes from use: `branch_prefix`, and the
`context` and `rules` of the processes.

Then:

8. **Write the config** by following the `gemba-config` skill from its step 4: edit
   `gemba.yaml` keeping the comments of the scaffold, run `gemba config check` until it
   exits 0, and run `gemba skills update` when `agent_providers` changed, telling the
   user which skills folder is left for them to delete.
9. **Report** the resulting config: the workstreams with their prefixes, the default,
   the fields, the providers, the IDE command and the repositories folder. End by
   naming the edits that come later, through the `gemba-config` skill: `branch_prefix`,
   the first segment of every branch of a run, `gemba` by default; and the `context`
   and `rules` of any process, which tell agents what to know and do in a workstream
   or in all of them. Do not commit: the user reviews and commits the tasks repo.

## Rules

- This interview is the first configuration only. Any later change of the config, a
  workstream, a field, a provider or a rule, follows the `gemba-config` skill.
- One question per message, in the order above; never ask for a value the user already
  gave.
