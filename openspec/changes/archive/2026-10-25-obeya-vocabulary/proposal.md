# Proposal

## Why

Gemba is an internal tool for developers to organize their own work, alone or with a
team, beside the way their company organizes its tasks and not in its place. Two words
say otherwise. The glossary defines the tasks repo as "the personal traceability layer
of someone who works for an organization", and `organization`, a key of the shared
config, names "the organization the tasks repo works for". But each person draws the
boundary of a tasks repo as they choose: the organization they work for, a project, a
team inside a company, or a whole startup. So the word can name neither a company nor
a team, and a tasks repo is not only personal.

Team mode, the next change, adds `team`, `member` and `owner` on top of the word that
names the place. That word should be settled first. Version 0.3.0 is not released yet
and already breaks `gemba.yaml` (`ide`, `repos_dir` and `branch_prefix` moved), so a
rename made now costs users one upgrade, not two.

## What Changes

- **obeya** replaces both *tasks repo* and *organization*. In lean, the obeya (大部屋,
  "big room") is the room where a program, a team or a project keeps all of its work in
  sight. In Gemba it is the repository that holds `gemba.yaml`, `tasks/` and
  `harnesses/`, drawn as its owner chooses and kept alone or shared with a team. It
  pairs with the gemba, the actual place where the work is done, which in Gemba is the
  harness. The word replaces the old ones in the README, `AGENTS.md`,
  `CONTRIBUTING.md`, `SECURITY.md`, the `[Unreleased]` section of `CHANGELOG.md`, the
  skills, the specs, the help and messages of the CLI, and the comments of the code.
- **BREAKING:** the `organization` key of `gemba.yaml` becomes `obeya`, the name of the
  obeya. Like the old key it is kebab-case, optional, shared-config only, and the middle
  segment of the branch of a run, `<branch_prefix>/<obeya>/<ref>`. Every command refuses
  a `gemba.yaml` or a `gemba.local.yaml` that declares `organization`, says it is now
  `obeya` in `gemba.yaml`, and reports it together with every other problem. With the
  same value the branches keep their names, so no run loses its branches. The
  `gemba-config` skill renames the key, as it already moves the keys of an earlier
  config.
- **BREAKING:** `gemba config show` prints `obeya` instead of `organization`, and
  `harness.guide.obeya` instead of `harness.guide.organization`. The skills that read it
  ship in the same version.
- A harness launched from now on titles the top-level guide text of the shared config
  `## Your obeya` instead of `## Your organization`. Guides already written are not
  touched.
- The CLI says obeya in its help and messages: the `--root` help of every subcommand,
  the help of `gemba init`, its next step, the refusal of an obeya nested in another,
  the refusal of a draft outside the obeya root, and the refusal of another harness's
  ref.
- "Organization-specific value" becomes "configured value": in the 11 skills that say
  it, in the principle "Three piles" of `AGENTS.md`, and in nine requirement titles,
  which are renamed.
- The README and the glossary describe the audience and the obeya. The `gemba-init`
  skill opens its interview by explaining what an obeya is, then asks for its name.
- In the code, `repo.py` becomes `obeya.py`, and the scope, target and place literal
  `"repo"` becomes `"obeya"`. After that, *repo* alone always means a code repository,
  one of the folders under `repos_dir`. Capability ids such as `repo-initialization`
  and the names of archived changes stay as they are.

Not in this change: `team`, `member` and `owner`, which come with `team-mode`; the
obeyas already in use and the guides of their harnesses, which their owners upgrade.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `gemba-config`: the shared config declares `obeya` in place of `organization`, and a
  file that declares `organization` is refused. Two requirements are renamed, and the
  rest of the prose says obeya.
- `config-maintenance`: `gemba config show` prints `obeya` and `harness.guide.obeya`;
  the `gemba-config` skill renames the key of an earlier config; its reference holds no
  configured value.
- `harness-guide`: the base guide text is rendered under `## Your obeya`; the guide
  asset holds no configured value (requirement renamed).
- `harness-worktrees`: the branch of a run is `<branch_prefix>/<obeya>/<ref>`, and
  `gemba worktree add` refuses a config without `obeya`; 23 cases declare the key.
- `harness-removal`: the branches of a run are found by the name of the obeya; the
  cases that declare the key follow.
- `repo-initialization`: the next step and the refusal of a nested obeya say obeya, the
  scaffolded `gemba.yaml` says it in its comment, and the `gemba-init` interview opens
  with the obeya. Two requirements and six scenarios are renamed.
- `built-in-skills`, `harness-launch`, `metadata-setting`, `platform-support`,
  `process-naming`, `task-archiving`, `task-creation`, `task-file-format`,
  `task-listing`, `task-marking`, `task-migration`, `task-recording` and
  `task-reporting`: no rule changes. Their requirements and scenario titles say obeya,
  and "Skill contains no organization-specific value" is renamed in six of them. Their
  scenarios name the cases whose names, messages or expected skill texts say obeya.

## Impact

- Code: `config.py` (the key, its layer, the refusal of `organization`, the guide
  field), `harness.py` (the heading), `worktree.py` and `commands/worktree.py` (the
  branch and its refusal), `commands/harness.py` (the branches of a removal),
  `commands/config.py` (the document of `show`), `repo.py` renamed `obeya.py` with
  `commands/init.py`, the literals of `skills.py`, `commands/skills.py`, `tasks.py` and
  `commands/record.py`, and the help of every subcommand. No new module, seam or
  dependency.
- Assets: the 12 skills that say tasks repo or organization, and the comment of the
  `gemba.yaml` template.
- Tests: 64 case files change, 14 of them renamed, and one is added. 10 entries of
  `tests/not-automated.yaml` change and two are added. The unit tests
  `test_config.py`, `test_harness.py`, `test_skills.py` and `test_repo.py` follow, the
  last renamed `test_obeya.py`.
- Specs: 72 requirements of 19 capabilities are MODIFIED, 15 of them renamed. The
  Purpose of 7 main specs is edited at apply, since a delta cannot carry it.
- Users: whoever upgrades from 0.2 renames `organization` to `obeya` in `gemba.yaml`,
  by hand or through the `gemba-config` skill, in the same step that moves `ide`,
  `repos_dir` and `branch_prefix`. Their branches keep their names.
