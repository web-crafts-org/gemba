# Design

## Context

See proposal.md for the motivation. What shapes the approach:

- The old words live in five places. The first is the `organization` key, declared in
  `LAYERS` of `config.py`, parsed by `_parse_name`, carried as `Config.organization`,
  printed by `config show`, passed to `worktree.branch_name(prefix, organization, ref)`
  by `commands/worktree.py` and by `orphan_branches` of `commands/harness.py`, and
  refused when absent by `gemba worktree add`. The second is the heading
  `ORGANIZATION_HEADING` of `harness.py`, fed by `Guide.organization`. The third is
  the phrase "organization-specific value", in 11 skills, a principle of `AGENTS.md` and
  9 requirement titles. The fourth is "tasks repo", in 51 of the 148 requirements, 7
  Purposes, 12 skills, about 30 help texts and messages, 20 cases, and the README, the
  glossary, `SECURITY.md`, `CONTRIBUTING.md` and `CHANGELOG.md`. The fifth is the
  literal `"repo"`, which names the obeya as a skill scope, a skill target and a record
  place in `skills.py`, `tasks.py` and three adapters, and the module `repo.py`.
- Elsewhere, *repo* already means a code repository: `repos_dir`, the `repo` argument
  of `gemba worktree add`, `worktree.repo_problem`.
- OpenSpec 1.14.1 cannot rename a scenario: a MODIFIED block whose scenario titles
  differ from the main spec's is refused by `validate` and by `archive`. A delta cannot
  carry a Purpose either. Both are edited directly in the main specs at apply, as
  Manuel chose on 2026-10-25.
- 0.3.0 is unreleased, and its `[Unreleased]` section already announces a break of
  `gemba.yaml`.

## Goals / Non-Goals

**Goals:**

- One word, obeya, in everything a person or an agent reads: docs, skills, specs, help,
  messages, comments and names in the code.
- Same branch names after the rename, so that no run loses its branches.
- One upgrade for whoever comes from 0.2, done by the same skill that already moves the
  keys of an earlier config.
- Spec deltas that can be checked mechanically, so that a reviewer reads the rules
  and the few hand edits, not 72 requirements.

**Non-Goals:**

- `team`, `member` and `owner`, which belong to `team-mode`.
- The obeyas already in use and the guides already written in their harnesses: a guide
  is written once at launch, and its `## Your organization` heading stays.
- History: the archived changes, their folder names such as `record-from-tasks-repo`,
  and the released sections of `CHANGELOG.md`.
- Capability ids: `repo-initialization` keeps its name. Renaming a capability means
  removing every requirement and adding it to a new spec, and changing the prefix of
  the `scenario:` field of all its cases.
- Refusing an obeya name that Windows reserves (`con`, `nul`, ...). It becomes a folder
  under `.git/refs/heads/<branch_prefix>/` when a loose branch is written. `organization`
  was never checked either, so this change neither causes nor fixes it.

## Decisions

### D1. The word and its definition

*Obeya* replaces both *tasks repo* and *organization* (Manuel, 2026-10-25). It names
the repository and its whole content. The value of the `obeya` key is its **name**.
One definition, used verbatim by the glossary and paraphrased by the README and the
`gemba-init` skill:

> The **obeya** (大部屋, "big room": in lean, the room where a program, a team or a
> project keeps all of its work in sight) is the repository that holds `gemba.yaml`,
> `tasks/` and `harnesses/`; `gemba init` creates one. Whoever creates it draws its
> boundary: the organization they work for, a project, a team inside a company, or a
> whole startup. One person may keep it alone, or a team may share it. Its name, the
> `obeya` of the shared config, is a segment of the branch of every run.

Plural: *obeyas*. Article: *an obeya*.

Alternatives (in `2026-10-25-112601-obeya-vocabulary-decisions.md` of the run):
`name`, `area`, `space` (close to *workspace*, rejected for the harness) and `scope`
(already the scope of a skill).

### D2. The `obeya` key keeps the shape and the layer of `organization`

The key is shared-config only, optional, kebab-case and refused when malformed, and it
is the middle segment of `<branch_prefix>/<obeya>/<ref>`. `gemba worktree add` refuses
without it: `no obeya declared: add obeya to gemba.yaml`. With the value unchanged,
every branch keeps its name, and `orphan_branches` still finds the branches of runs
launched before the upgrade.

- Considered: moving it to the personal config, as `branch_prefix` moved, since a branch
  never leaves the machine under its own name. Rejected for now. It would be a second
  break of another kind in the same release, and the name is what the members of a team
  share once `team-mode` lands.

### D3. `organization` is refused, never aliased nor ignored

`config.py` gains a table beside `LAYERS`, `RENAMED_KEYS = {"organization": "obeya"}`.
A top-level key found in it, in either file, adds the problem
`organization was renamed obeya, which belongs in gemba.yaml, the shared config`
under the path of that file. The problem joins every other problem of both files, as
the misplaced keys do, and the key is then left out of parsing. The domain module
`config.py` owns the rule; no adapter changes for it.

- Alias: accepting both keys keeps two words alive. Every reader of `config show`
  would have to know both, and the old word would never leave.
- Ignored as an unknown key: `gemba worktree add` would then say
  `no obeya declared`, which hides the cause.

### D4. The guide heading and the document of `config show`

`Guide.organization` becomes `Guide.obeya`, and `ORGANIZATION_HEADING` becomes
`OBEYA_HEADING = "## Your obeya"`. `config show` prints the top-level `obeya` and
`harness.guide.obeya`, in the same positions as before. The skills that read the
document (`gemba-config` for its reference, none for the guide) change in the same
version. Guides already written are not rewritten: launch writes a guide once, and
`gemba skills update` never touches it.

### D5. "Configured value" for "organization-specific value"

A value a gemba config declares is a **configured value**, whoever it belongs to. The
11 skill lines read: "Every configured value (workstreams and their rules) lives in the
gemba config at the obeya root." That also corrects them: since
`personal-config-layer`, a rule may live in `gemba.local.yaml` too. The principle "Three
piles" of `AGENTS.md` reads: "No module and no skill contains a configured value; every
one is read from the gemba config at run time." The nine requirement titles are renamed
in the deltas (RENAMED), for example "Skill contains no configured value".

### D6. Messages and help

Every help text and message that says *tasks repo* says *obeya*. The texts that cases
assert:

| Where | Today | After |
|---|---|---|
| `NEXT_STEP` of `repo.py` | `open this tasks repo with your agent ...` | `open this obeya with your agent ...` |
| `nested_problem` | `... is inside the tasks repo <root>: a tasks repo is never created inside another one` | `... is inside the obeya <root>: an obeya is never created inside another one` |
| `read_draft` of `tasks.py` | `is not directly in the tasks repo root (paths are relative to the tasks repo root)` | `is not directly in the obeya root (paths are relative to the obeya root)` |
| `ref_problem` of `harness.py` | `record <ref> from the tasks repo or from its own harness` | `record <ref> from the obeya or from its own harness` |
| `commands/worktree.py` | `no organization declared: add organization to gemba.yaml` | `no obeya declared: add obeya to gemba.yaml` |
| template `gemba.yaml` | `# The gemba config of this tasks repo, ...` | `# The gemba config of this obeya, ...` |

Also changed, though no case asserts them: the `--root` help of every subcommand
(`obeya root (default: walk up to the nearest gemba.yaml)`), the help of `gemba init`
(`make a folder an obeya`), `gemba record`, `gemba skills update` and `gemba config`,
the `repos_dir` message of `config.py`, and the removal message of `harness.py`.
`gemba config check` prints no word that changes.

### D7. Names in the code: *repo* alone means a code repository

- `repo.py` becomes `obeya.py`, and `tests/test_repo.py` becomes `tests/test_obeya.py`.
  `commands/init.py` is their only other importer.
- The literal `"repo"` becomes `"obeya"` in `skills.Target`, `skills.Scope`, the
  `SKILLS` registry, `tasks.Place`, and the calls of `commands/init.py`,
  `commands/skills.py` and `commands/record.py`, with `tests/test_skills.py`.
- `Config.organization` becomes `Config.obeya`, and the parameter of
  `worktree.branch_name` becomes `obeya`. Every docstring and comment that says *tasks
  repo* or *organization* follows.
- Kept: `repos_dir`, the `repo` argument of `gemba worktree add` and `remove`, and
  `worktree.repo_problem`, which name code repositories; the capability id
  `repo-initialization` (see Non-Goals).

No new module, seam, dependency or output: the domain modules keep their rules
(`config.py` the key and its refusal, `harness.py` the heading, `worktree.py` the
branch, `obeya.py` the layout of init), and the adapters keep printing what the domain
modules return.

### D8. How the specs change, and how that is checked

The deltas were generated from the main specs by these rules, applied to whole
requirements, phrases wrapped across lines included: *a/A tasks repo* → *an/An obeya*;
*tasks repos* → *obeyas*; *tasks repo* and *tasks-repo* → *obeya*;
*organization-specific value/rule* → *configured value/rule*; *no organization value*,
*free of organization values*, *no value specific to an organization* → *configured*;
*of any organization* → *of any obeya*; *specific to the organization or to the
person* → *specific to one obeya or to the person*; *for one organization* → *for one
obeya*; `` `organization` ``, `<organization>`, `organization: nakatomi` and *Your
organization* → their `obeya` forms. A requirement enters the delta when its text holds
one of the words, or when one of its scenarios names a case or an exemption that
changes. The `**Cases**` line of every scenario is computed from `tests/cases` and
`tests/not-automated.yaml`.

Hand edits on top of the rules, the only text a reviewer has to read closely:

- `gemba-config`, "Obeya, repositories folder and branch prefix": the first sentence
  defines the key as the name of the obeya.
- `gemba-config`, "Keys of each layer": the refusal of `organization` and the scenario
  "Former organization key refused".
- `config-maintenance`, "The config is edited by hand through the skill": the skill
  renames `organization`, and the scenario "Former organization key renamed".
- `repo-initialization`, "Guided initial configuration": the first question explains
  the obeya and asks what it holds, and the scenario "Obeya explained before its name".

The scenario titles stay the current ones in the deltas (see Context). Task 1.1
renames these 21 titles in the main specs, in the deltas, in the `scenario:` field of
their cases and in their entries of `tests/not-automated.yaml`, all at once. Task 1.2
then checks the deltas with a script: for every MODIFIED requirement, the block with
its `**Cases**` lines removed must equal the main block with the rules applied, apart
from the four edits above.

| Capability | Title today | Title after |
|---|---|---|
| `built-in-skills` | No tasks repo | No obeya |
| `built-in-skills` | Personal providers leave the tasks repo skills | Personal providers leave the obeya skills |
| `config-maintenance` | Reference free of organization values | Reference free of configured values |
| `gemba-config` | Organization and repositories folder accepted | Obeya and repositories folder accepted |
| `gemba-config` | Malformed organization or branch prefix refused | Malformed obeya or branch prefix refused |
| `harness-guide` | Guide free of organization values | Guide free of configured values |
| `harness-guide` | Organization section rendered | Obeya section rendered |
| `harness-guide` | Organization and workstream sections rendered | Obeya and workstream sections rendered |
| `harness-launch` | Harnesses ignored by the tasks repo | Harnesses ignored by the obeya |
| `harness-worktrees` | Repositories folder relative to the tasks repo | Repositories folder relative to the obeya |
| `harness-worktrees` | Config without organization or repositories folder refused | Config without obeya or repositories folder refused |
| `platform-support` | Tasks repo used across platforms | Obeya used across platforms |
| `repo-initialization` | Tasks repo scaffolded in the working directory | Obeya scaffolded in the working directory |
| `repo-initialization` | Tasks repo scaffolded at a given path | Obeya scaffolded at a given path |
| `repo-initialization` | Personal config ignored in an earlier tasks repo | Personal config ignored in an earlier obeya |
| `repo-initialization` | Draft ignored in an earlier tasks repo | Draft ignored in an earlier obeya |
| `repo-initialization` | Nested tasks repo refused | Nested obeya refused |
| `repo-initialization` | Agent configures a new tasks repo | Agent configures a new obeya |
| `task-recording` | Task named by ref from the tasks repo | Task named by ref from the obeya |
| `task-recording` | Draft out of place refused in the tasks repo | Draft out of place refused in the obeya |
| `task-recording` | Task with a harness recorded from the tasks repo | Task with a harness recorded from the obeya |

The two new scenarios about the former key keep `organization` in their titles, since
they are about that key. The Purposes of `gemba-config`, `built-in-skills`,
`platform-support`, `repo-initialization`, `task-migration`, `task-recording` and
`harness-worktrees` are edited in the main specs by the same rules.

### D9. The cases

64 case files change. Each one is listed under its scenario, with the reason. 35 declare
the key, 11 expect a document or a guide that says `obeya`, and the rest expect a
message or a skill text, or only carry the old words in their name or comment. The 14
whose file names carry the old words are renamed with `git mv` in task 1.1, with the
scenario titles and before any content changes, for example
`tasks-repo-scaffolded.yaml` → `obeya-scaffolded.yaml` and
`config-without-organization-or-repos-dir-refused.yaml` →
`config-without-obeya-or-repos-dir-refused.yaml`. One case is new,
`config/former-organization-key-refused.yaml`, with one document for `gemba.yaml` and
one for `gemba.local.yaml`. `tests/not-automated.yaml` gains two entries, "Former
organization key renamed" and "Obeya explained before its name", and 10 entries change
their scenario or their reason.

### D10. The README and the glossary

The README opens with the audience and the obeya (draft):

> Gemba is a task-based system for working with AI agents, made for developers to
> organize their own work, alone or with a team, beside the way their company organizes
> its tasks rather than in its place. Every unit of work is one Markdown file in a
> repository of your own, the obeya. Your agent registers, launches, updates and closes
> those tasks through fixed processes, and each task is worked on inside a harness: a
> folder of its own, with its notes, its evidence and the code it touches, where nothing
> leaves without your written approval. What an obeya holds is yours to draw: the
> organization you work for, a project, a team inside a company, or a whole startup.
> Everything specific to it, its kinds of work, its fields and its rules, lives in its
> config, so the agent behaves the same in every obeya you keep.

The paragraph on the name adds the obeya after the gemba: the harness is the actual
place where one task is worked on, and the obeya, 大部屋, "the big room", is where lean
teams keep all of their work in sight: in Gemba, the repository where every task, its
record and every report of a period are within reach. The diagram reads
`your obeya` and `gemba.yaml   the config:`. The examples use `~/nakatomi-obeya` and
`../old-obeya`, and `## Bring tasks from another tasks repo` becomes
`## Bring tasks from another obeya`.

`AGENTS.md`: "What this repository is" gains the audience sentence. The glossary
replaces the tasks repo entry with the definition of D1, and says, in the worktrees
entry, that *repo* alone always means one of the repositories under `repos_dir`. The
gemba config is "the customization of the obeya ... what everyone who uses the obeya
agrees on". The rejected words become: *sandbox* and *workspace* for the harness;
*ledger*, *tasks repo* and *harness* for the obeya; *organization* for the obeya or its
name; *task type*; *daily status* for the report. `CONTRIBUTING.md` and `SECURITY.md`
follow the same words.

### D11. The changelog

The `[Unreleased]` section is rewritten in the new words, since nothing in it is
released. Under Changed it gains a **Breaking** entry: the `organization` key is now
`obeya`; every command refuses `organization`, naming the rename; branches keep their
names; the `gemba-config` skill renames it. A second entry says that the tasks repo is
now called the obeya everywhere: help, messages, skills, `config show` and the guide
heading. It also tells users to run `gemba skills update` to refresh the skills of an
obeya made by an earlier version. The released sections keep their words.

### Cross-platform

Following `.claude/skills/guidelines/cross-platform`:

- Paths printed (Rule 1, 2): the messages of D6 keep their path arguments and the code
  that renders them. Only the words around them change. A unit test that checks the
  nested refusal builds its expected text from the same `Path` objects.
- Names of files and folders (Rule 4): `obeya.py`, `test_obeya.py` and the 14 renamed
  case files have no reserved names. The obeya name in a branch is discussed in
  Non-Goals.
- Text files (Rule 5): every file is edited in place with its encoding and LF endings.
  The renames go through `git mv`. No new read or write is added.
- Processes (Rule 6): none added.

## Risks / Trade-offs

- [Scenario titles renamed outside the delta mechanism] → One scripted task renames
  exactly the 21 titles of the table, in all four places. It checks that every
  requirement keeps its number of scenarios and that no other title moved. Then
  `openspec validate --strict`, `openspec validate --specs` and `test_scenarios.py`
  must pass.
- [A mechanical diff hides a behaviour change] → The check of D8 allows only the four
  hand edits. The new behaviour (the key, the refusal, the heading, the document) has
  its own scenarios and cases.
- [Every command refuses an obeya made by 0.2 until it is upgraded] → The refusal names
  the rename and the file. The `gemba-config` skill renames it in the same pass that
  moves `ide`, `repos_dir` and `branch_prefix`. The changelog says so.
- [Skills written by an earlier version still say tasks repo] → `gemba init` and
  `gemba skills update` rewrite them, and the changelog says to run one.
- [An unfamiliar word] → The README explains it next to *gemba*, the glossary defines
  it, and the `gemba-init` skill explains it before asking for the name.
- [A large diff to review] → Most of it is generated. The review reads the rules, the
  hand edits, the code of D3 and D4, the docs, and the generated diff only by sampling.

## Migration Plan

For whoever upgrades: rename `organization` to `obeya` in `gemba.yaml`, by hand or by
asking the agent (the `gemba-config` skill), with `ide`, `repos_dir` and
`branch_prefix` moved in the same pass; run `gemba skills update` (or `gemba init`). The
branches of live runs keep their names. Harnesses launched earlier keep their
`## Your organization` heading, which nothing reads. Rollback is a revert of the change,
after which the key is named `organization` again.
