# Spec Delta

## ADDED Requirements

### Requirement: The agent points out a parent whose children are done
After marking a task `done` whose record names a parent, the agent SHALL list the
parent's children with `gemba list --parent <parent> --include-archived` and, when every
one is `done` and the parent is not, say that the parent may be ready to close: offering
to mark it when it is the user's own, naming its owner otherwise. It SHALL mark nothing
the user did not ask for.

#### Scenario: Parent of another member pointed out
- **WHEN** `me` is `manuel`, `MR-DEV-2` is marked `done`, and every child of its parent `AG-DEV-1`, a task of `ana`, is now `done`
- **THEN** the agent says that `AG-DEV-1` may be ready to close and that closing it is `ana`'s decision, and runs no other command
- **Cases**: adds the entry `task-marking: Parent of another member pointed out` of `tests/not-automated.yaml`

#### Scenario: Own parent offered
- **WHEN** the last child of `SUP-1`, a task of the user's own, is marked `done`
- **THEN** the agent offers to mark `SUP-1` done, and runs `gemba mark SUP-1 done` only when the user agrees
- **Cases**: adds the entry `task-marking: Own parent offered` of `tests/not-automated.yaml`
