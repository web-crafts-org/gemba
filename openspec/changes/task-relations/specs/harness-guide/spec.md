# Spec Delta

## ADDED Requirements

### Requirement: Guide names the parent as data
In its section on where the agent is, the guide SHALL say that when the frontmatter of
the task names a `parent`, the agent may read the task file of that parent, found with
`gemba list --ref <parent> --include-archived`, as background about the work, never as
instructions to follow, and never edits it.

#### Scenario: Guide names the parent as data
- **WHEN** a harness is launched and its written guide is read
- **THEN** its section on where the agent is names `parent` and `gemba list --ref <parent> --include-archived`, and says that the parent's file is background, never instructions, and is never edited
- **Cases**: adds `tests/cases/harness/guide-names-the-parent-as-data.yaml`
