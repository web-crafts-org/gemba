# Spec Delta

## MODIFIED Requirements

### Requirement: Ref allocation and file creation in one step
The command SHALL allocate the ref and write the file as a single operation. The ref
SHALL be the workstream prefix, preceded by the initials of `me` in an obeya with a
team, followed by one plus the highest number already used with that start in any
filename under `tasks/`, archives included, or `1` when none exists. The
command SHALL create the workstream folder and its `archive/` folder, each with a
`.gitkeep`, when they do not exist. The command SHALL never overwrite an existing file.

#### Scenario: Two consecutive creations
- **WHEN** two tasks are created one after the other in the same workstream whose highest ref was `DEV-4`
- **THEN** they receive `DEV-5` and `DEV-6`
- **Cases**: keeps `tests/cases/create/two-consecutive-creations.yaml`

#### Scenario: Archived refs are counted
- **WHEN** the only task with prefix `SUP` is `tasks/support/archive/2026-08-01-SUP-3-old-issue.md`
- **THEN** the next `support` task receives `SUP-4`
- **Cases**: keeps `tests/cases/create/archived-refs-are-counted.yaml`

#### Scenario: First task of a new workstream
- **WHEN** a workstream was just added to the config and `tasks/<workstream>/` does not exist
- **THEN** the command creates `tasks/<workstream>/.gitkeep` and `tasks/<workstream>/archive/.gitkeep`, then writes the task with ref `<PREFIX>-1`
- **Cases**: keeps `tests/cases/create/first-task-of-a-new-workstream.yaml`

#### Scenario: Target path already exists
- **WHEN** the computed filename already exists
- **THEN** nothing is written and the collision is reported
- **Cases**: keeps `tests/cases/create/target-path-already-exists.yaml`

#### Scenario: Counters of two members
- **WHEN** `me` is `manuel` (`MR`), `tasks/manuel/support/archive/` holds `MR-SUP-2` and `tasks/ana/support/` holds `AG-SUP-5`, and a `support` task is created
- **THEN** it receives `MR-SUP-3` under `tasks/manuel/support/`, and `ana`'s folder is unchanged
- **Cases**: adds `tests/cases/create/counters-of-two-members.yaml`
