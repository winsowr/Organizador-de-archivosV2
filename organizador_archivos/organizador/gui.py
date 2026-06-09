#!/usr/bin/env python3
"""
gui.py — Interfaz gráfica (tkinter) del Organizador de Archivos.
Ejecutar: python gui.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import importlib.util
import sys

# ── Cargar core (compatible con ejecución normal y con PyInstaller --onefile)
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


# ─────────────────────────────────────────────
# Paleta de colores (funciona en light y dark)
# ─────────────────────────────────────────────
COLORS = {
    "bg":       "#1e1e2e",
    "surface":  "#2a2a3e",
    "card":     "#313150",
    "border":   "#44445a",
    "accent":   "#7c6ff7",
    "accent2":  "#5dd6c0",
    "text":     "#cdd6f4",
    "muted":    "#7f849c",
    "success":  "#a6e3a1",
    "warning":  "#fab387",
    "error":    "#f38ba8",
    "yellow":   "#f9e2af",
}


class OrganizadorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador de Archivos v2.0")
        self.geometry("900x700")
        self.minsize(780, 580)
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        self._org = None  # instancia actual de Organizer
        self._selected_dir = tk.StringVar()
        self._selected_param = tk.StringVar(value="tipo")
        self._dry_run = tk.BooleanVar(value=True)
        self._status = tk.StringVar(value="Listo.")

        self._build_ui()
        self._center_window()

    # ─────────────────────────────────────────
    # Construcción de la UI
    # ─────────────────────────────────────────

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Configurar estilos ttk
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=COLORS["bg"], foreground=COLORS["text"],
                         fieldbackground=COLORS["surface"], font=("Segoe UI", 10))
        style.configure("TFrame",  background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["surface"],
                         relief="flat", borderwidth=1)
        style.configure("Accent.TButton",
                         background=COLORS["accent"], foreground="#ffffff",
                         font=("Segoe UI", 10, "bold"), relief="flat", padding=(12, 6))
        style.map("Accent.TButton",
                  background=[("active", "#9b8fff"), ("disabled", COLORS["border"])])
        style.configure("Flat.TButton", background=COLORS["card"],
                         foreground=COLORS["text"], relief="flat", padding=(10, 5))
        style.map("Flat.TButton", background=[("active", COLORS["border"])])
        style.configure("TCombobox", selectbackground=COLORS["accent"],
                         fieldbackground=COLORS["surface"])
        style.configure("Horizontal.TProgressbar",
                         troughcolor=COLORS["surface"], background=COLORS["accent"],
                         thickness=6)
        style.configure("TCheckbutton", background=COLORS["bg"],
                         foreground=COLORS["text"])
        style.configure("Treeview",
                         background=COLORS["surface"], foreground=COLORS["text"],
                         fieldbackground=COLORS["surface"], rowheight=24)
        style.configure("Treeview.Heading",
                         background=COLORS["card"], foreground=COLORS["accent2"],
                         relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", COLORS["accent"])])

        # ── Header
        header = tk.Frame(self, bg=COLORS["surface"], pady=14)
        header.pack(fill="x")
        tk.Label(header, text="📂  Organizador de Archivos",
                 bg=COLORS["surface"], fg=COLORS["accent"],
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=20)
        tk.Label(header, text="v2.0 · escalable · con undo",
                 bg=COLORS["surface"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(side="left")

        # ── Main paned
        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=12, pady=10)

        # ── Panel izquierdo (controles)
        left = ttk.Frame(main, width=290)
        left.pack_propagate(False)
        main.add(left, weight=0)
        self._build_left_panel(left)

        # ── Panel derecho (preview / resultado)
        right = ttk.Frame(main)
        main.add(right, weight=1)
        self._build_right_panel(right)

        # ── Status bar
        status_bar = tk.Frame(self, bg=COLORS["card"], pady=4)
        status_bar.pack(fill="x", side="bottom")
        self._progress = ttk.Progressbar(status_bar, style="Horizontal.TProgressbar",
                                          length=180, mode="determinate")
        self._progress.pack(side="right", padx=10)
        tk.Label(status_bar, textvariable=self._status,
                 bg=COLORS["card"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(side="left", padx=10)

    def _build_left_panel(self, parent):
        # Sección: Directorio
        self._section(parent, "1. Directorio de origen")
        dir_frame = tk.Frame(parent, bg=COLORS["bg"])
        dir_frame.pack(fill="x", padx=12, pady=(0, 10))
        dir_entry = tk.Entry(dir_frame, textvariable=self._selected_dir,
                              bg=COLORS["surface"], fg=COLORS["text"],
                              insertbackground=COLORS["text"], relief="flat",
                              font=("Segoe UI", 9), width=22)
        dir_entry.pack(side="left", fill="x", expand=True, ipady=5)
        ttk.Button(dir_frame, text="…", style="Flat.TButton",
                   command=self._browse_dir).pack(side="left", padx=(4, 0))

        # Sección: Parámetro
        self._section(parent, "2. Parámetro de organización")
        param_frame = tk.Frame(parent, bg=COLORS["bg"])
        param_frame.pack(fill="x", padx=12, pady=(0, 4))

        param_names = list(core.PARAMETERS.keys())
        combo = ttk.Combobox(param_frame, textvariable=self._selected_param,
                              values=param_names, state="readonly",
                              font=("Segoe UI", 10))
        combo.pack(fill="x")
        combo.bind("<<ComboboxSelected>>", self._on_param_change)

        self._param_desc = tk.Label(parent, text="", bg=COLORS["bg"],
                                     fg=COLORS["muted"], font=("Segoe UI", 8),
                                     wraplength=240, justify="left")
        self._param_desc.pack(fill="x", padx=12, pady=(2, 10))
        self._update_param_desc()

        # Sección: Opciones
        self._section(parent, "3. Opciones")
        opt_frame = tk.Frame(parent, bg=COLORS["bg"])
        opt_frame.pack(fill="x", padx=12, pady=(0, 10))

        tk.Checkbutton(opt_frame, text="Modo simulación (dry-run)",
                       variable=self._dry_run,
                       bg=COLORS["bg"], fg=COLORS["text"],
                       selectcolor=COLORS["surface"],
                       activebackground=COLORS["bg"],
                       font=("Segoe UI", 9)).pack(anchor="w")

        tk.Label(opt_frame, text="   sin mover archivos reales",
                 bg=COLORS["bg"], fg=COLORS["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")

        # Sección: Acciones
        self._section(parent, "4. Acciones")
        btn_frame = tk.Frame(parent, bg=COLORS["bg"])
        btn_frame.pack(fill="x", padx=12, pady=(0, 6))

        ttk.Button(btn_frame, text="🔍  Vista previa", style="Flat.TButton",
                   command=self._run_preview).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🚀  Organizar", style="Accent.TButton",
                   command=self._run_organize).pack(fill="x", pady=2)

        sep = tk.Frame(btn_frame, bg=COLORS["border"], height=1)
        sep.pack(fill="x", pady=6)

        ttk.Button(btn_frame, text="↩  Deshacer última operación",
                   style="Flat.TButton", command=self._run_undo).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🔎  Buscar duplicados",
                   style="Flat.TButton", command=self._run_duplicates).pack(fill="x", pady=2)

    def _build_right_panel(self, parent):
        # Título del panel
        header = tk.Frame(parent, bg=COLORS["bg"])
        header.pack(fill="x")
        tk.Label(header, text="Vista previa / Resultado",
                 bg=COLORS["bg"], fg=COLORS["accent2"],
                 font=("Segoe UI", 11, "bold")).pack(side="left", pady=(0, 6))

        # Árbol de resultados
        tree_frame = tk.Frame(parent, bg=COLORS["bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("carpeta", "archivos", "tamaño")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                   selectmode="browse")
        self._tree.heading("carpeta",  text="Carpeta destino")
        self._tree.heading("archivos", text="Archivos")
        self._tree.heading("tamaño",   text="Estado")
        self._tree.column("carpeta",  width=220)
        self._tree.column("archivos", width=80,  anchor="center")
        self._tree.column("tamaño",   width=180)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Área de log
        log_label = tk.Label(parent, text="Log de operaciones",
                              bg=COLORS["bg"], fg=COLORS["muted"],
                              font=("Segoe UI", 9))
        log_label.pack(anchor="w", pady=(8, 2))

        log_frame = tk.Frame(parent, bg=COLORS["surface"], padx=2, pady=2)
        log_frame.pack(fill="x")
        self._log = tk.Text(log_frame, height=7, bg=COLORS["surface"],
                             fg=COLORS["text"], insertbackground=COLORS["text"],
                             relief="flat", font=("Consolas", 9),
                             state="disabled", wrap="word")
        lsb = ttk.Scrollbar(log_frame, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=lsb.set)
        self._log.pack(side="left", fill="both", expand=True)
        lsb.pack(side="right", fill="y")

    # ─────────────────────────────────────────
    # Helpers UI
    # ─────────────────────────────────────────

    def _section(self, parent, text):
        f = tk.Frame(parent, bg=COLORS["bg"])
        f.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(f, text=text, bg=COLORS["bg"], fg=COLORS["accent"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Frame(f, bg=COLORS["border"], height=1).pack(
            side="left", fill="x", expand=True, padx=(6, 0), pady=1)

    def _log_write(self, msg: str, color: str = None):
        self._log.configure(state="normal")
        tag = f"c_{color}" if color else None
        if tag and color:
            self._log.tag_configure(tag, foreground=color)
        self._log.insert("end", msg + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _log_clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _tree_clear(self):
        for row in self._tree.get_children():
            self._tree.delete(row)

    def _update_param_desc(self, *_):
        p = self._selected_param.get()
        desc = core.PARAMETERS.get(p, core.BySemanticType()).descripcion
        self._param_desc.configure(text=desc)

    def _on_param_change(self, *_):
        self._update_param_desc()

    # ─────────────────────────────────────────
    # Lógica de acciones
    # ─────────────────────────────────────────

    def _browse_dir(self):
        d = filedialog.askdirectory(title="Seleccionar directorio")
        if d:
            self._selected_dir.set(d)

    def _get_dir(self) -> Path | None:
        d = self._selected_dir.get()
        if not d:
            messagebox.showwarning("Sin directorio", "Seleccioná un directorio primero.")
            return None
        p = Path(d)
        if not p.exists():
            messagebox.showerror("Error", f"El directorio no existe:\n{p}")
            return None
        return p

    def _make_organizer(self, dry_run=True) -> core.Organizer | None:
        d = self._get_dir()
        if not d:
            return None
        return core.Organizer(
            source_dir=d,
            parameter=self._selected_param.get(),
            dry_run=dry_run,
            progress_callback=self._on_progress,
        )

    def _on_progress(self, filename: str, current: int, total: int):
        pct = int(100 * current / total)
        self._progress["value"] = pct
        self._status.set(f"Procesando {current}/{total}: {filename[:40]}")
        self.update_idletasks()

    def _run_preview(self):
        org = self._make_organizer(dry_run=True)
        if not org:
            return
        self._log_clear()
        self._tree_clear()
        self._log_write("🔍 Generando vista previa...", COLORS["accent2"])
        preview = org.preview()
        if not preview:
            self._log_write("⚠️  No se encontraron archivos.", COLORS["warning"])
            return
        for folder, files in sorted(preview.items()):
            iid = self._tree.insert("", "end",
                                     values=(f"📁 {folder}", len(files), "pendiente"))
            for f in files[:30]:
                self._tree.insert(iid, "end", values=(f"   └ {f}", "", ""))
        total = sum(len(v) for v in preview.values())
        self._log_write(f"✅ {total} archivos en {len(preview)} carpeta(s).", COLORS["success"])
        self._status.set(f"Vista previa: {total} archivos → {len(preview)} carpetas")

    def _run_organize(self):
        dry = self._dry_run.get()
        if not dry:
            if not messagebox.askyesno(
                "Confirmar",
                "¿Mover archivos reales?\nEsta acción se puede deshacer con 'Deshacer'.",
                icon="warning",
            ):
                return

        org = self._make_organizer(dry_run=dry)
        if not org:
            return
        self._org = org
        self._log_clear()
        self._tree_clear()
        self._progress["value"] = 0
        label = "Simulando" if dry else "Organizando"
        self._log_write(f"🚀 {label}...", COLORS["accent"])

        def run():
            result = org.run()
            self.after(0, lambda: self._show_result(result, dry))

        threading.Thread(target=run, daemon=True).start()

    def _show_result(self, result: dict, dry: bool):
        self._tree_clear()
        for folder, count in sorted(result["detalle"].items(), key=lambda x: -x[1]):
            self._tree.insert("", "end",
                               values=(f"📁 {folder}", count,
                                       "simulado" if dry else "✅ movido"))
        verb = "simulados" if dry else "movidos"
        msg = (f"{'✅' if not dry else '🧪'} {result['movidos']} archivos {verb} "
               f"en {len(result['carpetas'])} carpeta(s).")
        self._log_write(msg, COLORS["success"] if not dry else COLORS["yellow"])
        if result["errores"]:
            self._log_write(f"⚠️  {result['errores']} error(es). Ver logs.", COLORS["error"])
        self._status.set(msg)
        self._progress["value"] = 100

    def _run_undo(self):
        if not self._org:
            messagebox.showinfo("Sin historial", "No hay operaciones para deshacer.")
            return
        count = self._org.undo()
        if count:
            self._log_write(f"↩️  Se revirtieron {count} archivo(s).", COLORS["accent2"])
            messagebox.showinfo("Deshacer", f"Se restauraron {count} archivo(s).")
        else:
            self._log_write("⚠️  No hay acciones para revertir.", COLORS["warning"])

    def _run_duplicates(self):
        org = self._make_organizer(dry_run=True)
        if not org:
            return
        self._log_clear()
        self._tree_clear()
        self._log_write("🔎 Buscando duplicados...", COLORS["accent2"])
        dupes = org.find_duplicates()
        if not dupes:
            self._log_write("✅ No se encontraron duplicados.", COLORS["success"])
            self._status.set("Sin duplicados.")
            return
        for h, files in dupes.items():
            iid = self._tree.insert("", "end",
                                     values=(f"🔁 Duplicado ({len(files)} archivos)",
                                             len(files), f"hash: {h[:12]}…"))
            for f in files:
                self._tree.insert(iid, "end", values=(f"   └ {f}", "", ""))
        self._log_write(
            f"⚠️  {len(dupes)} grupo(s) de duplicados encontrados.", COLORS["warning"]
        )
        self._status.set(f"Duplicados: {len(dupes)} grupo(s)")


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = OrganizadorApp()
    app.mainloop()
