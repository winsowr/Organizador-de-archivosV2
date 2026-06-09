#!/usr/bin/env python3
"""
cli.py — Interfaz de línea de comandos del Organizador de Archivos.

Uso rápido:
    python cli.py /ruta/al/directorio --parametro tipo
    python cli.py /ruta/al/directorio --parametro extension --dry-run
    python cli.py /ruta/al/directorio --parametro fecha --undo
    python cli.py /ruta/al/directorio --duplicados
    python cli.py --listar-parametros

Parámetros disponibles: extension, tipo, proposito, año, año_mes, tamaño, inicial, tipo_y_fecha
"""

import argparse
import sys
from pathlib import Path

# Colores ANSI para la terminal
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    GRAY   = "\033[90m"
    PURPLE = "\033[95m"

def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
def green(s):  return f"{C.GREEN}{s}{C.RESET}"
def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
def red(s):    return f"{C.RED}{s}{C.RESET}"
def cyan(s):   return f"{C.CYAN}{s}{C.RESET}"
def gray(s):   return f"{C.GRAY}{s}{C.RESET}"
def purple(s): return f"{C.PURPLE}{s}{C.RESET}"


BANNER = f"""
{C.PURPLE}{C.BOLD}╔══════════════════════════════════════════╗
║   Organizador de Archivos  v2.0          ║
║   Escalable · Multi-parámetro · Con undo ║
╚══════════════════════════════════════════╝{C.RESET}
"""


def print_banner():
    print(BANNER)


def print_parameters(params: dict):
    print(bold("\n📦 Parámetros disponibles:\n"))
    for name, obj in params.items():
        print(f"  {cyan(name):<20} {gray(obj.descripcion)}")
    print()


def progress_callback(filename: str, current: int, total: int):
    bar_len = 30
    filled = int(bar_len * current / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = int(100 * current / total)
    # Truncar nombre largo
    name = filename[:35] + "…" if len(filename) > 36 else filename
    print(f"\r  [{bar}] {pct:3d}%  {gray(name):<38}", end="", flush=True)
    if current == total:
        print()


def print_preview(preview: dict[str, list[str]]):
    print(bold("\n📋 Vista previa (sin mover archivos):\n"))
    for folder, files in sorted(preview.items()):
        print(f"  {yellow('📁')} {bold(folder)}/  ({len(files)} archivo{'s' if len(files) != 1 else ''})")
        for f in files[:5]:
            print(f"     {gray('└─')} {f}")
        if len(files) > 5:
            print(f"     {gray(f'   ... y {len(files) - 5} más')}")
    print()


def print_result(result: dict):
    print(bold("\n✅ Resultado:\n"))
    print(f"  {'Total escaneados:':<22} {bold(str(result['total']))}")
    print(f"  {'Archivos movidos:':<22} {green(str(result['movidos']))}")
    if result["errores"]:
        print(f"  {'Con errores:':<22} {red(str(result['errores']))}")
    print(f"\n  {'Carpetas creadas:':<22} {len(result['carpetas'])}")
    print()
    print(bold("  Distribución:"))
    for folder, count in sorted(result["detalle"].items(), key=lambda x: -x[1]):
        bar = "▮" * min(count, 30)
        print(f"  {cyan(folder):<25} {bar} {count}")
    print()


def print_duplicates(dupes: dict[str, list[str]]):
    if not dupes:
        print(green("\n✅ No se encontraron duplicados.\n"))
        return
    print(red(f"\n⚠️  Se encontraron {len(dupes)} grupo(s) de duplicados:\n"))
    for h, files in dupes.items():
        print(f"  {gray(h[:12])}…  →  {yellow(str(len(files)))} archivos:")
        for f in files:
            print(f"    {gray('•')} {f}")
    print()


def confirm(msg: str) -> bool:
    resp = input(f"\n{yellow('?')} {msg} [s/N]: ").strip().lower()
    return resp in ("s", "si", "sí", "y", "yes")


def main():
    # ── Importar core (permite ejecutar desde cualquier directorio)
    import importlib.util, os, sys

    # Cargar core (compatible con ejecución normal y con PyInstaller --onefile)
    if 'core' in sys.modules:
        core = sys.modules['core']
    else:
        try:
            import core
        except Exception:
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys._MEIPASS)
            else:
                base_dir = Path(__file__).parent
            core_path = base_dir / "core.py"
            spec = importlib.util.spec_from_file_location("core", core_path)
            core = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(core)

    # Cargar plugins desde la ubicación correcta
    if getattr(sys, 'frozen', False):
        plugin_dir = Path(sys._MEIPASS) / "plugins"
    else:
        plugin_dir = Path(__file__).parent / "plugins"
    core.load_plugin_parameters(plugin_dir)

    # ── Parser
    parser = argparse.ArgumentParser(
        description="Organiza archivos de un directorio con múltiples criterios.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("directorio", nargs="?", help="Directorio a organizar")
    parser.add_argument(
        "-p", "--parametro",
        default="tipo",
        choices=list(core.PARAMETERS.keys()),
        metavar="PARAMETRO",
        help=f"Criterio de organización. Opciones: {', '.join(core.PARAMETERS)}",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula sin mover archivos")
    parser.add_argument("--undo", action="store_true",
                        help="Revierte la última operación")
    parser.add_argument("--duplicados", action="store_true",
                        help="Detecta y muestra archivos duplicados")
    parser.add_argument("--listar-parametros", action="store_true",
                        help="Lista todos los parámetros disponibles")
    parser.add_argument("--sin-confirmacion", action="store_true",
                        help="Ejecuta sin pedir confirmación")

    args = parser.parse_args()
    print_banner()

    if args.listar_parametros:
        print_parameters(core.PARAMETERS)
        sys.exit(0)

    if not args.directorio:
        parser.print_help()
        sys.exit(0)

    directorio = Path(args.directorio)
    if not directorio.exists():
        print(red(f"\n❌ El directorio no existe: {directorio}\n"))
        sys.exit(1)

    # ── Crear organizador
    org = core.Organizer(
        source_dir=directorio,
        parameter=args.parametro,
        dry_run=args.dry_run,
        progress_callback=progress_callback,
    )

    # ── Modo duplicados
    if args.duplicados:
        print(cyan(f"\n🔍 Buscando duplicados en {directorio}...\n"))
        dupes = org.find_duplicates()
        print_duplicates(dupes)
        sys.exit(0)

    # ── Modo undo
    if args.undo:
        count = org.undo()
        if count:
            print(green(f"\n↩️  Se revirtieron {count} archivo(s).\n"))
        else:
            print(yellow("\n⚠️  No hay acciones para revertir.\n"))
        sys.exit(0)

    # ── Preview
    param_obj = core.PARAMETERS[args.parametro]
    print(f"  {gray('Directorio:')} {directorio}")
    print(f"  {gray('Parámetro:')}  {cyan(args.parametro)} — {gray(param_obj.descripcion)}")
    if args.dry_run:
        print(f"  {yellow('Modo:')}        simulación (dry-run)")
    print()

    preview = org.preview()
    print_preview(preview)

    if not args.dry_run:
        if not args.sin_confirmacion:
            if not confirm("¿Proceder con la organización?"):
                print(gray("\nOperación cancelada.\n"))
                sys.exit(0)

        print(bold("\n🚀 Organizando...\n"))
        result = org.run()
        print_result(result)

        if result["errores"]:
            print(red("  ⚠️  Algunos archivos tuvieron errores. Revisá los logs.\n"))
        else:
            print(green("  ✅ ¡Listo! Podés usar --undo para revertir.\n"))
    else:
        print(yellow("  ℹ️  Modo simulación: ningún archivo fue movido.\n"))


if __name__ == "__main__":
    main()
