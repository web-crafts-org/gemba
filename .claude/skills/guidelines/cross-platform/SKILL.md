---
name: cross-platform
description: This skill should be used when designing or writing gemba code or tests that print, compare, store or link a path, read or write a text file, name a file or folder, or start a process, before that code is written, so that it holds on Windows as it does on Linux and macOS.
---

# Cross-platform

Gemba runs on Linux, macOS and Windows, and the CI tests all three, but a change is
written and tested on one of them. A line that holds on Linux and breaks on Windows
passes every local gate and the pre-push hook, and fails only in the Windows jobs of
the pull request, one round trip later.

Origin: the first Windows run of the CI (windows-support, PR #13, fixed in `3ae5c82`)
failed on unit tests that spelled an absolute path with `/`, on a symbolic link whose
target held `/`, and on a case that wrote files with reserved names before its setup
ran `git add -A`. The rules of that change were written in its design, archived since,
which no agent reads when it writes the next change: in personal-config-layer
(PR #16) a new unit test spelled `/r/gemba.yaml` in an expected message, and the two
Windows jobs failed on it. The rules below are those failures and the gaps the
windows-support design found in the code, each shown with gemba's own code.

## Rule 1: an absolute path is printed in the form of the system, and a test builds it the same way

A message renders an absolute path with `str()`, so on Windows `Path("/r/gemba.yaml")`
prints as `\r\gemba.yaml`. A test that compares that message with a literal spelled
with `/` passes on Linux and macOS only. Build the expected text from the same `Path`
objects.

```
WRONG  error = config.ConfigError(problems=[(Path("/r/gemba.yaml"), "one")])
       self.assertEqual(str(error), "invalid gemba config:\n- /r/gemba.yaml: one")
RIGHT  shared = Path("/r/gemba.yaml")
       error = config.ConfigError(problems=[(shared, "one")])
       self.assertEqual(str(error), f"invalid gemba config:\n- {shared}: one")
```

A class that tests many messages names its path once, as `REPOS = Path("/r")` in
`tests/test_worktree.py`. A case never assumes an absolute path starts with `/`: it
uses the `{root}` token and checks the rest separately, as
`tests/cases/harness/ide-opened.yaml` checks `opening: code -n {root}` and the harness
folder name.

## Rule 2: a path stored in a file or printed relative to a root is POSIX

What gemba writes into a task, a harness or `gemba.yaml`, and every path it prints
relative to a root, reads the same on every platform: build it with `PurePosixPath`
or render it with `as_posix()`.

```
WRONG  relative = str(target.relative_to(gemba_config.root))   # tasks\support\... on Windows
RIGHT  relative = target.relative_to(gemba_config.root).as_posix()
```

As `commands/create.py`, `worktree.relative_path` and `harness.task_link_target` do.
Only absolute paths keep the form of the system (Rule 1).

## Rule 3: a symbolic link is created with the separators of the system

Windows creates a link whose target holds `/`, but the link resolves to nothing. Create
links through `symlink()` of `commands/harness.py`, which turns the POSIX target into a
`Path` first; compare link targets as POSIX paths after normalizing the separators,
since `os.readlink` on Windows may return backslashes or a prefix.

```
WRONG  path.symlink_to(harness.task_link_target(task))
RIGHT  symlink(path, harness.task_link_target(task))   # path.symlink_to(Path(target))
```

## Rule 4: a name a person chooses may be reserved on Windows

`con`, `prn`, `aux`, `nul`, `com0` to `com9` and `lpt0` to `lpt9`, with or without an
extension, are device names on Windows, as `platform.RESERVED_NAMES` lists them. Validate a name that becomes a file or folder with
`platform.is_reserved_name()`, where the other checks of that name run, as `config.py`
does for a workstream and `harness.check_draft` for a note slug. In a case, a file with
such a name goes under `tree_after_setup`, never `tree`: Git for Windows refuses to
open it, so a setup that runs `git add -A` fails before the command under test runs
(`tests/cases/harness/reserved-note-slug-refused.yaml`).

## Rule 5: text is UTF-8 with LF, whatever the platform does

- Every read and write names `encoding="utf-8"`.
- Every write of text passes `newline="\n"`, as `create.py`, `init.py`, `skills.py` and
  `harness.py` under `commands/` do; without it Windows writes CRLF.
- A file gemba reads as bytes goes through `platform.decode()`, which turns CRLF and CR
  into LF and drops a byte-order mark; never `read_bytes().decode()` followed by a split
  on `"\n"`. The Windows CI runs git with `core.autocrlf=true`, so a checked-out file
  holds CRLF there.
- A case that requires a file to end its lines with LF lists it under `lf_only`, since
  `files:` reads with universal newlines and cannot see a CR.

## Rule 6: a process starts from an argument list, and a platform rule lives in `platform.py`

- Run git and every other program from an argument list, never through a shell.
- Resolve an executable with `shutil.which`, which honours `PATHEXT` on Windows and
  finds `code.cmd` for `code`; a bare `Popen(["code", ...])` does not.
- Detach a child with the options of `platform.detached_start()`;
  `start_new_session` alone is ignored on Windows.
- Delete a folder through `delete_tree` of `commands/harness.py`, which clears the
  read-only bit and retries a path another process holds; a bare `shutil.rmtree` fails
  on both on Windows.
- An adapter never checks `os.name` itself: a new platform rule goes into
  `src/gemba/platform.py`, the domain module that owns them, with its unit test.

## Before calling the work done

The local suite cannot see any of these failures; check the diff instead:

1. `git diff -- tests | grep -n 'Path("/'`: for every hit, the expected text that
   names that path is built from the same `Path` (Rule 1).
2. Every new `write_text` or `open(..., "w")` of text passes `encoding="utf-8"` and
   `newline="\n"`, and every new read of bytes goes through `platform.decode()`
   (Rule 5).
3. Every new path written to a file or printed relative to a root goes through
   `as_posix()` or `PurePosixPath` (Rule 2).
4. Every new name that becomes a file or folder is checked with
   `platform.is_reserved_name()` (Rule 4), and every new process starts from a list,
   resolved with `shutil.which` (Rule 6).

## In the OpenSpec flow

- **Design**: say how the change prints, stores or links each new path, which text it
  reads or writes, and which rule of `platform.py` it uses or adds.
- **Apply**: read this guideline before writing a test or code that touches any of the
  above, and run the checks of the previous section before marking the task done.
- The Windows jobs of the CI stay the proof; this guideline is what keeps them from
  being the first to see the failure.
