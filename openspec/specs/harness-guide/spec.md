# harness-guide Specification

## Purpose

The guide is the text every agent provider loads at the start of a session inside a
harness: thin, always present, holding what the agent must keep in mind at every step
and pointing to the skill for the rest.

## Requirements

### Requirement: The guide is a package asset with no organization value
The guide SHALL ship inside the gemba CLI package as one asset, SHALL be written by
`launch` under each declared provider's guide filename with identical content, and
SHALL contain no value specific to an organization: no workstream, prefix, field, tool
or person. The names it uses for the files of the harness SHALL be fixed (`task.md`,
`harness.yaml`, `notes/`, `assets/`, `worktrees/`) so that no value of the run needs
to be rendered into it.

#### Scenario: Same guide for every provider
- **WHEN** a harness is launched with `agent_providers: [claude, agents]`
- **THEN** `CLAUDE.md` and `AGENTS.md` have identical content

#### Scenario: Guide free of organization values
- **WHEN** the guide asset is read
- **THEN** it names no workstream, prefix or field of any organization

### Requirement: Guide content
The guide SHALL state, in this order: where the agent is (the harness of one run of
one task; the task is `task.md`, the identity of the run is `harness.yaml`; nothing
above the harness concerns it); the rules that hold at every step (write a note before
acting; no action outside the harness without an `external-action` note whose
frontmatter reads `approved: true`, which only the user sets and the agent checks by
reading the file; `task.md` is read-only, gemba updates the task from the notes
through the `gemba-record` skill; `harness.yaml` and the frontmatter of every note are
written by gemba; `worktrees/` holds checkouts of other repositories, created through
the `gemba-worktree` skill); the layout of the harness; working in a worktree (each
folder under `worktrees/` is a checkout of another repository on one local branch
named by gemba, which exists only on this machine and is never pushed under that name;
commits, fetches and pulls inside a worktree are free; pushing, opening a merge
request or anything that reaches the remote is an external action that needs an
approved `external-action` note; a push always names its target, `git push -u origin
HEAD:<the branch the note names>`, and never `git push` alone or `git push origin
HEAD`; the repository the worktree comes from is outside the harness and the agent
never runs git in it; `git worktree` and `git branch` are never run by the agent, the
`gemba-worktree` skill creates, moves and removes worktrees); notes and assets (notes
are the memory of the run, small and frequent; a note is drafted under `notes/` and
filed with the `gemba-harness` skill, never with a hand-written frontmatter; the five
types with the question each answers; assets are saved under `assets/` named with a
timestamp and referenced from the note that explains them); and that commits are made
by gemba when a note is filed. It SHALL NOT describe the steps of `note`, `resolve`,
`record` or the worktree verbs, which belong to the skills, nor any rule about how the
work of the task is done.

#### Scenario: Guide names the always-rules
- **WHEN** the written guide is read
- **THEN** it holds the five rules of the second section, `task.md`, `harness.yaml`, the five note types, the `gemba-harness` skill and the `gemba-record` skill

#### Scenario: Guide explains the worktree rules
- **WHEN** the written guide is read
- **THEN** it holds a section on working in a worktree that names the local branch that is never pushed under its name, `git push -u origin HEAD:`, the forbidden `git push` alone and `git push origin HEAD`, `git worktree`, `git branch` and the `gemba-worktree` skill

### Requirement: The workstream's guide text is rendered at launch
When the task's workstream declares `harness.guide` in the gemba config, `launch`
SHALL append it to the guide as a final section titled `Your workstream`, verbatim.
When it does not, the guide SHALL end without that section. The guide SHALL be written
once; `gemba skills update` SHALL NOT touch it and a relaunch SHALL NOT rewrite it.

#### Scenario: Workstream section rendered
- **WHEN** workstream `support` declares `harness.guide: "Write for the client."` and a `support` task is launched
- **THEN** every guide in the harness ends with a `## Your workstream` section whose body is `Write for the client.`

#### Scenario: No workstream section
- **WHEN** the task's workstream declares no `harness.guide`
- **THEN** no `Your workstream` section appears in the guide

### Requirement: The base guide text is rendered at launch
When the top level of the gemba config declares `harness.guide`, `launch` SHALL render
it into the guide, verbatim, as a section titled `Your organization`, after the text of
the guide asset and before the `Your workstream` section when the task's workstream
declares one, so that the text of the workstream stays the final section. When the top
level declares no `harness.guide`, no `Your organization` section SHALL appear. Like the
rest of the guide, the section SHALL be written once; `gemba skills update` SHALL NOT
touch it and a relaunch SHALL NOT rewrite it.

#### Scenario: Organization section rendered
- **WHEN** the top level of the config declares `harness.guide: "Open the harness through its workspace."`, workstream `support` declares no `harness.guide`, and a `support` task is launched
- **THEN** every guide in the harness holds, right after the text of the guide asset, a `## Your organization` section whose body is `Open the harness through its workspace.`

#### Scenario: Organization and workstream sections rendered
- **WHEN** the top level of the config declares `harness.guide: "Open the harness through its workspace."`, workstream `support` declares `harness.guide: "Write for the client."`, and a `support` task is launched
- **THEN** every guide in the harness holds a `## Your organization` section whose body is `Open the harness through its workspace.`, followed by a `## Your workstream` section whose body is `Write for the client.`, which closes the guide
