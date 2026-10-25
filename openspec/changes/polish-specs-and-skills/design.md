# Design

## Context

See proposal.md for the motivation. What shapes the approach:

- OpenSpec 1.14.1 warns on a requirement whose text, the non-blank lines before its
  first scenario, passes `MAX_REQUIREMENT_TEXT_LENGTH = 500`. No config raises that
  limit. `openspec validate <change>` checks the limit on ADDED requirements only. After
  the archive, `openspec validate --specs` checks every requirement of the main specs.
- OpenSpec refuses a MODIFIED block that drops a scenario of the current spec, in
  `validate` as an error and in `archive` as a failure, and refuses a name that is both
  REMOVED and ADDED. So the only way to split a requirement is to remove it and add
  its parts under new names.
- `tests/test_scenarios.py` keys a scenario by capability and title, and applies
  RENAMED, REMOVED, MODIFIED and ADDED. A scenario that moves to another requirement of
  the same spec keeps its case. Nothing outside the specs and the archived changes
  names a requirement.
- `gemba harness note` and `gemba harness resolve` print the note path relative to the
  harness root, built with `as_posix()`. A filed name is
  `notes/YYYY-MM-DD-HHMMSS-<slug>.md`, and a slug holds only `[a-z0-9-]`.
- `commands/worktree.py` already scans `repos_dir` in `repositories()`. It returns the
  folders directly under `repos_dir` that hold a `.git`, in name order, and
  `worktree.repo_problem` prints them when `add` is given an unknown name.
- The guide of a harness says that nothing above the harness concerns the agent.
  `repos_dir` usually lies above it.

## Goals / Non-Goals

**Goals:**

- `openspec validate --specs` reports no warning after the archive, and stays so.
- No change of behavior in the 76 requirements. Every existing scenario keeps its title
  and its text, except the two of `harness-notes` this change means to change. No
  existing case changes.
- A note reaches the user as one click from the chat, under its final name.
- The agent finds a repository from loose words without reading above the harness.

**Non-Goals:**

- Requirements of 500 characters or fewer, and the Purposes of the specs.
- Shortening scenarios, which have no limit.
- Matching repositories by anything other than their folder names, such as their
  remotes or READMEs.
- Links in any other output than notes: the harness path of a launch, the task path of
  `record`.

## Decisions

### D1. Condense one behavior, split several

Each of the 76 requirements is rewritten to 500 characters or fewer, measured as
OpenSpec measures it:

- **Condense** (34) when it states one behavior: a MODIFIED block with the same name and
  every scenario, word for word.
- **Split** (42, into 104 requirements) when it states several: the requirement is
  REMOVED, with its Reason and its Migration naming the parts, and each part is ADDED
  under a new name with the scenarios of its behavior, word for word. Every scenario of
  the removed requirement goes to exactly one part.

A rewrite keeps every SHALL, every refusal, every printed text and every value. It
drops rationale that the text does not need, and it drops a sentence that another
requirement already states:

- `gemba-config`: the rationale of `ide` as a personal key, which "Keys of each layer"
  and `SECURITY.md` carry; "the worktree process reports the absence itself", which
  "Config without obeya or repositories folder refused" covers; the definition of
  snake_case; and the list of checks that run only on what parsed, which the scenario
  "One mistake reported once" shows.
- `task-creation`: the forms of each metadata type, which "Values follow the declared
  type" of `metadata-setting` and the scenarios "Typed metadata values" and "Text kept
  as written" state.
- `task-file-format`: "the commands of later sprints move the fields their process
  owns", which binds no command.
- `task-recording`: "The command SHALL validate the gemba config as every process
  does", which "Config validation precedes any write" states for every process; and
  "the requirements on the draft apply to a record made from a draft".

Two parts make explicit what only a scenario said before. "Launch finds a task it can
launch" names the refusal when no agent provider is declared, and "Add moves the base
of an attached worktree" says the command never rebases. One leftover of
`obeya-vocabulary` goes too: "Set reports each value" says "obeya root" where the old
requirement said "tasks repo root".

Two splits leave a behavior with no scenario. In `harness-guide`, the notes, assets
and commits part of "Guide content" gets the new scenario "Guide explains notes and
assets" with its case. The `harness-notes` and `harness-worktrees` agent parts get the
new scenarios of D4 and D6.

Alternatives considered:

- The split that the OpenSpec specs instruction gives: the first behavior under
  MODIFIED with every scenario, each other behavior ADDED with new scenarios. The old
  scenarios would stay under a requirement that no longer states them, and each of the
  104 parts would need a new scenario and a new case.
- Condensing all 76 in place, with the detail moved into the WHEN and THEN of their
  scenarios. No rename, but a 2296-character requirement does not condense to 500
  without becoming a list of section names, and its scenarios would grow to carry what
  it states.

### D2. The archive puts each part where its requirement stood

`openspec archive` appends ADDED requirements at the end of a spec. A split
requirement would then leave its place and land after unrelated ones. The specs are
synced by a script, as for the three previous changes. The script replaces each
MODIFIED block in place, puts the parts of a split requirement in its place in the
order of the delta, puts the new requirement of `harness-worktrees` after "List reads
the state of every worktree", and drops the `**Cases**` lines. Then
`openspec archive polish-specs-and-skills --skip-specs --yes` moves the change.

The script ran on a copy while this change was proposed. Its result: 21 specs valid,
0 issues, 211 requirements, none over 500; no scenario lost; the seven new scenarios
added; the text of no scenario changed except "Agent files a note" and "Agent acts on
an approved note"; titles, Purposes and every requirement the delta does not name
unchanged.

### D3. A rule keeps new requirements under the limit

`rules.specs` of `openspec/config.yaml` gains one rule: keep the text of a requirement
that a delta adds or modifies at 500 characters or fewer, one behavior per
requirement, with examples and edge cases in its scenarios. `openspec instructions
specs` delivers it when a delta is written. `openspec validate <change>` checks ADDED
requirements only, so the rule also names MODIFIED ones.

Alternative considered: a unit test that reads the main specs and fails on a long
requirement. It would catch a MODIFIED one at apply time, but it would check OpenSpec's
format with a second parser, and `openspec validate --specs` already reports it.

### D4. A note is given as a Markdown link to the path the command printed

After `gemba harness note` and after `gemba harness resolve`, the `gemba-harness` skill
has the agent give the note as `[<path>](<path>)`, where `<path>` is exactly what the
command printed: the final name, relative to the harness root. It is never the path
of the draft. A note that waits for approval also gets the existing reminder that
the user sets `approved: true` in its frontmatter, opened from that link, and that a
yes in the chat is not an approval.

- **Relative, not absolute.** The harness is the root the IDE opens, its first workspace
  folder, and an IDE chat resolves a relative link against it. The printed path holds
  only `notes/`, digits, hyphens, `[a-z0-9]` and `.md`, so it needs no URL encoding.
  An absolute path holds the separators of the system and may hold spaces. On Windows
  it holds a drive and backslashes, which a Markdown link target does not take as they
  are.
- **The text of the link is the path too**, so that an agent UI that does not render
  links still shows where the note is.
- **Windows**: the commands already print the path with `as_posix()`, so the link is
  the same on every platform. No path is built by the skill.
- **Owner**: the skill asset only. No command changes, and no new seam.

The guide of the harness does not change: by "Guide explains notes and assets" it does
not describe the steps of `note`.

### D5. `gemba worktree list --available`

A flag of `list`, not a new verb: the group's verbs are `add`, `list` and `remove`,
and listing what can be added is a listing. A verb such as `repos` would be a noun,
and `add` with no repository would be an add that adds nothing.

- **Output**: the folder names that `repositories()` returns, one per line, in its order
  (Python string order, the same on every platform), or `no repositories` when the
  list is empty, then exit 0. An attached repository is listed like any other, not
  marked: `gemba worktree list` shows the attached ones, and a plain list is what the
  agent matches against.
- **Refusals**, the same messages as `add`: `no repos_dir declared: add repos_dir to
  gemba.local.yaml` without `repos_dir`, and `repos_dir <folder> is not a folder` when
  it names no folder, through `fail("list", ...)`. `obeya` is not needed: no branch is
  named.
- **Where it runs**: inside a harness, located as every verb of the group, with the
  config loaded from the harness.
- **Owners**: the flag and the scan in `commands/worktree.py`, the adapter, which already
  owns `repositories()`. The messages go into `worktree.py`, the domain module: the
  constant `NO_REPOSITORIES` and the refusal of a missing `repos_dir`, which `add`
  builds inline today and both verbs then share. No new seam: the read of `repos_dir`
  exists.
- **Windows**: the command prints names, not paths. It reads folders and writes nothing.
  A name that Windows reserves cannot exist there as a folder, so nothing is validated.
  The `.git` check is `exists()`, as for `add`, so a repository whose `.git` is a file
  is listed as `add` accepts it.

### D6. The agent looks the repository up through the command

Step 1 of Add in the `gemba-worktree` skill becomes:

1. Take the repositories the task needs from the request, `task.md` and the notes.
2. Run `gemba worktree list --available`.
3. A name equal to a listed one, with the same spelling, is used as it is.
4. Otherwise, ask the user to choose among the listed repositories the request may
   mean: those whose names share a word or a stem with it, or that `task.md` or the
   notes name. Ask with the agent's tool for questions with options, a panel, when it
   has one, offering the likeliest first and saying the user may name another;
   otherwise ask with a numbered list in the chat. When no listed name fits, say so
   and show the list. Never guess, and never run `add` on a name the user did not
   confirm.
5. Never read `repos_dir` or any folder above the harness. The command reads it.

The refusal of `add` for an unknown name already lists the repositories. The skill
treats it as step 4 does.

The guide does not change: the agent still reads nothing above the harness. The
requirement "The agent looks up the repositories of the task" replaces the sentence of
"Worktrees by the agent" that forbade browsing `repos_dir`.

Alternative considered (Manuel chose the command): the agent lists `repos_dir` with
its own tools. It needs no code, but it needs an exception in the guide, permission
prompts for reads above the harness, and a second definition of what a repository is.

## Risks / Trade-offs

- [A rewrite drops something a requirement required] → D1 lists everything dropped.
  The checks of D2 hold every scenario word for word. Each part is reviewed against the
  REMOVED requirement whose Migration names it.
- [104 new requirement names] → nothing in the repository names a requirement outside
  the specs and the archived changes, which keep the old names as history.
- [An agent UI does not render Markdown links, or resolves them against another root]
  → the text of the link is the path itself, readable anyway.
- [A request matches many repositories] → the agent offers the likeliest few and lets
  the user name another, rather than listing every folder in a panel.
- [Obeyas and harnesses keep the old skills] → `gemba skills update` refreshes them, as
  the `[Unreleased]` section of `CHANGELOG.md` already asks for this version.

## Migration Plan

No breaking change. The `[Unreleased]` section of `CHANGELOG.md` gains entries for
`gemba worktree list --available` and for the two skills. An existing harness keeps
its copies of the harness skills until `gemba skills update` runs inside it. The
archive follows D2.
