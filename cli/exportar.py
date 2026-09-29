"""exportar: el informe de un laboratorio en un solo archivo HTML, para compartirlo sin servidor."""
from pathlib import Path

from nucleo import informe, laboratorios

AYUDA = "exporta el informe de un laboratorio a un solo archivo HTML (sin servidor)"


def configurar(p):
    p.add_argument("--lab", required=True)
    p.add_argument("--salida", help="por defecto laboratorios/<lab>/informe.html")


def ejecutar(args):
    salida = Path(args.salida) if args.salida else laboratorios.carpeta(args.lab) / "informe.html"
    html = informe.html(args.lab, servido=False)
    salida.write_text(html)
    print(f"{salida} ({len(html) // 1024} KB)")
    return 0
