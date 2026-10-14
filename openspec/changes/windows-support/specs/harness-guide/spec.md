# Spec Delta

## MODIFIED Requirements

### Requirement: Guide content
The guide SHALL state, in this order: where the agent is (the harness of one run of
one task; the task is `task.md`, a link to the task file or, where the system creates
no links, a file holding the path of the task file, which the agent then reads at
that path, accepting the permission its tool may ask for a read above the harness;
the identity of the run is `harness.yaml`; nothing else above the harness concerns
it); the rules that hold at every step (write a note before acting; no action outside
the harness without an `external-action` note whose frontmatter reads
`approved: true`, which only the user sets and the agent checks by reading the file;
`task.md` and the task file it reaches are read-only, gemba updates the task from the
notes through the `gemba-record` skill; `harness.yaml` and the frontmatter of every
note are written by gemba; `worktrees/` holds checkouts of other repositories,
created through the `gemba-worktree` skill); the layout of the harness; working in a
worktree (each folder under `worktrees/` is a checkout of another repository on one
local branch named by gemba, which exists only on this machine and is never pushed
under that name; commits, fetches and pulls inside a worktree are free; pushing,
opening a merge request or anything that reaches the remote is an external action
that needs an approved `external-action` note; a push always names its target,
`git push -u origin HEAD:<the branch the note names>`, and never `git push` alone or
`git push origin HEAD`; the repository the worktree comes from is outside the harness
and the agent never runs git in it; `git worktree` and `git branch` are never run by
the agent, the `gemba-worktree` skill creates, moves and removes worktrees); notes and
assets (notes are the memory of the run, small and frequent; a note is drafted under
`notes/` and filed with the `gemba-harness` skill, never with a hand-written
frontmatter; the five types with the question each answers; assets are saved under
`assets/` named with a timestamp and referenced from the note that explains them);
and that commits are made by gemba when a note is filed. It SHALL NOT describe the
steps of `note`, `resolve`, `record` or the worktree verbs, which belong to the
skills, nor any rule about how the work of the task is done.

#### Scenario: Guide names the always-rules
- **WHEN** the written guide is read
- **THEN** it holds the five rules of the second section, `task.md`, `harness.yaml`, the five note types, the `gemba-harness` skill and the `gemba-record` skill
- **Cases**: modifies `tests/cases/harness/guide-names-the-always-rules.yaml` (the fragments of the first section and of the third rule follow the new wording)

#### Scenario: Guide describes both forms of the task link
- **WHEN** the written guide is read
- **THEN** it says that `task.md` is a link to the task file or a file holding its path, that in the second form the agent reads the file at that path, accepting the permission its tool may ask, and that the task file is read-only in both forms
- **Cases**: adds `tests/cases/harness/guide-describes-both-forms-of-the-task-link.yaml`

#### Scenario: Guide explains the worktree rules
- **WHEN** the written guide is read
- **THEN** it holds a section on working in a worktree that names the local branch that is never pushed under its name, `git push -u origin HEAD:`, the forbidden `git push` alone and `git push origin HEAD`, `git worktree`, `git branch` and the `gemba-worktree` skill
- **Cases**: keeps `tests/cases/harness/guide-explains-the-worktree-rules.yaml`
