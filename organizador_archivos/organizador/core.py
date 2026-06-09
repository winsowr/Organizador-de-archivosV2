"""
core.py — Motor central del organizador de archivos.
Toda la lógica de análisis y movimiento de archivos vive aquí.
Las interfaces (CLI y GUI) lo importan y usan.
"""

import os
import shutil
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "organizador.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Mapa de tipos semánticos
# Podés ampliar este diccionario sin tocar nada más.
# ─────────────────────────────────────────────
SEMANTIC_MAP = {
    # Documentos
    "documentos": [".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md"],
    # Hojas de cálculo
    "hojas_calculo": [".xls", ".xlsx", ".ods", ".csv", ".tsv"],
    # Presentaciones
    "presentaciones": [".ppt", ".pptx", ".odp", ".key"],
    # Imágenes
    "imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
                 ".tiff", ".ico", ".heic", ".raw"],
    # Videos
    "videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
               ".m4v", ".3gp"],
    # Audio
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    # Código
    "codigo": [".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp",
               ".cs", ".go", ".rs", ".php", ".rb", ".sh", ".bat", ".sql",
               ".json", ".xml", ".yaml", ".yml", ".toml"],
    # Archivos comprimidos
    "comprimidos": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    # Ejecutables e instaladores
    "ejecutables": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"],
    # Fuentes tipográficas
    "fuentes": [".ttf", ".otf", ".woff", ".woff2"],
    # Ebooks
    "ebooks": [".epub", ".mobi", ".azw", ".fb2"],
    # Bases de datos
    "bases_de_datos": [".db", ".sqlite", ".sqlite3", ".mdb"],
    # Backups
    "backups": [".bak", ".backup", ".old", ".orig"],
    # Temporales / basura
    "temporales": [".tmp", ".temp", ".cache", ".DS_Store", "thumbs.db"],
}

# Patrones en el nombre de archivo → tipo de informe/propósito
KEYWORD_PATTERNS = {
    "informes":     ["informe", "reporte", "report", "resumen", "summary"],
    "facturas":     ["factura", "invoice", "recibo", "receipt", "ticket"],
    "contratos":    ["contrato", "contract", "acuerdo", "agreement", "nda"],
    "presupuestos": ["presupuesto", "budget", "cotizacion", "quote", "oferta"],
    "curriculum":   ["cv", "curriculum", "resume", "hoja_de_vida"],
    "fotos":        ["foto", "photo", "img", "image", "pic", "captura"],
    "backups":      ["backup", "bak", "respaldo", "copia"],
    "formularios":  ["formulario", "form", "solicitud", "request"],
}


# ─────────────────────────────────────────────
# Rangos de tamaño
# ─────────────────────────────────────────────
SIZE_RANGES = {
    "micro":   (0,            100 * 1024),          # < 100 KB
    "pequeño": (100 * 1024,   10 * 1024 * 1024),    # 100 KB – 10 MB
    "mediano": (10 * 1024 * 1024, 100 * 1024 * 1024), # 10–100 MB
    "grande":  (100 * 1024 * 1024, float("inf")),   # > 100 MB
}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def file_hash(path: Path, chunk=65536) -> str:
    """MD5 del archivo para detección de duplicados."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def get_semantic_type(ext: str) -> str:
    ext = ext.lower()
    for tipo, exts in SEMANTIC_MAP.items():
        if ext in exts:
            return tipo
    return "otros"


def get_keyword_type(filename: str) -> str | None:
    name = filename.lower().replace("-", "_").replace(" ", "_")
    for tipo, keywords in KEYWORD_PATTERNS.items():
        for kw in keywords:
            if kw in name:
                return tipo
    return None


def get_size_bucket(size_bytes: int) -> str:
    for bucket, (lo, hi) in SIZE_RANGES.items():
        if lo <= size_bytes < hi:
            return bucket
    return "desconocido"


def human_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def load_custom_rules(config_path: Path) -> dict:
    """Carga reglas JSON personalizadas desde archivo."""
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}


# ─────────────────────────────────────────────
# Analizador de archivos
# ─────────────────────────────────────────────

class FileInfo:
    """Representa un archivo con todos sus metadatos."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.stem = path.stem
        self.ext = path.suffix.lower()
        stat = path.stat()
        self.size = stat.st_size
        self.created = datetime.fromtimestamp(stat.st_ctime)
        self.modified = datetime.fromtimestamp(stat.st_mtime)

    @property
    def semantic_type(self):
        return get_semantic_type(self.ext)

    @property
    def keyword_type(self):
        return get_keyword_type(self.name)

    @property
    def size_bucket(self):
        return get_size_bucket(self.size)

    def to_dict(self):
        return {
            "nombre": self.name,
            "extension": self.ext,
            "tipo_semantico": self.semantic_type,
            "tipo_keyword": self.keyword_type,
            "tamaño": human_size(self.size),
            "tamaño_bytes": self.size,
            "creado": self.created.strftime("%Y-%m-%d"),
            "modificado": self.modified.strftime("%Y-%m-%d"),
        }


# ─────────────────────────────────────────────
# Parámetros de ordenamiento (clases plugin)
# Cada uno define: nombre, descripción y
# el método `classify(file_info) -> str`
# ─────────────────────────────────────────────

class ParameterBase:
    nombre: str = ""
    descripcion: str = ""

    def classify(self, fi: FileInfo) -> str:
        raise NotImplementedError


class ByExtension(ParameterBase):
    nombre = "extension"
    descripcion = "Organiza por extensión (.pdf, .jpg, etc.)"

    def classify(self, fi):
        return fi.ext.lstrip(".") or "sin_extension"


class BySemanticType(ParameterBase):
    nombre = "tipo"
    descripcion = "Organiza por tipo semántico (documentos, imágenes, videos...)"

    def classify(self, fi):
        return fi.semantic_type


class ByKeyword(ParameterBase):
    nombre = "proposito"
    descripcion = "Organiza por propósito según el nombre (informe, factura, contrato...)"

    def classify(self, fi):
        return fi.keyword_type or fi.semantic_type


class ByYear(ParameterBase):
    nombre = "año"
    descripcion = "Organiza por año de modificación"

    def classify(self, fi):
        return str(fi.modified.year)


class ByYearMonth(ParameterBase):
    nombre = "año_mes"
    descripcion = "Organiza por año y mes de modificación"

    def classify(self, fi):
        return fi.modified.strftime("%Y-%m")


class BySize(ParameterBase):
    nombre = "tamaño"
    descripcion = "Organiza por tamaño (micro, pequeño, mediano, grande)"

    def classify(self, fi):
        return fi.size_bucket


class ByFirstLetter(ParameterBase):
    nombre = "inicial"
    descripcion = "Organiza por letra inicial del nombre de archivo"

    def classify(self, fi):
        ch = fi.stem[0].upper() if fi.stem else "_"
        return ch if ch.isalpha() else "0-9_especiales"


class ByTypeAndDate(ParameterBase):
    nombre = "tipo_y_fecha"
    descripcion = "Combina tipo semántico + año (ej: imagenes/2024)"

    def classify(self, fi):
        return f"{fi.semantic_type}/{fi.modified.year}"


# Registro de todos los parámetros disponibles
PARAMETERS: dict[str, ParameterBase] = {
    p.nombre: p for p in [
        ByExtension(),
        BySemanticType(),
        ByKeyword(),
        ByYear(),
        ByYearMonth(),
        BySize(),
        ByFirstLetter(),
        ByTypeAndDate(),
    ]
}


def load_plugin_parameters(plugin_dir: Path):
    """
    Carga parámetros extra desde /plugins/*.py.
    Cada archivo debe tener una clase que herede ParameterBase.
    Así el sistema es infinitamente escalable.
    """
    import importlib.util
    for file in plugin_dir.glob("*.py"):
        if file.stem.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(file.stem, file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in dir(mod):
            obj = getattr(mod, name)
            if (isinstance(obj, type) and issubclass(obj, ParameterBase)
                    and obj is not ParameterBase):
                instance = obj()
                PARAMETERS[instance.nombre] = instance
                logger.info(f"Plugin cargado: {instance.nombre}")


# ─────────────────────────────────────────────
# Motor principal de organización
# ─────────────────────────────────────────────

class Organizer:
    """
    Analiza un directorio y organiza los archivos según
    el parámetro elegido. Soporta modo simulación (dry_run).
    """

    def __init__(
        self,
        source_dir: str | Path,
        parameter: str = "tipo",
        dry_run: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ):
        self.source_dir = Path(source_dir)
        self.parameter = PARAMETERS.get(parameter, BySemanticType())
        self.dry_run = dry_run
        self.progress_callback = progress_callback

        self.actions: list[dict] = []   # historial para undo
        self.errors: list[str] = []
        self.stats: dict[str, int] = {}

    def scan(self) -> list[FileInfo]:
        """Escanea el directorio fuente (no recursivo por defecto)."""
        files = []
        for p in self.source_dir.iterdir():
            if p.is_file():
                try:
                    files.append(FileInfo(p))
                except PermissionError as e:
                    self.errors.append(str(e))
        return files

    def preview(self) -> dict[str, list[str]]:
        """
        Devuelve un dict {carpeta_destino: [lista de archivos]}
        sin mover nada. Útil para la GUI y el dry_run.
        """
        result: dict[str, list[str]] = {}
        for fi in self.scan():
            bucket = self.parameter.classify(fi)
            result.setdefault(bucket, []).append(fi.name)
        return result

    def run(self) -> dict:
        """
        Ejecuta la organización. Si dry_run=True, solo simula.
        Devuelve un resumen de lo realizado.
        """
        files = self.scan()
        total = len(files)
        moved = 0
        skipped = 0

        for i, fi in enumerate(files):
            bucket = self.parameter.classify(fi)
            dest_dir = self.source_dir / bucket
            dest_path = dest_dir / fi.name

            if self.progress_callback:
                self.progress_callback(fi.name, i + 1, total)

            if not self.dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                # Manejo de nombre duplicado en destino
                if dest_path.exists():
                    stem, suffix = fi.path.stem, fi.path.suffix
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest_path = dest_dir / f"{stem}_{ts}{suffix}"

                try:
                    shutil.move(str(fi.path), str(dest_path))
                    self.actions.append({
                        "origen": str(fi.path),
                        "destino": str(dest_path),
                        "bucket": bucket,
                    })
                    moved += 1
                    logger.info(f"Movido: {fi.name} → {bucket}/")
                except Exception as e:
                    self.errors.append(f"{fi.name}: {e}")
                    skipped += 1
            else:
                moved += 1  # simulado

            self.stats[bucket] = self.stats.get(bucket, 0) + 1

        return {
            "total": total,
            "movidos": moved,
            "errores": skipped,
            "carpetas": list(self.stats.keys()),
            "detalle": self.stats,
            "dry_run": self.dry_run,
        }

    def undo(self) -> int:
        """Revierte el último proceso moviendo archivos a su origen."""
        count = 0
        for action in reversed(self.actions):
            try:
                shutil.move(action["destino"], action["origen"])
                count += 1
            except Exception as e:
                logger.warning(f"Undo fallido: {e}")
        self.actions.clear()
        logger.info(f"Undo: {count} archivos restaurados.")
        return count

    def find_duplicates(self) -> dict[str, list[str]]:
        """Agrupa archivos con el mismo hash MD5."""
        hashes: dict[str, list[str]] = {}
        for fi in self.scan():
            h = file_hash(fi.path)
            hashes.setdefault(h, []).append(fi.name)
        return {h: names for h, names in hashes.items() if len(names) > 1}
