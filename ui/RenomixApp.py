import os
import sys
import csv
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox,PhotoImage
import tkinter.messagebox as mbox
from datetime import datetime

from core.file_renamer import FileRenamer
from data.database import DatabaseManager

class RenomixApp(tk.Tk):
    def __init__(self, db_path="renomix.db"):
        super().__init__()
        self.title("Renomix")
        self.geometry("1100x680")
        self.minsize(980, 600)
        
        # --- Icono multiplataforma ---
        try:
            here = os.path.dirname(__file__)
            # Ruta al favicon.ico y favicon.png
            ico = os.path.abspath(os.path.join(here, "..", "favicon.ico"))
            png = os.path.abspath(os.path.join(here, "..", "favicon.png"))

            if sys.platform.startswith("win") and os.path.exists(ico):
                self.iconbitmap(ico)  # Windows usa .ico
                self._icon_path = ico
            elif os.path.exists(png):
                self.iconphoto(False, PhotoImage(file=png))  # macOS/Linux usan .png
                self._icon_path = png
            else:
                self._icon_path = None
        except Exception:
            self._icon_path = None

        self.db = DatabaseManager(db_path=db_path)

        self._build_menubar()
        self._build_main_body()
        self._refresh_menu_state()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ============================
    # Menú bar
    # ============================
    def _build_menubar(self):
        menubar = tk.Menu(self)

        # Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exportar historial a CSV…", command=self._export_history_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Abrir carpeta de la BD", command=self._open_db_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._on_close)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Ver (dependiente de datos)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Actividad reciente", command=self._win_recent_activity)
        view_menu.add_command(label="Lotes (batches)", command=self._win_batches)
        view_menu.add_command(label="Top extensiones", command=self._win_top_ext)
        menubar.add_cascade(label="Ver", menu=view_menu)

        # Reportes
        rep_menu = tk.Menu(menubar, tearoff=0)
        rep_menu.add_command(label="Resumen de operaciones", command=self._win_ops_breakdown)
        menubar.add_cascade(label="Reportes", menu=rep_menu)

        # Herramientas
        tool_menu = tk.Menu(menubar, tearoff=0)
        tool_menu.add_command(label="Vaciar y compactar BD (VACUUM)", command=self._vacuum_db)
        menubar.add_cascade(label="Herramientas", menu=tool_menu)

        # Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentación", command=lambda: webbrowser.open("https://github.com/jonatanLara"))
        help_menu.add_command(label="Acerca de…", command=self._about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.config(menu=menubar)
        self._menu = {
            "menubar": menubar,
            "view_menu": view_menu,
            "rep_menu": rep_menu,
        }

    def _refresh_menu_state(self):
        has_data = self.db.count_rows() > 0
        state = "normal" if has_data else "disabled"
        self._menu["view_menu"].entryconfig(0, state=state)
        self._menu["view_menu"].entryconfig(1, state=state)
        self._menu["view_menu"].entryconfig(2, state=state)
        self._menu["rep_menu"].entryconfig(0, state=state)

    # ============================
    # Cuerpo principal
    # ============================
    def _build_main_body(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        # Panel superior: selección y opciones
        top = ttk.LabelFrame(root, text="Parámetros")
        top.pack(fill="x", padx=12, pady=12)

        # Carpeta origen
        self.var_src = tk.StringVar()
        ttk.Label(top, text="Carpeta origen:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.var_src, width=70).grid(row=0, column=1, sticky="we", padx=6, pady=6)
        ttk.Button(top, text="Buscar…", command=self._choose_src).grid(row=0, column=2, padx=6, pady=6)

        # Extensiones
        self.var_exts = tk.StringVar(value="jpg,png,tif,jpeg")
        ttk.Label(top, text="Extensiones (coma):").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.var_exts, width=40).grid(row=1, column=1, sticky="w", padx=6, pady=6)

        # Recursivo
        self.var_recursive = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Buscar recursivo", variable=self.var_recursive).grid(row=1, column=2, sticky="w", padx=6, pady=6)

        # Prefijo / Sufijo / Separador
        self.var_prefix = tk.StringVar(value="")
        self.var_suffix = tk.StringVar(value="")
        self.var_sep = tk.StringVar(value=" ")

        ttk.Label(top, text="Prefijo:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.var_prefix, width=20).grid(row=2, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(top, text="Sufijo:").grid(row=2, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.var_suffix, width=20).grid(row=2, column=3, sticky="w", padx=6, pady=6)
        ttk.Label(top, text="Separador:").grid(row=2, column=4, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.var_sep, width=8).grid(row=2, column=5, sticky="w", padx=6, pady=6)

        # Patrón
        self.var_pattern = tk.StringVar(value="{prefix}{name}{suffix}{ext}")
        ttk.Label(top, text="Patrón:").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.var_pattern, width=60).grid(row=3, column=1, columnspan=3, sticky="we", padx=6, pady=6)
        ttk.Label(top, text="Vars: {prefix}{name}{suffix}{ext}").grid(row=3, column=4, columnspan=2, sticky="w", padx=6, pady=6)

        # Destino y conflicto
        self.var_dest_mode = tk.StringVar(value="overwrite")
        self.var_conflict = tk.StringVar(value="increment")
        self.var_dest_dir = tk.StringVar(value="")

        dest = ttk.LabelFrame(root, text="Destino y conflictos")
        dest.pack(fill="x", padx=12, pady=6)

        ttk.Radiobutton(dest, text="Renombrar en la misma carpeta", variable=self.var_dest_mode, value="overwrite").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Radiobutton(dest, text="Copiar a carpeta destino", variable=self.var_dest_mode, value="copy").grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Entry(dest, textvariable=self.var_dest_dir, width=60).grid(row=0, column=2, sticky="we", padx=6, pady=6)
        ttk.Button(dest, text="Elegir…", command=self._choose_dest).grid(row=0, column=3, padx=6, pady=6)

        ttk.Label(dest, text="Si el destino existe:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Combobox(dest, textvariable=self.var_conflict, values=["increment", "overwrite", "skip"], width=12, state="readonly").grid(row=1, column=1, sticky="w", padx=6, pady=6)

        for c in range(6):
            top.grid_columnconfigure(c, weight=1)
        dest.grid_columnconfigure(2, weight=1)

        # Botones acciones
        actions = ttk.Frame(root)
        actions.pack(fill="x", padx=12, pady=6)
        ttk.Button(actions, text="Previsualizar", command=self._preview).pack(side="left", padx=4)
        ttk.Button(actions, text="Aplicar cambios", command=self._apply).pack(side="left", padx=4)
        ttk.Button(actions, text="Deshacer último lote", command=self._undo_last).pack(side="left", padx=4)

        # Tabla preview
        table = ttk.Frame(root)
        table.pack(fill="both", expand=True, padx=12, pady=12)

        cols = ("old_path", "new_path", "operation", "note")
        self.tv = ttk.Treeview(table, columns=cols, show="headings")
        for c in cols:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=240, anchor="w")
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tv.yview)
        hsb = ttk.Scrollbar(table, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)

    # ============================
    # Handlers UI
    # ============================
    def _choose_src(self):
        d = filedialog.askdirectory(title="Seleccionar carpeta origen")
        if d:
            self.var_src.set(d)

    def _choose_dest(self):
        d = filedialog.askdirectory(title="Seleccionar carpeta destino")
        if d:
            self.var_dest_dir.set(d)

    def _get_extensions(self):
        raw = self.var_exts.get().strip()
        if not raw:
            return None
        return [p.strip() for p in raw.split(',') if p.strip()]

    def _build_plan_from_ui(self):
        src = self.var_src.get().strip()
        if not src or not os.path.isdir(src):
            raise ValueError("Selecciona una carpeta de origen válida")

        fr = FileRenamer(source_dir=src)
        plan = fr.build_plan(
            prefix=self.var_prefix.get(),
            suffix=self.var_suffix.get(),
            separator=self.var_sep.get(),
            pattern=self.var_pattern.get(),
            recursive=self.var_recursive.get(),
            extensions=self._get_extensions(),
            destination_mode=self.var_dest_mode.get(),
            dest_dir=(self.var_dest_dir.get().strip() or None),
            conflict_policy=self.var_conflict.get(),
        )
        return fr, plan

    def _preview(self):
        try:
            _, plan = self._build_plan_from_ui()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        for i in self.tv.get_children():
            self.tv.delete(i)
        for row in plan[:1000]:
            self.tv.insert("", "end", values=(row["old_path"], row["new_path"], row["operation"], row.get("note", "")))

    def _apply(self):
        try:
            fr, plan = self._build_plan_from_ui()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        if not plan:
            self._msg_info("Aplicar", "No hay archivos que procesar")
            return

        if self.var_dest_mode.get() == "copy" and not self.var_dest_dir.get().strip():
            messagebox.showwarning("Destino", "Selecciona la carpeta destino para copiar")
            return

        if not messagebox.askyesno("Confirmar", f"Se procesarán {len(plan)} elementos. ¿Continuar?"):
            return

        res = fr.apply_plan(plan, conflict_policy=self.var_conflict.get())

        batch_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        rows_to_db = []
        ok_count = 0
        for r in res:
            if r.get("status") == "ok":
                ok_count += 1
                rows_to_db.append({
                    "batch_id": batch_id,
                    "old_path": r["old_path"],
                    "new_path": r["new_path"],
                    "operation": r["operation"],
                    "note": r.get("note", ""),
                })

        if rows_to_db:
            self.db.insert_many(rows_to_db)
            self.on_changes_applied()

        self._preview()
        self._msg_info("Resultado", f"Procesados OK: {ok_count} / {len(plan)}")

    def _undo_last(self):
        last = self.db.get_last_batch_id()
        if not last:
            self._msg_info("Deshacer", "No hay lotes anteriores")
            return
        rows = self.db.get_rows_by_batch(last)
        if not rows:
            self._msg_info("Deshacer", "Lote vacío")
            return
        if not messagebox.askyesno("Deshacer", f"Revertir el lote {last} con {len(rows)} elementos?"):
            return

        fr = FileRenamer(source_dir=os.path.dirname(rows[0]["old_path"]))
        undo_res = fr.undo_batch(list(reversed(rows)))

        self.db.delete_by_batch(last)
        self.on_undo_done()

        ok = sum(1 for r in undo_res if r.get("status") == "ok")
        self._msg_info("Deshacer", f"Revertidos OK: {ok} / {len(rows)}")
        self._preview()

    # ============================
    # Ventanas de datos (Ver/Reportes)
    # ============================
    def _win_recent_activity(self):
        data = self.db.get_recent_activity(limit=200)
        self._open_table_window(
            title="Actividad reciente",
            rows=data,
            columns=[
                ("batch_id", "Batch"),
                ("operation", "Operación"),
                ("old_path", "Origen"),
                ("new_path", "Destino"),
                ("timestamp", "Fecha/Hora"),
            ],
        )

    def _win_batches(self):
        from datetime import datetime as _dt
        data = self.db.get_batches_summary(limit=200)
        for r in data:
            try:
                st = _dt.fromisoformat(r["started_at"]) if r["started_at"] else None
                en = _dt.fromisoformat(r["ended_at"]) if r["ended_at"] else None
                r["duration_s"] = (en - st).total_seconds() if (st and en) else None
            except Exception:
                r["duration_s"] = None
        self._open_table_window(
            title="Lotes (batches)",
            rows=data,
            columns=[
                ("batch_id", "Batch"),
                ("items", "Ítems"),
                ("renames", "Renames"),
                ("copies", "Copias"),
                ("started_at", "Inicio"),
                ("ended_at", "Fin"),
                ("duration_s", "Duración (s)"),
            ],
        )

    def _win_top_ext(self):
        data = self.db.get_top_extensions(limit=50)
        self._open_table_window(
            title="Top extensiones",
            rows=data,
            columns=[
                ("extension", "Extensión"),
                ("count", "Cantidad"),
            ],
        )

    def _win_ops_breakdown(self):
        br = self.db.get_operations_breakdown()
        total = br["copy"] + br["rename"]
        rows = [
            {"operacion": "copy", "cantidad": br["copy"]},
            {"operacion": "rename", "cantidad": br["rename"]},
            {"operacion": "TOTAL", "cantidad": total},
        ]
        self._open_table_window(
            title="Resumen de operaciones",
            rows=rows,
            columns=[
                ("operacion", "Operación"),
                ("cantidad", "Cantidad"),
            ],
        )

    # ============================
    # Utilidades comunes
    # ============================
    def _open_table_window(self, title: str, rows, columns):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("920x520")
        
        # Aplicar el mismo icono en subventanas
        try:
            if self._icon_path:
                if sys.platform.startswith("win") and self._icon_path.endswith(".ico"):
                    win.iconbitmap(self._icon_path)
                else:
                    win.iconphoto(False, PhotoImage(file=self._icon_path))
        except Exception:
            pass

        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        tv = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", height=18)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tv.xview)
        tv.configure(yscroll=vsb.set, xscroll=hsb.set)

        for key, header in columns:
            tv.heading(key, text=header)
            tv.column(key, width=160, stretch=True)

        for r in rows:
            tv.insert("", "end", values=[r.get(k, "") for k, _ in columns])

        tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        btns = ttk.Frame(win)
        btns.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(btns, text="Exportar CSV…", command=lambda: self._export_table_to_csv(rows, columns)).pack(side="left")

    def _export_history_csv(self):
        if self.db.count_rows() == 0:
            self._msg_info("Exportar", "No hay datos en el historial todavía.")
            return
        save_to = filedialog.asksaveasfilename(
            title="Guardar historial como CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"renomix_historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not save_to:
            return
        rows = self.db.get_recent_activity(limit=1_000_000)
        self._write_csv(save_to, rows)
        self._msg_info("Exportar", f"Historial exportado a:\n{save_to}")

    def _export_table_to_csv(self, rows, columns):
        save_to = filedialog.asksaveasfilename(
            title="Exportar tabla como CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"renomix_tabla_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not save_to:
            return
        keys = [k for k, _ in columns]
        processed = [{k: r.get(k, "") for k in keys} for r in rows]
        self._write_csv(save_to, processed)
        self._msg_info("Exportar", f"Tabla exportada a:\n{save_to}")

    def _write_csv(self, path, rows):
        if not rows:
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write("")
            return
        keys = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow(r)

    def _open_db_folder(self):
        abs_db = os.path.abspath(self.db.db_path)
        folder = os.path.dirname(abs_db)
        if os.name == "nt":
            os.startfile(folder)
        elif os.name == "posix":
            try:
                if os.uname().sysname == "Darwin":
                    os.system(f'open "{folder}"')
                else:
                    os.system(f'xdg-open "{folder}"')
            except Exception:
                webbrowser.open(f"file://{folder}")

    def _vacuum_db(self):
        if messagebox.askyesno("VACUUM", "Esto compactará la base de datos. ¿Continuar?"):
            self.db.vacuum()
            self._msg_info("VACUUM", "Base de datos compactada correctamente.")

    def _about(self):
        self._msg_info("Acerca de Renomix", "Renomix – Renombrado por lotes con historial y deshacer.\n© 2025")

    # Hooks para refrescar estado del menú tras cambios
    def on_changes_applied(self):
        self._refresh_menu_state()

    def on_undo_done(self):
        self._refresh_menu_state()

    def _on_close(self):
        try:
            self.db.close()
        finally:
            self.destroy()
    
    def _msg_info(self, title, message):
        temp = tk.Toplevel(self)
        temp.withdraw()  # ventana oculta

        # Asignar icono a la ventana padre
        try:
            if self._icon_path:
                if sys.platform.startswith("win") and self._icon_path.endswith(".ico"):
                    temp.iconbitmap(self._icon_path)
                else:
                    temp.iconphoto(False, PhotoImage(file=self._icon_path))
        except Exception:
            pass

        mbox.showinfo(title, message, parent=temp)
        temp.destroy()
    