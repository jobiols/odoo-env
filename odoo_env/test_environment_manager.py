from unittest.mock import PropertyMock, patch

from odoo_env.managers.environment_manager import EnvironmentManager
from odoo_env.odooenv import OdooEnv
from odoo_env.test_helpers import MockArgs, OdooEnvTestCase


class TestBuildModuleCommandWithDemo(OdooEnvTestCase):
    """oe --create-test-db must pass --with-demo on Odoo >=19 installs.

    Odoo 19 no longer loads demo data by default on -i; without this flag,
    modules installed on the freshly created test DB silently end up
    without their demo records.
    """

    def _make_em(self, numeric_ver):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        patcher = patch.object(
            type(oe._client),
            "numeric_ver",
            new_callable=PropertyMock,
            return_value=numeric_ver,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return EnvironmentManager(oe)

    def test_install_adds_with_demo_for_ge19(self):
        em = self._make_em(19.0)
        cmds = em._build_module_command("test_client_test", ["mod_a"], "-i")
        self.assertIn("--with-demo", cmds[0].command)

    def test_install_omits_with_demo_for_le18(self):
        em = self._make_em(17.0)
        cmds = em._build_module_command("test_client_test", ["mod_a"], "-i")
        self.assertNotIn("--with-demo", cmds[0].command)

    def test_update_never_adds_with_demo(self):
        """--with-demo only matters at initial install, not at update."""
        em = self._make_em(19.0)
        cmds = em._build_module_command("test_client_test", ["mod_a"], "-u")
        self.assertNotIn("--with-demo", cmds[0].command)


class TestModuleCommandTty(OdooEnvTestCase):
    """-Q / -i / -u / --create-test-db must adapt to TTY presence.

    These commands build `docker run` for a non-interactive Odoo job
    (--stop-after-init + --test-enable). They must NOT hardcode -it: when
    stdin is not a terminal (CI, agents, cron, piped stdin), docker rejects
    `-it` and the container never starts. The discriminator is
    `sys.stdin.isatty()`, not "manual vs agent".
    """

    def _make_em(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        return EnvironmentManager(oe)

    def test_qa_uses_it_when_tty(self):
        em = self._make_em()
        with patch("sys.stdin.isatty", return_value=True):
            cmds = em.qa("test_client_test", ["mod_a"], [])
        self.assertEqual(cmds[0].command[cmds[0].command.index("--rm") + 1], "-it")

    def test_qa_omits_it_when_no_tty(self):
        em = self._make_em()
        with patch("sys.stdin.isatty", return_value=False):
            cmds = em.qa("test_client_test", ["mod_a"], [])
        cmd = cmds[0].command
        self.assertNotIn("-it", cmd)
        self.assertEqual(cmd[cmd.index("--rm") + 1], "--network")

    def test_build_module_command_uses_it_when_tty(self):
        em = self._make_em()
        with patch("sys.stdin.isatty", return_value=True):
            cmds = em._build_module_command("test_client_test", ["mod_a"], "-i")
        self.assertEqual(cmds[0].command[cmds[0].command.index("--rm") + 1], "-it")

    def test_build_module_command_omits_it_when_no_tty(self):
        em = self._make_em()
        with patch("sys.stdin.isatty", return_value=False):
            cmds = em._build_module_command("test_client_test", ["mod_a"], "-i")
        cmd = cmds[0].command
        self.assertNotIn("-it", cmd)
        self.assertEqual(cmd[cmd.index("--rm") + 1], "--network")


class TestDebugMountings(OdooEnvTestCase):

    def _make_em(self, odoo_version: int):
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        with (
            patch.object(
                type(oe._client),
                "numeric_ver",
                new_callable=PropertyMock,
                return_value=float(odoo_version),
            ),
            patch.object(
                type(oe._client),
                "version_dir",
                new_callable=PropertyMock,
                return_value=f"/odoo_ar/odoo-{odoo_version}.0/",
            ),
        ):
            em = EnvironmentManager(oe)
            result = em._get_debug_mountings()
        return result

    def test_odoo14_dist_packages_mount(self):
        """v14 (.deb) monta el dist-packages ENTERO, no solo odoo/."""
        result = self._make_em(14)
        self.assertEqual(
            result["/odoo_ar/odoo-14.0/dist-packages"],
            {"bind": "/usr/lib/python3/dist-packages"},
        )

    def test_odoo14_dist_local_packages_mount(self):
        result = self._make_em(14)
        self.assertEqual(
            result["/odoo_ar/odoo-14.0/dist-local-packages"],
            {"bind": "/usr/local/lib/python3.9/dist-packages/"},
        )

    def test_odoo15_lib_mount(self):
        result = self._make_em(15)
        self.assertEqual(
            result["/odoo_ar/odoo-15.0/lib"],
            {"bind": "/usr/local/lib/python3.9/dist-packages/"},
        )

    def test_odoo16_lib_mount(self):
        result = self._make_em(16)
        self.assertEqual(
            result["/odoo_ar/odoo-16.0/lib"],
            {"bind": "/usr/local/lib/python3.9/dist-packages/"},
        )

    def test_odoo17_lib_mount(self):
        result = self._make_em(17)
        self.assertEqual(
            result["/odoo_ar/odoo-17.0/lib"],
            {"bind": "/usr/local/lib/python3.10/dist-packages/"},
        )

    def test_odoo18_lib_mount(self):
        result = self._make_em(18)
        self.assertEqual(
            result["/odoo_ar/odoo-18.0/lib"],
            {"bind": "/usr/local/lib/python3.12/dist-packages/"},
        )

    def test_odoo19_unchanged(self):
        result = self._make_em(19)
        self.assertEqual(
            result,
            {
                "/odoo_ar/odoo-19.0/src": {"bind": "/odoo/odoo-src"},
                "/odoo_ar/odoo-19.0/site-packages": {
                    "bind": "/odoo/venv/lib/python3.10/site-packages"
                },
            },
        )

    def test_legacy_11_has_extra_addons(self):
        result = self._make_em(11)
        self.assertIn("/odoo_ar/odoo-11.0/extra-addons", result)

    def test_legacy_12_has_extra_addons(self):
        result = self._make_em(12)
        self.assertIn("/odoo_ar/odoo-12.0/extra-addons", result)

    def test_legacy_13_has_extra_addons(self):
        result = self._make_em(13)
        self.assertIn("/odoo_ar/odoo-13.0/extra-addons", result)

    def test_unknown_version_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._make_em(20)

    def test_odoo14_uses_dist_packages_keys(self):
        result = self._make_em(14)
        self.assertIn("/odoo_ar/odoo-14.0/dist-packages", result)
        self.assertIn("/odoo_ar/odoo-14.0/dist-local-packages", result)

    def test_odoo14_does_not_use_src_lib_keys(self):
        # El layout src/lib + /odoo rompia v14 (tapaba odoo con un dir vacio).
        result = self._make_em(14)
        self.assertNotIn("/odoo_ar/odoo-14.0/src", result)
        self.assertNotIn("/odoo_ar/odoo-14.0/lib", result)

    def test_odoo17_lib_contains_python310(self):
        result = self._make_em(17)
        lib_bind = result.get("/odoo_ar/odoo-17.0/lib", {}).get("bind", "")
        self.assertIn("python3.10", lib_bind)

    def test_odoo14_core_bind_is_whole_dist_packages(self):
        # El core se monta entero, NO solo .../odoo.
        result = self._make_em(14)
        bind = result["/odoo_ar/odoo-14.0/dist-packages"]["bind"]
        self.assertEqual(bind, "/usr/lib/python3/dist-packages")
        self.assertFalse(bind.endswith("/odoo"))

    def test_odoo14_lib_bind_ends_with_slash(self):
        result = self._make_em(14)
        lib_bind = result.get("/odoo_ar/odoo-14.0/dist-local-packages", {}).get(
            "bind", ""
        )
        self.assertTrue(lib_bind.endswith("/"))


class TestEnvironmentManager(OdooEnvTestCase):

    def test_install_never_calls_extract_sources(self):
        with patch("odoo_env.odooenv.OdooEnv.do_extract_sources") as mock_extract:
            options = MockArgs(debug=True, client="test_client")
            oe = OdooEnv(options)
            oe.install()
            mock_extract.assert_not_called()

    def test_install_does_not_call_extract_sources_in_debug_mode(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.install()
        for c in cmds:
            has_rm_rf = "rm" in c.command and "-rf" in c.command
            self.assertFalse(
                has_rm_rf,
                f"Found rm -rf command in install() debug mode: {c.command}",
            )

    def test_install_does_not_call_extract_sources_in_non_debug_mode(self):
        options = MockArgs(debug=False, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.install()
        for c in cmds:
            has_rm_rf = "rm" in c.command and "-rf" in c.command
            self.assertFalse(
                has_rm_rf,
                f"Found rm -rf command in install() non-debug mode: {c.command}",
            )

    def test_install_does_not_reference_dist_dirs(self):
        self.mock_config_data.return_value["environment"] = "debug"
        options = MockArgs(debug=True, client="test_client")
        oe = OdooEnv(options)
        cmds = oe.install()
        for c in cmds:
            cmd_str = " ".join(str(t) for t in c.command)
            self.assertNotIn(
                "dist-packages",
                cmd_str,
                f"install() references dist-packages: {c.command}",
            )
            self.assertNotIn(
                "dist-local-packages",
                cmd_str,
                f"install() references dist-local-packages: {c.command}",
            )
