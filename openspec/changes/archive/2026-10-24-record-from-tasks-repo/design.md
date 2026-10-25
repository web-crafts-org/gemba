# Design

## Context

See proposal.md for the motivation. What shapes the approach:

- `commands/record.py` holds the whole flow in the adapter. It locates the harness
  with `harness_command.locate`, which raises "no harness found" outside one, loads the
  config from the harness folder, and reads the task `harness.yaml` names, archived or
  not. Its own `read_draft` checks the draft relative to the harness root and inside
  it. The rules of the content and of the write are domain functions of `tasks.py`
  (`parse_bullets`, `date_problem`, `updates_problem`, `record`), and none of them
  changes.
- `gemba mark` and `gemba set` name a task by a positional ref through
  `tasks.find_by_ref`, from anywhere under the tasks repo, and refuse an unknown ref
  with `no task has ref '<ref>' under tasks/, archives included`.
- `gemba skills update` already resolves "a harness first, else the tasks repo" in its
  adapter (`commands/skills.py`, `target`): `harness.find_root` from the working
  directory, then `config.load`.
- `repo.IGNORED_LINES` holds two unanchored lines, completed by `_completed` when
  `gemba init` converges. `skills.SKILLS` gives each skill its scope.
- `openspec/config.yaml` lets the apply phase touch a case only when a delta spec names
  its scenario. A probe on a scratch copy of the tree measured what the two registry
  changes break: 11 cases and 7 unit tests, all named in the delta specs or in the
  tasks.

## Goals / Non-Goals

**Goals:**
- One `gemba record` with one set of rules, whichever place it runs from. The two
  places differ only in how the task is found and where the draft may lie.
- A refusal in either place reports every problem at once, as today.
- Nothing changes for a harness: every existing call keeps its meaning and its
  output.

**Non-Goals:**
- The migration mode, `--from <task file>`, which is `task-migration`.
- Recording another task from inside a harness, or a harness's notes from the tasks
  repo.
- The `gemba-mark` skill, which offers to record before `done` only inside a harness,
  from its notes. Nothing in the tasks repo tells it a day is missing.
- Any git operation.

## Decisions

### D1. The place is resolved in the adapter, harness first

`commands/record.py` decides the place the way `commands/skills.py` decides its
target. With `--harness`, or when `harness.find_root` finds a `harness.yaml` at or
above the working directory, the record is made inside that harness, exactly as
today. Otherwise it is made from the tasks repo: `config.load(root=args.root)` walks up
from the working directory, and the task is `tasks.find_by_ref(root, workstreams,
ref)`, archives included, as in `mark` and `set`. Choosing the place reads files and
needs no new rule worth a domain function. It adds no seam: no new write, clock or
output.

Alternative: decide the place by the presence of `<ref>`. Rejected: inside a harness a
ref would then move the draft to the tasks repo root, away from where the agent of the
harness writes it (the decision note of the run, "any ref from anywhere").

### D2. The command line: an optional positional ref before the draft

`gemba record [<ref>] <file> [--date YYYY-MM-DD] [--harness PATH] [--root PATH]`, with
`ref` declared as `nargs="?"` before `file`. One positional is the draft, two are the
ref and the draft, so `gemba record update.md` keeps its meaning. `--root`, hidden
today, is shown, since it now names the tasks repo of a record made from it. A ref
written as a positional, as `mark` and `set` take it, also reads naturally in the
migration's `gemba record <ref> --from <file>`.

Known limit: argparse fills the positionals in one run, so an option written between
the ref and the draft (`gemba record SUP-1 --date D update.md`) is a usage error, exit
1. The skill always writes the ref and the draft together.

Alternative: a `--ref` option. Rejected: `mark` and `set` take the ref positionally,
and the agent would meet two spellings of the same thing.

### D3. Where the draft may lie: one domain function, two places

`read_draft` moves from `commands/record.py` into `tasks.py`, beside `parse_bullets`,
and takes the place, a `Literal["harness", "repo"]` alias like `skills.Target`:

- `harness`: relative to the harness root and inside it, unchanged.
- `repo`: relative to the tasks repo root and directly in it. The path is resolved,
  which also follows a symbolic link, and its parent must be the root, compared with
  `Path.samefile` once the parent exists. A spelling of the root that differs only in
  case, on Windows or macOS, is still the root.

"Directly in the root" replaces the wording of the decision note, "outside `tasks/`
and `harnesses/`". One check covers both folders, a link into either, and every other
subfolder, and the only draft a refusal can leave behind sits where the `.gitignore`
line of D5 expects it. The messages name the draft as the person gave it, like today's
`is not inside the harness (paths are relative to the harness root)`. The new one
reads `is not directly in the tasks repo root (paths are relative to the tasks repo
root)`.

### D4. A ref inside a harness is checked by the harness module

`harness.py` gains `ref_problem(given, harness_config)`. It returns `None` when the ref
is the one of `harness.yaml`, and otherwise says `<given> is not the task of this
harness, <ref>: record <given> from the tasks repo or from its own harness`. The
adapter adds it to the problems it already accumulates (date, draft, `## Updates`), so
a refusal still lists everything at once.

From the tasks repo, without a ref, the adapter refuses with
`no harness found and no ref given: outside a harness, name the task by its ref, as in
gemba record <ref> update.md`. It names no absolute path. An unknown ref gets the
message of `mark` and `set`. When no task was found, the date is checked against today
only, as `mark` does.

### D5. `/update.md`, anchored, is the third ignored line

`repo.IGNORED_LINES` becomes `("harnesses/", config.LOCAL_FILENAME, "/update.md")`,
and `_completed` appends whichever lines are missing, in order, as it does for two. The
line is anchored, unlike the other two: a person may keep an `update.md` of their own
elsewhere in the tasks repo, and only the draft at the root must stay out of the
history. The drafts of a harness are already ignored through `harnesses/`. The comment
above the constant says why the third line differs. An earlier tasks repo gets the line
and the `gemba-record` skill by running `gemba init` again, which writes a missing skill
and keeps the others, or the skill alone with `gemba skills update`.

### D6. `gemba-record` becomes `both`, with two paths in one skill

The registry entry becomes `Skill("gemba-record", "both")`. The asset keeps one body
with a common introduction, prerequisite and rules, and two processes, as `gemba-set`
describes both places:

- **Inside a harness**: the current steps, unchanged. The notes of the date are the
  only source.
- **From the tasks repo**:
  1. Identify the task by its ref, through the `gemba-list` skill when the user names
     it otherwise.
  2. Choose the date.
  3. Take the content from the user: what they say was done. When they said nothing
     concrete, ask, and record nothing they did not say.
  4. When `harnesses/<workstream>/<task file name without .md>/` exists, say that the
     work of the run is recorded from inside it, and read none of its notes.
  5. Read the `record` block of the workstream whose `prefix` is the prefix of the ref.
  6. Distill one to five bullets with the same rules as inside a harness.
  7. Write `update.md` at the tasks repo root.
  8. Run `gemba record <ref> update.md [--date D]` and relay the result.

  When the user drops a record the command refused, the agent deletes `update.md`.

The description says both places and adds the words a person uses for work outside a
run ("a meeting", "a review"). It keeps "whatever the workstream" and names no
organization value, as the `task-recording` requirement on organization values says.

### D7. `gemba-report` sends a gap to either place

The closing paragraph of the skill, "The report never fills a gap", points to the
`gemba-record` skill in two places: inside the task's harness for the work of its run,
and from the tasks repo for work done outside one. It drops the advice to launch a
harness only to record.

### D8. Tests

- New record cases, one per new scenario. Each puts `update.md` at the root in
  `tree`, sets `cwd` where the scenario says, and declares `unchanged: true` for
  refusals. The harness cases launch in `setup`, as the existing ones do. The case of
  a draft out of place has three documents: `../outside.md`, `tasks/support/update.md`
  and `harnesses/support/<stem>/update.md`.
- `record/no-harness-found.yaml` expects the new message.
- `init/draft-ignored-in-an-earlier-tasks-repo.yaml` runs `init` in `setup`, then
  writes the `.gitignore` of the previous version under `tree_after_setup`.
- The 11 cases named in the deltas gain `gemba-record` in their lists of tasks-repo
  skills, after `gemba-harness` in registry order, and `/update.md` in their
  `.gitignore`.
- `tests/not-automated.yaml` gains four entries: three for the agent's steps from the
  tasks repo and one for `task-reporting: Gap pointed to recording`.
- Unit tests: `GitignoreTest` of `tests/test_repo.py` follows the third line, and
  `test_scopes_and_providers` of `tests/test_skills.py` the new scope. No new unit
  test: every new rule is reached through a case.

### Windows

Read against `.claude/skills/guidelines/cross-platform`:

- Printed paths: the new messages name the draft as the user typed it and a ref, never
  an absolute path. The task path is the POSIX `task.path` of the scan, as today
  (Rules 1 and 2).
- Compared paths: the root of the tasks repo is compared with `Path.samefile`, not by
  spelling, so case and separators do not matter (Rule 1). The harness check keeps
  `is_relative_to` on resolved paths.
- Text: the draft is read as bytes through `platform.decode()`, and the task is
  written as UTF-8 with LF, as today. The `.gitignore` line goes through `_completed`
  and the existing writer of `init` (Rule 5).
- Names: no new file or folder name comes from a person. `update.md` is not reserved,
  and the cases write no reserved name (Rule 4).
- Processes and links: none (Rules 3 and 6).

## Risks / Trade-offs

- [An earlier tasks repo does not ignore `/update.md` until `gemba init` runs again] →
  The `CHANGELOG.md` entry says so. The command deletes the draft on success, and the
  skill deletes a draft the user abandons.
- [Two agents recording from the same tasks repo at once share `update.md`] → The skill
  writes the draft and runs the command in one step, one task at a time. Concurrent
  recording is out of scope, as concurrent harness launches already are.
- [The same day recorded from both places] → The bullets are appended to the same
  `### D`, which `record` already supports. The skill separates the sources: notes
  inside a harness, the user's words from the tasks repo.
- [`task-migration` will make `<file>` optional for `--from`] → With two optional
  positionals argparse puts a lone value in `ref`. The next change's adapter then reads
  it as the draft without `--from` and as the ref with it. Nothing here blocks that.

## Migration Plan

Nothing breaks: every `gemba record <file>` inside a harness behaves as before. The
`[Unreleased]` section of `CHANGELOG.md` gains the new form of `gemba record` and the
skill now written into the tasks repo (Added). Under Changed, it says that `gemba init`
writes `/update.md` into the `.gitignore` and that an earlier tasks repo gets the line
and the skill by running `gemba init` again. `README.md` shows the form from the tasks
repo in its "Record the day" section. At apply, the Purpose of the `task-recording`
main spec drops "of a run", since a record is no longer only the promotion of a run's
notes. Rollback is reverting the change. A tasks repo keeps working with an extra
ignored line and an extra skill.
