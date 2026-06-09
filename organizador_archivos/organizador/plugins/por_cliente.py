"""
plugins/por_cliente.py — Plugin de ejemplo.

Para agregar un nuevo parámetro de organización:
1. Creá un archivo .py en esta carpeta
2. Definí una clase que herede de ParameterBase
3. Implementá el método classify(fi) → str
4. ¡Listo! El sistema lo detecta automáticamente al iniciar.

Este ejemplo organiza archivos según el cliente mencionado
en el nombre del archivo (basado en palabras clave configurables).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import ParameterBase, FileInfo

# Mapa de keywords → nombre de cliente
# Personalizar según tus necesidades
CLIENTES = {
    "cliente_acme":    ["acme", "acmecorp"],
    "cliente_globex":  ["globex", "glbx"],
    "cliente_initech": ["initech", "init"],
    "cliente_hooli":   ["hooli"],
    "sin_cliente":     [],   # fallback
}


class ByClient(ParameterBase):
    nombre = "cliente"
    descripcion = "Organiza por nombre de cliente mencionado en el archivo (configurable en plugins/por_cliente.py)"

    def classify(self, fi: FileInfo) -> str:
        name_lower = fi.name.lower()
        for cliente, keywords in CLIENTES.items():
            for kw in keywords:
                if kw in name_lower:
                    return cliente
        return "sin_cliente"
