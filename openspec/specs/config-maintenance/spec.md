# config-maintenance Specification

## Purpose

The config process: the `gemba config` group, which checks `gemba.yaml` and shows the
effective config without ever writing it, and the `gemba-config` skill, which carries
the reference of every key and guides any edit of the file by hand.

## Requirements

### Requirement: Check validates the config without writing
`gemba config check` SHALL locate the gemba config as every command does and validate
it against every rule of the gemba config. When the config is valid, it SHALL print,
on standard output, a line stating that `gemba.yaml` is valid, a `workstreams:` line
listing every workstream as `<id> (<PREFIX>)` in the order of the catalogue, a
`default workstream:` line, and an `agent providers:` line listing the declared
providers in order or `none declared`, and SHALL exit 0. When the config is invalid,
it SHALL exit 1 and report the problem as every command reports it, the path of the
file and the first invalid element, or the parse error for malformed YAML. When no
config is found, it SHALL exit 1 and say so. The command SHALL write nothing in any
case.

#### Scenario: Valid config summarized
- **WHEN** `gemba config check` runs in a tasks repo whose config declares `support` (`SUP`) and `operations` (`OPS`), the default `operations`, and `agent_providers: [claude, agents]`
- **THEN** the output is the valid line, `workstreams: support (SUP), operations (OPS)`, `default workstream: operations` and `agent providers: claude, agents`, the tree is untouched and the exit code is 0

#### Scenario: Providers absent summarized
- **WHEN** `gemba config check` runs with a valid config that declares no `agent_providers`
- **THEN** the `agent providers:` line reads `none declared` and the exit code is 0

#### Scenario: Invalid config reported
- **WHEN** `gemba config check` runs with two workstreams declaring the same prefix, or with a `gemba.yaml` that is not valid YAML
- **THEN** the command exits 1, names the file and the problem, and the tree is untouched

#### Scenario: Check without a config
- **WHEN** no ancestor of the working directory holds `gemba.yaml`
- **THEN** `gemba config check` exits 1 and reports that no gemba config was found

### Requirement: Show prints the effective config
`gemba config show [--workstream <id>]` SHALL validate the config as `check` does and
print one JSON document holding the effective config: `organization`, `branch_prefix`
(the default when the config declares none), `repos_dir`, `ide` and `agent_providers`
as declared or `null`, `default_workstream`, and `workstreams`, a list in the order of
the catalogue where each entry holds `id`, `prefix`, `description`, `metadata`, the
effective metadata schema of the workstream as a list of `name`, `type`, `required`
and `description` (`null` when absent), and `processes`, one entry per process the
gemba config knows. The entry of a verb process holds its effective block: `context`,
the base context followed by the workstream's, separated by one empty line, the one
present when only one is, or `null`; and `rules`, every base rule followed by every
rule of the workstream, an empty list when none. The entry of a group holds one such
block per verb of the group and, for `harness`, `guide`, an object with the base guide
under `organization` and the workstream's under `workstream`, each `null` when absent.
Every process and verb SHALL be present even when neither level declares it. With
`--workstream`, the list SHALL hold that workstream only; an identifier not in the
catalogue SHALL be refused naming the valid ones. The command SHALL run from any folder
inside the tasks repo, a harness included, and SHALL write nothing.

#### Scenario: Effective config shown
- **WHEN** `gemba config show` runs in a tasks repo whose config declares the base field `client`, workstream `support` redeclaring `client` as required and adding `project`, and `operations` with no fields
- **THEN** the document lists `support` with `client` required and `project`, `operations` with `client` optional, every process entry with `context: null` and `rules: []`, and the top-level keys as declared

#### Scenario: Blocks combined from both levels
- **WHEN** the top level declares `create.context`, `create.rules`, `harness.guide` and `worktree.add.rules`, and workstream `support` declares `create.rules`, `harness.guide` and `worktree.add.rules`
- **THEN** the `support` entry holds `create.context` as the base text, `create.rules` with the base rule first, `harness.guide` with both texts under `organization` and `workstream`, and `worktree.add.rules` with the base rule then the workstream's, while `operations` holds the base values alone

#### Scenario: One workstream shown
- **WHEN** `gemba config show --workstream support` runs
- **THEN** `workstreams` holds the `support` entry only and the top-level keys are unchanged

#### Scenario: Unknown workstream refused
- **WHEN** `gemba config show --workstream billing` runs and `billing` is not in the catalogue
- **THEN** the command exits 1 and names the valid workstreams

#### Scenario: Show from inside a harness
- **WHEN** `gemba config show --workstream support` runs from inside the harness of a `support` task
- **THEN** the document is the same as from the tasks repo root

#### Scenario: Show refuses an invalid config
- **WHEN** `gemba config show` runs with a config whose `default_workstream` names a missing workstream
- **THEN** the command exits 1 and reports the problem as `check` does

### Requirement: The config is edited by hand through the skill
The CLI SHALL NOT write `gemba.yaml` after `gemba init` created it: every change to the
config is an edit of the file, by the person or by the agent on their behalf. The
`gemba-config` skill SHALL be the one process an agent follows for that edit, and its
description SHALL carry the phrases that make an agent choose it when the user asks to
add, change or remove a workstream, a field, a provider, the IDE command, the
repositories folder or the context and rules of a process, or asks what the config can
hold. The skill SHALL carry the reference of every key of the gemba config, its shape
and its constraints, as the gemba config specifies them, with no organization-specific
value in it. Following it, the agent SHALL read the current state with
`gemba config show`, ask for what the edit needs and the user did not say, edit the
file keeping every other line, comment and key as it was, run `gemba config check` and
fix the file until it exits 0, run `gemba skills update` when `agent_providers`
changed, tell the user that the skills folder of a removed provider is left for them to
delete, report the edit, and SHALL NOT commit. The skill SHALL never move, rename or
edit a task file for a workstream that changed.

#### Scenario: Agent edits the config by hand
- **WHEN** the user asks to add a workstream, a field or a provider, or to change the IDE command
- **THEN** the agent reads the effective config, asks for what is missing, edits `gemba.yaml` keeping the rest of the file as it was, and reports the edit without committing

#### Scenario: Edit verified by check
- **WHEN** the agent has edited `gemba.yaml`
- **THEN** it runs `gemba config check` and corrects the file until the command exits 0, never leaving an invalid config behind

#### Scenario: Providers change refreshes the skills
- **WHEN** the edit added or removed an entry of `agent_providers`
- **THEN** the agent runs `gemba skills update` and, for a removed provider, tells the user which skills folder is left for them to delete

#### Scenario: Reference free of organization values
- **WHEN** the `gemba-config` skill is read
- **THEN** it names every key of the gemba config and no workstream, prefix, field or value of any organization
