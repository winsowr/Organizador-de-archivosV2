# Organizador de Archivos v2.0

Organiza archivos de un directorio usando múltiples criterios inteligentes.  
Escalable: agregar nuevos parámetros es tan simple como crear un archivo `.py`.

---

## Estructura del proyecto

```
organizador/
├── core.py          # Motor central (lógica compartida)
├── cli.py           # Interfaz de línea de comandos
├── gui.py           # Interfaz gráfica (tkinter)
├── plugins/         # Parámetros personalizados (auto-cargados)
│   └── por_cliente.py   # Ejemplo de plugin
├── config/          # Reglas JSON personalizadas (futuro)
└── logs/            # Log automático de operaciones
```

---

## Uso en terminal (CLI)

```bash
# Ver todos los parámetros disponibles
python cli.py --listar-parametros

# Vista previa (sin mover nada)
python cli.py /ruta/carpeta --parametro tipo --dry-run

# Organizar por tipo semántico
python cli.py /ruta/carpeta --parametro tipo

# Organizar por fecha
python cli.py /ruta/carpeta --parametro año_mes

# Organizar por propósito (informe, factura, contrato...)
python cli.py /ruta/carpeta --parametro proposito

# Organizar por extensión
python cli.py /ruta/carpeta --parametro extension

# Deshacer la última operación
python cli.py /ruta/carpeta --undo

# Buscar duplicados
python cli.py /ruta/carpeta --duplicados

# Sin pedir confirmación (útil para scripts)
python cli.py /ruta/carpeta --parametro tipo --sin-confirmacion
```

---

## Uso con interfaz gráfica

```bash
python gui.py
```

---

## Parámetros disponibles

| Parámetro   | Descripción                                         |
|-------------|-----------------------------------------------------|
| `extension` | Por extensión de archivo (.pdf, .jpg, .mp4...)     |
| `tipo`      | Por tipo semántico (documentos, imágenes, videos...) |
| `proposito` | Por propósito según el nombre (informe, factura...) |
| `año`       | Por año de modificación                             |
| `año_mes`   | Por año y mes de modificación                       |
| `tamaño`    | Por tamaño (micro, pequeño, mediano, grande)        |
| `inicial`   | Por letra inicial del nombre                        |
| `tipo_y_fecha` | Tipo semántico + año (ej: imagenes/2024)         |
| `cliente`   | Por cliente (plugin, configurable)                  |

---

## Cómo agregar un nuevo parámetro (sistema de plugins)

1. Creá un archivo en `plugins/mi_parametro.py`
2. Definí una clase:

```python
from core import ParameterBase, FileInfo

class MiParametro(ParameterBase):
    nombre = "mi_parametro"
    descripcion = "Descripción de lo que hace"

    def classify(self, fi: FileInfo) -> str:
        # fi tiene: fi.name, fi.ext, fi.size, fi.created,
        #           fi.modified, fi.semantic_type, fi.keyword_type
        return "nombre_de_carpeta"
```

3. Reiniciá la app. El parámetro aparece automáticamente en el menú.

---

## Características

- ✅ Vista previa (dry-run) antes de mover archivos
- ✅ Deshacer (undo) la última operación
- ✅ Detección de duplicados por hash MD5
- ✅ Log automático de todas las operaciones
- ✅ Manejo de conflictos de nombres (no sobreescribe)
- ✅ Sistema de plugins para nuevos parámetros
- ✅ Interfaz CLI con colores y barra de progreso
- ✅ Interfaz gráfica moderna con tkinter
- ✅ Sin dependencias externas (solo Python estándar)

---

## Requisitos

- Python 3.10+
- Sin librerías externas (usa solo la biblioteca estándar)
