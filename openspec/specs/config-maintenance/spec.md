# config-maintenance Specification

## Purpose

The config process: the `gemba config` group, which checks `gemba.yaml` and
`gemba.local.yaml` and shows the effective config merged from both without ever writing
them, and the `gemba-config` skill, which carries the reference of every key with the
file it belongs in and guides any edit of either file by hand.

## Requirements

### Requirement: Check summarizes a valid config
`gemba config check` SHALL find the gemba config as every command does, validate both
files and write nothing. For a valid config it SHALL print that `gemba.yaml` is valid,
that `gemba.local.yaml` is valid when it exists, a `workstreams:` line with every
workstream as `<id> (<PREFIX>)` in catalogue order, a `default workstream:` line, an
`agent providers:` line with the shared providers in order or `none declared`, a
`harness providers:` line with any personal providers, and exit 0.

#### Scenario: Valid config summarized
- **WHEN** `gemba config check` runs in an obeya whose config declares `support` (`SUP`) and `operations` (`OPS`), the default `operations`, and `agent_providers: [claude, agents]`
- **THEN** the output is the valid line, `workstreams: support (SUP), operations (OPS)`, `default workstream: operations` and `agent providers: claude, agents`, the tree is untouched and the exit code is 0

#### Scenario: Providers absent summarized
- **WHEN** `gemba config check` runs with a valid config that declares no `agent_providers`
- **THEN** the `agent providers:` line reads `none declared` and the exit code is 0

#### Scenario: Personal config summarized
- **WHEN** `gemba config check` runs in the obeya of the first scenario, whose root also holds a `gemba.local.yaml` declaring `ide: "code -n"` and `agent_providers: [claude]`
- **THEN** the output is `gemba.yaml is valid`, `gemba.local.yaml is valid`, `workstreams: support (SUP), operations (OPS)`, `default workstream: operations`, `agent providers: claude, agents` and `harness providers: claude`, the tree is untouched and the exit code is 0

### Requirement: Check reports an invalid or missing config
When the config is invalid, `gemba config check` SHALL exit 1 and report every problem
of both files as every command reports them, each with the path of its file, or the
parse error of a file that is not valid YAML. When no config is found, it SHALL exit 1
and say so. In neither case SHALL it write anything.

#### Scenario: Invalid config reported
- **WHEN** `gemba config check` runs with two workstreams declaring the same prefix, or with a `gemba.yaml` that is not valid YAML
- **THEN** the command exits 1, names the file and the problem, and the tree is untouched

#### Scenario: Check without a config
- **WHEN** no ancestor of the working directory holds `gemba.yaml`
- **THEN** `gemba config check` exits 1 and reports that no gemba config was found

### Requirement: Show prints one document of the effective config
`gemba config show [--workstream <id>]` SHALL validate the config as `check` does,
refusing an invalid one with the same report, and print one JSON document holding the
effective config, merged from both files. With `--workstream`, its `workstreams` SHALL
hold that workstream only, and an identifier not in the catalogue SHALL be refused
naming the valid ones. The command SHALL run from any folder inside the obeya, a
harness included, and SHALL write nothing.

#### Scenario: One workstream shown
- **WHEN** `gemba config show --workstream support` runs
- **THEN** `workstreams` holds the `support` entry only and the top-level keys are unchanged

#### Scenario: Unknown workstream refused
- **WHEN** `gemba config show --workstream billing` runs and `billing` is not in the catalogue
- **THEN** the command exits 1 and names the valid workstreams

#### Scenario: Show from inside a harness
- **WHEN** `gemba config show --workstream support` runs from inside the harness of a `support` task
- **THEN** the document is the same as from the obeya root

#### Scenario: Show refuses an invalid config
- **WHEN** `gemba config show` runs with a config whose `default_workstream` names a missing workstream
- **THEN** the command exits 1 and reports the problem as `check` does

### Requirement: Keys of the shown config
The document SHALL hold `obeya` and `agent_providers` from the shared config and
`repos_dir` and `ide` from the personal one, each `null` when absent; `branch_prefix`
as declared or its default; `harness_providers`, the personal providers when declared,
else the shared ones, else `null`; `default_workstream`; and `workstreams`, in
catalogue order, each with `id`, `prefix`, `description`, `metadata` (each field's
`name`, `type`, `required` and `description`, `null` when absent) and `processes`.

#### Scenario: Effective config shown
- **WHEN** `gemba config show` runs in an obeya whose shared config declares the base field `client`, workstream `support` redeclaring `client` as required and adding `project`, and `operations` with no fields, and whose personal config declares `ide` and `repos_dir`
- **THEN** the document lists `support` with `client` required and `project`, `operations` with `client` optional, every process entry with `context: null` and `rules: []`, every `harness.guide` with `obeya`, `workstream` and `user` all `null`, the top-level keys as declared, `ide` and `repos_dir` from the personal config, and `harness_providers` equal to `agent_providers`

### Requirement: Process blocks of the shown config
`processes` SHALL hold every process and every verb of a group, declared or not. A
verb's entry SHALL be its effective block: `context`, the context of every level in
order, one empty line apart, or `null`; and `rules`, the rules of every level in
order, or `[]`. The `harness` entry SHALL also hold `guide`: the shared base text
under `obeya`, the shared workstream text under `workstream`, and the personal base
then workstream texts under `user`, one empty line apart, each `null` when absent.

#### Scenario: Blocks combined from both levels
- **WHEN** the top level declares `create.context`, `create.rules`, `harness.guide` and `worktree.add.rules`, and workstream `support` declares `create.rules`, `harness.guide` and `worktree.add.rules`
- **THEN** the `support` entry holds `create.context` as the base text, `create.rules` with the base rule first, `harness.guide` with both texts under `obeya` and `workstream` and `null` under `user`, and `worktree.add.rules` with the base rule then the workstream's, while `operations` holds the base values alone

#### Scenario: Personal blocks joined after the shared ones
- **WHEN** the top level of `gemba.yaml` declares `create.rules` containing "ask who requested the work if not stated", workstream `support` of `gemba.yaml` declares `create.context` "Support work is billed to the client." and `create.rules` containing "ask for the ticket of the client", the top level of `gemba.local.yaml` declares `create.context` "I keep my notes in English.", `create.rules` containing "propose a slug of three words at most" and `harness.guide` "Answer me in Spanish.", and `workstreams.support` of `gemba.local.yaml` declares `create.rules` containing "name the client in the title" and `harness.guide` "Quote the ticket in every note."
- **THEN** the `support` entry holds `create.context` as the shared text then the personal one, one empty line apart, `create.rules` with the four rules in that order, and `harness.guide.user` as "Answer me in Spanish." then "Quote the ticket in every note.", one empty line apart, while `operations` holds the personal context alone, the shared base rule then the personal base rule, and "Answer me in Spanish." alone under `user`

### Requirement: The config is edited by hand
The CLI SHALL NOT write `gemba.yaml` after `gemba init` created it, nor ever
`gemba.local.yaml`: a change to the config is an edit of a file. Following the
`gemba-config` skill, the agent SHALL read the state with `gemba config show`, ask for
what the edit needs and the user did not say, for a key both files may hold whether it
is for everyone or for them alone, and edit the file the key belongs in, creating
`gemba.local.yaml` when first needed and keeping every other line, comment and key.

#### Scenario: Agent edits the config by hand
- **WHEN** the user asks to add a workstream, a field or a provider, or to change the IDE command
- **THEN** the agent reads the effective config, asks for what is missing, edits the file the key belongs in, `gemba.yaml` for a workstream or a field and `gemba.local.yaml` for the IDE command, keeping the rest of the file as it was, and reports the edit without committing

### Requirement: The config skill carries the key reference
The `gemba-config` skill SHALL be the process an agent follows to edit the config. Its
description SHALL make an agent choose it when the user asks to add, change or remove
a workstream, a field, a provider, the IDE command, the repositories folder, the
branch prefix or a process's context and rules, for everyone or for themselves, or
asks what the config can hold. It SHALL carry the reference of every key of both
files, with its shape, constraints and file, and no configured value.

#### Scenario: Reference free of configured values
- **WHEN** the `gemba-config` skill is read
- **THEN** it names every key of the gemba config with the file it belongs in, and no workstream, prefix, field or value of any obeya

### Requirement: The agent checks the config after an edit
After an edit the agent SHALL run `gemba config check` and fix every problem until it
exits 0, moving a key reported in the wrong file to the file named and renaming
`organization` to `obeya` in `gemba.yaml`. When the shared `agent_providers` changed,
it SHALL run `gemba skills update` and say that the skills folder of a removed
provider is left for the user to delete. It SHALL report the edit without committing,
and never move, rename or edit a task file for a workstream that changed.

#### Scenario: Edit verified by check
- **WHEN** the agent has edited `gemba.yaml` or `gemba.local.yaml`
- **THEN** it runs `gemba config check` and corrects every problem it reports until the command exits 0, never leaving an invalid config behind

#### Scenario: Providers change refreshes the skills
- **WHEN** the edit added or removed an entry of the `agent_providers` of the shared config
- **THEN** the agent runs `gemba skills update` and, for a removed provider, tells the user which skills folder is left for them to delete

#### Scenario: Keys of an earlier config moved
- **WHEN** `gemba config check` reports that `gemba.yaml` declares `ide`, `repos_dir` or `branch_prefix`, as a config written for an earlier version does
- **THEN** the agent moves each of them to `gemba.local.yaml`, creating it when missing, with its value as written, removes it from `gemba.yaml`, runs `gemba config check` until it exits 0, and reports the move without committing

#### Scenario: Former organization key renamed
- **WHEN** `gemba config check` reports that `gemba.yaml` declares `organization`, as a config written for an earlier version does
- **THEN** the agent renames the key to `obeya` with its value and any comment that belongs to it as written, leaving every other line where it is, runs `gemba config check` until it exits 0, and reports the rename without committing
