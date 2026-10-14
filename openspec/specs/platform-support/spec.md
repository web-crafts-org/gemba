# platform-support Specification

## Purpose

The promises that belong to no single command: which platforms Gemba runs on and
with what prerequisites, the text contract every command honours, and the
portability of what gemba names and writes, so that a tasks repo and a harness move
between platforms.

## Requirements

### Requirement: Supported platforms
The gemba CLI SHALL run on Linux, macOS and Windows 10 or later, needing only Python
3.11 or later and `git` on PATH, with no administrator rights, no developer mode and
no particular shell, and SHALL behave the same on every platform: same commands,
same output, same exit codes. A tasks repo or a harness created on one platform
SHALL be usable on another.

#### Scenario: Suite passes on every platform
- **WHEN** a commit is pushed or a pull request is opened
- **THEN** the full test suite passes on Linux, on macOS and on Windows

#### Scenario: Tasks repo used across platforms
- **WHEN** a tasks repo created on Linux, with its tasks and its config, is cloned on Windows
- **THEN** every command reads its tasks, creates and marks tasks in it, and launches a harness, with no edit to any file

### Requirement: Lines written end with LF
Every file gemba writes or rewrites, a task file, a note, a config, a guide, a skill
or a harness file, SHALL end each of its lines with LF, on every platform, whatever
the line endings the file or the draft had before. Assets, which gemba never writes,
are the only raw bytes of a harness.

#### Scenario: Task file created with LF
- **WHEN** `gemba create` writes a task file on any platform
- **THEN** no line of the file ends with CRLF

#### Scenario: Task file with CRLF rewritten with LF
- **WHEN** a task file whose lines end with CRLF is recorded with `gemba record`
- **THEN** every line of the file ends with LF afterwards and the content is what the recording produces

### Requirement: Files read accept CRLF
Every file gemba reads, a task file, a draft, a note, a config or a harness config,
SHALL be accepted with CRLF line endings and read as if its lines ended with LF, so
that a checkout made with `core.autocrlf=true` works like any other.

#### Scenario: Task file with CRLF recorded
- **WHEN** a task file whose lines end with CRLF holds an `## Updates` section and `gemba record` runs for it
- **THEN** the section is found, the update is inserted as for an LF file, and the command exits 0

#### Scenario: Task file with CRLF started
- **WHEN** an `open` task whose file has CRLF line endings is launched
- **THEN** its frontmatter is rewritten to `status: in-progress` and the body is kept, line endings aside

### Requirement: Output is UTF-8
The standard output and the standard error of every command SHALL be encoded in UTF-8
on every platform, whether they go to a terminal or to a pipe, whatever the console
code page, so that a title or a value with any character reaches the agent intact.

#### Scenario: Non-ASCII text listed through a pipe
- **WHEN** a task whose description holds accented letters and an emoji is listed with `gemba list --json` and the output goes to a pipe
- **THEN** the JSON holds the description character for character and the command exits 0

#### Scenario: Non-ASCII error reported
- **WHEN** a command refuses a value that holds accented letters, such as an unknown workstream named with them
- **THEN** the error names the value character for character on the standard error

### Requirement: Names portable to every platform
Every name gemba validates that becomes a folder or file name, a workstream
identifier or a note slug, SHALL be refused, on every platform, when it is a reserved
device name of Windows: `con`, `prn`, `aux`, `nul`, `com0` to `com9` and `lpt0` to
`lpt9`, so that what one platform creates another can clone.

#### Scenario: Rule applied wherever a name is validated
- **WHEN** a reserved device name is given where gemba validates a workstream identifier or a note slug
- **THEN** the command refuses it on Linux, macOS and Windows alike

### Requirement: Long path failure hinted
When git fails because a path exceeds the length Windows allows by default, the
command SHALL relay git's message and add a hint naming `git config --global
core.longpaths true`, as it adds the identity hint when git lacks a user identity.

#### Scenario: Git failure on a long path hinted
- **WHEN** a git command run by gemba fails with a message saying a filename is too long
- **THEN** the output holds git's message followed by the hint naming `core.longpaths`
