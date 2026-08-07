import unittest
from types import SimpleNamespace
from unittest.mock import patch

from odoo_env import sd

SAMPLE_IMAGES = [
    ("odoo:16.0", "aaa111"),
    ("odoo:17.0", "bbb222"),
    ("jobiols/odoo-19e:latest", "ccc333"),
    ("postgres:13", "ddd444"),
    ("<none>:<none>", "eee555"),
]


class TestFilterImagesByMask(unittest.TestCase):

    def test_plain_text_matches_as_substring(self):
        # Sin metacaracteres glob -> substring sobre repository:tag.
        ids = sd.filter_images_by_mask(SAMPLE_IMAGES, "odoo")
        self.assertEqual(ids, ["aaa111", "bbb222", "ccc333"])

    def test_plain_text_substring_single_image(self):
        images = [("debian:bullseye-slim", "f00"), ("postgres:13", "bar")]
        ids = sd.filter_images_by_mask(images, "debian")
        self.assertEqual(ids, ["f00"])

    def test_plain_text_substring_matches_tag_part(self):
        ids = sd.filter_images_by_mask(SAMPLE_IMAGES, "17.0")
        self.assertEqual(ids, ["bbb222"])

    def test_plain_text_no_match(self):
        ids = sd.filter_images_by_mask(SAMPLE_IMAGES, "mariadb")
        self.assertEqual(ids, [])

    def test_prefix_glob_matches_repository_with_tag(self):
        ids = sd.filter_images_by_mask(SAMPLE_IMAGES, "odoo*")
        self.assertEqual(ids, ["aaa111", "bbb222"])

    def test_wildcard_both_sides_matches_substring(self):
        ids = sd.filter_images_by_mask(SAMPLE_IMAGES, "*odoo*")
        self.assertEqual(ids, ["aaa111", "bbb222", "ccc333"])

    def test_question_mark_glob(self):
        ids = sd.filter_images_by_mask(SAMPLE_IMAGES, "odoo:1?.0")
        self.assertEqual(ids, ["aaa111", "bbb222"])

    def test_exact_full_name(self):
        ids = sd.filter_images_by_mask(SAMPLE_IMAGES, "postgres:13")
        self.assertEqual(ids, ["ddd444"])

    def test_no_match_returns_empty(self):
        ids = sd.filter_images_by_mask(SAMPLE_IMAGES, "nomatch*")
        self.assertEqual(ids, [])

    def test_empty_image_list(self):
        self.assertEqual(sd.filter_images_by_mask([], "odoo*"), [])


class TestGetImages(unittest.TestCase):

    def _run_result(self, returncode, stdout="", stderr=""):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    def test_parses_name_and_id(self):
        stdout = "odoo:16.0 aaa111\njobiols/odoo-19e:latest ccc333\n"
        with patch.object(
            sd.subprocess, "run", return_value=self._run_result(0, stdout)
        ):
            images = sd.get_images()
        self.assertEqual(
            images,
            [("odoo:16.0", "aaa111"), ("jobiols/odoo-19e:latest", "ccc333")],
        )

    def test_skips_blank_lines(self):
        with patch.object(
            sd.subprocess,
            "run",
            return_value=self._run_result(0, "\n\nodoo:16.0 aaa\n"),
        ):
            images = sd.get_images()
        self.assertEqual(images, [("odoo:16.0", "aaa")])

    def test_returns_empty_on_error(self):
        with patch.object(
            sd.subprocess, "run", return_value=self._run_result(1, "", "boom")
        ):
            self.assertEqual(sd.get_images(), [])


class TestProcessInputRmdisk(unittest.TestCase):

    def test_rmdisk_with_mask_filters_images(self):
        with patch.object(sd, "get_images", return_value=SAMPLE_IMAGES):
            cmd = sd.process_input(["sd", "rmdisk", "odoo*"])
        self.assertEqual(cmd, ["sudo", "docker", "rmi", "-f", "aaa111", "bbb222"])

    def test_rmdisk_with_mask_no_match_returns_none(self):
        with patch.object(sd, "get_images", return_value=SAMPLE_IMAGES):
            cmd = sd.process_input(["sd", "rmdisk", "nomatch*"])
        self.assertIsNone(cmd)

    def test_rmdisk_without_mask_removes_all(self):
        with patch.object(sd, "get_image_ids", return_value=["aaa", "bbb", "ccc"]):
            cmd = sd.process_input(["sd", "rmdisk"])
        self.assertEqual(cmd, ["sudo", "docker", "rmi", "-f", "aaa", "bbb", "ccc"])

    def test_rmdisk_without_mask_no_images_returns_none(self):
        with patch.object(sd, "get_image_ids", return_value=[]):
            cmd = sd.process_input(["sd", "rmdisk"])
        self.assertIsNone(cmd)

    def test_old_rmdiskall_is_no_longer_special(self):
        # rmdiskall ya no es un subcomando: se pasa tal cual a docker.
        cmd = sd.process_input(["sd", "rmdiskall"])
        self.assertEqual(cmd, ["sudo", "docker", "rmdiskall"])


class TestProcessInputOther(unittest.TestCase):

    def test_no_params_returns_none(self):
        self.assertIsNone(sd.process_input(["sd"]))

    def test_help_returns_none(self):
        self.assertIsNone(sd.process_input(["sd", "-h"]))

    def test_inside_builds_run_command(self):
        cmd = sd.process_input(["sd", "inside", "odoo:16.0"])
        self.assertEqual(
            cmd,
            [
                "sudo",
                "docker",
                "run",
                "-it",
                "--rm",
                "--entrypoint=/bin/bash",
                "odoo:16.0",
            ],
        )

    def test_attach_builds_exec_command(self):
        cmd = sd.process_input(["sd", "attach", "mycontainer"])
        self.assertEqual(cmd, ["sudo", "docker", "exec", "-it", "mycontainer", "bash"])

    def test_rmall_with_containers(self):
        with patch.object(sd, "get_container_ids", return_value=["c1", "c2"]):
            cmd = sd.process_input(["sd", "rmall"])
        self.assertEqual(cmd, ["sudo", "docker", "rm", "-f", "c1", "c2"])

    def test_passthrough_unknown_command(self):
        cmd = sd.process_input(["sd", "ps", "-a"])
        self.assertEqual(cmd, ["sudo", "docker", "ps", "-a"])


if __name__ == "__main__":
    unittest.main()
