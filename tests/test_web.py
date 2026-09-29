"""JavaScript de la web: sintaxis de cada página y pruebas de comun.js. Necesita Node (se salta si no está)."""
import re, shutil, subprocess, tempfile, unittest
from pathlib import Path

from tests.ayuda import ConLaboratorio, LAB
from nucleo import config, ensayos, informe, motor

NODE = shutil.which("node")


def scripts(html):
    return [s for s in re.findall(r"<script>(.*?)</script>", html, re.S) if s.strip()]


@unittest.skipUnless(NODE, "sin Node")
class JavaScript(ConLaboratorio):
    def comprobar_sintaxis(self, codigo, nombre):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(codigo)
        r = subprocess.run([NODE, "--check", f.name], capture_output=True, text=True)
        Path(f.name).unlink()
        self.assertEqual(r.returncode, 0, f"{nombre}: {r.stderr}")

    def test_sintaxis_de_las_paginas(self):
        for pagina in ["portada.html", "banco.html"]:
            for s in scripts((config.WEB / pagina).read_text()):
                self.comprobar_sintaxis(s, pagina)
        self.comprobar_sintaxis((config.WEB / "comun.js").read_text(), "comun.js")

    def test_sintaxis_del_informe_con_datos(self):
        e = ensayos.nuevo(LAB, base=self.base)
        motor.correr(e, base=self.base)
        for servido in (True, False):
            for s in scripts(informe.html(LAB, servido=servido, base=self.base)):
                self.comprobar_sintaxis(s, f"informe (servido={servido})")

    def test_comun_js(self):
        r = subprocess.run([NODE, str(Path(__file__).parent / "js" / "comun.test.mjs")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
