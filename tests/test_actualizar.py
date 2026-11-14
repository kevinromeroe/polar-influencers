"""Pruebas de las reglas de scripts/actualizar_cifras.py.  Correr: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from actualizar_cifras import actualizar  # noqa: E402

JS = '''window.REPORTE={
corte:"2026-11-11",
corteTexto:"11 de noviembre de 2026",
rows:[
 ["PAN","a","ig","https://www.instagram.com/reels/AAA/",{v:3644,l:184,c:33,s:19}],
 ["PAN","b","ig","https://www.instagram.com/reels/AAA/",{v:3644,l:184,c:33,s:19}],
 ["DK","c","ig","https://www.instagram.com/reel/BBB/",{v:1049,l:0,c:0,s:0,hl:1}],
 ["DK","d","ig","https://www.instagram.com/p/CCC/",{v:5000,l:990,c:3,s:1}]
]};'''


class Reglas(unittest.TestCase):
    def run_(self, pubs):
        return actualizar(JS, {"fecha": "2026-11-13", "publicaciones": pubs})

    def test_solo_sube_y_filas_que_comparten_enlace(self):
        t, _, _ = self.run_({"AAA": {"views": 3600, "likes": "185", "comments": 40}})
        self.assertEqual(t.count("{v:3644,l:185,c:40,s:19}"), 2)

    def test_likes_ocultos_siguen_ocultos(self):
        t, _, _ = self.run_({"BBB": {"views": 1060, "likes": 50}})
        self.assertIn("{v:1060,l:0,c:0,s:0,hl:1}", t)

    def test_redondeado_no_se_usa_y_avisa(self):
        t, _, avisos = self.run_({"CCC": {"likes": "1.2K"}})
        self.assertIn("l:990", t)
        self.assertTrue(any("redondeado" in a for a in avisos))

    def test_corte(self):
        t, _, _ = self.run_({})
        self.assertIn('corte:"2026-11-13"', t)
        self.assertIn('corteTexto:"13 de noviembre de 2026"', t)

    def test_publicacion_desconocida_avisa(self):
        _, _, avisos = self.run_({"ZZZ": {"views": 1}})
        self.assertTrue(any("ZZZ" in a for a in avisos))


if __name__ == "__main__":
    unittest.main()
