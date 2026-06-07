from unittest.mock import patch

from odoo_env.odooenv import OdooEnv
from odoo_env.test_helpers import MockArgs, OdooEnvTestCase


class TestImageManager(OdooEnvTestCase):

    def test_pull_images_uses_pull_not_run(self):
        with (
            patch(
                "odoo_env.services.docker_client.DockerClient.get_pull_command",
                return_value=["docker", "pull", "jobiols/odoo-jeo:9.0"],
            ) as mock_pull,
            patch(
                "odoo_env.services.docker_client.DockerClient.get_run_command"
            ) as mock_run,
        ):
            options = MockArgs(debug=False, client="test_client")
            oe = OdooEnv(options)
            oe.pull_images()
            mock_pull.assert_called()
            mock_run.assert_not_called()

    def test_pull_images_command_starts_with_docker_pull(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        self.assertEqual(cmds[0].command[:2], ["docker", "pull"])

    def test_pull_images_calls_extract_sources_in_debug_mode(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        has_rm = any("rm" in c.command for c in cmds)
        self.assertTrue(has_rm, "Expected extract_sources rm commands in debug mode")

    def test_pull_images_no_extract_sources_in_non_debug_mode(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        for c in cmds:
            self.assertNotIn(
                "rm",
                c.command,
                f"Unexpected rm command in non-debug pull_images: {c.command}",
            )
            self.assertFalse(
                c.command and c.command[0] == "mkdir",
                f"Unexpected mkdir command in non-debug pull_images: {c.command}",
            )

    def test_extract_sources_uses_cp_not_entrypoint(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        docker_run_cmds = [
            c.command for c in cmds if c.command[:2] == ["docker", "run"]
        ]
        for cmd in docker_run_cmds:
            self.assertNotIn("--entrypoint", cmd)

    def test_extract_sources_no_extract_sh_reference(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        for c in cmds:
            cmd_str = " ".join(str(t) for t in c.command)
            self.assertNotIn("extract_", cmd_str)

    def test_extract_sources_removes_legacy_dist_packages(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        rm_cmds = [" ".join(c.command) for c in cmds if "rm" in c.command]
        self.assertTrue(
            any("dist-packages" in s and "dist-local" not in s for s in rm_cmds),
            f"Expected legacy dist-packages cleanup, got: {rm_cmds}",
        )

    def test_extract_sources_removes_legacy_dist_local_packages(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        rm_cmds = [" ".join(c.command) for c in cmds if "rm" in c.command]
        self.assertTrue(
            any("dist-local-packages" in s for s in rm_cmds),
            f"Expected legacy dist-local-packages cleanup, got: {rm_cmds}",
        )

    def test_extract_sources_legacy_cleanup_uses_force(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        legacy_rm_cmds = [
            c.command
            for c in cmds
            if "rm" in c.command
            and any(
                "dist-packages" in tok or "dist-local-packages" in tok
                for tok in c.command
            )
        ]
        self.assertEqual(
            len(legacy_rm_cmds), 2, f"Expected 2 legacy rm cmds, got: {legacy_rm_cmds}"
        )
        for cmd in legacy_rm_cmds:
            self.assertIn("-f", cmd, f"Legacy cleanup must use -f, got: {cmd}")

    def test_extract_sources_uses_two_docker_run_rm_v_commands(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        cp_cmds = [
            c.command
            for c in cmds
            if len(c.command) >= 8
            and c.command[:3] == ["docker", "run", "--rm"]
            and "cp" in c.command
        ]
        self.assertEqual(
            len(cp_cmds), 2, f"Expected 2 docker cp commands, got: {cp_cmds}"
        )
