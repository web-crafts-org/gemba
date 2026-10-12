"""Unit tests for the platform rules: the text contract, the reserved names, the detached start, the deletion policy."""

import os
import unittest

from gemba import platform


class DecodeTest(unittest.TestCase):
    def test_lf_text_is_kept(self):
        self.assertEqual(platform.decode(b"---\nstatus: open\n---\n"), "---\nstatus: open\n---\n")

    def test_crlf_and_cr_become_lf(self):
        self.assertEqual(platform.decode(b"one\r\ntwo\rthree\n"), "one\ntwo\nthree\n")

    def test_leading_byte_order_mark_is_dropped(self):
        self.assertEqual(platform.decode("﻿one\r\n".encode()), "one\n")
        self.assertEqual(platform.decode("one﻿two\n".encode()), "one﻿two\n")

    def test_characters_are_kept(self):
        self.assertEqual(platform.decode("Señal ✅\r\n".encode()), "Señal ✅\n")

    def test_not_utf_8_is_refused(self):
        with self.assertRaises(UnicodeDecodeError):
            platform.decode("one\n".encode("utf-16"))


class ReservedNameTest(unittest.TestCase):
    def test_every_reserved_name(self):
        for name in ("con", "prn", "aux", "nul", "com0", "com1", "com9", "lpt0", "lpt1", "lpt9"):
            with self.subTest(name=name):
                self.assertTrue(platform.is_reserved_name(name))

    def test_case_does_not_matter(self):
        self.assertTrue(platform.is_reserved_name("NUL"))
        self.assertTrue(platform.is_reserved_name("Com1"))

    def test_other_names_are_free(self):
        for name in ("console", "com10", "lpt", "nul-check", "auxiliary", "support", ""):
            with self.subTest(name=name):
                self.assertFalse(platform.is_reserved_name(name))


class DetachedStartTest(unittest.TestCase):
    def test_posix(self):
        self.assertEqual(platform.detached_start("posix"), {"start_new_session": True})

    def test_windows(self):
        options = platform.detached_start("nt")
        self.assertEqual(list(options), ["creationflags"])
        flags = options["creationflags"]
        self.assertIsInstance(flags, int)
        assert isinstance(flags, int)
        self.assertEqual(flags & 0x00000008, 0x00000008, "DETACHED_PROCESS")
        self.assertEqual(flags & 0x00000200, 0x00000200, "CREATE_NEW_PROCESS_GROUP")

    def test_default_is_this_system(self):
        self.assertEqual(platform.detached_start(), platform.detached_start(os.name))


class DeletionErrorTest(unittest.TestCase):
    def test_read_only_file(self):
        self.assertEqual(platform.classify_deletion_error(PermissionError(13, "denied"), writable=False), "read-only")

    def test_held_path(self):
        self.assertEqual(platform.classify_deletion_error(PermissionError(13, "denied"), writable=True), "held")

    def test_anything_else(self):
        self.assertEqual(platform.classify_deletion_error(FileNotFoundError(2, "gone"), writable=True), "other")
        self.assertEqual(platform.classify_deletion_error(OSError(39, "not empty"), writable=False), "other")
        self.assertEqual(platform.classify_deletion_error(ValueError("x"), writable=False), "other")

    def test_retry_schedule_is_brief(self):
        self.assertTrue(platform.HELD_RETRY_DELAYS)
        self.assertTrue(all(delay > 0 for delay in platform.HELD_RETRY_DELAYS))
        self.assertLess(sum(platform.HELD_RETRY_DELAYS), 5)


if __name__ == "__main__":
    unittest.main()
