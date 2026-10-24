# Proposal

## Why

A tasks repo is about to be shared by a team, and `gemba.yaml` mixes two kinds of
values: what the people who share the repo agree on (workstreams, fields, the
organization) and what belongs to one person on one machine (the command that opens
their editor, where their repositories live, how their local branches are named).
Committed together, a teammate's `ide` would run on your machine and your
`repos_dir` would break theirs. Splitting the config into a shared layer and a
private one is the base of team mode and of git control, and it is the one breaking
change of the set, so it goes first, while gemba is 0.x.

## What Changes

- The gemba config becomes two files at the tasks repo root: `gemba.yaml`, the
  **shared config**, committed, and `gemba.local.yaml`, the **personal config**,
  optional, private to the clone and ignored by git. Commands still find the root by
  the nearest `gemba.yaml` and read the personal config beside it.
- Each key has a layer. Only in the shared config: `workstreams` (with `prefix`,
  `description`, `metadata`), the top-level `metadata`, `default_workstream` and
  `organization`. Only in the personal config: `ide`, `repos_dir` and
  `branch_prefix`. In both: `agent_providers` and the process blocks (`context`,
  `rules`, `harness.guide`), at the top level and per workstream; the personal config
  may only name workstreams of the shared catalogue.
- **BREAKING**: a `gemba.yaml` that declares `ide`, `repos_dir` or `branch_prefix` is
  refused by every command, naming each key and saying it goes in `gemba.local.yaml`.
  No command rewrites the config: the `gemba-config` skill moves the keys, and the
  changelog announces it. A relative `repos_dir` keeps resolving against the tasks
  repo root.
- The personal blocks come after the shared ones: the effective block of a process is
  the shared base, the shared workstream, the personal base and the personal
  workstream, in that order, so the personal rule wins a contradiction under the
  existing "the later rule wins" convention. The harness guide gains a third and final
  section, `Your user`, for the personal `harness.guide` texts.
- `agent_providers` of the shared config keeps deciding the skills of the tasks repo
  (`gemba init`, `gemba skills update`), which are committed; `agent_providers` of the
  personal config, when declared, replaces it for the harnesses launched from that
  clone, and for nothing else.
- Every config refusal reports every problem of both files at once, each with the path
  of its file, instead of the first one: a check that depends on another value runs
  only when that value is valid, so one mistake is reported once.
- `gemba config check` reports on both files and summarizes the personal providers;
  `gemba config show` prints the merged result, with `ide`, `repos_dir` and
  `branch_prefix` from the personal config, a new `harness_providers` key and the
  personal guide under `user`.
- `gemba init` adds `gemba.local.yaml` to the `.gitignore` it writes and completes an
  existing one; it never writes the personal config itself.
- The `gemba-init` skill writes the IDE and the repositories folder into the personal
  config; the `gemba-config` skill holds the reference of both files and moves the keys
  of an older `gemba.yaml`. The skills that read the config through
  `gemba config show` do not change.

Not in this change: policies (team rules a person cannot override), considered and
rejected; the `team` block and `me`, which belong to team mode.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `gemba-config`: two files and the layer of each key; personal process blocks and the
  four-level effective block; `agent_providers` in both layers; `ide`, `repos_dir`
  and `branch_prefix` in the personal config only; every problem of both files
  reported at once.
- `config-maintenance`: `check` validates both files and summarizes the personal
  providers; `show` prints the merged config with `harness_providers` and the personal
  guide; the `gemba-config` skill edits the file a key belongs to and moves misplaced
  keys.
- `repo-initialization`: the `.gitignore` of the scaffold holds `gemba.local.yaml`;
  init validates both files; the guided configuration writes the personal keys into
  the personal config.
- `harness-launch`: the IDE comes from the personal config; the harness is written for
  the personal providers when declared.
- `harness-guide`: the personal guide texts are rendered as a final `Your user`
  section.
- `harness-removal`: the repositories it checks for orphan branches are under the
  `repos_dir` of the personal config.
- `harness-worktrees`: `repos_dir` and `branch_prefix` come from the personal config,
  `organization` from the shared one; the refusal names the file of the missing key.
- `built-in-skills`: the skills of the tasks repo are written for the providers of the
  shared config, never for those of the personal config.

## Impact

- `src/gemba/config.py`: a second file, the layer rules, the personal blocks, the
  four-level effective block, the providers of a launch, and a validator that
  accumulates every problem instead of raising on the first.
- `src/gemba/commands/config.py` (`check`, `show`), `commands/harness.py` (launch
  providers, the guide), `harness.py` (`render_guide` with a third section),
  `commands/worktree.py` (the message of a missing `repos_dir`), `commands/init.py`
  and `repo.py` (a list of ignored lines).
- `tests/test_cases.py`: a `local_config` key for `gemba.local.yaml` and a
  `stderr_excludes` check. 37 case files move `ide`, `repos_dir` or `branch_prefix`
  into it, 7 more change what they expect (the documents of `show`, the `.gitignore`
  of `init`), 21 cases are new and `tests/not-automated.yaml` gains 2 entries; the
  unit tests of `tests/test_config.py` and `tests/test_metadata.py` follow the new
  messages.
- Skills `gemba-init` and `gemba-config`; `README.md`, `SECURITY.md` (the `ide` and
  `repos_dir` of the personal config), `AGENTS.md` (vocabulary: the shared and the
  personal config) and `CHANGELOG.md` (the breaking entry).
- Every existing tasks repo that declares `ide`, `repos_dir` or `branch_prefix` must
  move them on upgrade. No new dependency.
