# repo-initialization Specification

## Purpose

How an obeya is started: what `gemba init` writes so that every command runs from
the first second, how it converges when run again, what it refuses, and how the
`gemba-init` skill guides a person through the first configuration of the result.

## Requirements

### Requirement: Init writes the config of a new obeya
`gemba init [path]` SHALL make `path`, or the working directory, an obeya, creating
the folder when missing, asking nothing on the terminal. It SHALL write a `gemba.yaml`
that every command accepts: `default_workstream: default`, a catalogue holding the one
workstream `default`, with the prefix `TASK` and a description naming it the place of
work no other workstream fits, and `agent_providers` with the providers selected as
the next requirement says. It SHALL NOT write a `gemba.local.yaml`.

#### Scenario: Obeya scaffolded at a given path
- **WHEN** `gemba init acme-tasks` runs and `acme-tasks` does not exist
- **THEN** the folder is created, holds the same files, and nothing is written in the working directory itself

#### Scenario: Scaffolded config accepted by every command
- **WHEN** a task is created in the `default` workstream right after `gemba init`
- **THEN** the task file appears under `tasks/default/` with the ref `TASK-1`

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

### Requirement: Providers of the scaffold
`--providers` SHALL take a comma-separated list of provider identifiers the CLI knows.
When it is absent, the scaffold SHALL select every known provider in the order the CLI
lists them. The written config SHALL declare exactly the selected providers in the
order given, and the skills SHALL be written for those providers only. An unknown or
repeated identifier SHALL be refused: the command exits 1, names the identifier and the
known providers, and writes nothing.

#### Scenario: Providers selected
- **WHEN** `gemba init --providers claude` runs in an empty folder
- **THEN** `gemba.yaml` declares `agent_providers: [claude]`, the skills appear under `.claude/skills/` and no `.agents/` folder is created

#### Scenario: Unknown or repeated provider refused
- **WHEN** `gemba init --providers claude,cursor` or `gemba init --providers claude,claude` runs
- **THEN** the command exits 1, names `cursor` or the repeated `claude` and the known providers, and the folder is untouched

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

#### Scenario: Missing pieces completed
- **WHEN** `gemba init` runs in a folder holding a valid `gemba.yaml` with `agent_providers: [claude]`, a `.gitignore` with none of its three lines, a `.gitattributes` holding only `*.md text eol=lf`, and no `tasks/` folder or skills
- **THEN** `gemba.yaml` is kept byte for byte, `harnesses/`, `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the `*.yaml` line is appended to `.gitattributes`, `tasks/.gitkeep` and the skills of `claude` are written, no `.agents/` folder appears, and the output reports `kept gemba.yaml`, `updated .gitignore`, `updated .gitattributes` and `written` for the rest

#### Scenario: Personal config ignored in an earlier obeya
- **WHEN** `gemba init` runs in an obeya made by an earlier version, whose `.gitignore` holds `harnesses/` alone and whose other files are all in place
- **THEN** `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0

#### Scenario: Draft ignored in an earlier obeya
- **WHEN** `gemba init` runs in an obeya whose `.gitignore` holds `harnesses/` and `gemba.local.yaml` and whose other files are all in place, as the version before this change left it
- **THEN** `/update.md` is appended to `.gitignore`, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0

#### Scenario: Existing skill kept whatever its state
- **WHEN** `gemba init` runs in an obeya where one skill was edited by hand and another was written by an older version
- **THEN** both files are left byte for byte as they were and reported as `kept`

### Requirement: Init refuses an existing config it cannot use
`gemba init` SHALL read the providers from the shared config, validated with the
personal config beside it, before writing anything: an invalid config, or a shared
config that declares no `agent_providers`, whatever the personal one declares, SHALL
be refused with its problems, nothing written. `--providers` SHALL be refused when
`gemba.yaml` exists, since the command never edits it.

#### Scenario: Providers flag refused with an existing config
- **WHEN** `gemba init --providers agents` runs in a folder that holds `gemba.yaml`
- **THEN** the command exits 1, says that the config already declares the providers and that `gemba.yaml` is edited by hand, and writes nothing

#### Scenario: Invalid existing config refused
- **WHEN** `gemba init` runs in a folder whose `gemba.yaml` declares two workstreams with the same prefix, or declares no `agent_providers`, or whose `gemba.local.yaml` declares `obeya`
- **THEN** the command exits 1, reports the problem as every command reports it, and writes nothing, not even `.gitignore` or `tasks/`

### Requirement: Init refuses a nested obeya
When a strict ancestor of the folder to initialize holds `gemba.yaml`, `gemba init`
SHALL exit 1, name the obeya found, and write nothing, so that no obeya is
ever created inside another one, a harness included.

#### Scenario: Nested obeya refused
- **WHEN** `gemba init` runs from a subfolder of an obeya, or `gemba init sub` runs at its root
- **THEN** the command exits 1, names the root of the obeya found, and the tree is untouched

### Requirement: Init creates no repository and no commit
`gemba init` SHALL create no git repository and no commit: making the obeya a repository,
and committing what `init` wrote, is the person's step. It SHALL run git only when the
obeya root holds `.git` and the shared config declares a team, and then only to read
where the hooks go and whether `core.hooksPath` is set.

#### Scenario: No repository created
- **WHEN** `gemba init` runs in an empty folder
- **THEN** no `.git` folder exists afterwards

#### Scenario: Hooks left alone without a team
- **WHEN** `gemba init` runs in the clone of an obeya without a team whose hooks folder holds a `pre-push` of another tool
- **THEN** that hook is byte for byte as it was, the output names no hook, and the exit code is 0

### Requirement: The init skill configures a new obeya once
The `gemba-init` skill SHALL be the one process an agent follows to configure an obeya
that `gemba init` just created, and its description SHALL make an agent choose it when
the user asks to configure, set up or customize gemba for the first time. It SHALL be
used for that first configuration only, and for the personal config of a new clone of
an obeya with a team: any later edit follows the `gemba-config` skill.

#### Scenario: Guided configuration is used once
- **WHEN** the user asks to add a workstream or a field to an obeya already configured
- **THEN** the agent follows the `gemba-config` skill, not the guided configuration

### Requirement: The questions of the guided configuration
Following the `gemba-init` skill, the agent SHALL ask one question at a time, in this
order, skipping what the user already said: what this obeya holds, after saying what
an obeya is, to propose its `obeya` name; whether a team shares it, then its members
and who the user is; the kinds of work, to propose workstreams; the default
workstream; what to record per task, to propose typed fields; the agent providers; the
IDE command; and the repositories folder, only for work with code.

#### Scenario: Obeya explained before its name
- **WHEN** the agent asks its first question of the guided configuration
- **THEN** it says what an obeya is, the room where one part of the person's work is kept in sight, drawn as they choose, such as the organization they work for, a project, a team inside a company or a whole company, asks what this one holds, and proposes the `obeya` name from the answer as a kebab-case name

#### Scenario: Team asked after the obeya's name
- **WHEN** the user, asked after the obeya's name whether a team shares it, says that `ana` and they share it
- **THEN** the agent proposes for each member a kebab-case folder name and initials used by no other, asks which member the user is, and goes on to the kinds of work

### Requirement: What the guided configuration leaves for later
The agent SHALL NOT ask for what has a default or comes from use, the branch prefix
and the `context` and `rules` of the processes, and SHALL name them at the end as
later edits of the `gemba-config` skill.

#### Scenario: Agent does not ask what has a default
- **WHEN** the agent runs the guided configuration
- **THEN** it never asks for the branch prefix or for the `context` and `rules` of a process, and names them at the end as edits the `gemba-config` skill makes later

### Requirement: The guided configuration writes both files
The agent SHALL then write the answers through the `gemba-config` skill, the IDE
command, the repositories folder and, with a team, the member the user is into
`gemba.local.yaml`, which it creates, and every other answer into `gemba.yaml`; check
them and refresh the skills; and report the resulting config, saying that
`gemba.local.yaml` stays on this machine and that git ignores it, without committing.

#### Scenario: Agent configures a new obeya
- **WHEN** the user asks the agent to configure gemba in an obeya that holds the scaffolded config
- **THEN** the agent asks the questions in the order above, one per message, proposes the workstreams and the fields from the answers, writes the IDE command and the folder of the repositories into `gemba.local.yaml` and the rest into `gemba.yaml`, verifies both with `gemba config check`, refreshes the skills when the providers changed, and reports the config without committing

### Requirement: A member configures a new clone
When the shared config declares a team and the clone has no `gemba.local.yaml`, the
agent following the `gemba-init` skill SHALL ask only which member the user is, the IDE
command and, for work with code, the repositories folder, write them into
`gemba.local.yaml`, verify it with `gemba config check`, and leave `gemba.yaml`
untouched.

#### Scenario: Member configures a new clone
- **WHEN** `ana` cloned an obeya whose team declares `manuel` and `ana`, ran `gemba init` in it, and asks the agent to configure gemba
- **THEN** the agent asks which member she is among `manuel` and `ana`, then her IDE command and her repositories folder, writes `me: ana` with them into `gemba.local.yaml`, verifies it with `gemba config check`, and leaves `gemba.yaml` as it was

#### Scenario: User not yet a member
- **WHEN** the user configuring a new clone is not among the members of the team
- **THEN** the agent says that the team first adds them to `team` in `gemba.yaml` through the `gemba-config` skill, and writes no `me`

### Requirement: Init installs the hooks a clone turns on
When the obeya root holds `.git`, the shared config declares a team and `git_hooks`
resolves to on for the clone, `gemba init` SHALL write `pre-push`, `post-merge` and
`post-rewrite` into the hooks folder git names, each a script that runs `gemba hook`
with its own name and git's arguments, and ask nothing. It SHALL report each after the
skills: `written`, `updated` over an earlier script of gemba, or `kept`.

#### Scenario: Hooks installed for a team
- **WHEN** `gemba init` runs in a clone whose `gemba.yaml` declares a team and `git_hooks: true` and whose hooks folder holds no hook
- **THEN** `.git/hooks/pre-push`, `.git/hooks/post-merge` and `.git/hooks/post-rewrite` each run `gemba hook` with their own name, the output reports each `written` after the skills, and the exit code is 0

#### Scenario: Hooks installed for a clone that turns them on
- **WHEN** `gemba init` runs in a clone whose `gemba.yaml` declares a team and no `git_hooks`, and whose `gemba.local.yaml` declares `git_hooks: true`
- **THEN** the three hooks are written as for a team that turns them on

#### Scenario: Hooks kept on a second run
- **WHEN** `gemba init` runs a second time in a clone where it installed the hooks
- **THEN** each hook is reported `kept` and is byte for byte as it was

#### Scenario: Earlier hook of gemba updated
- **WHEN** `.git/hooks/pre-push` holds a script that gemba wrote with another text, and `gemba init` runs with the hooks on
- **THEN** the script is rewritten with the current text and reported `updated`

### Requirement: The pre-push hook fails closed
Each hook script SHALL check that `gemba` is on PATH, and when it is not, say how to
install it and that `git push --no-verify` skips the checks; the `pre-push` script SHALL
then refuse the push, and the other two SHALL let git go on.

#### Scenario: Gemba missing from PATH
- **WHEN** `git push` runs in a clone whose `pre-push` hook gemba wrote, from a client whose PATH does not hold `gemba`
- **THEN** the push is refused with a message that names `uv tool install gemba-cli` and `git push --no-verify`

### Requirement: Init never writes over a hook of another
A hook in the hooks folder that gemba did not write SHALL be kept as it is when it runs
`gemba hook` with its own name. Otherwise, while the hooks are on, `gemba init` SHALL
refuse with every other problem and write nothing, naming the hook, how to run
`gemba hook` from it, and `git_hooks: false` in `gemba.local.yaml`.

#### Scenario: Hook of another refused
- **WHEN** the hooks are on and `.git/hooks/pre-push` holds a script of another tool that does not run `gemba hook pre-push`
- **THEN** the command exits 1, names `.git/hooks/pre-push`, says to run `gemba hook pre-push "$@"` from it or to turn the hooks off in `gemba.local.yaml`, and the tree is untouched

#### Scenario: Chained hook kept
- **WHEN** the hooks are on and `.git/hooks/pre-push` holds a script of another tool that also runs `gemba hook pre-push "$@"`
- **THEN** that script is byte for byte as it was and reported `kept`, and the other two hooks are written

### Requirement: Init writes no hook under a hooks path of its own
When git's `core.hooksPath` is set, `gemba init` SHALL write and remove no hook. While the
hooks are on, each of the three that is missing there or does not run `gemba hook` with
its own name SHALL be refused as a hook of another, naming `core.hooksPath` and its
folder.

#### Scenario: Hooks path refused
- **WHEN** the hooks are on and the clone sets `core.hooksPath` to a folder that holds no hook
- **THEN** the command exits 1, names `core.hooksPath`, its folder and the three hooks, writes no hook there, and the tree is untouched

### Requirement: Init removes its hooks when they are off
When the obeya root holds `.git`, the shared config declares a team and `git_hooks`
resolves to off for the clone, `gemba init` SHALL delete each of the three hooks that
gemba wrote, reporting it `removed`, and leave every other hook as it is.

#### Scenario: Hooks removed for a clone that turns them off
- **WHEN** `gemba init` installed the hooks in a clone, its `gemba.local.yaml` then declares `git_hooks: false`, and `gemba init` runs again
- **THEN** the three hooks are deleted and each is reported `removed`

### Requirement: The guided configuration asks a team about the hooks
With a team, right after who the user is, the agent following the `gemba-init` skill
SHALL ask whether the team turns on gemba's git hooks, saying what they check and that
each member may turn them off for their own clone. On a yes it SHALL write
`git_hooks: true` into `gemba.yaml` and, once the config is checked, run `gemba init`
again so that it installs them.

#### Scenario: Hooks asked of a new team
- **WHEN** the user configuring a new obeya says that `ana` and they share it, and names which member they are
- **THEN** the agent asks whether the team turns on gemba's git hooks, explains that they check every push against the members' folders and show what a pull changes in the user's tasks, writes `git_hooks: true` on a yes, and runs `gemba init` after `gemba config check` passes

### Requirement: A member hears of the team's hooks
When the agent configures the clone of a member and `git_hooks` of `gemba.yaml` is on,
it SHALL ask nothing about the hooks, and SHALL say in its report that `gemba init`
installed them and that `git_hooks: false` in `gemba.local.yaml`, then `gemba init`,
turns them off for this clone.

#### Scenario: Team hooks reported to a member
- **WHEN** `ana` configures her clone of an obeya whose `gemba.yaml` declares `git_hooks: true`
- **THEN** the agent asks no question about the hooks, and its report says that they are installed and how she turns them off for her clone
