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
