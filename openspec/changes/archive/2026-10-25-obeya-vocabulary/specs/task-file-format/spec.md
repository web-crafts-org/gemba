# Spec Delta

## MODIFIED Requirements

### Requirement: Task location
A task SHALL be a single Markdown file stored directly under `tasks/<workstream>/` in
the obeya, where `<workstream>` is a workstream identifier from the
gemba config. Each workstream folder SHALL contain an `archive/` subfolder into which
finished tasks are moved unchanged. Both folders SHALL exist in version control even
when empty, holding a `.gitkeep` file.

#### Scenario: Task placed in its workstream folder
- **WHEN** a task is created for workstream `support`
- **THEN** its file is written directly under `tasks/support/` and nowhere else
- **Cases**: keeps `tests/cases/create/task-placed-in-workstream-folder.yaml`

#### Scenario: Archived task
- **WHEN** a task file is moved from `tasks/support/` to `tasks/support/archive/`
- **THEN** its content is unchanged and processes that list active tasks skip it unless archived tasks are explicitly requested
- **Cases**: keeps `tests/cases/create/archived-task.yaml`; keeps `tests/cases/list/archived-task.yaml`
