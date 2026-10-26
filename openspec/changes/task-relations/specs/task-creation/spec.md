# Spec Delta

## ADDED Requirements

### Requirement: The parent at creation
Creating a task MAY take a parent ref. The command SHALL find the task that holds it in
the obeya, archives and every member's folder included, and write that ref as the
`parent` of the new task. When no task holds it, the command SHALL write nothing and
report, with every other problem of the call, that the ref is not a task of this clone,
to be pulled first when it was created in another clone.

#### Scenario: Child of an archived parent
- **WHEN** `SUP-1` is `done` and archived under `tasks/support/archive/`, and `gemba create --workstream operations --slug follow-up --parent SUP-1` runs
- **THEN** `OPS-1` is created with `parent: SUP-1`, and the exit code is 0
- **Cases**: adds `tests/cases/create/child-of-an-archived-parent.yaml`

#### Scenario: Parent not in the clone
- **WHEN** `gemba create --workstream support --slug Bad-Slug --parent SUP-9` runs and no task has the ref `SUP-9`
- **THEN** nothing is written, the exit code is 1, and one message says that `SUP-9` is not a task of this clone, suggests a pull, and names the invalid slug
- **Cases**: adds `tests/cases/create/parent-not-in-the-clone.yaml`

### Requirement: The agent creates a subtask
When the user asks to split a task, or to register work as part of another task, the
agent SHALL pass that task's ref as the parent, finding it with the `gemba-list` skill
when the user names it otherwise. In an obeya with a team, the child SHALL be the
user's own, whoever owns the parent; a part another member will do is that member's to
create, with the same parent.

#### Scenario: Subtask asked
- **WHEN** the user asks to register the CSS fix as a subtask of `SUP-1`
- **THEN** the agent runs `gemba create` with `--parent SUP-1`, in the workstream it chooses for the fix
- **Cases**: adds the entry `task-creation: Subtask asked` of `tests/not-automated.yaml`

#### Scenario: Task split among members
- **WHEN** `me` is `manuel` and the user asks to split `MR-DEV-1` into a part of their own and a part for `ana`
- **THEN** the agent creates the user's part with `--parent MR-DEV-1`, and drafts what `ana` needs to create hers with `--parent MR-DEV-1`, running no command on her behalf
- **Cases**: adds the entry `task-creation: Task split among members` of `tests/not-automated.yaml`
