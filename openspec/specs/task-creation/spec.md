# task-creation Specification

## Purpose

Task creation registers a new unit of work as a task file: an agent resolves the
workstream and gathers what the config requires, and a gemba command validates the
request, allocates the ref and writes the file in one step so that no task can be
created with a wrong ref, a wrong folder or a wrong frontmatter.

## Requirements

### Requirement: Creation inputs
Creating a task SHALL take a workstream identifier and a slug, and MAY take a creation
date (default: today), an initial status (default: `open`; `in-progress` or `blocked`
when the user says so; `done` refused), a description, and metadata values as key and
value pairs. Each value SHALL be converted by its field's type, never read as YAML,
the literal `null` giving no value. A key given twice or more SHALL become a list, for
a `text` field only.

#### Scenario: Typed metadata values
- **WHEN** the metadata values `hours=3`, `billed=false`, `client=Acme Corp` and `due=2026-10-15` are supplied for a number, a boolean, a text and a date field
- **THEN** the frontmatter contains `hours: 3` as a number, `billed: false` as a boolean, `client: Acme Corp` as a string and `due: 2026-10-15` as a date

#### Scenario: Text kept as written
- **WHEN** the values `client=no` and `code=007` are supplied for two text fields
- **THEN** the frontmatter contains `client: 'no'` and `code: '007'`, both read back as strings

#### Scenario: Repeated key becomes a list
- **WHEN** the values `project=checkout`, then `project=landing`, then `project=3` are supplied for a text field
- **THEN** the frontmatter contains `project: [checkout, landing, '3']`

#### Scenario: Repeated key on a field that is not text
- **WHEN** the values `hours=1` and `hours=2` are supplied for a number field
- **THEN** the task is not created and the message says only a text field holds a list

#### Scenario: Done requested at creation
- **WHEN** the initial status `done` is requested
- **THEN** the task is not created and the reason is reported

### Requirement: Workstream selection by the agent
The agent SHALL choose the workstream from the `description` of each workstream in the
gemba config, SHALL use `default_workstream` for work that matches no description,
and SHALL ask the user when the request fits more than one workstream equally. The
agent SHALL NOT rely on any workstream knowledge that is not in the config.

#### Scenario: Clear match
- **WHEN** the user asks to register a review of a merge request and a workstream's description covers reviewing merge requests
- **THEN** the agent selects that workstream without asking

#### Scenario: No match
- **WHEN** the user asks to register work that matches no workstream description
- **THEN** the agent selects `default_workstream`

#### Scenario: Ambiguous match
- **WHEN** the request fits two workstream descriptions equally well
- **THEN** the agent asks the user which one to use before creating anything

### Requirement: Metadata gathering by the agent
The agent SHALL read the effective schema of the chosen workstream and ask only for
the required fields the user has not given, phrasing each from its field's description
when present; optional fields are filled only when the user mentions them. It SHALL
write each value in the form of its type and, for a text field, reuse the spelling of
a value in use, found with `gemba report --by <field>`, when the user means it. It
SHALL follow the workstream's `create.rules` and read its `create.context`.

#### Scenario: Required field missing
- **WHEN** the workstream requires `merge_url` and the user did not give a link
- **THEN** the agent asks for the merge request link before running the command

#### Scenario: Optional field not mentioned
- **WHEN** the schema declares an optional `hours` and the user did not mention hours
- **THEN** the agent does not ask and the field is written as `null`

#### Scenario: Optional field mentioned
- **WHEN** the schema declares an optional `client` and the user says the task is for Acme
- **THEN** the agent passes `client=acme` to the command

#### Scenario: Text value in use reused
- **WHEN** the user says a new task is for "ACME" and the text field `client` already holds `acme` on other tasks
- **THEN** the agent finds `acme` with `gemba report --by client` and passes `client=acme`, asking when it cannot tell whether the user means the value in use

### Requirement: Validation and refusal by the command
Before writing anything, the command SHALL check that the gemba config is valid, the
workstream exists, the slug is valid, the status is allowed at creation, every
metadata key is in the effective schema, every required key has a non-null value,
every value converts to its field's type, and a key is repeated only for a text field.
On any failure it SHALL write nothing, exit non-zero, and report in one message every
missing required key, undeclared key and value that does not convert.

#### Scenario: Unknown workstream
- **WHEN** the workstream identifier is not in the config
- **THEN** nothing is written and the message lists the valid workstream identifiers

#### Scenario: Missing required keys reported together
- **WHEN** the effective schema requires `client` and `project` and neither is supplied
- **THEN** nothing is written and the message names both `client` and `project`

#### Scenario: Undeclared key
- **WHEN** a value is supplied for `ticket_id` and no such field is declared
- **THEN** nothing is written and the message names `ticket_id` as undeclared

#### Scenario: Values of the wrong type reported together
- **WHEN** the values `hours=three`, `due=2026-13-01` and `billed=yes` are supplied for a number, a date and a boolean field
- **THEN** nothing is written and one message names the three keys, each with its type

### Requirement: Ref allocation and file creation in one step
The command SHALL allocate the ref and write the file as a single operation. The ref
SHALL be the workstream prefix followed by one plus the highest number already used
with that prefix in any filename under `tasks/`, including every `archive/` folder, or
`1` when none exists. The command SHALL create the workstream folder and its `archive/`
folder, each with a `.gitkeep`, when they do not exist. The command SHALL never
overwrite an existing file.

#### Scenario: Two consecutive creations
- **WHEN** two tasks are created one after the other in the same workstream whose highest ref was `DEV-4`
- **THEN** they receive `DEV-5` and `DEV-6`

#### Scenario: Archived refs are counted
- **WHEN** the only task with prefix `SUP` is `tasks/support/archive/2026-08-01-SUP-3-old-issue.md`
- **THEN** the next `support` task receives `SUP-4`

#### Scenario: First task of a new workstream
- **WHEN** a workstream was just added to the config and `tasks/<workstream>/` does not exist
- **THEN** the command creates `tasks/<workstream>/.gitkeep` and `tasks/<workstream>/archive/.gitkeep`, then writes the task with ref `<PREFIX>-1`

#### Scenario: Target path already exists
- **WHEN** the computed filename already exists
- **THEN** nothing is written and the collision is reported

### Requirement: Written file content
The created file SHALL conform to the task file format: frontmatter with `status`,
`ref`, `updated_at` equal to the creation date, and `metadata` with every effective
key present (`null` when unset), then the description when supplied, then an empty
`## Updates` section.

#### Scenario: Complete creation
- **WHEN** a `support` task is created on 2026-09-30 with slug `login-fails-on-safari`, description "Login fails on Safari for the checkout app" and `client=acme`, in a schema declaring `client` and `project`
- **THEN** `tasks/support/2026-09-30-SUP-1-login-fails-on-safari.md` contains a frontmatter with `status: open`, `ref: SUP-1`, `updated_at: 2026-09-30`, `metadata` with `client: acme` and `project: null`, followed by the description and an empty `## Updates` section

### Requirement: Reporting
On success the command SHALL print the path of the created file and its ref. The agent
SHALL then add the description to the body if it was not passed to the command, and
SHALL report to the user the path, the ref and a one-line summary. The agent SHALL NOT
commit the repository as part of creation.

#### Scenario: Successful creation reported
- **WHEN** the command creates `tasks/support/2026-09-30-SUP-1-login-fails-on-safari.md`
- **THEN** the user is told that path and the ref `SUP-1`, and the repository is left uncommitted

### Requirement: Skill contains no configured value
The `gemba-create` skill SHALL contain only the process: how to resolve the config, how
to choose the workstream, how to gather metadata, how to run the command and how to
report. It SHALL NOT name any workstream, prefix, metadata field or configured
rule.

#### Scenario: Config change without skill change
- **WHEN** the workstream catalogue or the metadata schema in `gemba.yaml` changes
- **THEN** the skill needs no edit for the create process to follow the new config
