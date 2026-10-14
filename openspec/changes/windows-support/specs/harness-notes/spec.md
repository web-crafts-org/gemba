# Spec Delta

## MODIFIED Requirements

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
- **Cases**: keeps `tests/cases/harness/note-filed.yaml`

#### Scenario: Draft with CRLF filed
- **WHEN** `notes/login-trace.md` holds a body whose lines end with CRLF, starting with a UTF-8 byte-order mark, and `gemba harness note notes/login-trace.md --type finding` runs
- **THEN** the filed note holds the frontmatter followed by the body with every line ending in LF and no byte-order mark, character for character otherwise, and the command exits 0
- **Cases**: adds `tests/cases/harness/draft-with-crlf-filed.yaml`

#### Scenario: Draft that is not UTF-8 refused
- **WHEN** the draft is encoded in UTF-16
- **THEN** the command exits 1, says the draft is not UTF-8 text, and changes nothing
- **Cases**: adds `tests/cases/harness/draft-not-utf-8-refused.yaml`

#### Scenario: Draft outside notes or misnamed refused
- **WHEN** the file is not directly under the harness `notes/`, or its name is not a slug followed by `.md`
- **THEN** the command exits 1, names the rule the path breaks, and changes nothing
- **Cases**: keeps `tests/cases/harness/draft-outside-notes-or-misnamed-refused.yaml`

#### Scenario: Reserved device name refused
- **WHEN** the draft is `notes/aux.md` or `notes/com1.md`, on any platform
- **THEN** the command exits 1, says the name is reserved on Windows, and changes nothing
- **Cases**: adds `tests/cases/harness/reserved-note-slug-refused.yaml`

#### Scenario: Already filed note refused
- **WHEN** the file given already starts with a frontmatter
- **THEN** the command exits 1, reports that the note is already filed, and changes nothing
- **Cases**: keeps `tests/cases/harness/already-filed-note-refused.yaml`
