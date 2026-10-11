# Spec Delta

## ADDED Requirements

### Requirement: Skills name the published package
Every skill SHALL state, as its prerequisite, that the `gemba` command must be on the
PATH, that it is installed with `uv tool install gemba-cli` and checked with
`gemba --version`, and SHALL have the agent stop and tell the user to install it with
that command when it is not found. No skill SHALL name a path of the product
repository or a development install.

#### Scenario: Command missing
- **WHEN** the agent follows a skill and `gemba` is not found on the PATH
- **THEN** the agent stops and tells the user to run `uv tool install gemba-cli`

#### Scenario: No development path in a skill
- **WHEN** the assets of every registered skill are read
- **THEN** each one names `uv tool install gemba-cli` and none names `./cli` or an editable install
