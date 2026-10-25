# Gemba

[![CI](https://github.com/web-crafts-org/gemba/actions/workflows/ci.yml/badge.svg)](https://github.com/web-crafts-org/gemba/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gemba-cli)](https://pypi.org/project/gemba-cli/)
[![Python](https://img.shields.io/pypi/pyversions/gemba-cli)](https://pypi.org/project/gemba-cli/)
[![License](https://img.shields.io/pypi/l/gemba-cli)](https://github.com/web-crafts-org/gemba/blob/main/LICENSE)

Gemba is a task-based system for working with AI agents. Every unit of work is one
Markdown file in a repository of your own, your agent registers, launches, updates and
closes those tasks through fixed processes, and each task is worked on inside a
harness: a folder of its own, with its notes, its evidence and the code it touches,
where nothing leaves without your written approval. Everything that is specific to one
organization, its kinds of work, its fields, its rules, lives in one config file, so
you keep one tasks repo per organization and the agent behaves the same in all of them.

The name is 現場, *gemba*: "the actual place", where the work happens. In Gemba that
place is the harness, a folder made for one task, where the agent works on it and on
nothing else, with everything the task needs inside and none of the noise of every
other pending thing. The task file is the logbook of that work: what was done, when,
and what it cost, recorded day by day. The harness is where the work gets done; the
task file is where you learn from it, the record that over time lets you see how you
work, measure it and improve it.

## The idea

```
  your tasks repo                                  the harness of one run
  +-------------------------------------+          +--------------------------------+
  | gemba.yaml   your organization:     |  launch  | task.md     the task, read-only|
  |              workstreams, fields,   | -------> | notes/      what the agent     |
  |              rules per process      |          |             found and decided  |
  | tasks/       one file per task,     |          | assets/     the raw evidence   |
  |              a ref like SUP-12      |  record  | worktrees/  the repositories,  |
  | .claude/     the skills: the        | <------- |             one branch per run |
  |   skills/    processes the agent    |          | CLAUDE.md   the guide of the   |
  |              follows                |          |             agent              |
  +-------------------------------------+          +--------------------------------+
```

The cycle of a task:

```
  create --> launch --> work in the harness --> record the day --> mark done
                          notes, worktrees,         |                  |
                          approved actions          v                  v
                                                 report             archive,
                                                 of the period      remove the harness
```

Three things keep it honest:

- **Commands own the frontmatter, agents own the body.** The status, the dates and the
  metadata of a task are written only by `gemba` commands; the agent writes prose.
- **Nothing leaves the harness without an approved note.** A push, a message, a
  deployment: the agent writes what it is about to do, and you approve it by editing
  the note. A yes in the chat does not count.
- **Every number comes from a command.** Counts and totals in a report are computed
  by `gemba report`, never by the agent.

Gemba works with any agent that reads skills from a folder: Claude Code
(`.claude/skills/`) and the agents that read `.agents/skills/` (Codex, Cursor,
Gemini CLI and others) are built in.

## Install and start

The prerequisites are [uv](https://docs.astral.sh/uv/) and `git` on PATH, on Linux,
macOS or Windows.

```bash
uv tool install gemba-cli
gemba --version
gemba init ~/nakatomi-tasks       # a tasks repo for the organization you work with
```

`gemba init` writes a minimal `gemba.yaml`, the `tasks/` folder, a `.gitignore` that
keeps the harnesses, your personal config, `gemba.local.yaml`, and a draft of an update
left at the root, `update.md`, out of the history, a `.gitattributes` that keeps LF line
endings in the files Gemba owns, and the skills for every agent it knows
(`--providers claude` keeps only one). It runs no git: make the folder a repository and
commit it when you like.

Then open the folder with your agent and ask it to configure Gemba. The `gemba-init`
skill asks, one question at a time, for your organization, the kinds of work you do,
which one takes a task that fits no other, what to record per task, your agents, your
editor and the folder of your repositories. It writes your editor and your
repositories folder into `gemba.local.yaml`, which stays on your machine, and the rest
into `gemba.yaml`.

From there, talk to the agent:

> Register a task: login fails on Safari for Acme's checkout app.

> Launch SUP-1.

> Record the day on this task.

> What did I do this week?

## The cycle of a task

Each step is a skill the agent follows and a command the skill runs. You can run the
commands yourself too; every one of them prints what it did or every problem it found,
at once, and exits 1 without writing anything when it refuses.

### Register

The `gemba-create` skill picks the workstream from the descriptions in `gemba.yaml`,
asks for any required field you did not give, and runs:

```bash
gemba create --workstream support --slug login-fails-on-safari \
  --description "Login fails on Safari for the checkout app" --set client=acme
```

The task file is `tasks/support/2026-09-30-SUP-1-login-fails-on-safari.md`:

```markdown
---
status: open
ref: SUP-1
updated_at: 2026-09-30
metadata:
  client: acme
  hours: null
---

Login fails on Safari for the checkout app

## Updates
```

The ref is allocated from the highest number already used, archives included, so it
is never reused. The metadata keys are exactly the ones declared for that workstream,
present even when unset, each read, compared and added by the type its field declares.

### Launch

```bash
gemba harness launch SUP-1
```

creates `harnesses/support/2026-09-30-SUP-1-login-fails-on-safari/` as a git
repository of its own, with `harness.yaml`, the run's identity; `task.md`, a link to
the task, or a file naming its path where the system creates no links; the guide of
the agent (`CLAUDE.md`, `AGENTS.md`); the harness skills;
`notes/`, `assets/` and `worktrees/`. It moves an `open` task to `in-progress` and
opens the folder with the `ide` command of `gemba.local.yaml` (`--no-open` skips it).
Launching again only reopens it. `harnesses/` is ignored by the tasks repo: a run is
not a record, the task is.

### Work in the harness

Start the agent inside the harness. The guide tells it to read the task and the notes
first, to write before it acts, and to keep every finding, blocker, decision or
summary as a small note, drafted as `notes/<slug>.md` and filed with the
`gemba-harness` skill, which names it after the clock, writes its frontmatter and
commits:

```bash
gemba harness note notes/login-trace.md --type finding --asset assets/1759350491-console.log
```

An `external-action` note describes, word for word, something to be done outside the
harness. Nothing happens until you set `approved: true` in its frontmatter from your
editor. After acting, the agent writes the outcome into the note and runs
`gemba harness resolve notes/<file>.md`, which records when.

When the task touches code, the agent checks out the repositories it needs as git
worktrees, each on a local branch named after the run:

```bash
gemba worktree add nakatomi-web                      # from the default branch of origin
gemba worktree add nakatomi-web --from release/2.4   # from another branch, or move to it
gemba worktree list                                  # branch, upstream, uncommitted, unpushed
gemba worktree remove nakatomi-web --yes             # the worktree and its branch
```

A repository is a folder under the `repos_dir` of `gemba.local.yaml`; Gemba never
clones.
The branch, `gemba/nakatomi/SUP-1`, exists only on your machine and is never pushed
under its own name: a push needs an approved note naming the branch of the remote, and
always names its target, `git push -u origin HEAD:<that branch>`. `add --from` and
`remove` refuse while anything is uncommitted or on no remote branch; `--force`
discards it, and the agent passes it only after you confirm what the command listed.

### Record the day

At the end of the day, ask the agent to record the day on the task. It distills the
notes of that date into a few bullets in `update.md` at the harness root and runs:

```bash
gemba record update.md                     # today
gemba record update.md --date 2026-09-30   # a past day
```

The bullets land under `### 2026-09-30` in the task's `## Updates` section,
`updated_at` moves forward, and the draft is deleted. Nothing is committed: the tasks
repo is yours to review and commit.

Work done outside a harness, such as a meeting or a review, is recorded from the tasks
repo. Tell the agent what was done: it writes only that into `update.md` at the tasks
repo root, never the notes of a harness, and names the task by its ref, archived or
not:

```bash
gemba record SUP-1 update.md                     # today
gemba record SUP-1 update.md --date 2026-09-30   # a past day
```

### Report

Ask the agent in the tasks repo for yesterday, for a day, a week or a month. The
`gemba-report` skill finds the tasks alive in the period with `gemba list`, reads the
subsections dated in it, groups what it finds by workstream, and lists the tasks
updated recently with nothing recorded. Every count and total comes from:

```bash
gemba report --done-from 2026-09-01 --done-to 2026-09-30 --by client --sum hours
```

which takes the filters of `gemba list`, groups with `--by` (`workstream`, `status`,
or a text or boolean field) and adds number fields with `--sum`, exactly.

### Close out

Three steps, each on its own, each asking before it deletes anything:

```bash
gemba mark SUP-1 done                  # done today: done_at and updated_at move
gemba mark SUP-1 open                  # reopened: done_at is removed
gemba harness remove SUP-1             # show what the run holds, delete nothing
gemba harness remove SUP-1 --yes       # delete the harness, its worktrees and branches
gemba archive SUP-1 OPS-2              # move each task file into archive/
```

A task done today can be reopened tomorrow in the same harness; a run can be thrown
away on a task still in progress; a task is archived only once it went cold, and only
after its harness is gone. Archived tasks leave `gemba list` unless
`--include-archived` is given.

### Keep the metadata

The hours grow, the work gets invoiced. Tell the agent, from the tasks repo or inside
the harness, and the `gemba-set` skill runs:

```bash
gemba set SUP-1 hours+=2                # added to the number the task holds
gemba set SUP-1 invoiced=2026-10-03     # a value, written by the type of its field
gemba set SUP-1 merge_requests=null     # cleared
```

It rewrites only the metadata, never `updated_at`, and refuses an undeclared key or a
value of the wrong type.

## The config

The config is two files at the root of the tasks repo. `gemba.yaml`, the shared
config, is committed: the workstreams, the fields, the organization and the rules
everyone who uses the tasks repo agrees on. `gemba.local.yaml`, the personal config, is
optional and ignored by git: what belongs to you and your machine. Both are edited by
hand, or by the `gemba-config` skill when you ask the agent to add a workstream, a
field or a rule, for everyone or for yourself; `gemba config check` validates both and
reports every problem at once, and `gemba config show` prints the config resolved, as
the skills read it. No command rewrites either.

`gemba.yaml`:

```yaml
default_workstream: operations

agent_providers: [claude, agents]
organization: nakatomi

metadata:
  - { name: client, type: text, required: true, description: Who the work is for }
  - { name: hours, type: number, description: Total hours spent on the task }
  - { name: invoiced, type: date, description: When the work was invoiced }

harness:
  guide: |
    Client data never leaves the harness: strip it from every asset you save.

workstreams:
  support:
    prefix: SUP
    description: Investigate a client-reported problem and deliver a report or a fix
    worktree:
      add:
        rules:
          - start from the branch deployed to production; ask when the task does not say it
  operations:
    prefix: OPS
    description: Anything that does not fit another workstream
```

`gemba.local.yaml`:

```yaml
ide: code -n
repos_dir: ~/projects

harness:
  guide: |
    Answer me in Spanish.

workstreams:
  support:
    create:
      rules:
        - name the client in the title
```

`ide`, `repos_dir` and `branch_prefix` go only in `gemba.local.yaml`: they run a
command or name paths and branches on your machine, so no command a teammate commits
runs on yours. `agent_providers` may go in both: the shared list decides the skills of
the tasks repo, and yours, when you declare one, the agents your harnesses are launched
for. The `context`, `rules` and `harness.guide` of your personal config come after the
shared ones, at the top level and for any workstream of the shared catalogue, so your
rule wins a contradiction; they add to the team's agreement and never remove from it.

What you can customize, all of it in the config and never in a skill:

- **Workstreams**, each with a prefix, a description the agent uses to choose one, and
  its own fields, and the one that takes a task that fits no other.
- **Metadata fields**, shared or per workstream, each of one type: `text`, `number`,
  `boolean` or `date`. Gemba reads, filters, groups and adds values by their type and
  never interprets their meaning.
- **Agent providers**, the organization, and in your personal config the IDE command
  (a string, or `{ command: code, args: [-n] }`), the repositories folder and the
  branch prefix.
- **`context` and `rules` for every process**, at the top level and per workstream, in
  either file: what the agent should know and do when it creates, lists, launches,
  notes, records, marks, archives or checks out, with the workstream's rule winning a
  contradiction, and yours winning over the shared ones.
- **The guide** of every harness, with a paragraph of your organization, one of the
  workstream and one of your own.

Changing any of it is a config edit: no skill and no code changes.

## On Windows

Gemba runs on Windows 10 or later with Git for Windows at its defaults, from
PowerShell, the command prompt or Git Bash, with no administrator rights:

```powershell
uv tool install gemba-cli
gemba init $HOME\nakatomi-tasks
```

- **The `ide` command** of `gemba.local.yaml`. A bare `code -n` works: the command is
  resolved on PATH the way Windows does, so `code` finds `code.cmd`. A string is split
  as a POSIX shell splits it, so a path with spaces or backslashes goes between double
  quotes, with each backslash doubled, or takes the map form, which needs no quoting
  rule:

  ```yaml
  ide: '"C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd" -n'
  ide: { command: 'C:\Program Files\Microsoft VS Code\bin\code.cmd', args: [-n] }
  ```
- **`task.md` in a harness** is a symbolic link where Windows lets Gemba create one,
  with Developer Mode on or a privileged account, and otherwise a file holding the
  relative path of the task; the guide tells the agent to read the task either way, so
  Developer Mode is optional.
- **Long paths.** When git fails with `Filename too long`, run
  `git config --global core.longpaths true`, which Gemba's message suggests.
- **An existing tasks repo.** Running `gemba init` again on a tasks repo made before
  this version adds the `.gitattributes`; on a checkout with `core.autocrlf=true`, run
  `git add --renormalize .` once and commit, so that the task files and the config are
  stored with LF.
- **WSL** is an alternative: inside it, Gemba is the Linux install above.

## Status

Gemba is young, at version 0.x, and built from daily use: the whole cycle above
works, and the shape of the commands may still change between minor versions, with
the changelog saying so. Ideas, questions and reports of what got in your way are the
most useful contribution right now: see [CONTRIBUTING.md](CONTRIBUTING.md), which also
describes how the product is developed, by specification, one case per scenario. What
each version changed is in [CHANGELOG.md](CHANGELOG.md), and every version has its
page under [Releases](https://github.com/web-crafts-org/gemba/releases).

## License

[MIT](LICENSE).
