# Spec Delta

## MODIFIED Requirements

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
- **Cases**: keeps `tests/cases/create/typed-metadata-values.yaml`

#### Scenario: Text kept as written
- **WHEN** the values `client=no` and `code=007` are supplied for two text fields
- **THEN** the frontmatter contains `client: 'no'` and `code: '007'`, both read back as strings
- **Cases**: keeps `tests/cases/create/text-kept-as-written.yaml`

#### Scenario: Repeated key becomes a list
- **WHEN** the values `project=checkout`, then `project=landing`, then `project=3` are supplied for a text field
- **THEN** the frontmatter contains `project: [checkout, landing, '3']`
- **Cases**: keeps `tests/cases/create/repeated-key-becomes-list.yaml`

#### Scenario: Repeated key on a field that is not text
- **WHEN** the values `hours=1` and `hours=2` are supplied for a number field
- **THEN** the task is not created and the message says only a text field holds a list
- **Cases**: keeps `tests/cases/create/repeated-key-on-a-field-that-is-not-text.yaml`

#### Scenario: Done requested at creation
- **WHEN** the initial status `done` is requested
- **THEN** the task is not created and the reason is reported
- **Cases**: keeps `tests/cases/create/done-requested-at-creation.yaml`

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
- **Cases**: keeps the entry `task-creation: Required field missing` of `tests/not-automated.yaml`

#### Scenario: Optional field not mentioned
- **WHEN** the schema declares an optional `hours` and the user did not mention hours
- **THEN** the agent does not ask and the field is written as `null`
- **Cases**: keeps the entry `task-creation: Optional field not mentioned` of `tests/not-automated.yaml`

#### Scenario: Optional field mentioned
- **WHEN** the schema declares an optional `client` and the user says the task is for Acme
- **THEN** the agent passes `client=acme` to the command
- **Cases**: keeps the entry `task-creation: Optional field mentioned` of `tests/not-automated.yaml`

#### Scenario: Text value in use reused
- **WHEN** the user says a new task is for "ACME" and the text field `client` already holds `acme` on other tasks
- **THEN** the agent finds `acme` with `gemba report --by client` and passes `client=acme`, asking when it cannot tell whether the user means the value in use
- **Cases**: keeps the entry `task-creation: Text value in use reused` of `tests/not-automated.yaml`

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
- **Cases**: keeps `tests/cases/create/unknown-workstream.yaml`

#### Scenario: Missing required keys reported together
- **WHEN** the effective schema requires `client` and `project` and neither is supplied
- **THEN** nothing is written and the message names both `client` and `project`
- **Cases**: keeps `tests/cases/create/missing-required-keys-reported-together.yaml`

#### Scenario: Undeclared key
- **WHEN** a value is supplied for `ticket_id` and no such field is declared
- **THEN** nothing is written and the message names `ticket_id` as undeclared
- **Cases**: keeps `tests/cases/create/undeclared-key.yaml`

#### Scenario: Values of the wrong type reported together
- **WHEN** the values `hours=three`, `due=2026-13-01` and `billed=yes` are supplied for a number, a date and a boolean field
- **THEN** nothing is written and one message names the three keys, each with its type
- **Cases**: keeps `tests/cases/create/values-of-the-wrong-type-refused.yaml`
