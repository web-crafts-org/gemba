# Design

## Context

See proposal.md for the motivation. What shapes the approach:

- The CLI is already close to portable: every read and write names UTF-8, the
  config, the skills and the guide are written with `newline="\n"`, stored and
  printed paths go through `PurePosixPath` and `as_posix()`, git runs from an
  argument list, never a shell, and the case runner already uses `os.pathsep` and
  `shutil.which`. The gaps are few and local: `task.md` is created with
  `symlink_to` (`commands/harness.py`), the harness is deleted with a bare
  `shutil.rmtree`, the IDE is started with `Popen` after a POSIX `shlex.split` and
  detached with `start_new_session`, which Windows ignores, `create.py` opens the
  task file without `newline="\n"`, `record.py` and the task start of `launch` read
  bytes and split on `\n`, and `cli.py` never touches the encoding of the standard
  streams, which Python 3.11 to 3.14 take from the console code page on Windows when
  the output is a pipe.
- The case runner stubs `code` with a `#!/bin/sh` script, checks `task.md` with
  `os.readlink`, and the IDE case expects the absolute path to start with `/`.
- GitHub's Windows runners run with administrator rights: they create symbolic links,
  so the file fallback of `task.md` cannot be exercised by a case on the CI.
- The tasks repo is personal and its harnesses are ignored by it, so the only files
  that travel between platforms are the task files, `gemba.yaml` and the skills; the
  paths they hold are already POSIX and relative.
- Seven skills tell the agent to read the date with `date +%F`, a POSIX command.
  Claude Code on Windows runs its Bash tool through Git Bash, where it works, but
  falls back to PowerShell without it.

## Goals / Non-Goals

**Goals:**
- One rule per concern, the same on every platform, decided by what the system does
  rather than by the name of the operating system.
- Every platform rule in one domain module, so no adapter carries a platform check
  of its own and the rules are unit-tested where a case cannot reach them.
- The CI proves the contract under the defaults of a Windows install rather than
  under a neutralized git.

**Non-Goals:**
- A table of IDE and agent tools with a style per tool, as OpenSpec's `openers`: this
  change only gives `ide` the shape such a table row has.
- Multi-root workspaces, or opening the tasks repo beside the harness.
- Making the developer tooling of this repository (pre-commit hooks written for
  `bash`) run on Windows: contributors on Windows use Git Bash, which the hooks
  assume; the CI is what checks a contribution.
- Any change to what a tasks repo stores.

## Decisions

### D1. A `platform` domain module owns every platform rule

`src/gemba/platform.py`, a domain module with no side effects, owns: the reserved
device names of Windows and `is_reserved_name()`; `decode()` for the read side of the
text contract, which decodes UTF-8 and turns CRLF and CR into LF; the detached-start
options of a child process (`start_new_session` on POSIX, `DETACHED_PROCESS` with
`CREATE_NEW_PROCESS_GROUP` on Windows) as a mapping of `Popen` keyword arguments;
the classification of a deletion error (read-only to clear, path held to retry,
anything else to report); the retry schedule of a held path; and the git hints
(`long_path_hint` beside the identity hint moved from `commands/harness.py` into a
`git_hints()` of `harness.py`). Alternative: a check per adapter next to each call.
Rejected: it spreads `os.name` across four files and leaves the rules untestable
without a Windows machine.

### D2. `task.md` is decided by the system, not the platform

`harness.task_link_content(task)` (domain) renders the file form: the same relative
POSIX path `task_link_target()` renders, plus a newline. The adapter `write_layout`
tries `symlink_to` first and, on `OSError`, writes the file with `write_new`. No
`os.name` check: a Windows user with developer mode gets the link, as git itself
decides `core.symlinks` by probing. Alternative: the file form on Windows always.
Rejected: it refuses the link to who can create it and names a platform in a rule.
The link creation is a seam of the adapter, injectable in the unit test that makes
it fail. `harness remove` treats `task.md` as any file: `rmtree` deletes a link
without following it on both platforms, so nothing changes there beyond the wording.

### D3. `ide` is parsed once into a command and its arguments

`config.py` parses `ide` into an `Ide` frozen dataclass, `command` and `args`, from
the string (`shlex.split` in POSIX mode on every platform, so the one quoting rule is
"a path with spaces or backslashes goes between quotes") or from the map; it keeps
the declaration as written for `config show`, which prints the config as declared.
`open_ide` (adapter) resolves `command` with `shutil.which`, which honours `PATHEXT`
on Windows and finds `code.cmd` for `code`; a `None` is the "could not be started"
failure before anything starts, the same message the `OSError` path prints today.
It starts `[executable, *args, folder]` with the detached options of D1 and prints
`opening: <command> <args...> <folder>` from the declaration, never the resolved
executable, so the printed line is the same on every platform. Alternative: split
with Windows rules on Windows. Rejected: no standard library implements them and the
spec would describe two rules. A later change adds `style` and the tools table on top
of this shape without touching the string form.

### D4. The text contract is enforced at the boundaries

Reads: every `read_bytes().decode()` of a task file or a draft, in `record.py` and in
`commands/harness.py`, goes through `platform.decode()`; `read_text` reads already
normalize through universal newlines and keep doing so. Writes: `create.py` opens
with `newline="\n"`; every other write already emits LF because it writes the text
it composed, which now holds no CR. The body of a draft filed as a note goes through
`platform.decode()` too, which also drops a leading byte-order mark, so a note holds
one convention whatever wrote the draft: the agent's write tool emits LF, but a draft
saved through PowerShell comes with CRLF and, on 5.1, a byte-order mark or UTF-16,
the latter still refused as not UTF-8. Normalizing at filing is what makes `resolve`
a frontmatter rewrite that never changes the body: it reads through the same
`decode()` and would otherwise turn a CRLF body into LF only when the note is
resolved. The boundary is the vocabulary's: notes are text gemba composes, assets
are the raw bytes it never touches, so a body needing its carriage returns belongs
under `assets/`. Alternative: keep the body byte for byte, as the notes spec said.
Rejected: it yields files with two conventions, LF frontmatter and CRLF body, which
editors rewrite whole and git diffs fill with `^M`. Output:
`cli.main` reconfigures `sys.stdout` and `sys.stderr` to UTF-8 before dispatching,
guarded for streams that lack `reconfigure` (a replaced stream in a test); this is
the output seam of the CLI. Python 3.15 makes UTF-8 the default; until the oldest
supported version is 3.15 the reconfigure stays. The case runner decodes the output
of the command as UTF-8 explicitly, so the cases read the same bytes on every runner.

### D5. `.gitattributes` mirrors the `.gitignore` of the scaffold

`repo.py` gains `GITATTRIBUTES_LINES` (`*.md text eol=lf`, `*.yaml text eol=lf`) and
`gitattributes_text(existing)` with the same contract as `gitignore_text`: `None`
when every line is present, the text with the missing lines appended otherwise.
`init.py` writes it after the `.gitignore`, reports `written`, `updated` or `kept`.
The scope is the files gemba owns, not `*`, so an asset a person keeps in the tasks
repo is not renormalized. On an existing repo checked out with CRLF on Windows, the
first commit after `gemba init` adds the file renormalizes `*.md` and `*.yaml`; the
README says so and names `git add --renormalize .`.

### D6. Deletion is a policy, performed by one adapter function

`commands/harness.py` gains `delete_tree(folder, *, rmtree=shutil.rmtree,
sleep=time.sleep) -> str | None`: it runs `rmtree` with an error handler
(`onexc` from Python 3.12, `onerror` on 3.11, chosen at import by `sys.version_info`)
that clears the read-only bit and retries the unlink; a held path is retried on the
schedule of `platform.py`; what is still held is reported with the message the spec
words. `rmtree` and `sleep` are the filesystem and clock seams, injected in the unit
test with a fake that keeps failing. `harness remove` calls it for the harness folder
and `worktree remove` wraps `git worktree remove` with the same retry and the same
message when git reports a held path, since git deletes the folder itself there. The
`Path.cwd()` refusal stays: on Windows a folder that is the working directory of any
process cannot be deleted, so the hint names a terminal beside the IDE.

### D7. Reserved names are refused where the name is validated

`config.py` refuses a workstream identifier that `platform.is_reserved_name()`
matches, with its own message ("reserved on Windows"), in the same pass that checks
kebab-case, so one call reports every problem. `harness.check_draft` does the same
for the slug of a draft. Task slugs are not checked: the task filename starts with
the date and the ref, so it is never a reserved name. Alternative: a check in
`tasks.is_valid_slug`, shared by both. Rejected: it would refuse task slugs that are
safe, and the two callers word their message for their own object.

### D8. The CI matrix covers the two axes

`ci.yml` keeps Linux on every supported Python, and runs macOS and Windows on 3.11
and 3.14, the extremes: 3.11 and 3.12 take different `rmtree` handlers, and the
output encoding changes course in 3.15. No step touches the runner's git, so Windows
runs with `core.autocrlf=true` and the CRLF cases prove the contract under the
default of a Windows install. The case runner writes a `code.cmd` stub beside the
shell stub, and the stub folder is first on PATH on every platform; `shutil.which`
in the runner and in `open_ide` resolves the right one. The runner gains a check for
a file holding no CR, used by the LF scenarios, since `files:` reads with universal
newlines and cannot see a CRLF. The IDE case stops assuming an absolute path starts
with `/`: it checks `opening: code -n ` and the harness folder name, separators aside.

### D9. The skills read the date without a shell

The seven skills that say `date +%F` say instead to read today's date from the
environment, naming `date +%F` for a POSIX shell and `Get-Date -Format yyyy-MM-dd`
for PowerShell. No spec names the command, so this is an asset edit; the copies in
tasks repos and harnesses follow through `gemba skills update` and the provenance
hash, as any skill edit.

## Risks / Trade-offs

- [The Windows CI runner creates symbolic links, so the file form of `task.md` is
  never exercised black-box] → the unit test injects a failing link creation; the
  scenario is in `not-automated.yaml` with that reason.
- [`os.readlink` on Windows may return the link target with backslashes or a prefix,
  failing the `links:` check of the case runner on the Windows job] → the runner
  compares targets as POSIX paths after normalizing separators; confirmed by the first
  Windows run of the suite.
- [The temporary folder of a Windows runner may be an 8.3 short name, and the
  worktree checks compare `resolve()`d paths with what git prints] → `resolve()`
  returns the long form on Windows since Python 3.8, as git does; if the first run
  disagrees, the comparison normalizes both sides through `resolve()`.
- [Antivirus or indexers on the Windows runner hold files briefly during deletion,
  making the removal cases flaky] → the retry schedule of D6 absorbs short holds; a
  persistent hold fails the case loudly rather than silently.
- [A `.cmd` IDE command runs through `cmd.exe`, which interprets metacharacters in
  arguments] → the only argument is the harness path, built from the tasks repo root
  and validated names; SECURITY.md states the qualification, and the threat model
  already puts what the `ide` command does on the person who wrote it.
- [`shlex` in POSIX mode eats unquoted backslashes, so `ide: C:\...\code.cmd` breaks
  silently into a wrong command] → the README states the quoting rule and the
  structured form exists for anyone who prefers no rule at all; the "could not be
  started" failure names the command it looked for.
- [Adding `.gitattributes` to an existing tasks repo renormalizes files on Windows
  checkouts] → `init` only adds it when run again on that repo, and the README names
  the renormalization step.

## Migration Plan

Nothing migrates. Existing harnesses keep their symbolic link; existing configs keep
their string `ide`; existing tasks repos get a `.gitattributes` only when `gemba init`
runs on them again. The change ships in the next release with its changelog entry
and the Windows classifier; no rollback beyond releasing the previous version.

## Open Questions

- Whether `os.readlink` on Windows returns a relative target exactly as given. The
  first Windows run of the suite answers it; only the normalization in the case
  runner depends on the answer, not a spec or a task.
