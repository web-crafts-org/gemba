# Design

## Context

See proposal.md for the motivation. What shapes the approach:

- `config.py` is the only entry point that validates the config. `load()` reads one
  file and `_parse()` raises `ConfigError` on the first problem; the field rules it
  delegates to `metadata.parse_fields()` and `metadata.types()` raise
  `MetadataError` on the first problem too. `Config` already carries `ide`,
  `repos_dir`, `branch_prefix` and `agent_providers` as fields, and the adapters
  (`commands/harness.py`, `commands/worktree.py`, `commands/skills.py`,
  `commands/init.py`) read them from there, never from the file.
- `effective_block()` joins two levels, the base and the workstream; `effective_guide()`
  returns two texts, which `harness.render_guide()` renders under `## Your
  organization` and `## Your workstream`.
- `repo.py` holds one ignored line and `gitignore_text()`; `GITATTRIBUTES_LINES` with
  `gitattributes_text()` is the list form already in place.
- The case runner writes `config:` as `gemba.yaml` and asserts standard error through
  `stderr_contains` fragments only; it has no way to write a second config file or to
  assert that a message is absent.
- `openspec/config.yaml` lets the apply phase touch a case only when the delta spec
  adds, modifies or removes the scenario it names. 37 case files declare `ide`,
  `repos_dir` or `branch_prefix` in their `config:`, and 3 more print the document of
  `gemba config show`, which gains keys.

## Goals / Non-Goals

**Goals:**
- One table that says which file each key belongs in, read by the validator for both
  files, so that the refusal of a misplaced key and the reference of the skill come
  from the same rule.
- A config refusal that a person or an agent fixes in one round: every problem of
  both files, each with its file, and no problem that is only the echo of another.
- No adapter learns about the second file: they keep reading `Config`.

**Non-Goals:**
- Policies, rules of the shared config that the personal config cannot override.
- Rewriting a config: no command moves the keys of an earlier `gemba.yaml`; the
  `gemba-config` skill does.
- The `team` block, `me` and anything else of team mode; any git operation.
- Changing the skills that read the config through `gemba config show`.

## Decisions

### D1. `config.py` reads both files; no new seam

`load()` finds the root by `gemba.yaml` as today, then reads `gemba.local.yaml` at that
root when it exists (`LOCAL_FILENAME`). Reading a file is the side effect a domain
module already has, so the change adds no seam: no filesystem write, clock or output.
An empty personal file loads as `None` and is read as an empty map; any other
non-map document is a problem of that file. The personal file is never discovered on
its own, so a folder that holds it without `gemba.yaml` is not a tasks repo.

### D2. One layer table, in `config.py`

`config.py` declares the keys of each layer: shared only (`metadata`,
`default_workstream`, `organization`, and `prefix`, `description`, `metadata` inside a
workstream), personal only (`ide`, `repos_dir`, `branch_prefix`), and both
(`agent_providers`, the process blocks, and `workstreams`, whose entries in the
personal config hold process blocks only). The validator checks each file against the
table and names the file a misplaced key goes in; the `gemba-config` skill states the
same table as its reference. Unknown keys stay ignored in both files, as `gemba.yaml`
ignores them today. Alternative: refuse unknown keys in the small personal file to
catch typos. Rejected: it departs from `gemba.yaml`, and an older CLI would refuse
the personal keys team mode and git control add later (`me`, `git`). A typo in
`repos_dir` still surfaces, as `gemba worktree add` names the missing key and its
file.

### D3. The validator accumulates problems

`_parse()` becomes a pass over both files that appends a problem, the path of its
file and a message, instead of raising, and returns the `Config` only when no problem
was found. Each `_parse_*` helper returns the parsed value, or `None` with its
problems appended. A check that needs another value runs only when that value parsed:
the default against a catalogue that is a map, the personal workstreams against the
shared catalogue, the one-type rule over the declarations that parsed. A file that is
not valid YAML contributes its parse error and the other file is still checked on its
own, without the checks that need the first. `ConfigError` carries the problems and
renders them as `invalid gemba config:` followed by one `- <path>: <message>` line
each; `no gemba config found` stays a one-line error. Every adapter keeps printing
`str(exc)`, so none changes for this.

`metadata.py` gets the same treatment for the rules it owns: `parse_fields()` checks
every declaration and returns the fields that parsed with the problems of the others,
and a `type_problems()` beside `types()` returns every disagreement instead of
raising on the first. `types()` keeps raising for its runtime callers, which only
ever see a valid config. Alternative: raise per section and report one problem per
section. Rejected: Manuel chose every problem; a section-level cut still needs a
second round for two bad fields of one list.

### D4. Four levels for the effective block, three texts for the guide

`Config` gains the personal base blocks and the personal blocks of each workstream.
`effective_block()` reads the levels in the order the spec gives, shared base, shared
workstream, personal base, personal workstream, and the context join generalizes from
two texts to any number, one empty line apart. `Guide` gains `user`, the personal base
text and the personal workstream's joined the same way, and `effective_processes()`
prints it under `harness.guide.user`. The personal layer only appends: it never
removes or replaces a shared rule, and wins a contradiction by coming last, under the
convention the skills already follow. Alternative: let a personal block replace the
shared block of the same process. Rejected by the task: a person adds to the team's
agreement, never deletes it silently.

### D5. Two provider lists, one rule for the launch

`Config.agent_providers` keeps meaning the list of the shared config, so `gemba init`
and `gemba skills update` (the skills of the tasks repo, which are committed) do not
change. `Config` gains the personal list and a `harness_providers` property, the
personal list when declared, else the shared one. The launch adapter
(`commands/harness.py`) reads `harness_providers` for the refusal of a missing list,
the guides, the harness skills and `harness.yaml`. Alternative: one merged
`agent_providers`. Rejected: `gemba skills update` in the tasks repo would write, and
a teammate would then commit, the skills of one person's agent.

### D6. `check` and `show` stay additive (adapter: `commands/config.py`)

`show` adds `harness_providers` after `agent_providers` and `user` to every
`harness.guide`; every other key keeps its meaning, so the skills that read the
document by key are unaffected. `check` prints `gemba.local.yaml is valid` and
`harness providers:` only when the personal config exists and declares providers, so
the summary of a tasks repo without one is byte for byte what it was.

### D7. The personal guide section is `Your user` (domain: `harness.py`)

`render_guide()` takes the third text and `USER_HEADING = "## Your user"`, rendered
last. The guide speaks to the agent ("Where you are", "Your organization", "Your
workstream"), so the person whose private text it is reads as "your user".
Alternatives: `Your preferences`, which reads as the agent's own; `Personal`, which
breaks the pattern of the other two titles.

### D8. A list of ignored lines (domain: `repo.py`)

`IGNORED_LINE` becomes `IGNORED_LINES = ("harnesses/", "gemba.local.yaml")` and
`gitignore_text()` mirrors `gitattributes_text()`: the missing lines appended in
order, `None` when both are present. The line is unanchored like `harnesses/`; the
file only exists at the root. `init.py` keeps calling `converge()` and only its help
text changes. The message of a missing `repos_dir` in `commands/worktree.py` names
`gemba.local.yaml`.

### D9. The case runner gains two keys

`tests/test_cases.py` writes `local_config:`, a map or raw text like `config:`, as
`gemba.local.yaml`, and checks `stderr_excludes:`, strings standard error must not
contain, which the "One mistake reported once" scenario needs. The 37 cases move their
personal keys from `config:` to `local_config:` with their assertions unchanged,
except the messages that now name a file and the documents of `show`, which gain
`harness_providers` and `guide.user`. Since a case may change only through its
scenario, the delta specs carry every requirement whose scenarios name a moved case
as MODIFIED, including three of `harness-worktrees` whose text does not change; their
`**Cases**` lines say what moves.

### D10. Skills and documents

The `gemba-config` skill gains the file of every key in its reference, a section on
`gemba.local.yaml`, the question of where a key both files hold goes, "fix every
problem" in place of "one problem at a time", and the move of the keys of an earlier
config. The `gemba-init` skill writes the IDE and the repositories folder into the
personal config and says it stays on the machine. `AGENTS.md` defines the shared and
the personal config; `README.md` shows both files; `SECURITY.md` says `ide` and
`repos_dir` come only from the personal config, which is never committed;
`CHANGELOG.md` carries the breaking entry and the upgrade, which the README leaves to
it. The Purpose of the `gemba-config` main
spec, "the single customization layer", is edited by hand, since archiving syncs
requirements only.

## Risks / Trade-offs

- [Every tasks repo that declares `ide`, `repos_dir` or `branch_prefix` stops working
  on upgrade] → one refusal names every key and the file it goes in, the
  `gemba-config` skill moves them, and the changelog announces it under a 0.x minor
  version.
- [A tasks repo made before this change does not ignore `gemba.local.yaml`, so it
  can be committed by accident] → running `gemba init` again appends the line, as it
  did for `.gitattributes`; the changelog says to run it after the upgrade.
- [Accumulating every problem can bury the real one under its echoes] → dependent
  checks run only on valid inputs, pinned by the "One mistake reported once"
  scenario and its case.
- [The personal layer is invisible to the team and can contradict its rules] →
  intended: no policies. The guide renders it under its own title, last, so the agent
  and the person see where a rule comes from.
- [An unknown personal key, a typo, is silently ignored] → accepted for forward
  compatibility (D2); the command that needs the key names it and its file.
- [Three MODIFIED requirements repeat their text unchanged] → stated in their
  `**Cases**` lines and in D9; archiving rewrites them identically.

## Migration Plan

1. Release as the next minor version, with the changelog entry under Changed.
2. After upgrading, any command refuses a `gemba.yaml` that declares a personal key,
   naming each one. The person asks the agent to fix the config (the `gemba-config`
   skill) or moves the keys into `gemba.local.yaml` by hand, then runs `gemba init`
   once to add the ignore line, and commits `gemba.yaml` and `.gitignore`.
3. Harnesses already launched keep their guide and `harness.yaml`: nothing to
   migrate there.
4. Rollback: install the previous version and move the keys back into `gemba.yaml`;
   it ignores `gemba.local.yaml` as an unknown file.
