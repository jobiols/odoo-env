from unittest.mock import patch

from odoo_env.constants import ODOO_VERSION_MAP
from odoo_env.managers.image_manager import ImageManager
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

    def test_extract_run_always_uses_entrypoint_cp(self):
        # El extract NO debe arrancar odoo. Si usa `docker run`, DEBE ser con
        # `--entrypoint cp` (reemplaza el entrypoint de odoo por cp).
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        run_cmds = [c.command for c in cmds if c.command[:2] == ["docker", "run"]]
        for cmd in run_cmds:
            self.assertIn(
                "--entrypoint",
                cmd,
                f"docker run en extract debe usar --entrypoint cp: {cmd}",
            )
            self.assertEqual(cmd[cmd.index("--entrypoint") + 1], "cp")

    def test_extract_sources_no_extract_sh_reference(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        for c in cmds:
            cmd_str = " ".join(str(t) for t in c.command)
            self.assertNotIn("extract_", cmd_str)

    def test_extract_sources_removes_legacy_src(self):
        # v14 vuelve al layout viejo: el dir legacy a limpiar pasa a ser src.
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        rm_cmds = [" ".join(c.command) for c in cmds if "rm" in c.command]
        self.assertTrue(
            any(tok.rstrip("/").endswith("/src") for s in rm_cmds for tok in s.split()),
            f"Expected legacy src cleanup, got: {rm_cmds}",
        )

    def test_extract_sources_removes_legacy_lib(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        rm_cmds = [" ".join(c.command) for c in cmds if "rm" in c.command]
        self.assertTrue(
            any(tok.rstrip("/").endswith("/lib") for s in rm_cmds for tok in s.split()),
            f"Expected legacy lib cleanup, got: {rm_cmds}",
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
                tok.rstrip("/").endswith("/src") or tok.rstrip("/").endswith("/lib")
                for tok in c.command
            )
        ]
        self.assertEqual(
            len(legacy_rm_cmds), 2, f"Expected 2 legacy rm cmds, got: {legacy_rm_cmds}"
        )
        for cmd in legacy_rm_cmds:
            self.assertIn("-f", cmd, f"Legacy cleanup must use -f, got: {cmd}")

    # ── v19 _resolve_extract_targets ──────────────────────────────

    def test_v19_resolve_targets_odoo_src_and_site_packages(self):
        targets, _ = ImageManager._resolve_extract_targets(19)
        self.assertEqual(
            targets,
            [
                ("src", "/odoo/odoo-src"),
                ("site-packages", "/odoo/venv/lib/python3.*/site-packages"),
            ],
        )

    def test_v19_legacy_dirs_clean_all_other_layouts(self):
        _, legacy = ImageManager._resolve_extract_targets(19)
        self.assertCountEqual(
            legacy,
            ("dist-packages", "dist-local-packages", "lib"),
        )

    def test_v19_not_in_odoo_version_map(self):
        """v19 tiene layout propio; NO debe ir en ODOO_VERSION_MAP."""
        self.assertNotIn(19, ODOO_VERSION_MAP)

    def test_v19_rejects_versions_beyond_19(self):
        with self.assertRaises(ValueError) as ctx:
            ImageManager._resolve_extract_targets(20)
        self.assertIn("v14-19", str(ctx.exception))

    # ── existing tests ────────────────────────────────────────────

    def test_extract_uses_entrypoint_cp_per_target(self):
        # v14 extrae 2 targets (dist-packages + dist-local-packages): un
        # `docker run --entrypoint cp` por cada uno, sin create/cp/rm.
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.pull_images()
        extract_runs = [
            c.command
            for c in cmds
            if c.command[:2] == ["docker", "run"] and "--entrypoint" in c.command
        ]
        creates = [c.command for c in cmds if c.command[:2] == ["docker", "create"]]
        docker_cps = [c.command for c in cmds if c.command[:2] == ["docker", "cp"]]
        self.assertEqual(
            len(extract_runs), 2, f"expected 2 entrypoint-cp runs: {extract_runs}"
        )
        self.assertEqual(creates, [], f"must not use docker create: {creates}")
        self.assertEqual(docker_cps, [], f"must not use docker cp: {docker_cps}")
