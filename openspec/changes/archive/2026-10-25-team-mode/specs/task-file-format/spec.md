# Spec Delta

## MODIFIED Requirements

### Requirement: Task location
A task SHALL be a single Markdown file stored directly under `tasks/<workstream>/` in
the obeya, where `<workstream>` is a workstream identifier from the gemba config, or
under `tasks/<member>/<workstream>/` when the shared config declares a team, where
`<member>` is the folder name of its owner. Each workstream folder SHALL contain an
`archive/` subfolder into which finished tasks are moved unchanged. Both folders SHALL
exist in version control even when empty, holding a `.gitkeep` file.

#### Scenario: Task placed in its workstream folder
- **WHEN** a task is created for workstream `support`
- **THEN** its file is written directly under `tasks/support/` and nowhere else
- **Cases**: keeps `tests/cases/create/task-placed-in-workstream-folder.yaml`

#### Scenario: Archived task
- **WHEN** a task file is moved from `tasks/support/` to `tasks/support/archive/`
- **THEN** its content is unchanged and processes that list active tasks skip it unless archived tasks are explicitly requested
- **Cases**: keeps `tests/cases/create/archived-task.yaml` and `tests/cases/list/archived-task.yaml`

#### Scenario: Task placed in its member's folder
- **WHEN** a task is created for workstream `support` in an obeya whose team declares `manuel`, and the personal config declares `me: manuel`
- **THEN** its file is written directly under `tasks/manuel/support/`, with `tasks/manuel/support/.gitkeep` and `tasks/manuel/support/archive/.gitkeep`, and nowhere else
- **Cases**: adds `tests/cases/create/task-placed-in-its-member-folder.yaml`

### Requirement: Task ref
Every task SHALL carry a ref `<PREFIX>-<N>`, or `<INITIALS>-<PREFIX>-<N>` in an obeya
with a team, with its owner's initials, `<PREFIX>` being the prefix of the workstream
it was created in and `<N>` a positive integer without leading zeros. The ref SHALL be unique across the obeya, allocated by Gemba, never chosen by
the user or the agent, and internal: an external identifier belongs in metadata or as a
link in the body. The ref in the frontmatter SHALL equal the ref in the filename.

#### Scenario: Consecutive refs within a workstream
- **WHEN** the highest existing ref with prefix `CR` anywhere under `tasks/` (including archive folders) is `CR-12`
- **THEN** the next task created in the workstream with prefix `CR` receives `CR-13`
- **Cases**: keeps `tests/cases/create/consecutive-refs-within-workstream.yaml`

#### Scenario: First task of a prefix
- **WHEN** no task with prefix `EST` exists anywhere under `tasks/`
- **THEN** the first task created in the workstream with prefix `EST` receives `EST-1`
- **Cases**: keeps `tests/cases/create/first-task-of-a-prefix.yaml`

#### Scenario: Moved task keeps its ref
- **WHEN** a task with ref `CR-7` is moved into another workstream folder or into an archive folder
- **THEN** it keeps `CR-7`, and `CR-7` is never allocated again because allocation scans every task folder
- **Cases**: keeps `tests/cases/create/moved-task-keeps-its-ref.yaml`

#### Scenario: External key offered as ref
- **WHEN** the user asks for a task to be identified by a ticket key such as `PROD-16283`
- **THEN** Gemba still allocates an internal ref and records the ticket key in metadata or in the body, never as the ref
- **Cases**: keeps `tests/cases/create/external-key-offered-as-ref.yaml`

#### Scenario: Ref of a member's task
- **WHEN** `manuel`, with initials `MR`, creates the first task of the workstream with prefix `SUP` on 2026-10-25 with slug `export-times-out`
- **THEN** the task receives `MR-SUP-1`, its filename is `2026-10-25-MR-SUP-1-export-times-out.md`, and `gemba list` reads it with that ref and the title `Export times out`
- **Cases**: adds `tests/cases/create/ref-of-a-members-task.yaml`
