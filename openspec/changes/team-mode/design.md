# Design

## Context

See proposal.md for the motivation. What shapes the approach:

- `tasks.py` knows one layout, `tasks/<workstream>/` and its `archive/`: `scan` reads
  those folders and reports any other entry under `tasks/`, `find_by_ref` goes through
  `scan`, `next_ref` counts one prefix over every filename under `tasks/`, and
  `FILENAME_PATTERN` reads a ref as `[A-Z]+-[1-9][0-9]*`, so it rejects `MR-SUP-3`.
  `Task` has no owner, and its fields are the listing record, in record order.
- The write commands, `create`, `record`, `mark`, `set`, `archive` and `harness launch`,
  find a task with `find_by_ref` (or, for `record` inside a harness, from
  `harness.yaml`), and none of them knows who runs it.
- `config.py` validates both files and reports every problem at once, each under the
  path of its file; `LAYERS` gives each top-level key its files, and a check that needs
  another value runs only when that value is valid.
- `harness.harness_path` is `harnesses/<workstream>/<stem>/`, `task.md` links
  `../../../<task path>`, and the branch of a run is `<branch_prefix>/<obeya>/<ref>`:
  all three hold for a task under `tasks/<member>/<workstream>/`, since the stem and the
  branch carry the ref with its initials and the link target is the task path.
- Manuel's decisions of 2026-10-25: `team` is a map keyed by member folder; a listing
  record carries `owner` only in an obeya with a team; `--owner` and `--by owner` are
  refused without a team.

## Goals / Non-Goals

**Goals:**
- An obeya without a team behaves exactly as today: no existing case changes its
  expectation, and no existing output gains a key.
- Each member's folder has one writer, enforced by the commands that write a task,
  with every problem of a call reported at once and nothing written on a refusal.
- Reading stays free: every member's tasks are listed, reported, found by ref and used
  by `gemba-migrate`, whether or not the clone declares `me`.

**Non-Goals:**
- Access control. The guard reads `me` from a file the person writes; it stops
  accidents. Who may push what is the git host's (CODEOWNERS, branch protection).
- Git: committing, pushing, hooks and `gemba sync` are `git-control`'s, and so are the
  git preferences the `gemba-init` interview will ask.
- Checking that a ref's initials match the folder that holds it. A file moved by hand
  into another member's folder is read as that member's; allocation still never reuses
  its number (D4), and `git-control` validates a member's own tasks before a push.
- The parent of a task, which `task-relations` designs on top of this layout.

## Decisions

### D1. `team.py`: the team as a domain module

A new domain module, `src/gemba/team.py`, owns the team: `Member` (`id`, `initials`,
`active`), the pattern of initials, who may write a task, and the layout check. It has
no side effect beyond reading the names of the folders directly under `tasks/`.

- `config.py` parses `team` into `dict[str, Member]` and `me` into a member id, as it
  parses the workstreams, and imports `Member` from `team`. `team` never imports
  `config`, so a message that names `gemba.local.yaml` takes the name of the file as an
  argument, as `worktree.missing_repos_dir_problem` does.
- `Config` gains `team: dict[str, Member] | None` and `me: str | None`, both `None`
  without a team, and the property `members`, the member ids in config order or `None`.
  Every adapter that scans passes `members` to `tasks`.

Alternative: the members and the guard in `config.py` and `tasks.py`. Rejected: neither
owns who may write, and `config.py` would grow a rule that adapters call.

### D2. Validating `team` and `me`

`LAYERS` gains `team: (gemba.yaml,)` and `me: (gemba.local.yaml,)`, so the misplaced
keys are refused by `_misplaced` as every other key is.

`_parse_team` appends one problem per fault, under `gemba.yaml`:

- `team must be a non-empty map keyed by the folder name of each member`;
- per member, prefixed `team member '<id>': `: a folder name not kebab-case, reserved on
  Windows (`platform.is_reserved_name`), or equal to a workstream identifier of the
  catalogue (checked only when the catalogue is a map); an entry that is not a map;
  `initials` missing or not `[A-Z]+`; `active` not a boolean; any other key, naming it
  and the allowed keys `initials` and `active`;
- `team members '<a>' and '<b>' declare the same initials '<XX>'`, checked over the
  members whose initials parsed.

`_parse_personal` receives the member ids of the shared team, or a marker that the
shared config declares none, or nothing when the shared file did not parse. `me` must be
a string; without a team it is refused as `me needs a team: gemba.yaml declares none`;
an id that is not a member as `me names no member of the team: 'bob' (members: manuel,
ana)`. The member ids are the keys of the declared map even when one member has a
fault, so a bad member is reported once and `me` naming it is not echoed. An inactive
`me` is valid config: reading stays free, and the guard refuses the writes (D5).

A member id may not equal a workstream identifier so that the layout check of D3 tells
the folder of a member from the folder of a workstream by name alone.

### D3. A team over the layout of an obeya without one

`team.layout_problem(root, workstream_ids)` returns one problem when the shared config
declares a team and a non-hidden folder directly under `tasks/` bears the identifier of
a workstream: `team is declared, but tasks/ holds tasks/operations and tasks/support,
the folders of an obeya without a team: a team starts in a new obeya, and the
gemba-migrate skill brings earlier tasks into it`. Paths are POSIX and sorted. `load`
calls it after parsing, only when `team` parsed and the catalogue is a map, and appends
it to the problems of `gemba.yaml`, so every command refuses with it, `config check`
included.

Alternatives: a problem of `gemba list` only, which would let every write proceed on a
mixed layout; or refusing any folder that is not a member, which `scan` already reports
as a stray (D6) without stopping the listing.

### D4. Refs, filenames and allocation

- `FILENAME_PATTERN` reads the ref as `(?:[A-Z]+-)?[A-Z]+-[1-9][0-9]*`. The slug is
  lowercase, so the boundary stays unambiguous. Both forms are read in any obeya: the
  source of `record --from` may come from an obeya of the other kind.
- `next_ref(root, prefix, initials=None)` matches `<date>-<initials>-<prefix>-<N>-` when
  initials are given and `<date>-<prefix>-<N>-` otherwise, over every filename under
  `tasks/` as today. A team ref never matches the pattern of a bare prefix, nor one
  member's the other's. Scanning the whole tree rather than the member's folder keeps
  one walk for both kinds of obeya, and a file moved by hand into another folder still
  holds its number.
- `create`, with a team, writes into `tasks/<me>/<workstream>/` and its `archive/`, each
  with a `.gitkeep`, with the initials of `me`.
- `display_title` strips the ref as given, so it needs no change.

### D5. The guard

`team.write_problems(team, me, task, personal_file)` returns the problems that stop a
write, empty without a team:

- no `me`: `no member declared for this clone: add me to gemba.local.yaml, the personal
  config (members: manuel, ana)`;
- an inactive `me`: `me is ana, an inactive member of the team, who writes no task`;
- with a task whose owner is not `me`: `AG-SUP-1 belongs to ana: only its owner writes
  it`.

`create` calls it with no task; `record`, `mark`, `set` and `harness launch` add its
problems to their own list, so a call reports the guard with every other problem;
`archive` calls it per ref, which prints `not archived: AG-SUP-1 belongs to ana: only
its owner writes it`. `harness remove` is not guarded: it deletes only local folders and
branches, and a harness of another member's task cannot be launched. The worktree
commands run inside a harness of the member's own task.

### D6. The owner of a task, and the scan

- `Task` gains `owner: str | None` right after `path`, so `dataclasses.asdict` gives the
  record order of the spec. `read` and `_parse` take the owner; `read_source` gives
  none.
- `scan(root, workstream_ids, include_archived, configured=None, owners=None)`: with
  `owners`, it reads `tasks/<owner>/<workstream>/` and its `archive/` for each owner and
  sets `owner`; without, today's folders. With `configured` (no filter given), it
  reports an entry directly under `tasks/` that is not among `owners`, as `folder is not
  a member of the team; its files are not listed` (or `entry is not a member folder of
  the team`), and an entry directly under a member's folder that is not configured,
  with today's messages. The sort key is unchanged; two members never share a filename,
  since the ref carries the initials.
- `find_by_ref` takes `owners` and passes it on. `record` inside a harness derives the
  owner from the task path of `harness.yaml`, its segment after `tasks/`, when the
  config declares a team.
- `archive_destination` becomes the task's own folder plus `archive/`, which holds for
  both layouts.

### D7. Listing and reporting

- `selection.add_options` gains `--owner MEMBER`, repeatable. `build` refuses it without
  a team (`--owner needs a team: this obeya declares none`, once whatever the number of
  values) and any value that is not a member (`unknown member 'bob' (members: manuel,
  ana)`). `Scope` gains `owners`, the filter or every member, `None` without a team;
  `filtered` is true when a workstream or an owner filter is given, which keeps strays
  unreported as the workstream filter does today.
- `gemba list` drops the `owner` key of every record when the config declares no team,
  so the record of an obeya without a team is the one of today (Manuel's choice).
- `metadata.RESERVED` gains `owner`, and with it `report.BUILT_IN`. `grouping_problem`
  takes the member ids: `owner` without a team is refused as `cannot group by 'owner':
  this obeya declares no team`. `_grouping_values` gives the task's owner, and `_rank`
  the index of the member in the team, so groups follow the config order.

### D8. The config commands

- `config check` prints, after `default workstream:`, `team: manuel (MR), ana (AG,
  inactive)` and, when declared, `me: manuel`.
- `config show` adds `team`, each member to `{initials, active}` with the default
  applied, and `me`, before `workstreams`, only when the config declares a team. The
  spec of show says a key absent from the files is `null`; here the key itself is left
  out without a team, as the record leaves out `owner`, so no existing document of show
  changes. This follows Manuel's choice for the record and is for review.

### D9. The skills

- `gemba-init`: the prerequisite admits a second case, a config that declares a team
  and a clone with no `gemba.local.yaml`, which asks only `me`, the IDE and the
  repositories folder and writes `gemba.local.yaml`; a user who is not a member is sent
  to the team, which adds them through `gemba-config`. The first configuration gains a
  question after the obeya's name: whether a team shares it, then each member with a
  kebab-case folder name and initials no other uses, and which one the user is; step 8
  writes `team` into `gemba.yaml` and `me` into `gemba.local.yaml`.
- `gemba-config`: the reference gains the rows `team` and `me` and a section on the
  team (a member is never removed and initials never reused, `active: false` for one
  who leaves, each member writes their own `me`, a team is never added over existing
  tasks and `gemba-migrate` brings them into a new obeya); `owner` joins the reserved
  field names.
- `gemba-list` and `gemba-report`: with a team, the user's own tasks and work are those
  of `me`, read from `gemba config show`; a member named is their folder; the team is no
  owner filter, and a report of the team groups `--by owner`.
- `gemba-create`: with a team the task lands in the folder of `me`; a task for another
  member is that member's to create.
- `gemba-record`, `gemba-mark`, `gemba-set`, `gemba-archive` and `gemba-harness`
  (launch): one rule each, a refusal of another member's task is relayed with a
  suggestion to ask its owner, and the file is never edited to get around it.
- No skill is added or removed, so the registry and the init and skills cases do not
  change. `gemba skills update` brings the new text to an existing obeya and harness.

### D10. Docs

`AGENTS.md`: *team*, *member* and *owner* in the vocabulary, the layout with a team in
the entry of a task, the ref with initials, and a principle, "one writer per folder".
README: a section "Share an obeya with a team", after the config, with the `team` and
`me` blocks, the layout, the refs, the guard and how a member joins; the section on
bringing tasks says a team starts in a new obeya. `SECURITY.md`: the guard is not
access control. `CHANGELOG.md`, `[Unreleased]`: under Added, the team, `me`, the owner
of a task, the guard, `--owner` and `--by owner`; under Changed, **Breaking**, `owner`
reserved as a field name; and the skills to update with `gemba skills update`.

### D11. Tests

- 32 new case files, each named by a scenario, and a new document in
  `config/reserved-field-name-refused.yaml` for `owner`. A team case declares `team` in
  `config` and `me` in `local_config`, and writes tasks under `tasks/<member>/` through
  `tree`; the runner needs nothing new.
- 12 new entries in `tests/not-automated.yaml`, the agent's steps.
- Unit tests: `tests/test_team.py` for `write_problems` and `layout_problem`;
  `tests/test_config.py` for `team` and `me`; `tests/test_tasks.py` for the filename
  pattern, `next_ref` with initials, the scan of member folders and its strays;
  `tests/test_report.py` for the owner grouping and its order.

### Windows

Following `.claude/skills/guidelines/cross-platform`:

- Names: a member id becomes a folder, so it is checked with
  `platform.is_reserved_name()` where its other checks run (Rule 4). Initials are
  uppercase ASCII inside a filename, as a prefix is.
- Printed paths: the layout problem and the strays print paths relative to the root
  with `as_posix()` (Rule 2); `create` prints the task path as today. No absolute path is
  added to a message, and the unit tests build no expected text from a literal
  absolute path (Rule 1).
- Files: no new text read or write; `create` writes the task through its existing
  UTF-8, LF write (Rule 5). No link changes (Rule 3), no process starts (Rule 6).
- Case-insensitive file systems: two members differ in their kebab-case ids and their
  initials, and a member id cannot equal a workstream id, so no two folders of
  `tasks/` collide on case alone.

## Risks / Trade-offs

- [A config with a field named `owner` breaks] → It is refused naming the field and
  the reason, in the unreleased 0.3.0 that already breaks `gemba.yaml`; the changelog
  says so and the `gemba-config` skill renames a field when asked.
- [`me` is self-declared] → The guard only stops accidents; the README and
  `SECURITY.md` send access control to the git host, and `git-control` adds the checks
  of a push.
- [The shape of a record depends on the obeya] → Manuel's choice: an individual obeya
  sees no new key. A consumer of `gemba list` in a team reads `owner`; `config show`
  says whether the obeya has a team.
- [A file moved by hand into another member's folder changes owner] → Allocation
  still never reuses its number; the move is visible in git; checking initials against
  the folder is left to `git-control`'s validation of a push.
- [Two clones of one member create the same ref without syncing] → Out of scope, as
  for one person today: its author has the context to fix it.

## Migration Plan

Nothing to migrate: an obeya without a team reads as before, and a team starts in a new
obeya, into which `gemba-migrate` brings earlier tasks. An obeya and its harnesses get
the new skill texts with `gemba skills update`.
