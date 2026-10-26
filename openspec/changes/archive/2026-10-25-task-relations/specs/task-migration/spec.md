# Spec Delta

## ADDED Requirements

### Requirement: The parent follows the task
When a chosen old task names a parent that is not chosen, the agent SHALL ask whether
to migrate it too. It SHALL migrate a parent before its children and create each child
with `--parent <new ref of its parent>`. A child whose parent is not migrated SHALL be
created without one, its migration paragraph naming the old ref of its parent too.

#### Scenario: Child migrated after its parent
- **WHEN** the old task `SUP-3` names `SUP-1` as parent, and both are chosen
- **THEN** the agent creates the new task of `SUP-1` first, then creates the one of `SUP-3` with `--parent` and the new ref of `SUP-1`
- **Cases**: adds the entry `task-migration: Child migrated after its parent` of `tests/not-automated.yaml`

#### Scenario: Parent left behind
- **WHEN** the old task `SUP-3` names `SUP-1` as parent, and the user declines to migrate `SUP-1`
- **THEN** the new task of `SUP-3` is created without a parent, and its migration paragraph names `SUP-3` and its parent `SUP-1` of the old obeya
- **Cases**: adds the entry `task-migration: Parent left behind` of `tests/not-automated.yaml`
