# Spec Delta

## REMOVED Requirements

### Requirement: A note is drafted by the agent and filed by the command
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "A draft
is filed under a dated name" and "Drafts the command refuses".

### Requirement: Note types and the approval gate
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The five
note types" and "The approval gate follows the type".

### Requirement: Notes by the agent
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The agent
files a note and links it" and "The agent acts on an approved note".

## ADDED Requirements

### Requirement: A draft is filed under a dated name
`gemba harness note <file> --type <type> [--approval] [--asset <path>]...` SHALL take
a Markdown draft directly under `notes/` of the harness, read the date and time from
the clock, rename it to `notes/YYYY-MM-DD-HHMMSS-<slug>.md`, prepend a frontmatter,
commit, and print the new path relative to the harness root. The body SHALL be kept
character for character, its line endings made LF and a leading byte-order mark
dropped, so that a note holds one convention whatever wrote the draft.

#### Scenario: Note filed
- **WHEN** `notes/login-trace.md` holds a body with no frontmatter and `gemba harness note notes/login-trace.md --type finding` runs on 2026-09-30
- **THEN** the file is now `notes/2026-09-30-HHMMSS-login-trace.md` with the run's time, its content is a frontmatter followed by the original body unchanged, no `notes/login-trace.md` remains, and the command prints the new path
- **Cases**: keeps `tests/cases/harness/note-filed.yaml`

#### Scenario: Draft with CRLF filed
- **WHEN** `notes/login-trace.md` holds a body whose lines end with CRLF, starting with a UTF-8 byte-order mark, and `gemba harness note notes/login-trace.md --type finding` runs
- **THEN** the filed note holds the frontmatter followed by the body with every line ending in LF and no byte-order mark, character for character otherwise, and the command exits 0
- **Cases**: keeps `tests/cases/harness/draft-with-crlf-filed.yaml`

### Requirement: Drafts the command refuses
The command SHALL refuse, changing nothing, a draft that is not directly under
`notes/`; whose name is not a slug (`^[a-z0-9]+(-[a-z0-9]+)*$`, not a reserved device
name of Windows: `con`, `prn`, `aux`, `nul`, `com0` to `com9`, `lpt0` to `lpt9`)
followed by `.md`; that already starts with a frontmatter; that is not UTF-8; or whose
target name already exists.

#### Scenario: Draft that is not UTF-8 refused
- **WHEN** the draft is encoded in UTF-16
- **THEN** the command exits 1, says the draft is not UTF-8 text, and changes nothing
- **Cases**: keeps `tests/cases/harness/draft-not-utf-8-refused.yaml`

#### Scenario: Draft outside notes or misnamed refused
- **WHEN** the file is not directly under the harness `notes/`, or its name is not a slug followed by `.md`
- **THEN** the command exits 1, names the rule the path breaks, and changes nothing
- **Cases**: keeps `tests/cases/harness/draft-outside-notes-or-misnamed-refused.yaml`

#### Scenario: Reserved device name refused
- **WHEN** the draft is `notes/aux.md` or `notes/com1.md`, on any platform
- **THEN** the command exits 1, says the name is reserved on Windows, and changes nothing
- **Cases**: keeps `tests/cases/harness/reserved-note-slug-refused.yaml`

#### Scenario: Already filed note refused
- **WHEN** the file given already starts with a frontmatter
- **THEN** the command exits 1, reports that the note is already filed, and changes nothing
- **Cases**: keeps `tests/cases/harness/already-filed-note-refused.yaml`

### Requirement: The five note types
The type SHALL be one of `finding` (what is true and the evidence for it), `blocker`
(why the run cannot continue, what was tried, what is needed), `decision` (the
options, their trade-offs and the recommendation or the choice), `summary` (where the
run stands at a milestone and what remains) and `external-action` (something to be
done outside the harness, word for word). An unknown type SHALL be refused, naming the
known types, and the command's help SHALL list the types with their definitions.

#### Scenario: Unknown type refused
- **WHEN** `--type` is not one of the five types
- **THEN** the command exits 1, names the known types, and changes nothing
- **Cases**: keeps `tests/cases/harness/unknown-type-refused.yaml`

### Requirement: The approval gate follows the type
The gate SHALL follow the type: an `external-action` SHALL always be filed with
`approved: false`; a `decision` SHALL be filed with `approved: false` only when
`--approval` is given; `--approval` SHALL be refused for `finding`, `blocker` and
`summary`.

#### Scenario: External action always gated
- **WHEN** an `external-action` note is filed without `--approval`
- **THEN** its frontmatter holds `approved: false`
- **Cases**: keeps `tests/cases/harness/external-action-always-gated.yaml`

#### Scenario: Decision gated on request
- **WHEN** a `decision` note is filed with `--approval`, and another without it
- **THEN** the first holds `approved: false` and the second has no `approved` key
- **Cases**: keeps `tests/cases/harness/decision-gated-on-request.yaml`

#### Scenario: Approval refused for ungated types
- **WHEN** `--approval` is given with type `finding`, `blocker` or `summary`
- **THEN** the command exits 1, says that type takes no approval, and changes nothing
- **Cases**: keeps `tests/cases/harness/approval-refused-for-ungated-types.yaml`

### Requirement: The agent files a note and links it
The `gemba-harness` skill SHALL have the agent write each note under `notes/` with its
own tools, choose its type by the question it answers, read the `harness.note` block
of the task's workstream and follow its `rules`, and file the note with
`gemba harness note` and the assets it references, never writing a frontmatter, a date
or a timestamp by hand. The agent SHALL then give the note in the chat as a Markdown
link to the path the command printed.

#### Scenario: Agent files a note
- **WHEN** the agent has something to record
- **THEN** it writes the draft under `notes/`, saves any evidence under `assets/` with a timestamp name, runs `gemba harness note` with the type and the assets, and gives the filed note as a Markdown link whose text and target are the path the command printed, relative to the harness root, such as `[notes/2026-09-30-101500-login-trace.md](notes/2026-09-30-101500-login-trace.md)`, and never the path of the draft
- **Cases**: keeps the entry `harness-notes: Agent files a note` of `tests/not-automated.yaml`

#### Scenario: Agent follows the verb's rules
- **WHEN** the task's workstream declares `harness.note.rules`
- **THEN** the agent follows them while drafting and filing a note
- **Cases**: keeps the entry `harness-notes: Agent follows the verb's rules` of `tests/not-automated.yaml`

#### Scenario: Note awaiting approval linked
- **WHEN** the agent files an `external-action` note, or a `decision` with `--approval`
- **THEN** it gives the filed note as a link, as for any note, and tells the user that they approve it by setting `approved: true` in its frontmatter, which they open from that link, and that a yes in the chat is not an approval
- **Cases**: adds the entry `harness-notes: Note awaiting approval linked` to `tests/not-automated.yaml`

### Requirement: The agent acts on an approved note
Before acting on a gated note, the agent SHALL read its frontmatter and act only when
`approved` is `true`, following the `rules` of the `harness.resolve` block of the
task's workstream. After acting it SHALL append what was done and where to the body,
with its own tools, run `gemba harness resolve` on the note, and give the note in the
chat as a link to the path that command printed, with the outcome.

#### Scenario: Agent acts on an approved note
- **WHEN** the user has set `approved: true` on an `external-action` note
- **THEN** the agent performs the action, appends the outcome to the note body, runs `gemba harness resolve` on it, and gives the resolved note as a Markdown link to the path the command printed, with the outcome
- **Cases**: keeps the entry `harness-notes: Agent acts on an approved note` of `tests/not-automated.yaml`
