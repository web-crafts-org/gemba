# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: The guide is a package asset with no organization value`
- TO: `### Requirement: The guide is a package asset with no configured value`

## MODIFIED Requirements

### Requirement: The guide is a package asset with no configured value
The guide SHALL ship inside the gemba CLI package as one asset, SHALL be written by
`launch` under each declared provider's guide filename with identical content, and
SHALL contain no configured value: no workstream, prefix, field, tool
or person. The names it uses for the files of the harness SHALL be fixed (`task.md`,
`harness.yaml`, `notes/`, `assets/`, `worktrees/`) so that no value of the run needs
to be rendered into it.

#### Scenario: Same guide for every provider
- **WHEN** a harness is launched with `agent_providers: [claude, agents]`
- **THEN** `CLAUDE.md` and `AGENTS.md` have identical content
- **Cases**: keeps `tests/cases/harness/same-guide-for-every-provider.yaml`

#### Scenario: Guide free of organization values
- **WHEN** the guide asset is read
- **THEN** it names no workstream, prefix or field of any obeya
- **Cases**: modifies the entry `harness-guide: Guide free of organization values` of `tests/not-automated.yaml` (now `harness-guide: Guide free of configured values`)

### Requirement: The workstream's guide text is rendered at launch
When the task's workstream declares `harness.guide` in the shared config, `launch`
SHALL render it into the guide, verbatim, as a section titled `Your workstream`, after
the `Your obeya` section when there is one and before the `Your user` section
when there is one. When it does not, no `Your workstream` section SHALL appear. The
guide SHALL be written once; `gemba skills update` SHALL NOT touch it and a relaunch
SHALL NOT rewrite it.

#### Scenario: Workstream section rendered
- **WHEN** workstream `support` declares `harness.guide: "Write for the client."` and a `support` task is launched
- **THEN** every guide in the harness ends with a `## Your workstream` section whose body is `Write for the client.`
- **Cases**: keeps `tests/cases/harness/workstream-section-rendered.yaml`

#### Scenario: No workstream section
- **WHEN** the task's workstream declares no `harness.guide`
- **THEN** no `Your workstream` section appears in the guide
- **Cases**: keeps `tests/cases/harness/same-guide-for-every-provider.yaml`

### Requirement: The base guide text is rendered at launch
When the top level of the shared config declares `harness.guide`, `launch` SHALL
render it into the guide, verbatim, as a section titled `Your obeya`, after the
text of the guide asset and before the `Your workstream` and `Your user` sections when
there are any. When the top level of the shared config declares no `harness.guide`, no
`Your obeya` section SHALL appear. Like the rest of the guide, the section
SHALL be written once; `gemba skills update` SHALL NOT touch it and a relaunch SHALL
NOT rewrite it.

#### Scenario: Organization section rendered
- **WHEN** the top level of the config declares `harness.guide: "Open the harness through its workspace."`, workstream `support` declares no `harness.guide`, and a `support` task is launched
- **THEN** every guide in the harness holds, right after the text of the guide asset, a `## Your obeya` section whose body is `Open the harness through its workspace.`
- **Cases**: modifies `tests/cases/harness/organization-section-rendered.yaml`, renamed `obeya-section-rendered.yaml` (the guide it expects holds `## Your obeya`; it names its scenario by the new title)

#### Scenario: Organization and workstream sections rendered
- **WHEN** the top level of the config declares `harness.guide: "Open the harness through its workspace."`, workstream `support` declares `harness.guide: "Write for the client."`, and a `support` task is launched
- **THEN** every guide in the harness holds a `## Your obeya` section whose body is `Open the harness through its workspace.`, followed by a `## Your workstream` section whose body is `Write for the client.`, which closes the guide
- **Cases**: modifies `tests/cases/harness/organization-and-workstream-sections-rendered.yaml`, renamed `obeya-and-workstream-sections-rendered.yaml` (the guide it expects holds `## Your obeya`; it names its scenario by the new title)

### Requirement: The personal guide text is rendered at launch
When the personal config declares `harness.guide` at its top level, under the task's
workstream, or both, `launch` SHALL render them into the guide, verbatim, as one final
section titled `Your user`, the top-level text first and the workstream's after one
empty line. When it declares neither, no `Your user` section SHALL appear. Like the
rest of the guide, the section SHALL be written once.

#### Scenario: User section rendered
- **WHEN** the top level of `gemba.local.yaml` declares `harness.guide: "Answer me in Spanish."`, `gemba.yaml` declares no `harness.guide`, and a `support` task is launched
- **THEN** every guide in the harness holds, right after the text of the guide asset, a `## Your user` section whose body is `Answer me in Spanish.`, which closes the guide
- **Cases**: keeps `tests/cases/harness/user-section-rendered.yaml`

#### Scenario: Every guide section rendered
- **WHEN** the top level of `gemba.yaml` declares `harness.guide: "Open the harness through its workspace."`, its workstream `support` declares `harness.guide: "Write for the client."`, the top level of `gemba.local.yaml` declares `harness.guide: "Answer me in Spanish."`, its `workstreams.support` declares `harness.guide: "Quote the ticket in every note."`, and a `support` task is launched
- **THEN** every guide in the harness holds the `## Your obeya`, `## Your workstream` and `## Your user` sections in that order, and the body of the last one, which closes the guide, is `Answer me in Spanish.` and `Quote the ticket in every note.`, one empty line apart
- **Cases**: modifies `tests/cases/harness/every-guide-section-rendered.yaml` (the guide it expects holds `## Your obeya`; its name says obeya)
