import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from odoo_env.command import WriteConfigFile


class TestWriteConfigFile(unittest.TestCase):
    """Generación del odoo.conf a partir del manifiesto."""

    def _write_config(self, debug):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            sources = tmp / "sources"
            (sources / "repo1" / "mod1").mkdir(parents=True)
            (sources / "repo1" / "mod1" / "__manifest__.py").write_text("{}")

            config_file = tmp / "config" / "odoo.conf"
            config_file.parent.mkdir(parents=True)

            client = SimpleNamespace(
                sources_dir=str(sources),
                config_file=str(config_file),
                config=["workers = 2"],
                debug=debug,
            )

            WriteConfigFile(None, args={"client": client}).execute()
            return config_file.read_text()

    def test_http_interface_written_in_prod(self):
        """Odoo 20 escucha en 127.0.0.1 por default; el contenedor necesita 0.0.0.0."""
        content = self._write_config(debug=False)
        self.assertIn("http_interface = 0.0.0.0", content)

    def test_http_interface_written_in_debug(self):
        content = self._write_config(debug=True)
        self.assertIn("http_interface = 0.0.0.0", content)
