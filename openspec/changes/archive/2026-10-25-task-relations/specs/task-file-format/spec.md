# Spec Delta

## MODIFIED Requirements

### Requirement: Built-in frontmatter fields
The frontmatter SHALL be a YAML block between `---` lines at the start of the file
holding exactly, in this order, `status`, `ref`, `parent` (only with a parent),
`updated_at`, `done_at` (only while `done`) and `metadata`. `status` SHALL be
`open`, `in-progress`, `blocked` or `done`. `updated_at` SHALL be an ISO date, the
creation date at creation, that only moves forward. `done_at` SHALL be the ISO date the
task reached `done`, removed when it leaves `done`: "done since", never "was once done".

#### Scenario: Frontmatter of a new task
- **WHEN** a task is created on 2026-09-30 in a workstream whose effective metadata schema declares `client` and `project`, with `client` supplied as `acme`
- **THEN** its frontmatter is exactly
  ```yaml
  ---
  status: open
  ref: SUP-1
  updated_at: 2026-09-30
  metadata:
    client: acme
    project: null
  ---
  ```
- **Cases**: keeps `tests/cases/create/frontmatter-of-a-new-task.yaml`

#### Scenario: Invalid status value
- **WHEN** a frontmatter `status` is anything other than `open`, `in-progress`, `blocked` or `done`
- **THEN** the file is not a valid task and processes report it instead of guessing
- **Cases**: keeps `tests/cases/create/invalid-status-value.yaml` and `tests/cases/list/invalid-status-value.yaml`

#### Scenario: Done at follows the status
- **WHEN** a task marked `done` on 2026-10-01 is marked `blocked` on 2026-10-02
- **THEN** its frontmatter reads `status: blocked`, `updated_at: 2026-10-02` and holds no `done_at` key, with every other key as it was
- **Cases**: keeps `tests/cases/mark/done-at-follows-the-status.yaml`

#### Scenario: Frontmatter of a child task
- **WHEN** a task is created on 2026-09-30 with the parent `SUP-1`, in a workstream whose effective metadata schema declares `client`, with no value supplied
- **THEN** its frontmatter is exactly
  ```yaml
  ---
  status: open
  ref: SUP-2
  parent: SUP-1
  updated_at: 2026-09-30
  metadata:
    client: null
  ---
  ```
- **Cases**: adds `tests/cases/create/frontmatter-of-a-child-task.yaml`

### Requirement: A file read as a task
A process that reads tasks SHALL accept a `.md` file as a task only when its filename
matches `YYYY-MM-DD-<ref>-<slug>.md` with a valid date, it starts with a YAML
frontmatter that parses to a map, `status` is allowed, `ref` is a string equal to the
filename's, any `parent` is another ref, `updated_at` and any `done_at` are ISO dates,
and `metadata` is a map of scalars or lists of scalars. A file that fails a check SHALL
be reported with its path and the rule, and never read as a task.

#### Scenario: Valid file read
- **WHEN** a file conforms to every rule above
- **THEN** the process reads its ref, status, dates, metadata and description
- **Cases**: keeps `tests/cases/list/complete-record.yaml`

#### Scenario: Missing or unparseable frontmatter
- **WHEN** a `.md` file in a workstream folder does not start with a frontmatter block, or the block is not valid YAML
- **THEN** the file is reported as invalid and is not read as a task
- **Cases**: keeps `tests/cases/list/missing-or-unparseable-frontmatter.yaml`

#### Scenario: Ref mismatch
- **WHEN** the filename says `SUP-3` and the frontmatter says `ref: SUP-4`
- **THEN** the file is reported as invalid, naming both refs
- **Cases**: keeps `tests/cases/list/ref-mismatch.yaml`

#### Scenario: Invalid date field
- **WHEN** `updated_at` is missing or is not an ISO date
- **THEN** the file is reported as invalid, naming the field
- **Cases**: keeps `tests/cases/list/invalid-date-field.yaml`

#### Scenario: Metadata not a map
- **WHEN** `metadata` is missing, or is a list or a scalar
- **THEN** the file is reported as invalid, naming `metadata`
- **Cases**: keeps `tests/cases/list/metadata-not-a-map.yaml`

#### Scenario: Invalid parent
- **WHEN** one task file holds `parent: sup-1`, another `parent: 7`, and the file of `SUP-3` holds `parent: SUP-3`
- **THEN** each of the three is reported as invalid, naming `parent`, and none is listed
- **Cases**: adds `tests/cases/list/invalid-parent.yaml`
