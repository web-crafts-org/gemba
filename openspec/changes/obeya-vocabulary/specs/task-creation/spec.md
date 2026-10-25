# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Skill contains no organization-specific value`
- TO: `### Requirement: Skill contains no configured value`

## MODIFIED Requirements

### Requirement: Skill contains no configured value
The `gemba-create` skill SHALL contain only the process: how to resolve the config, how
to choose the workstream, how to gather metadata, how to run the command and how to
report. It SHALL NOT name any workstream, prefix, metadata field or configured
rule.

#### Scenario: Config change without skill change
- **WHEN** the workstream catalogue or the metadata schema in `gemba.yaml` changes
- **THEN** the skill needs no edit for the create process to follow the new config
- **Cases**: keeps the entry `task-creation: Config change without skill change` of `tests/not-automated.yaml`
