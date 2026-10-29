import unittest

from odoo_env.images import DockerImage
from odoo_env.messages import OeError


class TestDockerImageMajorVer(unittest.TestCase):
    """major_ver parsea los tags reales del ecosistema postgres.

    Incluidos los de pgvector: `pg18` arranca con letras y `0.8.0-pg18`
    pone la version de la extension antes que la de postgres. El parser
    debe devolver el major de POSTGRES, no el primer numero que vea.
    """

    CASES = {
        "pgvector/pgvector:pg18": 18,
        "pgvector/pgvector:pg18-bookworm": 18,
        "pgvector/pgvector:0.8.0-pg18": 18,
        "postgres:17.5-alpine": 17,
        "postgres:13": 13,
    }

    def test_major_ver_parses_real_tags(self):
        for image_url, expected in self.CASES.items():
            with self.subTest(image=image_url):
                di = DockerImage(f"postgres {image_url}")
                self.assertEqual(di.major_ver, expected)

    def test_major_ver_raises_on_unreadable_tag(self):
        di = DockerImage("postgres postgres:latest")
        with self.assertRaises(OeError):
            _ = di.major_ver
