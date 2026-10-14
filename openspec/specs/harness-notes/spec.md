# harness-notes Specification

## Purpose

Notes and assets are the memory of a run: the agent writes them in free form inside
the harness, and the command files each note with the frontmatter, the name and the
commit that make it findable later, including the approval gate for anything that acts
outside the harness.

## Requirements

### Requirement: A note is drafted by the agent and filed by the command
`gemba harness note <file> --type <type> [--approval] [--asset <path>]...` SHALL take a
Markdown file directly under `notes/` of the harness whose name is a slug (matching
`^[a-z0-9]+(-[a-z0-9]+)*$` and not a reserved device name of Windows: `con`, `prn`,
`aux`, `nul`, `com0` to `com9`, `lpt0` to `lpt9`) followed by `.md` and that does not
start with a frontmatter, read the current date and time from the clock, rename it to
`notes/YYYY-MM-DD-HHMMSS-<slug>.md`, prepend a frontmatter, commit, and print the
new path relative to the harness root. The body SHALL be kept character for
character, with its line endings made LF and a leading byte-order mark dropped, so
that a note holds one convention whatever wrote the draft; a draft that is not UTF-8
SHALL be refused. The command SHALL refuse, changing nothing, when the file is not
directly under `notes/`, when its name is not a slug, when it already starts with a
frontmatter, or when the target name already exists.

#### Scenario: Note filed
- **WHEN** `notes/login-trace.md` holds a body with no frontmatter and `gemba harness note notes/login-trace.md --type finding` runs on 2026-09-30
- **THEN** the file is now `notes/2026-09-30-HHMMSS-login-trace.md` with the run's time, its content is a frontmatter followed by the original body unchanged, no `notes/login-trace.md` remains, and the command prints the new path

#### Scenario: Draft with CRLF filed
- **WHEN** `notes/login-trace.md` holds a body whose lines end with CRLF, starting with a UTF-8 byte-order mark, and `gemba harness note notes/login-trace.md --type finding` runs
- **THEN** the filed note holds the frontmatter followed by the body with every line ending in LF and no byte-order mark, character for character otherwise, and the command exits 0

#### Scenario: Draft that is not UTF-8 refused
- **WHEN** the draft is encoded in UTF-16
- **THEN** the command exits 1, says the draft is not UTF-8 text, and changes nothing

#### Scenario: Draft outside notes or misnamed refused
- **WHEN** the file is not directly under the harness `notes/`, or its name is not a slug followed by `.md`
- **THEN** the command exits 1, names the rule the path breaks, and changes nothing

#### Scenario: Reserved device name refused
- **WHEN** the draft is `notes/aux.md` or `notes/com1.md`, on any platform
- **THEN** the command exits 1, says the name is reserved on Windows, and changes nothing

#### Scenario: Already filed note refused
- **WHEN** the file given already starts with a frontmatter
- **THEN** the command exits 1, reports that the note is already filed, and changes nothing

### Requirement: Note frontmatter
The frontmatter of a filed note SHALL hold, in this order: `type`; `date`, the filing
date as an ISO date; `time`, the filing time as `HH:MM:SS`; `approved: false`, present
only when the note is gated; and `assets`, a list of asset paths relative to the
harness root, present only when assets were given. `resolve` MAY append `resolved_at`.
No other key SHALL be written, and agents SHALL NOT write or edit the frontmatter of a
note.

#### Scenario: Frontmatter of a plain note
- **WHEN** a `finding` note is filed on 2026-09-30 at 15:30:12 without assets
- **THEN** its frontmatter is exactly `type: finding`, `date: 2026-09-30`, `time: "15:30:12"`, between `---` lines

#### Scenario: Frontmatter of a gated note with assets
- **WHEN** an `external-action` note is filed with `--asset assets/1759350491-console.log`
- **THEN** its frontmatter holds `type`, `date`, `time`, `approved: false` and `assets: [assets/1759350491-console.log]`, in that order

### Requirement: Note types and the approval gate
The type SHALL be one of `finding` (what is true and the evidence for it), `blocker`
(why the run cannot continue, what was tried, what is needed), `decision` (the options,
their trade-offs and the recommendation or the choice), `summary` (where the run stands
at a milestone and what remains) and `external-action` (something to be done outside
the harness, word for word). The gate SHALL follow the type: an `external-action` SHALL
always be filed with `approved: false`; a `decision` SHALL be filed with `approved:
false` only when `--approval` is given; `--approval` SHALL be refused for `finding`,
`blocker` and `summary`. An unknown type SHALL be refused, naming the known types. The
command's help SHALL list the types with their one-line definitions.

#### Scenario: External action always gated
- **WHEN** an `external-action` note is filed without `--approval`
- **THEN** its frontmatter holds `approved: false`

#### Scenario: Decision gated on request
- **WHEN** a `decision` note is filed with `--approval`, and another without it
- **THEN** the first holds `approved: false` and the second has no `approved` key

#### Scenario: Approval refused for ungated types
- **WHEN** `--approval` is given with type `finding`, `blocker` or `summary`
- **THEN** the command exits 1, says that type takes no approval, and changes nothing

#### Scenario: Unknown type refused
- **WHEN** `--type` is not one of the five types
- **THEN** the command exits 1, names the known types, and changes nothing

### Requirement: Assets are saved by the agent and referenced by the command
Assets SHALL be files the agent or the user saves under `assets/` of the harness, named
`<unix-timestamp>-<slug>.<ext>` with the timestamp taken from the system clock. `gemba
harness note` SHALL accept each `--asset` as a path under `assets/` of the harness,
relative to the harness root, SHALL refuse, changing nothing, when a given asset does
not exist or is not under `assets/`, and SHALL list the given assets in the
frontmatter. The command SHALL NOT copy, move or rename an asset.

#### Scenario: Asset referenced
- **WHEN** `assets/1759350491-console.log` exists and a note is filed with `--asset assets/1759350491-console.log`
- **THEN** the frontmatter lists it under `assets` and the file is left as it was

#### Scenario: Missing or misplaced asset refused
- **WHEN** a `--asset` names a file that does not exist, or one outside `assets/`
- **THEN** the command exits 1, names the asset, and changes nothing

### Requirement: Filing commits the note and the assets
`gemba harness note` SHALL stage `notes/` and `assets/` of the harness and commit them
in one commit whose message is `note <type> <slug>`, so that a filed note is never
left uncommitted and the assets it references travel with it. `launch` SHALL commit as
`launch <ref>` and `resolve` as `resolve <slug>`.

#### Scenario: Note committed
- **WHEN** a note is filed in a harness with one launch commit
- **THEN** the harness repository has two commits, the latest with message `note finding login-trace`, and the working tree is clean

### Requirement: Resolving a gated note
`gemba harness resolve <note>` SHALL take a filed note under `notes/` of the harness
that holds `approved`, SHALL refuse, changing nothing, when the note is not filed, has
no `approved` key, has `approved` other than `true`, or already holds `resolved_at`,
and otherwise SHALL append `resolved_at`, the current date and time as an ISO 8601
string, to the frontmatter, commit `notes/` and `assets/`, and print the note path.
The body is the agent's: the command SHALL leave it as it finds it.

#### Scenario: Approved note resolved
- **WHEN** a filed `external-action` note holds `approved: true` and `gemba harness resolve` runs on it
- **THEN** its frontmatter gains `resolved_at` as the last key, the body is unchanged, the harness repository gains a commit with message `resolve <slug>`, and the command exits 0

#### Scenario: Unapproved note refused
- **WHEN** the note holds `approved: false`
- **THEN** the command exits 1, says the note is not approved, and changes nothing

#### Scenario: Ungated or resolved note refused
- **WHEN** the note has no `approved` key, or already holds `resolved_at`
- **THEN** the command exits 1, says why, and changes nothing

#### Scenario: Approval is set by the user in the file
- **WHEN** a gated note awaits approval
- **THEN** only the user changes `approved` to `true`, editing the note in the IDE; a request in the conversation is not an approval

### Requirement: Notes by the agent
The `gemba-harness` skill SHALL have the agent write each note as a file directly under
`notes/` with its own tools, choose the type by the question the note answers, file it
with `gemba harness note` passing the assets it references, and never write a
frontmatter, a date or a timestamp into a note by hand. Before acting on a gated note
the agent SHALL read its frontmatter and SHALL act only when `approved` is `true`;
after acting it SHALL append what was done and where to the body, with its own tools,
and run `gemba harness resolve` on the note. The skill SHALL have the agent read the
`harness.note` or `harness.resolve` block of the task's workstream in the gemba config
before running that verb and follow its `rules`.

#### Scenario: Agent files a note
- **WHEN** the agent has something to record
- **THEN** it writes the draft under `notes/`, saves any evidence under `assets/` with a timestamp name, runs `gemba harness note` with the type and the assets, and relays the filed path

#### Scenario: Agent acts on an approved note
- **WHEN** the user has set `approved: true` on an `external-action` note
- **THEN** the agent performs the action, appends the outcome to the note body and runs `gemba harness resolve` on it

#### Scenario: Agent follows the verb's rules
- **WHEN** the task's workstream declares `harness.note.rules`
- **THEN** the agent follows them while drafting and filing a note
