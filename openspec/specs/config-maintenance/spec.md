# config-maintenance Specification

## Purpose

The config process: the `gemba config` group, which checks `gemba.yaml` and
`gemba.local.yaml` and shows the effective config merged from both without ever writing
them, and the `gemba-config` skill, which carries the reference of every key with the
file it belongs in and guides any edit of either file by hand.

## Requirements

### Requirement: Check validates the config without writing
`gemba config check` SHALL locate the gemba config as every command does and validate
both files against every rule of the gemba config. When the config is valid, it SHALL
print, on standard output, a line stating that `gemba.yaml` is valid, a line stating
that `gemba.local.yaml` is valid when the personal config exists, a `workstreams:` line
listing every workstream as `<id> (<PREFIX>)` in the order of the catalogue, a
`default workstream:` line, an `agent providers:` line listing the providers of the
shared config in order or `none declared`, and, when the personal config declares
`agent_providers`, a `harness providers:` line listing them in order, and SHALL exit
0. When the config is invalid, it SHALL exit 1 and report every problem of both files
as every command reports them, each with the path of its file, or the parse error of
a file that is not valid YAML. When no config is found, it SHALL exit 1 and say so.
The command SHALL write nothing in any case.

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

#### Scenario: Personal config summarized
- **WHEN** `gemba config check` runs in the tasks repo of the first scenario, whose root also holds a `gemba.local.yaml` declaring `ide: "code -n"` and `agent_providers: [claude]`
- **THEN** the output is `gemba.yaml is valid`, `gemba.local.yaml is valid`, `workstreams: support (SUP), operations (OPS)`, `default workstream: operations`, `agent providers: claude, agents` and `harness providers: claude`, the tree is untouched and the exit code is 0

### Requirement: Show prints the effective config
`gemba config show [--workstream <id>]` SHALL validate the config as `check` does and
print one JSON document holding the effective config, merged from both files:
`organization` as the shared config declares it or `null`; `branch_prefix` as the
personal config declares it, or the default when it declares none; `repos_dir` and
`ide` as the personal config declares them or `null`; `agent_providers` as the shared
config declares it or `null`; `harness_providers`, the providers a launch writes the
harness for: the list of the personal config when it declares one, else the list of
the shared config, else `null`; `default_workstream`; and `workstreams`, a list in the
order of the catalogue where each entry holds `id`, `prefix`, `description`,
`metadata`, the effective metadata schema of the workstream as a list of `name`,
`type`, `required` and `description` (`null` when absent), and `processes`, one entry
per process the gemba config knows. The entry of a verb process holds its effective
block: `context`, the context of every level that declares one, in the order of the
effective block, separated by one empty line, or `null`; and `rules`, every rule of
every level in that order, an empty list when none. The entry of a group holds one
such block per verb of the group and, for `harness`, `guide`, an object with the base
guide of the shared config under `organization`, the workstream's guide of the shared
config under `workstream`, and the guide texts of the personal config under `user`,
its base text followed by the workstream's, one empty line apart, each `null` when
absent. Every process and verb SHALL be present even when no level declares it. With
`--workstream`, the list SHALL hold that workstream only; an identifier not in the
catalogue SHALL be refused naming the valid ones. The command SHALL run from any
folder inside the tasks repo, a harness included, and SHALL write nothing.

#### Scenario: Effective config shown
- **WHEN** `gemba config show` runs in a tasks repo whose shared config declares the base field `client`, workstream `support` redeclaring `client` as required and adding `project`, and `operations` with no fields, and whose personal config declares `ide` and `repos_dir`
- **THEN** the document lists `support` with `client` required and `project`, `operations` with `client` optional, every process entry with `context: null` and `rules: []`, every `harness.guide` with `organization`, `workstream` and `user` all `null`, the top-level keys as declared, `ide` and `repos_dir` from the personal config, and `harness_providers` equal to `agent_providers`

#### Scenario: Blocks combined from both levels
- **WHEN** the top level declares `create.context`, `create.rules`, `harness.guide` and `worktree.add.rules`, and workstream `support` declares `create.rules`, `harness.guide` and `worktree.add.rules`
- **THEN** the `support` entry holds `create.context` as the base text, `create.rules` with the base rule first, `harness.guide` with both texts under `organization` and `workstream` and `null` under `user`, and `worktree.add.rules` with the base rule then the workstream's, while `operations` holds the base values alone

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

#### Scenario: Personal blocks joined after the shared ones
- **WHEN** the top level of `gemba.yaml` declares `create.rules` containing "ask who requested the work if not stated", workstream `support` of `gemba.yaml` declares `create.context` "Support work is billed to the client." and `create.rules` containing "ask for the ticket of the client", the top level of `gemba.local.yaml` declares `create.context` "I keep my notes in English.", `create.rules` containing "propose a slug of three words at most" and `harness.guide` "Answer me in Spanish.", and `workstreams.support` of `gemba.local.yaml` declares `create.rules` containing "name the client in the title" and `harness.guide` "Quote the ticket in every note."
- **THEN** the `support` entry holds `create.context` as the shared text then the personal one, one empty line apart, `create.rules` with the four rules in that order, and `harness.guide.user` as "Answer me in Spanish." then "Quote the ticket in every note.", one empty line apart, while `operations` holds the personal context alone, the shared base rule then the personal base rule, and "Answer me in Spanish." alone under `user`

### Requirement: The config is edited by hand through the skill
The CLI SHALL NOT write `gemba.yaml` after `gemba init` created it, and SHALL never
write `gemba.local.yaml`: every change to the config is an edit of a file, by the
person or by the agent on their behalf. The `gemba-config` skill SHALL be the one
process an agent follows for that edit, and its description SHALL carry the phrases
that make an agent choose it when the user asks to add, change or remove a workstream,
a field, a provider, the IDE command, the repositories folder, the branch prefix or
the context and rules of a process, for everyone who uses the tasks repo or for
themselves alone, or asks what the config can hold. The skill SHALL carry the
reference of every key of both files, its shape, its constraints and the file it
belongs in, as the gemba config specifies them, with no organization-specific value
in it. Following it, the agent SHALL read the current state with `gemba config show`,
ask for what the edit needs and the user did not say, including, for a key both files
may hold, whether it is for everyone who uses the tasks repo or for the person alone;
edit the file the key belongs in, creating `gemba.local.yaml` when a personal key is
first set, keeping every other line, comment and key as it was; run
`gemba config check` and fix every problem it reports until it exits 0, moving a key
it reports in the wrong file to the file it names; run `gemba skills update` when the
`agent_providers` of the shared config changed; tell the user that the skills folder
of a removed provider is left for them to delete; report the edit, and SHALL NOT
commit. The skill SHALL never move, rename or edit a task file for a workstream that
changed.

#### Scenario: Agent edits the config by hand
- **WHEN** the user asks to add a workstream, a field or a provider, or to change the IDE command
- **THEN** the agent reads the effective config, asks for what is missing, edits the file the key belongs in, `gemba.yaml` for a workstream or a field and `gemba.local.yaml` for the IDE command, keeping the rest of the file as it was, and reports the edit without committing

#### Scenario: Edit verified by check
- **WHEN** the agent has edited `gemba.yaml` or `gemba.local.yaml`
- **THEN** it runs `gemba config check` and corrects every problem it reports until the command exits 0, never leaving an invalid config behind

#### Scenario: Providers change refreshes the skills
- **WHEN** the edit added or removed an entry of the `agent_providers` of the shared config
- **THEN** the agent runs `gemba skills update` and, for a removed provider, tells the user which skills folder is left for them to delete

#### Scenario: Reference free of organization values
- **WHEN** the `gemba-config` skill is read
- **THEN** it names every key of the gemba config with the file it belongs in, and no workstream, prefix, field or value of any organization

#### Scenario: Keys of an earlier config moved
- **WHEN** `gemba config check` reports that `gemba.yaml` declares `ide`, `repos_dir` or `branch_prefix`, as a config written for an earlier version does
- **THEN** the agent moves each of them to `gemba.local.yaml`, creating it when missing, with its value as written, removes it from `gemba.yaml`, runs `gemba config check` until it exits 0, and reports the move without committing
