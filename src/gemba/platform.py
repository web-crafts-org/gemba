"""Platform rules: the text contract on the read side, the names Windows reserves, how a child process is
detached, and the policy of a deletion the system interrupts; every rule in one place, none in an adapter."""

import os
import subprocess
from typing import Any, Literal

# The device names Windows reserves as file and folder names, whatever their case or extension.
RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul", *(f"com{digit}" for digit in range(10)), *(f"lpt{digit}" for digit in range(10))}
)

# Seconds to wait before each retry of a deletion the system refuses because a path is held: brief, so that a
# file an indexer or an antivirus holds for a moment is deleted, and a file an IDE holds is reported soon.
HELD_RETRY_DELAYS = (0.1, 0.2, 0.4, 0.8)

BYTE_ORDER_MARK = "﻿"

DeletionError = Literal["read-only", "held", "other"]


def decode(data: bytes) -> str:
    """The text of a file gemba reads: UTF-8, a leading byte-order mark dropped, every CRLF and CR made LF.

    Raises UnicodeDecodeError when the bytes are not UTF-8; the caller words the refusal.
    """
    text = data.decode("utf-8")
    return text.removeprefix(BYTE_ORDER_MARK).replace("\r\n", "\n").replace("\r", "\n")


def is_reserved_name(name: str) -> bool:
    """Whether `name`, a workstream identifier, a member folder name or a slug, is a device name Windows reserves."""
    return name.lower() in RESERVED_NAMES


def detached_start(system: str = os.name) -> dict[str, Any]:
    """The `Popen` keyword arguments that start a child without a console of its own and without waiting for it.

    POSIX gives the child a session of its own; Windows ignores that and takes its two creation flags instead.
    `system` is `os.name`, injectable so that both branches are tested on one machine.
    """
    if system == "nt":
        detached = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        new_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        return {"creationflags": detached | new_group}
    return {"start_new_session": True}


def classify_deletion_error(error: BaseException, writable: bool) -> DeletionError:
    """What a failed unlink or rmdir means: a read-only file to clear, a held path to retry, or something else.

    `writable` says whether the path had its write bit when the error was raised. Windows refuses to delete a
    read-only file, as git marks its objects, and refuses to delete a path a program holds open, both with a
    PermissionError; POSIX raises it for neither, so there every error is reported as it is.
    """
    if not isinstance(error, PermissionError):
        return "other"
    return "held" if writable else "read-only"
