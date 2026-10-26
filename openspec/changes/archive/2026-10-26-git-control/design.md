# Design

## Context

See proposal.md for the motivation. What shapes the approach:

- No module reads the git state of the obeya today. Git runs only in adapters, through
  `git()` and `git_lines()` of `commands/harness.py`, from argument lists, on harnesses
  and on the repositories under `repos_dir`. `git_lines` passes `--no-optional-locks`
  and refuses a folder without a `.git` of its own, so that git never reads the
  repository around it.
- `config.py` gives every top-level key its files in `LAYERS`, refuses a key in the
  wrong file, and reads the team and `me`; `team.write_problems` words the refusal of a
  clone with no `me`. `tasks.py` reads a task file by the reading rules (`_parse`), and
  its filename carries the ref (`FILENAME_PATTERN`).
- `obeya.py` owns the layout `gemba init` converges; `commands/init.py` validates
  everything before writing anything, then reports one line per path.
- Manuel's decisions of 2026-10-25: the change is team-only; the CLI never pulls and
  never pushes, the agent does through the skill; the hooks are an opt-in of the team,
  installed by `init` without a question, that each person turns on or off for their
  clone; a push of shared files is refused until confirmed; no commit or push is made by
  a command; trust-on-change stays out.
- Probed on git 2.56.0 (notes of the harness): a pull that fast-forwards or merges runs
  `post-merge`, in rebase mode too when nothing local is rebased; a rebasing pull with
  local commits runs `post-rewrite rebase`, whose standard input pairs each local commit
  with its rewritten one. `pre-push` gets the remote's name and URL as arguments and one
  `<local ref> <local id> <remote ref> <remote id>` line per ref, the remote id all zeros
  for a new branch; `git config --get gemba.shared` inside it reads the value of
  `git -c gemba.shared=<id> push`, which is never written to `.git/config`.
- Probed too (notes of the harness): with the bases of a range taken as the independent
  commits of its boundary, a merge pull with no resolution changes in the end only the
  clone's own files, while a merge that keeps an old copy of another member's file, or a
  resolution that edits `gemba.yaml`, shows in the net change and in no commit that is not
  a merge; the same holds for a new branch, and for `ORIG_HEAD..HEAD` after a pull.

## Goals / Non-Goals

**Goals:**
- One check, two consumers: the hooks and `gemba sync` compute their verdict with the
  same functions of one domain module and print the same lines.
- Every git command gemba runs on the obeya only reads: no fetch, no pull, no push, no
  write to the index or the config, so `gemba sync` leaves the clone byte for byte as it
  was.
- An obeya without a team, or a team that leaves the hooks off, behaves exactly as
  before: no existing case changes but those that list every obeya skill and the two
  that print the team.

**Non-Goals:**
- Access control. The hooks run in the member's clone, read `me` from a file the member
  writes, and are skipped by `--no-verify`; the git host decides who may push what.
- Trust-on-change: the shared files that came in are shown; accepting them is not added.
- Network: the agent fetches before `gemba sync`; the CLI reads the upstream as last
  fetched.

## Decisions

### D1. `sync.py`: the map and the verdicts as a domain module

A new domain module, `src/gemba/sync.py`, owns the ownership map, the checks of an
outgoing and an incoming change, the confirmation, and every line they print. It has no
side effect: the adapters read git and hand it plain data.

- `classify(path, me, members)` returns the owner kind of a POSIX path, `own`,
  `member` (with the member's name), `private` or `shared`: `tasks/<me>/...` is `own`;
  `tasks/<m>/...` for any other member of the team, active or not, `member`;
  `gemba.local.yaml` exactly, or `harnesses/...`, `private`; anything else, `tasks/`
  files outside every member's folder included, `shared`.
- `Commit` holds the full id, the short id, the author's name, the subject and the
  paths it changes. `OwnFile` holds a path under `tasks/<me>/` and its text as of the
  commit pushed, or `None` when it was deleted there.
- `outgoing(net, commits, merges, own_files, own_paths, context, confirmed)` returns the
  problems and the shared lines (D4, D5); `incoming(net, commits, merges, patch,
  context)` returns the lines of what came in (D6). `net` holds the paths of the net
  change (D3), `commits` the commits of the range that are not merges, each with the
  paths it changes, and `merges` its merges; together they name the commits behind a
  path. `confirmed(values, tip)` says whether a `gemba.shared` value names the commit
  pushed; `confirm_command(tip)` gives `git -c gemba.shared=<tip> push`.
  `context` carries `me`, the initials of `me`, the members and the workstream
  identifiers, taken from `Config` by the adapter.
- The validity of a task file reuses the reading rules: `tasks.py` exposes `_parse` as
  the public `parse`, and `sync.py` calls it with the text read from git. A
  `TaskError` becomes `<path> is not a valid task: <rule>`.

Alternative: the checks inside the hook adapter, which `gemba sync` would import.
Rejected: an adapter would hold rules, and the checks would be tested through git only.

### D2. Reading the obeya with git: `commands/obeya_git.py`

A helper of the adapters, as `selection.py` is for `list` and `report`, owns every git
command run on the obeya. Each one is an argument list, with
`git --no-optional-locks -c core.quotePath=false -C <root>`, and only reads:

- `rev-parse --abbrev-ref --symbolic-full-name @{upstream}` and `rev-parse --verify`
  for the branch, its upstream and the ids;
- `rev-list --no-merges --reverse <tip> --not <excluded...>` and `rev-list --merges` with
  the same range for its commits, and `rev-list --boundary` with `merge-base
  --independent` for its bases (D3);
- `log -1 --format=%H%x00%h%x00%an%x00%s` and `diff-tree -r --root --no-commit-id
  --name-only --no-renames -z <id>` for a commit and its paths;
- `diff --name-only --no-renames -z <base> <tip>` for the net change, and `ls-tree -r
  --name-only -z <tip>` for a range with no base;
- `ls-tree -r --name-only -z <tip> -- tasks/<me>/` and `cat-file blob <tip>:<path>` for
  the member's own files as of the commit pushed, each decoded with `platform.decode`;
- `diff --no-color --no-ext-diff --no-textconv <base> <tip> -- <paths>` for the patch of
  the member's own tasks in a net change: no external diff and no text conversion, so no
  program a config names runs;
- `status --porcelain=v1 -z --no-renames --untracked-files=all` for the uncommitted
  changes, ignored files left out;
- `config --get-all gemba.shared` for the confirmation, and `rev-parse --git-path
  hooks` and `config --get core.hooksPath` for the hooks folder (D8).

Each returns `None` with git's message on a failure, as `git()` does, and the adapter
words the refusal. The root must hold `.git`, as `git_lines` requires.

### D3. The outgoing commits and the net change

- `gemba hook pre-push` reads its standard input as bytes, decoded as UTF-8, one line per
  pushed ref. A line whose local id is all zeros deletes a branch and is skipped. Its
  range is `<local id> --not <remote id>`, or, when the remote id is all zeros or not
  known to the clone, `<local id> --not` every `refs/remotes/<remote>/` ref, read with
  `for-each-ref`. Ids are checked as 40 or 64 hexadecimal digits before they reach an
  argument list. `gemba sync` takes the range `HEAD --not @{upstream}`.
- The net change of the range is what the push is checked on (D4). Its bases are the
  boundary commits of the range, the lines of `rev-list --boundary` that start with `-`,
  reduced with `merge-base --independent`; a path is in the net change when `diff
  --name-only` lists it against every base, and a range with no base counts every path of
  its tip. In a fast-forward the one base is the remote's previous commit, so the net
  change is what the push changes on the remote, merges included; after a merge pull it
  is the upstream, which already holds the other members' changes, so they are not
  counted. No commit is checked against its first parent: so compared, the merge of a
  pull would carry every change of the other members.
- The commits of the range that are not merges are read for two things: to name the
  commits behind each path of a problem, from the paths each changes, and to refuse a
  private path that any of them changes, even one a later commit removes, since the
  remote's history would keep it. A change to another member's file or to a shared file
  made and undone among them leaves the remote's tree as it was and is not reported.

### D4. The checks of an outgoing change

Every problem is collected, in this order, each one line. `<who>` names the commits of
the range that are not merges and change the path, as `<short>`, `<short> and <short>`
or `<short>, <short> and <short>`, or, when none does, its merges, as `merge <short>` or
`merges <short> and <short>`:

- `<who> changes <path>, in the folder of <member>: only <member> writes it`, for each
  such path of the net change;
- `<short> changes <path>, private to each clone: it never leaves the clone`, for each
  commit that is not a merge and each private path it changes, and the same line with
  `<who>` for a private path of the net change that no such commit changes;
- for each `.md` file under `tasks/<me>/` that the net change adds or changes and that
  exists as of the commit pushed: `<path> is not in a workstream folder of tasks/<me>/`
  when it lies outside `tasks/<me>/<workstream>/` and its `archive/`; `<path> is not a
  valid task: <rule>`; `<path> holds <ref>, without the initials of <me> (<INITIALS>)`;
- `<ref> is held by <path> and <path>: a ref is never held twice`, over the filenames
  of `tasks/<me>/` as of the commit pushed, when one of them is in the net change;
- without a confirmation, `<who> changes the shared file <path>` per path, then one line
  `confirm them with git -c gemba.shared=<full id of the commit pushed> push`.

A path changed by three commits makes one line, and a merge that keeps an old copy of
another member's file reads `merge 7e8f9a0 changes
tasks/ana/support/2026-10-20-AG-SUP-1-export.md, in the folder of ana: only ana writes
it`.

A clone without `me` gets the one problem of `team.write_problems` for a missing `me`,
which names `gemba.local.yaml` and the members, and no other. The pre-push hook prints
`gemba hook pre-push: push to <remote ref> refused:`, the lines as `- <line>`, and
`the gemba-sync skill explains each problem; git push --no-verify skips these checks`,
on its standard error, and exits 1; with no problem it prints nothing and exits 0.

### D5. The confirmation

`git -c gemba.shared=<id> push` sets the value for that one command; git passes it to
the hook through its environment, and `config --get-all gemba.shared` reads it. A pushed
ref is confirmed when one value equals its local id in full. The confirmation lifts the
shared lines only. A value written to `.git/config` by hand would confirm only the one
commit it names, so it cannot turn the check off for later pushes.

Alternatives: an environment variable read by gemba, which `SECURITY.md` says it never
reads; a question on the terminal, which an agent and a GUI client cannot answer.

### D6. What came in

- `post-merge` takes the range `HEAD --not ORIG_HEAD`. `post-rewrite` acts only when its
  argument is `rebase`, and takes the range `<onto> --not ORIG_HEAD`, where `<onto>` is
  the first parent of the new commit, the second id, on the first line of its standard
  input, or `HEAD` when it holds no line; with `amend` it does nothing. `gemba sync` takes
  `@{upstream} --not HEAD`. Each range gives its commits that are not merges, its merges
  and its net change, as in D3.
- The report lists the paths of the net change, each `by <who>` as in D4, every commit
  followed by its author, `1a2b3c4 (Ana Gómez)`: `- your tasks:`, then `  <path>, by
  <who>` per path and the patch of those paths from the first base to the tip, each line
  indented by four spaces; `- shared files:`, then `  <path>, by <who>` per path; and
  `- <path>, private to each clone, by <who>: the pull wrote it over yours` after a pull,
  or `a pull writes it over yours` in `gemba sync`. The commits that are not merges and
  change only other members' folders close the report as `- <n> commits change only the
  tasks of other members`.
- The hooks print `gemba hook <verb>: <n> commits came in` and those lines on the
  standard error, only when one path is listed, and always exit 0; git ignores what a
  `post-merge` or `post-rewrite` returns, and the report is all they owe.

### D7. `gemba sync`

A bare verb on the obeya (`commands/sync.py`), with `--root` as every other command. It
loads the config and refuses, with every problem at once and exit 1, an obeya without a
team (`sync needs a team: gemba.yaml declares none`), a clone without `me`, a root
without `.git`, a detached `HEAD`, and a branch with no upstream (`branch <name> has no
upstream`). Otherwise it prints to the standard output, and exits 0:

```text
branch main, upstream origin/main
incoming: 2 commits
- your tasks:
  tasks/manuel/support/2026-10-20-MR-SUP-1-export.md, by 1a2b3c4 (Ana Gómez)
    @@ -3 +3 @@
    -status: open
    +status: blocked
- 1 commit changes only the tasks of other members
outgoing: 1 commit
- 3c4d5e6 Manuel Robles: Add MR-SUP-2
uncommitted:
- yours: tasks/manuel/support/2026-10-25-MR-SUP-2-invoices.md
- of ana: tasks/ana/support/2026-10-21-AG-SUP-1-login.md
- shared: README.md
push: ready
```

- `incoming: none`, `outgoing: none` and `uncommitted: none` when empty. Every commit of
  the outgoing range is listed, merges included; what comes in is listed as D6 says.
- The problems of D4 follow the outgoing commits under `refused:`, and the shared lines
  under `to confirm:`.
- An uncommitted line reads `yours`, `of <member>`, `private` or `shared`, from the map.
- `hooks: on for this clone, but <names> not installed: run gemba init`, or `hooks: off
  for this clone, but <names> written by gemba still there: run gemba init`, from the
  states of D8, only when they disagree with `git_hooks`.
- The last line is the verdict: `push: nothing to push`, `push: ready`,
  `push: needs confirmation: git -c gemba.shared=<full id of HEAD> push`, or
  `push: refused` when one problem of D4 stands.

Exit 0 whatever the verdict: the command reports, the skill decides, and the hook is
what refuses. The patch of the member's own tasks is printed whole: the agent reads it,
and a person reads `git diff` the same way.

### D8. The hooks as part of the layout: `obeya.py`

- `HOOKS = ("pre-push", "post-merge", "post-rewrite")`, `HOOK_MARKER`, the comment on the
  second line of every script gemba writes, and `hook_script(name)`:

  ```sh
  #!/bin/sh
  # Written by gemba init for the git hooks of a team (git_hooks); gemba init removes it.
  if ! command -v gemba >/dev/null 2>&1; then
    echo "gemba hook pre-push: gemba is not on PATH: install it with uv tool install gemba-cli; git push --no-verify skips these checks" >&2
    exit 1
  fi
  exec gemba hook pre-push "$@"
  ```

  `post-merge` and `post-rewrite` print the same and `exit 0`. `exec` hands the
  script's standard input to `gemba hook`.
- `hook_state(name, text)` is `missing` (no file), `current` (the script of this
  version), `earlier` (the marker with another text), `chained` (no marker, a line that
  runs `gemba hook <name>`) or `other`.
- `hook_problem(location, name)` words the refusal of D9.

### D9. Installing, keeping and removing the hooks in `init`

`commands/init.py`, after loading an existing config and before writing anything, when
the config declares a team and the root holds `.git` (a folder, or the file of a linked
worktree):

1. Reads `git_hooks` as both files resolve it (D10), the hooks folder with
   `rev-parse --git-path hooks` and `core.hooksPath` with `config --get`. A git failure
   refuses the command with git's message and its hints.
2. On: each hook `missing` or `earlier` is planned `written` or `updated`, unless
   `core.hooksPath` is set; `current` and `chained` are `kept`; `other`, and with
   `core.hooksPath` set also `missing` and `earlier`, are problems:
   `<location> is a hook gemba did not write: run gemba hook <name> "$@" from it, or turn
   the hooks off for this clone with git_hooks: false in gemba.local.yaml`, or
   `core.hooksPath is set to <folder>, where gemba writes no hook: ...` with the same
   two ways out. The problems join the other refusals of `init`, nothing written.
3. Off: each hook `current` or `earlier` is planned `removed`, unless
   `core.hooksPath` is set; every other hook is left out of the report.

After the skills, `init` writes each planned script with `newline="\n"`, sets its mode
to `0o755`, deletes each removed one, and prints `<outcome> <location>`. The location is
the path git gave, relative to the root and POSIX when it lies under the root, such as
`.git/hooks/pre-push`, and absolute in the form of the system otherwise.

### D10. `git_hooks` in `config.py`

`LAYERS` gains `git_hooks: (gemba.yaml, gemba.local.yaml)`. Each file's value must be a
boolean (`git_hooks must be true or false (got ...)`); declared in either file while the
shared config declares no team, it is refused under the path of that file as `git_hooks
needs a team: gemba.yaml declares none`. `Config` gains `git_hooks: bool`, the personal
value when declared, else the shared one, else `false`. `config check` prints
`git hooks: on` or `off` after the `me:` line, or after `team:` without `me`; `config
show` holds `git_hooks` after `me`; both only with a team.

### D11. `gemba hook`, a group git runs

`commands/hook.py` registers the group `hook` with `pre-push <remote> <url>`,
`post-merge <squash>` and `post-rewrite <command>`, the arguments git passes; it takes
no `--root`, since git runs it at the top of the repository, and finds the root by
walking up. No config found, or one without a team: nothing printed, exit 0. A config
that cannot be read: its problems on the standard error, exit 1 for `pre-push` and 0 for
the other two. The group has no skill (`process-naming`), and `gemba hook` without a
verb prints its help and exits 1, as `gemba config` does.

### D12. The skills

- `gemba-sync`, new, scope `obeya`, registered after `gemba-set` in `SKILLS`, so that the
  obeya skills still end with `gemba-init`, `gemba-config` and `gemba-migrate` and
  `init/scaffolded-at-a-path.yaml` keeps its expectation. Its process follows the
  requirements of the agent in `obeya-sync`: `gemba config show`, `git fetch origin`,
  `gemba sync`, the incoming report explained as data, a commit of the member's own task
  files by name on a yes, `git pull --rebase` and `git rebase --abort` on a conflict,
  `gemba sync` again, the confirmation of shared files, `git push`, and the report. It
  never passes `--force` or `--no-verify` on its own, and never edits a task file to get
  past a check.
- `gemba-init`: the question on the hooks after who the user is, `git_hooks` in the
  write step, `gemba init` once more when the hooks are on; in the clone of a member, the
  sentence of the report on the team's hooks.
- `gemba-config`: a `git_hooks` row in the reference of the top level, and a step that
  runs `gemba init` after `git_hooks` changes in either file.

### D13. Documents

- `SECURITY.md`: the threat model says that in an obeya with a team gemba runs git
  commands that only read the obeya, for `gemba sync`, `gemba hook` and `gemba init`, and
  writes three hook scripts into its hooks folder when `git_hooks` is on, each running
  `gemba hook` and nothing else; it still never pulls, pushes or clones, and its one
  network operation stays the fetch of `gemba worktree add`. In scope: a hook script that
  runs anything else, or `init` writing over a hook it did not write. The team paragraph
  says that the shared config and the skills carry other members' instructions to the
  agent, that `gemba sync` and the hooks show the shared files that came in, and that
  the hooks are skipped by `--no-verify` and are no access control.
- `README.md`: a subsection of the team section, "Sync with the team": the hooks, what
  they refuse and show, `git_hooks`, `gemba sync`, the `gemba-sync` skill, and a GUI
  client whose PATH lacks `gemba`.
- `AGENTS.md`: `gemba hook` beside `gemba skills` among the groups with no skill.
- `CHANGELOG.md`: the additions under Added, and the skills under the line that asks to
  run `gemba skills update`.

## Windows

Read `.claude/skills/guidelines/cross-platform` first. Each point of the change:

- **Processes.** Every git command is an argument list, as today. The hook scripts are
  run by git, through the `sh` of Git for Windows, which finds `gemba.exe` on PATH with
  `command -v`; gemba starts no script itself (Rule 6).
- **Files written.** The scripts are written with `encoding="utf-8"` and `newline="\n"`
  (Rule 5); `chmod(0o755)` makes them executable on Linux and macOS and only clears the
  read-only flag on Windows, where Git for Windows runs a hook without an executable
  bit. No `os.name` check is needed, so `platform.py` gains no rule.
- **Paths printed.** Paths from git come with `-z` and `core.quotePath=false`, POSIX and
  UTF-8, and are classified and printed as they are (Rule 2). The location of a hook is
  printed relative to the root with `as_posix()`, or as an absolute path with `str()`
  (Rule 1); git gives forward slashes on Windows, so the adapter makes a `Path` of it
  before either.
- **Text read.** The task files read from git objects, the standard input of a hook and
  the patches go through `platform.decode()`, the patches with invalid bytes replaced,
  since a patch is shown, never parsed (Rule 5).
- **Names.** The change names no new file or folder from a person's input; the hook
  names are fixed.
- **Tests.** Cases spell no absolute path; a commit id comes from the token of D14. The
  hook cases run `git push` and `git pull` on the Windows jobs too, which is where the
  `sh` of Git for Windows is proven.

## Tests

D14. The runner of `tests/test_cases.py` gains three things, documented in its
docstring:

- `stdin`: text given to the command's standard input, tokens expanded; without it the
  command gets an empty input, as today.
- `git` as a name of `run` and `setup`, run as `git <args>` in `cwd`, which it requires,
  with no `--root`; the case environment is the one every command gets.
- `{rev:<path>:<revision>}`: the full id of `<revision>` in the repository at `<path>`,
  relative to the root, resolved after `git_after_setup`, in `run`, `stdin`, `stdout`,
  `stdout_contains` and `stderr_contains`, so that a case gives and expects the id of a
  commit made while it runs.

An obeya with a remote is a `repos` entry, `obeya`, whose `main` holds `gemba.yaml` and
the tasks, with `cwd: repos/obeya`, its `gemba.local.yaml` written by `tree`, outgoing
commits made by `tree_after_setup` and `git_after_setup`, and incoming ones by
`unfetched` and a `git fetch` in `git_after_setup`. The hooks of a hook case are
installed by `setup: [[init]]`, so every hook case also runs the scripts `init` writes.
`git_log` on `remotes/obeya.git` proves what reached the remote.

Unit tests: `tests/test_sync.py` for `classify`, `outgoing`, `incoming` and `confirmed`,
with plain data; `tests/test_obeya.py` for `hook_script` and `hook_state`;
`tests/test_config.py` for `git_hooks`.

## Risks / Trade-offs

- [A GUI client whose PATH lacks `gemba` cannot push once the hooks are on] → The
  script names `uv tool install gemba-cli` and `--no-verify`; the README names the case,
  and `git_hooks: false` turns the hooks off for that clone.
- [A person bypasses the checks with `--no-verify`, or never runs `gemba init`] → The
  hooks prevent accidents; anything pushed stays in the history, and the host's
  CODEOWNERS and branch protection are the control. `gemba sync` says when the hooks of
  an opted-in clone are missing.
- [A pull writes a forced `gemba.local.yaml` over the clone's own, since git writes over
  an ignored file] → `gemba sync` warns before the pull, the hooks name it after, and the
  pre-push hook of the clone that forced it refuses it.
- [A new branch that merges two branches of the remote, neither holding the other, has
  two bases, and a path counts in its net change only when it differs from both] → A
  change that one of those branches already holds is not reported, since the remote
  already has it.
- [A change to another member's file or to a shared file, made and undone among the
  outgoing commits, goes out unreported] → The remote's tree ends as it was, and the
  members' tasks are no secret within the team; only a private path is refused for
  entering the history (D3).
- [The net change of a push that is not a fast-forward is taken from the merge base, not
  from the remote's current commit] → Git refuses such a push unless it is forced, and
  neither the skill nor gemba ever forces one.
- [A push takes longer with the hooks] → One start of `gemba` and a handful of git reads
  per pushed ref.
- [A team with `core.hooksPath` cannot get the hooks installed] → `init` names the
  folder and the line that chains `gemba hook`; a chained hook counts as installed.

## Migration Plan

Nothing breaks and nothing is on by default. A team that wants the hooks adds
`git_hooks: true` to `gemba.yaml` through the `gemba-config` skill and pushes it; each
member pulls and runs `gemba init`, which `gemba sync` and the `gemba-sync` skill
suggest. A clone turns them off with `git_hooks: false` in `gemba.local.yaml` and
`gemba init`. Every obeya gets the `gemba-sync` skill and the edited `gemba-init` and
`gemba-config` with `gemba skills update` or `gemba init`. Rolling back the package
leaves scripts that call a `gemba hook` it does not know: `pre-push` then fails, and
`git_hooks: false` with `gemba init` of this version, or deleting the three scripts,
undoes them.
