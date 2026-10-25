# Spec Delta

## MODIFIED Requirements

### Requirement: The base guide text is rendered at launch
When the top level of the shared config declares `harness.guide`, `launch` SHALL
render it into the guide, verbatim, as a section titled `Your obeya`, after the text
of the guide asset and before the `Your workstream` and `Your user` sections when
there are any; otherwise no `Your obeya` section SHALL appear. Like the rest of the
guide, the section SHALL be written once: `gemba skills update` SHALL NOT touch it and
a relaunch SHALL NOT rewrite it.

#### Scenario: Obeya section rendered
- **WHEN** the top level of the config declares `harness.guide: "Open the harness through its workspace."`, workstream `support` declares no `harness.guide`, and a `support` task is launched
- **THEN** every guide in the harness holds, right after the text of the guide asset, a `## Your obeya` section whose body is `Open the harness through its workspace.`
- **Cases**: keeps `tests/cases/harness/obeya-section-rendered.yaml`

#### Scenario: Obeya and workstream sections rendered
- **WHEN** the top level of the config declares `harness.guide: "Open the harness through its workspace."`, workstream `support` declares `harness.guide: "Write for the client."`, and a `support` task is launched
- **THEN** every guide in the harness holds a `## Your obeya` section whose body is `Open the harness through its workspace.`, followed by a `## Your workstream` section whose body is `Write for the client.`, which closes the guide
- **Cases**: keeps `tests/cases/harness/obeya-and-workstream-sections-rendered.yaml`

## REMOVED Requirements

### Requirement: Guide content
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Guide
says where the agent is", "Guide names the rules at every step", "Guide explains
working in a worktree" and "Guide explains notes and assets".

## ADDED Requirements

### Requirement: Guide says where the agent is
The guide SHALL hold, in this order: where the agent is, the rules at every step, the
layout of the harness, working in a worktree, notes and assets, and commits. Where the
agent is SHALL say: the harness of one run of one task; the task is `task.md`, a link
to the task file or a file holding its path, which the agent then reads at that path,
accepting the permission its tool may ask; the identity of the run is `harness.yaml`;
nothing else above the harness concerns it.

#### Scenario: Guide describes both forms of the task link
- **WHEN** the written guide is read
- **THEN** it says that `task.md` is a link to the task file or a file holding its path, that in the second form the agent reads the file at that path, accepting the permission its tool may ask, and that the task file is read-only in both forms
- **Cases**: keeps `tests/cases/harness/guide-describes-both-forms-of-the-task-link.yaml`

### Requirement: Guide names the rules at every step
The rules at every step SHALL be: a note before acting; no action outside the harness
without an `external-action` note reading `approved: true`, which only the user sets
and the agent checks in the file; `task.md` and its task file are read-only, updated
by gemba through the `gemba-record` skill; gemba writes `harness.yaml` and the
frontmatter of notes; `worktrees/` holds checkouts made by the `gemba-worktree` skill.
It SHALL also give the five note types and the question each answers.

#### Scenario: Guide names the always-rules
- **WHEN** the written guide is read
- **THEN** it holds the five rules of the second section, `task.md`, `harness.yaml`, the five note types, the `gemba-harness` skill and the `gemba-record` skill
- **Cases**: keeps `tests/cases/harness/guide-names-the-always-rules.yaml`

### Requirement: Guide explains working in a worktree
Its section on worktrees SHALL say: each folder of `worktrees/` is a checkout on one
local branch named by gemba, never pushed under that name; commits, fetches and pulls
there are free; anything that reaches the remote needs an approved `external-action`
note, and a push names its target, `git push -u origin HEAD:<branch>`, never
`git push` alone or `git push origin HEAD`; the agent never runs git in the base
repository, nor `git worktree` or `git branch`: the `gemba-worktree` skill does.

#### Scenario: Guide explains the worktree rules
- **WHEN** the written guide is read
- **THEN** it holds a section on working in a worktree that names the local branch that is never pushed under its name, `git push -u origin HEAD:`, the forbidden `git push` alone and `git push origin HEAD`, `git worktree`, `git branch` and the `gemba-worktree` skill
- **Cases**: keeps `tests/cases/harness/guide-explains-the-worktree-rules.yaml`

### Requirement: Guide explains notes and assets
Its notes and assets section SHALL say that notes are the run's memory, small and
frequent, drafted under `notes/` and filed with the `gemba-harness` skill, never with
a hand-written frontmatter, and that assets are saved under `assets/`, named with a
timestamp and referenced from the note that explains them. A last section SHALL say
gemba commits when a note is filed. The guide SHALL NOT describe the steps of `note`,
`resolve`, `record` or the worktree verbs, nor how the task's work is done.

#### Scenario: Guide explains notes and assets
- **WHEN** the written guide is read
- **THEN** it says that notes are the memory of the run, small and frequent, drafted under `notes/` and filed with the `gemba-harness` skill, never with a hand-written frontmatter, that assets are saved under `assets/` named `<unix-timestamp>-<slug>.<ext>` and referenced from the note that explains them, and that gemba commits when a note is filed
- **Cases**: adds `tests/cases/harness/guide-explains-notes-and-assets.yaml`
