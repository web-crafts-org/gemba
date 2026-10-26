"""Black-box case runner: the executable specification of the gemba commands.

Every `cases/<process>/*.yaml` file covers one spec scenario and may hold several
YAML documents, one case each. A case uses this vocabulary:

- `name`: short case name, shown when the case fails.
- `scenario`: the spec scenario it covers, as `<capability>: <scenario title>`.
- `config`: content of `gemba.yaml`, as a map or as raw text; omitted means no config.
- `local_config`: content of `gemba.local.yaml`, the personal config, written like
  `config`; omitted means no personal config.
- `repos`: git repositories to build before `tree`, each name mapped to `branches`
  (each branch name mapped to its files, as `path: content`), `default` (the default
  branch of the remote, the first branch when omitted) and `unfetched` (branches
  mapped to files, as `branches`). For each name the runner creates the bare remote
  `remotes/<name>.git`, with one commit per branch, subject `add <branch>`, holding
  exactly the files declared for it and whose parent is the commit of the default
  branch; it clones it to `repos/<name>`, so `origin` is a file URL, `origin/HEAD` is
  the default branch and that branch is checked out; and it then pushes one commit per
  `unfetched` branch, subject `unfetched <branch>`, adding its files to the tip of the
  branch, so that the clone is behind its remote. A case declares `repos_dir: repos`
  in `local_config`.
- `tree`: files to create before running, as `path: content`. The content is written
  as UTF-8 with its line endings as given, so `\r\n` escapes make a CRLF file; a
  `!!binary` value is written as those bytes, for a file in another encoding.
- `run`: command name followed by its arguments; the name is resolved through COMMANDS,
  or is `git`, run as `git <arguments>` in `cwd`, which it requires, with no `--root`
  and the environment every command gets, so that a case runs a `git push` or a
  `git pull` and the hooks it triggers.
- `stdin`: text given to the standard input of the `run` command, as UTF-8 bytes with
  its newlines as written on every platform, as git gives a hook; without it the
  command gets an empty input, never the one of the suite, which a hook may have given.
- `cwd`: folder, relative to the root, to start the command from. When present,
  `--root` is not passed, so the command must discover the root by walking up.
- `setup`: commands, each written like `run`, `git` included, run in order before the
  snapshot that `unchanged` compares with, each with an empty input; each must exit 0.
- `tree_after_setup`: files to create like `tree`, after the `setup` commands and
  before the snapshot, so that a file can sit uncommitted in a harness that a `launch`
  in `setup` created and committed.
- `git_after_setup`: git commands run after `tree_after_setup` and before the
  snapshot, each written as the repository path, relative to the root, followed by the
  arguments of git; each must exit 0. `{root}` in an argument stands for the root.
- `exit`: expected exit code.
- `stdout`: the exact expected standard output.
- `stdout_contains`, `stderr_contains`: strings the output must contain.
- `stderr_excludes`: strings standard error must not contain, for a message that must
  not appear.
- `stdout_json`: the document standard output must hold, written as YAML. Both sides
  are compared as parsed JSON, so indentation and key order do not matter while every
  key, value, type and list order does. Unquoted YAML dates stand for ISO strings.
- `files`: paths with their exact expected content.
- `files_contain`: paths with the strings each file must contain, for files whose
  full content the case should not embed. A path may be a glob, for files named after
  the clock, and must then match exactly one file.
- `lf_only`: paths whose bytes hold no CR, for a file that must end its lines with LF;
  `files` cannot tell, since it reads with universal newlines. A path may be a glob,
  for files named after the clock, and must then match exactly one file.
- `absent`: paths that must not exist. A path may be a glob, which must match nothing,
  so `<folder>/*` checks that a folder is empty.
- `folders`: paths that must be folders.
- `links`: paths that must be symbolic links, each with its exact target, compared as
  POSIX paths whatever separator the system reports.
- `git_log`: git repositories, each path relative to the root, with the subjects of
  their commits, newest first, as `git log --format=%s` prints them.
- `git_clean`: git repositories whose working tree must have nothing to commit and no
  untracked file, as `git status --porcelain` reports it.
- `git_branches`: git repositories, bare ones included, each with the exact list of
  its local branches in sorted order.
- `unchanged`: when true, the tree must be identical to the one before running.

The token `{today}` in `files`, `files_contain`, `lf_only`, `absent`, `folders` and
`links` paths and contents, and in the expected output (`stdout_json` included), stands
for the current date, so a case can check the default date. The token `{version}`, in
the same places, stands for the version of the installed gemba CLI package, and
`{root}` for the absolute path of the root the case runs in, as the system spells it.

The token `{rev:<path>:<revision>}` stands for the full id of the commit `<revision>`
names in the git repository at `<path>`, relative to the root, and `{short:<path>:
<revision>}` for its short id, as `git rev-parse --short` and `%h` abbreviate it there.
Both are resolved once, after `git_after_setup` and before `run`, in `run`, `stdin`,
`stdout`, `stdout_contains` and `stderr_contains`, so that a case gives and expects the
id of a commit made while it runs.

Git must be on PATH: harness commands run it. Every command runs with the user's and
the system's git config ignored, a fixed identity and none of the variables that tie
git to a repository, so commits never depend on the machine running the suite, and a
suite run from a git hook never reaches the repository of the hook. The IDE is never
started: every command runs with a stub for each name in STUBS first on PATH, a shell
script and a `.cmd` script side by side so that the stub resolves on every platform,
each exiting 0 and doing nothing. The output of every command is decoded as UTF-8, the
encoding gemba promises.
"""

import datetime
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

CASES_DIR = Path(__file__).parent / "cases"

# A port of the CLI is done when every case passes with this table pointing at it.
COMMANDS = {
    "init": ["gemba", "init"],
    "create": ["gemba", "create"],
    "list": ["gemba", "list"],
    "skills": ["gemba", "skills"],
    "harness": ["gemba", "harness"],
    "record": ["gemba", "record"],
    "mark": ["gemba", "mark"],
    "archive": ["gemba", "archive"],
    "report": ["gemba", "report"],
    "set": ["gemba", "set"],
    "worktree": ["gemba", "worktree"],
    "config": ["gemba", "config"],
    "sync": ["gemba", "sync"],
    "hook": ["gemba", "hook"],
    # Not a subcommand: the option of the command itself, run with no subcommand.
    "--version": ["gemba", "--version"],
}
VERSION = importlib.metadata.version("gemba-cli")
GIT_ENVIRONMENT = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    # No background maintenance: a detached gc would rewrite .git/objects between the
    # snapshots of a case, under no control of the command under test.
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": "gc.auto",
    "GIT_CONFIG_VALUE_0": "0",
    "GIT_CONFIG_KEY_1": "maintenance.auto",
    "GIT_CONFIG_VALUE_1": "false",
    "GIT_AUTHOR_NAME": "Gemba Cases",
    "GIT_AUTHOR_EMAIL": "cases@gemba.invalid",
    "GIT_COMMITTER_NAME": "Gemba Cases",
    "GIT_COMMITTER_EMAIL": "cases@gemba.invalid",
}
# The variables that tie git to one repository, as `git rev-parse --local-env-vars` lists
# them, dropped from the inherited environment as git drops them on entering another one:
# a hook run from a linked worktree exports GIT_DIR, which would point every git of a case
# at that repository.
GIT_LOCAL_VARIABLES = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
        "GIT_OBJECT_DIRECTORY",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_GRAFT_FILE",
        "GIT_INDEX_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_REPLACE_REF_BASE",
        "GIT_PREFIX",
        "GIT_SHALLOW_FILE",
        "GIT_COMMON_DIR",
    }
)
GLOB_CHARACTERS = "*?["
# The name of `run` and `setup` that runs git itself rather than a gemba command.
GIT = "git"
# `{rev:<path>:<revision>}` and `{short:<path>:<revision>}`: the full or short id of a commit made while a case runs.
REVISION_TOKEN = re.compile(r"\{(rev|short):([^:{}]+):([^{}]+)\}")
# The keys whose tokens of a revision are resolved before the command runs.
REVISION_KEYS = ("run", "stdin", "stdout", "stdout_contains", "stderr_contains")
# Executables the cases may name in a config, such as `ide: "code -n"`, replaced by stubs.
STUBS = ("code",)
_STUBS_DIR = tempfile.TemporaryDirectory(prefix="gemba-stubs-")
for _stub in STUBS:
    _path = Path(_STUBS_DIR.name) / _stub
    _path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8", newline="\n")
    _path.chmod(0o755)
    _path.with_suffix(".cmd").write_text("@exit /b 0\r\n", encoding="utf-8", newline="")


def load_cases():
    for path in sorted(CASES_DIR.rglob("*.yaml")):
        documents = [doc for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")) if doc]
        for index, case in enumerate(documents, start=1):
            suffix = f"_{index}" if len(documents) > 1 else ""
            test_name = f"test_{path.parent.name}_{path.stem}{suffix}".replace("-", "_")
            yield test_name, path.relative_to(CASES_DIR), case


def snapshot(root):
    """Every path under `root` mapped to its bytes, or None for folders."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


def expand(text, root=None):
    """`text` with `{today}` and `{version}` expanded, and `{root}` when the root is given."""
    expanded = str(text).replace("{today}", datetime.date.today().isoformat()).replace("{version}", VERSION)
    return expanded if root is None else expanded.replace("{root}", str(root))


def expand_json(expected, root=None):
    """The expected document serialized to JSON, the tokens expanded, and parsed back."""
    return json.loads(expand(json.dumps(expected, default=lambda value: value.isoformat()), root))


def canonical(document):
    """One line per value with sorted keys, so a failed comparison shows a readable diff."""
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False)


def is_glob(relative):
    return any(character in relative for character in GLOB_CHARACTERS)


def environment():
    path = os.pathsep.join([_STUBS_DIR.name, os.environ.get("PATH", "")])
    inherited = {name: value for name, value in os.environ.items() if name not in GIT_LOCAL_VARIABLES}
    return {**inherited, **GIT_ENVIRONMENT, "PATH": path}


def write_tree(root, tree):
    """Create every file of `tree`, a map of path to content, under `root`, byte for byte as declared."""
    for relative, content in (tree or {}).items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else (content or "").encode("utf-8"))


def git(root, relative, *args):
    """Run git in the repository at `relative` without writing to it, not even the index."""
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(root / expand(relative)), *args],
        env=environment(),
        capture_output=True,
        encoding="utf-8",
        timeout=60,
    )


def branches(root, relative):
    """The local branches of the repository at `relative`, sorted, or None when git cannot read them."""
    result = git(root, relative, "branch", "--format=%(refname:short)")
    return sorted(result.stdout.splitlines()) if result.returncode == 0 else None


class CaseRunner(unittest.TestCase):
    """Builds the tree of a case, runs its command and checks the result; holds no test of its own."""

    maxDiff = None

    def run_case(self, source, case):
        label = f"[{case.get('name', source)}] ({source})"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, label)
            case = self.resolve_revisions(root, case, label)
            before = snapshot(root)
            result = self.execute(root, case, label, case["run"], case.get("stdin", ""))
            self.check(root, case, label, before, result)

    def prepare(self, root, case, label):
        """Build the tree the command runs in: `config`, `local_config`, `repos`, `tree`, `cwd`, the `setup`
        commands, `tree_after_setup` and `git_after_setup`."""
        self.materialize(root, case, label)
        for run in case.get("setup") or []:
            prepared = self.execute(root, case, label, run)
            self.assertEqual(prepared.returncode, 0, f"{label} setup {run}\n{prepared.stdout}{prepared.stderr}")
        write_tree(root, case.get("tree_after_setup"))
        for relative, *args in case.get("git_after_setup") or []:
            args = [expand(arg, root) for arg in args]
            self.run_git(root / expand(relative), *args, label=f"{label} git_after_setup")

    def materialize(self, root, case, label):
        for key, filename in (("config", "gemba.yaml"), ("local_config", "gemba.local.yaml")):
            if key in case:
                config = case[key]
                text = config if isinstance(config, str) else yaml.safe_dump(config, sort_keys=False)
                (root / filename).write_text(text, encoding="utf-8")
        for name, declaration in (case.get("repos") or {}).items():
            self.build_repository(root, name, declaration or {}, f"{label} repos {name}")
        write_tree(root, case.get("tree"))
        if "cwd" in case:
            (root / case["cwd"]).mkdir(parents=True, exist_ok=True)

    def build_repository(self, root, name, declaration, label):
        """The bare remote `remotes/<name>.git` and its clone `repos/<name>`, as `repos` describes them."""
        declared = declaration.get("branches") or {"main": {}}
        default = declaration.get("default") or next(iter(declared))
        self.assertIn(default, declared, f"{label}: default branch '{default}' is not declared")
        remote = root / "remotes" / f"{name}.git"
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp)
            self.run_git(scratch, "init", "--quiet", "--initial-branch", default, label=label)
            write_tree(scratch, declared[default])
            self.commit_all(scratch, f"add {default}", label)
            for branch, files in declared.items():
                if branch != default:
                    self.run_git(scratch, "checkout", "--quiet", "-b", branch, default, label=label)
                    self.run_git(scratch, "rm", "-r", "--quiet", "--ignore-unmatch", ".", label=label)
                    write_tree(scratch, files)
                    self.commit_all(scratch, f"add {branch}", label)
            remote.parent.mkdir(parents=True, exist_ok=True)
            self.run_git(root, "init", "--quiet", "--bare", "--initial-branch", default, str(remote), label=label)
            self.run_git(scratch, "push", "--quiet", str(remote), "refs/heads/*:refs/heads/*", label=label)
            clone = root / "repos" / name
            clone.parent.mkdir(parents=True, exist_ok=True)
            self.run_git(root, "clone", "--quiet", remote.as_uri(), str(clone), label=label)
            for branch, files in (declaration.get("unfetched") or {}).items():
                self.run_git(scratch, "checkout", "--quiet", branch, label=label)
                write_tree(scratch, files)
                self.commit_all(scratch, f"unfetched {branch}", label)
                self.run_git(scratch, "push", "--quiet", str(remote), branch, label=label)

    def commit_all(self, repository, subject, label):
        self.run_git(repository, "add", "-A", label=label)
        self.run_git(repository, "commit", "--quiet", "--allow-empty", "-m", subject, label=label)

    def run_git(self, cwd, *args, label):
        result = subprocess.run(
            ["git", "-C", str(cwd), *args], env=environment(), capture_output=True, encoding="utf-8", timeout=60
        )
        self.assertEqual(result.returncode, 0, f"{label}: git {' '.join(args)}\n{result.stdout}{result.stderr}")
        return result

    def resolve_revisions(self, root, case, label):
        """The case with every token of a revision in REVISION_KEYS replaced by the id of its commit."""

        def resolved(text):
            return REVISION_TOKEN.sub(lambda match: self.revision(root, *match.groups(), label=label), str(text))

        replaced = dict(case)
        for key in REVISION_KEYS:
            if key in case:
                value = case[key]
                replaced[key] = [resolved(item) for item in value] if isinstance(value, list) else resolved(value)
        return replaced

    def revision(self, root, kind, relative, revision, label):
        """The full id, or the short one for `short`, of the commit `revision` names in the repository at `relative`."""
        short = ["--short"] if kind == "short" else []
        result = git(root, relative, "rev-parse", "--verify", *short, f"{revision}^{{commit}}")
        self.assertEqual(
            result.returncode, 0, f"{label}: {{{kind}:{relative}:{revision}}} names no commit\n{result.stderr}"
        )
        return result.stdout.strip()

    def execute(self, root, case, label, run, stdin=""):
        name, *args = [str(arg) for arg in run]
        if name == GIT:
            self.assertIn("cwd", case, f"{label} run: git needs cwd, the repository it runs in")
            command = [GIT]
        else:
            self.assertIn(name, COMMANDS, f"{label} run: unknown command name '{name}'")
            command = COMMANDS[name]
        executable = shutil.which(command[0])
        if executable is None:
            self.fail(f"{label} run: '{command[0]}' is not on PATH")
        if "cwd" in case:
            cwd = root / case["cwd"]
        else:
            cwd = root
            args += ["--root", str(root)]
        # A file in binary mode, since input= in text mode turns "\n" into "\r\n" on Windows.
        with tempfile.TemporaryFile() as source:
            source.write(stdin.encode("utf-8"))
            source.seek(0)
            return subprocess.run(
                [executable, *command[1:], *args],
                cwd=cwd,
                env=environment(),
                stdin=source,
                capture_output=True,
                encoding="utf-8",
                timeout=60,
            )

    def check(self, root, case, label, before, result):
        output = f"\n--- stdout ---\n{result.stdout}--- stderr ---\n{result.stderr}"
        if "exit" in case:
            self.assertEqual(result.returncode, case["exit"], f"{label} exit{output}")
        if "stdout" in case:
            self.assertEqual(result.stdout, expand(case["stdout"], root), f"{label} stdout{output}")
        for expected in case.get("stdout_contains") or []:
            self.assertIn(expand(expected, root), result.stdout, f"{label} stdout_contains{output}")
        for expected in case.get("stderr_contains") or []:
            self.assertIn(expand(expected, root), result.stderr, f"{label} stderr_contains{output}")
        for unexpected in case.get("stderr_excludes") or []:
            self.assertNotIn(expand(unexpected, root), result.stderr, f"{label} stderr_excludes{output}")
        if "stdout_json" in case:
            try:
                actual = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                self.fail(f"{label} stdout_json: standard output is not JSON: {exc}{output}")
            expected = expand_json(case["stdout_json"], root)
            self.assertEqual(canonical(actual), canonical(expected), f"{label} stdout_json")
        for relative, expected in (case.get("files") or {}).items():
            path = root / expand(relative)
            self.assertTrue(path.is_file(), f"{label} files: {expand(relative)} does not exist{output}")
            actual = path.read_text(encoding="utf-8")
            self.assertEqual(actual, expand(expected, root), f"{label} files: {expand(relative)}")
        for relative, fragments in (case.get("files_contain") or {}).items():
            path = self.one_file(root, relative, "files_contain", label, output)
            actual = path.read_text(encoding="utf-8")
            for fragment in fragments:
                self.assertIn(expand(fragment, root), actual, f"{label} files_contain: {expand(relative)}")
        for relative in case.get("lf_only") or []:
            path = self.one_file(root, relative, "lf_only", label, output)
            self.assertNotIn(b"\r", path.read_bytes(), f"{label} lf_only: {expand(relative)} holds a CR byte")
        for relative in case.get("absent") or []:
            relative = expand(relative)
            if is_glob(relative):
                matches = sorted(match.relative_to(root).as_posix() for match in root.glob(relative))
                self.assertEqual(matches, [], f"{label} absent: {relative} matches")
            else:
                self.assertFalse((root / relative).exists(), f"{label} absent: {relative} exists")
        for relative in case.get("folders") or []:
            self.assertTrue((root / expand(relative)).is_dir(), f"{label} folders: {expand(relative)} is not a folder")
        for relative, target in (case.get("links") or {}).items():
            path = root / expand(relative)
            self.assertTrue(path.is_symlink(), f"{label} links: {expand(relative)} is not a symbolic link{output}")
            actual = os.readlink(path).replace("\\", "/")
            self.assertEqual(actual, expand(target), f"{label} links: {expand(relative)}")
        for relative, subjects in (case.get("git_log") or {}).items():
            log = git(root, relative, "log", "--format=%s")
            self.assertEqual(log.returncode, 0, f"{label} git_log: {expand(relative)}\n{log.stderr}{output}")
            self.assertEqual(log.stdout.splitlines(), [expand(subject) for subject in subjects], f"{label} git_log")
        for relative in case.get("git_clean") or []:
            status = git(root, relative, "status", "--porcelain")
            self.assertEqual(status.returncode, 0, f"{label} git_clean: {expand(relative)}\n{status.stderr}{output}")
            self.assertEqual(status.stdout, "", f"{label} git_clean: {expand(relative)} has changes")
        for relative, expected in (case.get("git_branches") or {}).items():
            actual = branches(root, relative)
            self.assertIsNotNone(actual, f"{label} git_branches: {expand(relative)} is not readable{output}")
            self.assertEqual(actual, [expand(name) for name in expected], f"{label} git_branches: {expand(relative)}")
        if case.get("unchanged"):
            self.assertEqual(snapshot(root), before, f"{label} unchanged: the tree was modified{output}")

    def one_file(self, root, relative, key, label, output):
        """The file at `relative`, a path or a glob matching exactly one file, which must exist."""
        relative = expand(relative)
        path = root / relative
        if is_glob(relative):
            matches = sorted(match.relative_to(root).as_posix() for match in root.glob(relative))
            self.assertEqual(len(matches), 1, f"{label} {key}: {relative} matches {matches}{output}")
            path = root / matches[0]
        self.assertTrue(path.is_file(), f"{label} {key}: {relative} does not exist{output}")
        return path


class CaseTest(CaseRunner):
    """One test per case document, added below from the files under CASES_DIR."""


class RunnerTest(CaseRunner):
    """The runner's own vocabulary, where no spec scenario covers it."""

    def test_tree_after_setup_is_not_committed_by_a_launch_in_setup(self):
        harness = "harnesses/support/2026-09-30-SUP-1-login-fails"
        case = {
            "config": {
                "default_workstream": "support",
                "agent_providers": ["claude"],
                "workstreams": {"support": {"prefix": "SUP", "description": "Investigate a problem"}},
            },
            "tree": {
                "tasks/support/2026-09-30-SUP-1-login-fails.md": (
                    "---\nstatus: open\nref: SUP-1\nupdated_at: 2026-09-30\nmetadata: {}\n---\n\n## Updates\n"
                ),
            },
            "setup": [["harness", "launch", "SUP-1", "--no-open"]],
            "tree_after_setup": {f"{harness}/notes/draft.md": "Not filed yet.\n"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "tree_after_setup")
            self.assertEqual((root / harness / "notes" / "draft.md").read_text(encoding="utf-8"), "Not filed yet.\n")
            status = git(root, harness, "status", "--porcelain")
            self.assertEqual(status.stdout, "?? notes/\n")
            log = git(root, harness, "log", "--format=%s")
            self.assertEqual(log.stdout.splitlines(), ["launch SUP-1"])

    def test_repos_are_clones_of_their_remote(self):
        case = {
            "repos": {
                "nakatomi-web": {
                    "branches": {"feature/a": {"a.txt": "a\n"}, "main": {"README.md": "main\n", "app.txt": "v1\n"}},
                    "default": "main",
                    "unfetched": {"main": {"new.txt": "new\n"}},
                },
                "group/other": {},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "repos")
            clone, remote = "repos/nakatomi-web", "remotes/nakatomi-web.git"
            url = git(root, clone, "remote", "get-url", "origin").stdout.strip()
            self.assertEqual(url, (root / remote).as_uri())
            head = git(root, clone, "symbolic-ref", "refs/remotes/origin/HEAD").stdout.strip()
            self.assertEqual(head, "refs/remotes/origin/main")
            self.assertEqual(branches(root, clone), ["main"])
            self.assertEqual(branches(root, remote), ["feature/a", "main"])
            self.assertEqual(sorted(path.name for path in (root / clone).iterdir()), [".git", "README.md", "app.txt"])
            feature = git(root, clone, "ls-tree", "--name-only", "origin/feature/a").stdout.splitlines()
            self.assertEqual(feature, ["a.txt"])
            parent = git(root, clone, "rev-parse", "origin/feature/a^", "origin/main").stdout.split()
            self.assertEqual(parent[0], parent[1])
            behind = git(root, remote, "log", "--format=%s", "main").stdout.splitlines()
            self.assertEqual(behind, ["unfetched main", "add main"])
            self.assertEqual(git(root, clone, "log", "--format=%s", "origin/main").stdout.splitlines(), ["add main"])
            self.assertEqual(branches(root, "repos/group/other"), ["main"])

    def test_git_after_setup_runs_in_a_repository_of_the_tree(self):
        case = {
            "repos": {"nakatomi-web": {}},
            "git_after_setup": [
                ["repos/nakatomi-web", "commit", "--quiet", "--allow-empty", "-m", "local work"],
                ["repos/nakatomi-web", "config", "gemba.root", "{root}"],
            ],
            "git_log": {"repos/nakatomi-web": ["local work", "add main"]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "git_after_setup")
            self.assertEqual(git(root, "repos/nakatomi-web", "config", "gemba.root").stdout.strip(), str(root))
            self.check(root, case, "git_after_setup", snapshot(root), subprocess.CompletedProcess([], 0, "", ""))

    def test_tree_is_written_byte_for_byte_and_lf_only_sees_a_cr(self):
        case = yaml.safe_load(
            'tree:\n  crlf.md: "one\\r\\ntwo\\r\\n"\n  lf.md: "one\\ntwo\\n"\n  utf16.md: !!binary "//5hAA=="\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "tree")
            self.assertEqual((root / "crlf.md").read_bytes(), b"one\r\ntwo\r\n")
            self.assertEqual((root / "utf16.md").read_bytes(), "a".encode("utf-16"))
            passing = {"lf_only": ["lf.md", "l*.md"], "stdout_contains": ["{root}"]}
            self.check(root, passing, "lf_only", snapshot(root), subprocess.CompletedProcess([], 0, str(root), ""))
            with self.assertRaises(AssertionError):
                self.check(root, {"lf_only": ["crlf.md"]}, "lf_only", {}, subprocess.CompletedProcess([], 0, "", ""))

    def test_local_config_is_written_like_config(self):
        cases = {
            "map": {
                "config": "default_workstream: support\n",
                "local_config": {"ide": "code -n", "repos_dir": "repos"},
            },
            "raw text": {"local_config": "ide: code -n\n# a comment\n"},
            "empty": {"local_config": ""},
        }
        expected = {"map": "ide: code -n\nrepos_dir: repos\n", "raw text": "ide: code -n\n# a comment\n", "empty": ""}
        for label, case in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                self.prepare(root, case, "local_config")
                self.assertEqual((root / "gemba.local.yaml").read_text(encoding="utf-8"), expected[label])
                self.assertEqual((root / "gemba.yaml").is_file(), "config" in case)

    def test_stderr_excludes_fails_on_a_fragment_found(self):
        result = subprocess.CompletedProcess([], 1, "", "invalid gemba config:\n- gemba.yaml: workstreams\n")
        passing = {"stderr_excludes": ["default_workstream", "{root}"]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.check(root, passing, "stderr_excludes", {}, result)
            with self.assertRaises(AssertionError):
                self.check(root, {"stderr_excludes": ["workstreams"]}, "stderr_excludes", {}, result)

    def test_git_of_a_hook_is_left_out(self):
        # A pre-push hook run from a linked worktree inherits GIT_DIR, the git dir of that worktree.
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp).resolve() / "outer"
            self.run_git(Path(tmp), "init", "--quiet", str(outer), label="outer")
            before = snapshot(outer / ".git")
            root = Path(tmp).resolve() / "case"
            root.mkdir()
            with mock.patch.dict(os.environ, {"GIT_DIR": str(outer / ".git")}):
                self.prepare(root, {"repos": {"nakatomi-web": {}}}, "hook")
            self.assertEqual(branches(root, "repos/nakatomi-web"), ["main"])
            self.assertEqual(snapshot(outer / ".git"), before)

    def test_git_runs_in_cwd_with_stdin_and_without_root(self):
        case = {
            "repos": {"nakatomi-web": {}},
            "cwd": "repos/nakatomi-web",
            "run": ["git", "hash-object", "--stdin"],
            "stdin": "a\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "git")
            result = self.execute(root, case, "git", case["run"], case["stdin"])
            self.assertEqual((result.returncode, result.stdout), (0, "78981922613b2afb6025042ff6bd878ac1994e85\n"))
            listed = self.execute(root, case, "git", ["git", "log", "--format=%s"])
            self.assertEqual(listed.stdout, "add main\n")
            with self.assertRaises(AssertionError):
                self.execute(root, {}, "git", ["git", "status"])

    def test_command_without_stdin_gets_an_empty_input(self):
        case = {"repos": {"nakatomi-web": {}}, "cwd": "repos/nakatomi-web"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "stdin")
            result = self.execute(root, case, "stdin", ["git", "hash-object", "--stdin"])
            self.assertEqual(result.stdout, "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391\n")

    def test_revision_tokens_name_a_commit_made_after_setup(self):
        case = {
            "repos": {"nakatomi-web": {}},
            "cwd": "repos/nakatomi-web",
            "git_after_setup": [["repos/nakatomi-web", "commit", "--quiet", "--allow-empty", "-m", "local work"]],
            "run": ["git", "log", "-1", "--format=%s %H", "{rev:repos/nakatomi-web:HEAD~1}"],
            "stdout": "add main {rev:repos/nakatomi-web:HEAD~1}\n",
            "stdout_contains": ["main {short:repos/nakatomi-web:HEAD~1}"],
            "stderr_contains": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "rev")
            resolved = self.resolve_revisions(root, case, "rev")
            full = git(root, "repos/nakatomi-web", "rev-parse", "HEAD~1").stdout.strip()
            short = git(root, "repos/nakatomi-web", "rev-parse", "--short", "HEAD~1").stdout.strip()
            self.assertEqual(resolved["run"][-1], full)
            self.assertEqual(resolved["stdout"], f"add main {full}\n")
            self.assertEqual(resolved["stdout_contains"], [f"main {short}"])
            self.assertTrue(full.startswith(short) and len(short) < len(full))
            self.assertEqual(resolved["git_after_setup"], case["git_after_setup"])
            result = self.execute(root, resolved, "rev", resolved["run"])
            self.check(root, resolved, "rev", snapshot(root), result)
            with self.assertRaises(AssertionError):
                self.resolve_revisions(root, {"stdout": "{rev:repos/nakatomi-web:no-such-branch}"}, "rev")

    def test_new_command_names_resolve_to_the_binary(self):
        for name in ("mark", "archive", "report", "set", "worktree", "init", "config"):
            with self.subTest(name=name):
                self.assertEqual(COMMANDS[name], ["gemba", name])
                with tempfile.TemporaryDirectory() as tmp:
                    result = self.execute(Path(tmp), {}, name, [name, "--help"])
                self.assertTrue((result.stdout + result.stderr).startswith("usage: gemba"), result.stderr)


def _make_test(source, case):
    def test(self):
        self.run_case(source, case)

    return test


for _name, _source, _case in load_cases():
    setattr(CaseTest, _name, _make_test(_source, _case))


if __name__ == "__main__":
    unittest.main()
