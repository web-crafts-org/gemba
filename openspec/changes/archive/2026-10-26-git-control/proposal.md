# Proposal

## Why

In an obeya shared by a team, git carries every member's work, and today nothing stands
between a member and a `git push` that carries another member's task, a personal config
forced into a commit, a task file that no command can read, or an edit to the team's
config or skills; and a pull can change a member's own tasks without them noticing. The
write guard of `team-mode` stops a command from writing another member's task, but not a
hand edit that reaches a commit. With the team, `me` and the parent of a task in place,
the obeya can now be pulled and pushed safely.

## What Changes

- **The ownership map of a change.** In an obeya with a team, every path a commit
  changes is the member's own under `tasks/<me>/`, another member's under
  `tasks/<member>/`, private for `gemba.local.yaml` and `harnesses/`, or shared for
  anything else, such as `gemba.yaml`, the skills and `.gitignore`.
- **What a push may carry.** An outgoing commit that changes another member's folder or
  a private path is refused; one that changes a shared file needs a confirmation bound
  to the commit pushed; the member's own task files must read as tasks, carry the
  member's initials and hold no ref twice, the case of a task created from two clones
  without a pull in between. The check is on what the push changes in the end, merges
  included, so that what a merge does by itself, a resolution or an old copy kept over
  another member's change, is seen too, one problem per path naming the commits behind
  it; a private path is refused as soon as an outgoing commit carries it, even when a
  later one removes it, since the history keeps it. Every problem is reported at once.
- **What a pull brings.** What a pull changes in the member's own tasks is shown with
  its diff and the commits behind it, merges included; the shared files it changes are
  listed, and a commit that carries a personal config, which a pull would write over the
  member's own, is warned about. Nothing incoming blocks.
- **`gemba sync`.** A read-only command, a bare verb on the obeya: it reports what a
  pull would bring and what a push would send against the upstream of the branch as
  last fetched, and the uncommitted changes by the same map, ending with the verdict of
  a push. It runs no fetch, no pull and no push, and writes nothing.
- **`gemba hook pre-push`, `post-merge` and `post-rewrite`.** The same checks, run by git
  inside the `git push` and `git pull` that a person or an agent starts. They only
  report, as a lint does: `pre-push` refuses a push with a problem, and the other two
  print what came in. A push touching shared files passes once confirmed with
  `git -c gemba.shared=<commit> push`; `git push --no-verify` stays the deliberate
  bypass.
- **An explicit opt-in for the hooks.** `git_hooks`, a boolean of both config files: the
  team turns the hooks on in `gemba.yaml`, and each person may turn them on or off for
  their clone in `gemba.local.yaml`, which always wins. It is refused in an obeya
  without a team. `gemba config check` and `show` print it.
- **`gemba init` installs the hooks.** In a git repository whose config declares a team
  and turns the hooks on, `init` writes three small scripts that run `gemba hook`, with
  no question; it never writes over a hook it did not write, keeps one that already
  calls `gemba hook`, and removes its own when the hooks are turned off. A pre-push
  script fails closed when `gemba` is not on PATH. `init` still creates no repository
  and no commit; it only reads with git where the hooks go.
- **The `gemba-sync` skill.** The safe way to pull and push an obeya with a team: the
  agent fetches, reads `gemba sync`, explains what comes in, commits only the member's
  own task files with their consent, pulls with rebase, aborts on a conflict and
  resolves none, checks again, asks before pushing shared files, and pushes, never
  forcing and never skipping the hooks on its own. The agent runs git; the CLI never
  pulls and never pushes.
- **Skills.** `gemba-init` asks a new team whether it turns the hooks on and runs `gemba
  init` once more to install them; `gemba-config` documents `git_hooks` and runs
  `gemba init` after changing it.
- **Naming.** `gemba sync` is a bare verb on the obeya, as `init` is, driven by the
  `gemba-sync` skill; `gemba hook` is a group with no skill, since git runs it.
- **Docs.** `SECURITY.md` says what the hooks run and that the CLI still never pulls or
  pushes, and that shared files changed by others are shown; the README gains a section
  on syncing a team's obeya; `AGENTS.md` names `gemba hook` beside `gemba skills`;
  `CHANGELOG.md` records the additions.

Not in this change: a commit or a push made by a command, which the plan once held and
Manuel dropped, since a team has no race for refs; a confirmation of the team's
instruction blocks after a pull (trust-on-change), beyond showing the shared files that
changed; anything in an obeya without a team.

## Capabilities

### New Capabilities

- `obeya-sync`: the ownership map of a change in an obeya with a team, the checks of an
  outgoing and an incoming change, `gemba sync`, the `gemba hook` verbs, and the
  `gemba-sync` skill.

### Modified Capabilities

- `gemba-config`: the `git_hooks` key of both files and its layer.
- `config-maintenance`: `check` and `show` print the hooks of a clone in an obeya with a
  team.
- `repo-initialization`: `init` installs, keeps and removes the hooks, reads with git
  only where they go, writes the `gemba-sync` skill, and the guided configuration asks a
  team about the hooks.
- `built-in-skills`: the registry holds `gemba-sync`, written into the obeya.
- `process-naming`: `gemba sync` is bare, and a group git runs has no skill.

## Impact

- New domain module `src/gemba/sync.py`: the ownership map, the outgoing and incoming
  checks, the confirmation, and the lines they print. `src/gemba/obeya.py`: the hook
  scripts, their names and their states. `src/gemba/config.py`: `git_hooks`.
- New adapters `src/gemba/commands/sync.py` and `src/gemba/commands/hook.py`, running
  git commands that only read the obeya; `src/gemba/commands/init.py` installs the
  hooks; `src/gemba/commands/config.py` prints the key; `src/gemba/cli.py` registers
  both commands.
- Skills: the new `gemba-sync`; `gemba-init` and `gemba-config`; `src/gemba/skills.py`
  registers `gemba-sync`.
- Tests: new cases under `sync/`, `hook/`, `init/` and `config/`; eleven case documents
  that list every obeya skill gain `gemba-sync`, and two cases of a team's config gain
  the hooks line; the runner of `tests/test_cases.py` gains a standard input, `git` as a
  command and a token for a commit; new entries in `tests/not-automated.yaml`; unit
  tests of `sync.py`, `obeya.py` and `config.py`.
- Docs: `README.md`, `SECURITY.md`, `AGENTS.md`, `CHANGELOG.md`. No new dependency.
