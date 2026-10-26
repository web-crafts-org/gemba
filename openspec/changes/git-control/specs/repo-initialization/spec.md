# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Init runs no git`
- TO: `### Requirement: Init creates no repository and no commit`

## MODIFIED Requirements

### Requirement: Init creates no repository and no commit
`gemba init` SHALL create no git repository and no commit: making the obeya a repository,
and committing what `init` wrote, is the person's step. It SHALL run git only when the
obeya root holds `.git` and the shared config declares a team, and then only to read
where the hooks go and whether `core.hooksPath` is set.

#### Scenario: No repository created
- **WHEN** `gemba init` runs in an empty folder
- **THEN** no `.git` folder exists afterwards
- **Cases**: keeps `tests/cases/init/no-git-repository-created.yaml`

#### Scenario: Hooks left alone without a team
- **WHEN** `gemba init` runs in the clone of an obeya without a team whose hooks folder holds a `pre-push` of another tool
- **THEN** that hook is byte for byte as it was, the output names no hook, and the exit code is 0
- **Cases**: adds `tests/cases/init/hooks-left-alone-without-a-team.yaml`

### Requirement: Init writes the layout and the skills
`init` SHALL also write `tasks/.gitkeep`; a `.gitignore` with `harnesses/`,
`gemba.local.yaml` and `/update.md`, the draft a refused record leaves; a
`.gitattributes` with `*.md text eol=lf` and `*.yaml text eol=lf`, so gemba's files
keep LF whatever `core.autocrlf` says; and the obeya skills of each selected provider,
as `gemba skills update` writes them. It SHALL print `written` and the path of each,
in that order, then the next step, the guided configuration through the agent, and
exit 0.

#### Scenario: Obeya scaffolded in the working directory
- **WHEN** `gemba init` runs in an empty folder with no `--providers`
- **THEN** the folder holds `gemba.yaml` with the `default` workstream as the default and `agent_providers` listing every known provider, `.gitignore` with `harnesses/`, `gemba.local.yaml` and `/update.md`, `.gitattributes` with the two `eol=lf` lines, `tasks/.gitkeep` and the obeya skills under `.claude/skills/` and `.agents/skills/`, `gemba-record`, `gemba-migrate` and `gemba-sync` among them, and no `gemba.local.yaml`; the output lists each path as `written` and ends with the next step, and the command exits 0
- **Cases**: modifies `tests/cases/init/obeya-scaffolded.yaml` (`gemba-sync` among the skills written and checked)

### Requirement: Init completes what is missing
Run where `gemba.yaml` or part of the layout already exists, `gemba init` SHALL write
only what is missing and report each path: `gemba.yaml` is never rewritten, `kept`; a
`.gitignore` or `.gitattributes` lacking some of its lines gets them appended in
order, `updated`, else `kept`; a missing `tasks/.gitkeep` or registered skill is
written; a skill on disk is `kept` whatever its state, as refreshing it is the work of
`gemba skills update`. A second run SHALL leave the tree identical.

#### Scenario: Second run changes nothing
- **WHEN** `gemba init` runs a second time with nothing changed in between
- **THEN** every path is reported as `kept`, the tree is identical and the command exits 0
- **Cases**: modifies `tests/cases/init/second-run-changes-nothing.yaml` (its output lists `gemba-sync`)

#### Scenario: Missing pieces completed
- **WHEN** `gemba init` runs in a folder holding a valid `gemba.yaml` with `agent_providers: [claude]`, a `.gitignore` with none of its three lines, a `.gitattributes` holding only `*.md text eol=lf`, and no `tasks/` folder or skills
- **THEN** `gemba.yaml` is kept byte for byte, `harnesses/`, `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the `*.yaml` line is appended to `.gitattributes`, `tasks/.gitkeep` and the skills of `claude` are written, no `.agents/` folder appears, and the output reports `kept gemba.yaml`, `updated .gitignore`, `updated .gitattributes` and `written` for the rest
- **Cases**: modifies `tests/cases/init/missing-pieces-completed.yaml` (`gemba-sync` among the skills written)

#### Scenario: Personal config ignored in an earlier obeya
- **WHEN** `gemba init` runs in an obeya made by an earlier version, whose `.gitignore` holds `harnesses/` alone and whose other files are all in place
- **THEN** `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0
- **Cases**: modifies `tests/cases/init/personal-config-ignored-in-an-earlier-obeya.yaml` (`gemba-sync` among the skills in place and kept)

#### Scenario: Draft ignored in an earlier obeya
- **WHEN** `gemba init` runs in an obeya whose `.gitignore` holds `harnesses/` and `gemba.local.yaml` and whose other files are all in place, as the version before this change left it
- **THEN** `/update.md` is appended to `.gitignore`, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0
- **Cases**: modifies `tests/cases/init/draft-ignored-in-an-earlier-obeya.yaml` (`gemba-sync` among the skills in place and kept)

#### Scenario: Existing skill kept whatever its state
- **WHEN** `gemba init` runs in an obeya where one skill was edited by hand and another was written by an older version
- **THEN** both files are left byte for byte as they were and reported as `kept`
- **Cases**: keeps `tests/cases/init/existing-skill-kept.yaml`

## ADDED Requirements

### Requirement: Init installs the hooks a clone turns on
When the obeya root holds `.git`, the shared config declares a team and `git_hooks`
resolves to on for the clone, `gemba init` SHALL write `pre-push`, `post-merge` and
`post-rewrite` into the hooks folder git names, each a script that runs `gemba hook`
with its own name and git's arguments, and ask nothing. It SHALL report each after the
skills: `written`, `updated` over an earlier script of gemba, or `kept`.

#### Scenario: Hooks installed for a team
- **WHEN** `gemba init` runs in a clone whose `gemba.yaml` declares a team and `git_hooks: true` and whose hooks folder holds no hook
- **THEN** `.git/hooks/pre-push`, `.git/hooks/post-merge` and `.git/hooks/post-rewrite` each run `gemba hook` with their own name, the output reports each `written` after the skills, and the exit code is 0
- **Cases**: adds `tests/cases/init/hooks-installed-for-a-team.yaml`

#### Scenario: Hooks installed for a clone that turns them on
- **WHEN** `gemba init` runs in a clone whose `gemba.yaml` declares a team and no `git_hooks`, and whose `gemba.local.yaml` declares `git_hooks: true`
- **THEN** the three hooks are written as for a team that turns them on
- **Cases**: adds `tests/cases/init/hooks-installed-for-a-clone.yaml`

#### Scenario: Hooks kept on a second run
- **WHEN** `gemba init` runs a second time in a clone where it installed the hooks
- **THEN** each hook is reported `kept` and is byte for byte as it was
- **Cases**: adds `tests/cases/init/hooks-kept-on-a-second-run.yaml`

#### Scenario: Earlier hook of gemba updated
- **WHEN** `.git/hooks/pre-push` holds a script that gemba wrote with another text, and `gemba init` runs with the hooks on
- **THEN** the script is rewritten with the current text and reported `updated`
- **Cases**: adds `tests/cases/init/earlier-hook-of-gemba-updated.yaml`

### Requirement: The pre-push hook fails closed
Each hook script SHALL check that `gemba` is on PATH, and when it is not, say how to
install it and that `git push --no-verify` skips the checks; the `pre-push` script SHALL
then refuse the push, and the other two SHALL let git go on.

#### Scenario: Gemba missing from PATH
- **WHEN** `git push` runs in a clone whose `pre-push` hook gemba wrote, from a client whose PATH does not hold `gemba`
- **THEN** the push is refused with a message that names `uv tool install gemba-cli` and `git push --no-verify`
- **Cases**: adds the entry `repo-initialization: Gemba missing from PATH` to `tests/not-automated.yaml`

### Requirement: Init never writes over a hook of another
A hook in the hooks folder that gemba did not write SHALL be kept as it is when it runs
`gemba hook` with its own name. Otherwise, while the hooks are on, `gemba init` SHALL
refuse with every other problem and write nothing, naming the hook, how to run
`gemba hook` from it, and `git_hooks: false` in `gemba.local.yaml`.

#### Scenario: Hook of another refused
- **WHEN** the hooks are on and `.git/hooks/pre-push` holds a script of another tool that does not run `gemba hook pre-push`
- **THEN** the command exits 1, names `.git/hooks/pre-push`, says to run `gemba hook pre-push "$@"` from it or to turn the hooks off in `gemba.local.yaml`, and the tree is untouched
- **Cases**: adds `tests/cases/init/hook-of-another-refused.yaml`

#### Scenario: Chained hook kept
- **WHEN** the hooks are on and `.git/hooks/pre-push` holds a script of another tool that also runs `gemba hook pre-push "$@"`
- **THEN** that script is byte for byte as it was and reported `kept`, and the other two hooks are written
- **Cases**: adds `tests/cases/init/chained-hook-kept.yaml`

### Requirement: Init writes no hook under a hooks path of its own
When git's `core.hooksPath` is set, `gemba init` SHALL write and remove no hook. While the
hooks are on, each of the three that is missing there or does not run `gemba hook` with
its own name SHALL be refused as a hook of another, naming `core.hooksPath` and its
folder.

#### Scenario: Hooks path refused
- **WHEN** the hooks are on and the clone sets `core.hooksPath` to a folder that holds no hook
- **THEN** the command exits 1, names `core.hooksPath`, its folder and the three hooks, writes no hook there, and the tree is untouched
- **Cases**: adds `tests/cases/init/hooks-path-refused.yaml`

### Requirement: Init removes its hooks when they are off
When the obeya root holds `.git`, the shared config declares a team and `git_hooks`
resolves to off for the clone, `gemba init` SHALL delete each of the three hooks that
gemba wrote, reporting it `removed`, and leave every other hook as it is.

#### Scenario: Hooks removed for a clone that turns them off
- **WHEN** `gemba init` installed the hooks in a clone, its `gemba.local.yaml` then declares `git_hooks: false`, and `gemba init` runs again
- **THEN** the three hooks are deleted and each is reported `removed`
- **Cases**: adds `tests/cases/init/hooks-removed-for-a-clone-that-turns-them-off.yaml`

### Requirement: The guided configuration asks a team about the hooks
With a team, right after who the user is, the agent following the `gemba-init` skill
SHALL ask whether the team turns on gemba's git hooks, saying what they check and that
each member may turn them off for their own clone. On a yes it SHALL write
`git_hooks: true` into `gemba.yaml` and, once the config is checked, run `gemba init`
again so that it installs them.

#### Scenario: Hooks asked of a new team
- **WHEN** the user configuring a new obeya says that `ana` and they share it, and names which member they are
- **THEN** the agent asks whether the team turns on gemba's git hooks, explains that they check every push against the members' folders and show what a pull changes in the user's tasks, writes `git_hooks: true` on a yes, and runs `gemba init` after `gemba config check` passes
- **Cases**: adds the entry `repo-initialization: Hooks asked of a new team` to `tests/not-automated.yaml`

### Requirement: A member hears of the team's hooks
When the agent configures the clone of a member and `git_hooks` of `gemba.yaml` is on,
it SHALL ask nothing about the hooks, and SHALL say in its report that `gemba init`
installed them and that `git_hooks: false` in `gemba.local.yaml`, then `gemba init`,
turns them off for this clone.

#### Scenario: Team hooks reported to a member
- **WHEN** `ana` configures her clone of an obeya whose `gemba.yaml` declares `git_hooks: true`
- **THEN** the agent asks no question about the hooks, and its report says that they are installed and how she turns them off for her clone
- **Cases**: adds the entry `repo-initialization: Team hooks reported to a member` to `tests/not-automated.yaml`
