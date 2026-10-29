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


class TestDockerImageDeclaredMajor(unittest.TestCase):
    """Tercer campo del manifiesto declara el major de postgres explícitamente.

    Cubre imágenes custom con tags opacos (sin número parseable), donde la
    heurística del tag no puede adivinar la versión.
    """

    def test_declared_major_overrides_opaque_tag(self):
        di = DockerImage("postgres jobiols/mypostgres:ultima-version 18")
        self.assertEqual(di.major_ver, 18)

    def test_declared_major_wins_over_parseable_tag(self):
        """El major declarado es autoritativo: gana sobre el tag parseable."""
        di = DockerImage("postgres postgres:13 18")
        self.assertEqual(di.major_ver, 18)

    def test_declared_major_bad_value_raises(self):
        di = DockerImage("postgres jobiols/mypostgres:ultima-version ultima")
        with self.assertRaises(OeError):
            _ = di.major_ver

    def test_invalid_declared_major_aborts_even_when_tag_parses(self):
        """Un major declarado inválido aborta aunque el tag sea parseable (R3)."""
        di = DockerImage("postgres postgres:13 ultima")
        with self.assertRaises(OeError):
            _ = di.major_ver

    def test_opaque_tag_without_declared_major_shows_friendly_error(self):
        """Sin tag legible y sin major declarado, el error debe indicar cómo resolverlo."""
        di = DockerImage("postgres jobiols/mypostgres:ultima-version")
        with self.assertRaises(OeError) as ctx:
            _ = di.major_ver
        self.assertIn("Declare it explicitly", str(ctx.exception))
