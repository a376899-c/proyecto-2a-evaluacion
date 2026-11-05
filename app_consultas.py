"""BDAutos - App de consultas MongoDB (Tkinter + PyMongo).

Ejecutar:  python app_consultas.py   (o doble clic en abrir_app.bat)
Requisitos: MongoDB encendido con la base BDAutos (python crear_bd.py) y  pip install pymongo
Las consultas se guardan en mis_consultas.json (se crea solo la primera vez).
"""
import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import consultas as C
from conexion import BD, URI, get_db

ARCHIVO = Path(__file__).parent / "mis_consultas.json"
FUENTE = ("Segoe UI", 10) if os.name == "nt" else ("DejaVu Sans", 10)
MONO = ("Consolas", 10) if os.name == "nt" else ("DejaVu Sans Mono", 10)
FONDO, BARRA, ACENTO, ROJO = "#f4f6f9", "#1f2937", "#2563eb", "#dc2626"
AYUDA = {  # qué escribir según el tipo de consulta (mismo formato que PyMongo)
    "aggregate": ('Escribe el pipeline (lista de etapas):',
                  '[\n    {"$match": {"maker.country": "japan"}},\n'
                  '    {"$group": {"_id": "$maker.name", "autos": {"$sum": 1}}},\n'
                  '    {"$sort": {"autos": -1}}\n]'),
    "find": ('Escribe el filtro; opcional, después de comas: proyección y orden:',
             '{"specs.mpg": {"$gte": 35}},\n{"_id": 0, "descr": 1, "specs.mpg": 1},\n{"specs.mpg": -1}'),
    "count_documents": ('Escribe el filtro:', '{"maker.country": "japan"}'),
}


def conectar():
    try:
        return get_db(URI, BD)
    except Exception:  # noqa: BLE001 - si MongoDB está apagado, la app abre sin conexión
        return None


def caja(padre, titulo):
    """Tarjeta blanca con título y un área de texto con barras de desplazamiento."""
    marco = tk.Frame(padre, bg="white", highlightbackground="#dde2ea", highlightthickness=1)
    marco.titulo = tk.Label(marco, text=titulo, bg="white", fg=BARRA, font=(FUENTE[0], 11, "bold"),
                            anchor="w", padx=12, pady=8)
    marco.titulo.grid(row=0, column=0, columnspan=2, sticky="ew")
    texto = tk.Text(marco, wrap="none", font=MONO, relief="flat", padx=12, pady=8, bg="#fafbfc",
                    selectbackground="#cfe0ff", highlightthickness=0)
    for tag, color in (("cad", "#047857"), ("num", "#c2410c"), ("op", "#7c3aed")):
        texto.tag_configure(tag, foreground=color)
    sy = ttk.Scrollbar(marco, command=texto.yview)
    sx = ttk.Scrollbar(marco, orient="horizontal", command=texto.xview)
    texto.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    texto.bind("<Button-1>", lambda e: texto.focus_set())  # para poder copiar con Ctrl+C
    texto.grid(row=1, column=0, sticky="nsew")
    sy.grid(row=1, column=1, sticky="ns")
    sx.grid(row=2, column=0, sticky="ew")
    marco.rowconfigure(1, weight=1)
    marco.columnconfigure(0, weight=1)
    return marco, texto


def poner(texto, contenido, color="#111827"):
    texto.config(state="normal", fg=color)
    texto.delete("1.0", "end")
    texto.insert("1.0", contenido)
    if color == "#111827":  # colores sencillos: textos, números y operadores $
        for tag, patron in (("cad", r"['\"][^'\"\n]*['\"]"), ("num", r"\m-?[0-9]+(\.[0-9]+)?\M"),
                            ("op", r"\$[A-Za-z]+")):
            inicio, largo = "1.0", tk.IntVar()
            while (pos := texto.search(patron, inicio, "end", regexp=True, count=largo)) and largo.get():
                texto.tag_add(tag, pos, f"{pos}+{largo.get()}c")
                inicio = f"{pos}+{largo.get()}c"
    texto.config(state="disabled")  # solo lectura (se puede seleccionar y copiar)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BDAutos - Consultas MongoDB")
        self.geometry("1200x720")
        self.minsize(850, 500)
        self.configure(bg=FONDO)
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure(".", font=FUENTE, background=FONDO)
        estilo.configure("TButton", padding=(12, 6), background="white", bordercolor="#d5dbe5", relief="flat")
        estilo.map("TButton", background=[("active", "#eef2f7")])
        estilo.configure("Primario.TButton", background=ACENTO, foreground="white", bordercolor=ACENTO)
        estilo.map("Primario.TButton", background=[("active", "#1d4ed8")])
        estilo.configure("Peligro.TButton", foreground=ROJO)
        estilo.configure("TCombobox", padding=6, fieldbackground="white", bordercolor="#d5dbe5")
        estilo.map("TCombobox", fieldbackground=[("readonly", "white")], selectbackground=[("readonly", "white")],
                   selectforeground=[("readonly", BARRA)])
        estilo.configure("TPanedwindow", background=FONDO)

        if ARCHIVO.exists():
            self.lista = json.loads(ARCHIVO.read_text(encoding="utf-8"))
        else:
            self.lista = [dict(c) for c in C.CONSULTAS]
        self.db = conectar()

        # --- barra con el nombre y el estado de la conexión
        barra = tk.Frame(self, bg=BARRA)
        barra.pack(fill="x")
        tk.Label(barra, text="BDAutos", bg=BARRA, fg="white", font=(FUENTE[0], 14, "bold"),
                 padx=16, pady=10).pack(side="left")
        tk.Label(barra, text="Consultas MongoDB", bg=BARRA, fg="#9ca3af", font=FUENTE).pack(side="left")
        conectado = self.db is not None
        tk.Label(barra, text=f"● {'Conectado a ' + BD if conectado else 'Sin conexión a MongoDB'}", bg=BARRA,
                 fg="#4ade80" if conectado else "#f87171", font=FUENTE, padx=16).pack(side="right")

        # --- fila de arriba: selector y botones
        arriba = ttk.Frame(self, padding=(12, 12, 12, 4))
        arriba.pack(fill="x")
        ttk.Label(arriba, text="Consulta:").pack(side="left")
        self.selector = ttk.Combobox(arriba, state="readonly", height=30)
        self.selector.pack(side="left", fill="x", expand=True, padx=8)
        self.selector.bind("<<ComboboxSelected>>", lambda e: self.mostrar())
        for texto, accion, estilo_b in (("Ejecutar", self.mostrar, "Primario.TButton"),
                                        ("+ Nueva", self.nueva, "TButton"),
                                        ("Eliminar", self.eliminar, "Peligro.TButton"),
                                        ("Restaurar 25", self.restaurar, "TButton")):
            ttk.Button(arriba, text=texto, command=accion, style=estilo_b).pack(side="left", padx=3)

        self.descripcion = ttk.Label(self, padding=(14, 6), foreground="#4b5563", justify="left")
        self.descripcion.pack(fill="x")
        self.bind("<Configure>", lambda e: self.descripcion.config(wraplength=self.winfo_width() - 40))

        # --- código y resultado lado a lado
        panel = ttk.PanedWindow(self, orient="horizontal")
        panel.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        marco_cod, self.codigo = caja(panel, "Código")
        self.marco_res, self.resultado = caja(panel, "Resultado")
        panel.add(marco_cod, weight=1)
        panel.add(self.marco_res, weight=1)

        self.bind("<F5>", lambda e: self.mostrar())
        self.actualizar_selector(0)

    # ------------------------------------------------------------ utilidades
    def guardar(self):
        ARCHIVO.write_text(json.dumps(self.lista, ensure_ascii=False, indent=2), encoding="utf-8")

    def actualizar_selector(self, indice):
        self.lista.sort(key=lambda c: c["num"])
        self.selector["values"] = [f"{c['num']:02d}. {c['titulo']}" for c in self.lista]
        if self.lista:
            self.selector.current(min(indice, len(self.lista) - 1))
        else:
            self.selector.set("")
        self.mostrar()

    def actual(self):
        i = self.selector.current()
        return self.lista[i] if 0 <= i < len(self.lista) else None

    # ---------------------------------------------------------- mostrar
    def mostrar(self):
        c = self.actual()
        if c is None:
            self.descripcion.config(text="No hay consultas. Crea una con «Nueva» o usa «Restaurar 25».")
            poner(self.codigo, "")
            poner(self.resultado, "")
            return
        self.descripcion.config(text=c.get("descripcion") or "")
        poner(self.codigo, C.codigo(c))
        if self.db is None:
            self.marco_res.titulo.config(text="Resultado")
            poner(self.resultado, "No hay conexión con MongoDB.\nRevisa que el servidor esté encendido "
                                  "y vuelve a abrir la app.", ROJO)
            return
        try:
            docs = C.ejecutar(self.db, c)
        except Exception as e:  # noqa: BLE001
            self.marco_res.titulo.config(text="Resultado")
            poner(self.resultado, f"Error:\n{e}", ROJO)
            return
        self.marco_res.titulo.config(text=f"Resultado ({len(docs)} documento{'s' if len(docs) != 1 else ''})")
        poner(self.resultado, json.dumps(docs, ensure_ascii=False, indent=2, default=str))

    # ------------------------------------------------ crear / eliminar / restaurar
    def nueva(self):
        Nueva(self)

    def agregar(self, consulta):
        consulta["num"] = max([c["num"] for c in self.lista] + [25]) + 1
        self.lista.append(consulta)
        self.guardar()
        self.actualizar_selector(len(self.lista) - 1)

    def eliminar(self):
        c = self.actual()
        if c and messagebox.askyesno("Eliminar", f"¿Eliminar la consulta {c['num']:02d}?\n\n{c['titulo']}"):
            i = self.selector.current()
            self.lista.remove(c)
            self.guardar()
            self.actualizar_selector(i)

    def restaurar(self):
        hay = {c["num"] for c in self.lista}
        faltan = [dict(c) for c in C.CONSULTAS if c["num"] not in hay]
        if not faltan:
            messagebox.showinfo("Restaurar", "Ya están las 25 consultas originales.")
            return
        self.lista += faltan
        self.guardar()
        self.actualizar_selector(0)
        messagebox.showinfo("Restaurar", f"Se recuperaron {len(faltan)} consulta(s).")


class Nueva(tk.Toplevel):
    """Ventana para crear una consulta escribiéndola con diccionarios de Python (como en PyMongo)."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Nueva consulta")
        self.geometry("720x600")
        self.transient(app)
        self.grab_set()
        self.configure(bg=FONDO)
        cont = ttk.Frame(self, padding=16)
        cont.pack(fill="both", expand=True)

        ttk.Label(cont, text="Título:").pack(anchor="w")
        self.titulo = ttk.Entry(cont)
        self.titulo.pack(fill="x", pady=(0, 8))
        ttk.Label(cont, text="Descripción (opcional):").pack(anchor="w")
        self.desc = ttk.Entry(cont)
        self.desc.pack(fill="x", pady=(0, 8))

        fila = ttk.Frame(cont)
        fila.pack(fill="x", pady=(0, 8))
        ttk.Label(fila, text="Colección:").pack(side="left")
        self.coleccion = ttk.Combobox(fila, values=["cars", "makers"], state="readonly", width=10)
        self.coleccion.current(0)
        self.coleccion.pack(side="left", padx=(6, 18))
        ttk.Label(fila, text="Tipo:").pack(side="left")
        self.tipo = ttk.Combobox(fila, values=list(AYUDA), state="readonly", width=16)
        self.tipo.current(0)
        self.tipo.pack(side="left", padx=6)
        self.tipo.bind("<<ComboboxSelected>>", lambda e: self.poner_ejemplo())

        self.ayuda = ttk.Label(cont)
        self.ayuda.pack(anchor="w")
        self.codigo = tk.Text(cont, font=MONO, height=12, wrap="none", relief="flat", padx=10, pady=8,
                              highlightthickness=1, highlightbackground="#d5dbe5", highlightcolor=ACENTO)
        self.codigo.pack(fill="both", expand=True)
        self.poner_ejemplo()

        self.mensaje = ttk.Label(cont, text="", padding=(0, 8), wraplength=660)
        self.mensaje.pack(anchor="w")
        botones = ttk.Frame(cont)
        botones.pack(fill="x")
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar", command=self.guardar, style="Primario.TButton").pack(side="right", padx=6)
        ttk.Button(botones, text="Probar", command=self.probar).pack(side="right")
        self.titulo.focus_set()

    def poner_ejemplo(self):
        """Cambia la ayuda y el ejemplo según el tipo elegido."""
        texto, ejemplo = AYUDA[self.tipo.get()]
        self.ayuda.config(text=texto)
        self.codigo.delete("1.0", "end")
        self.codigo.insert("1.0", ejemplo)

    def probar(self):
        """Lee y ejecuta lo escrito. Regresa la consulta si funciona, o None."""
        try:
            c = {"coleccion": self.coleccion.get(), "tipo": self.tipo.get()}
            c.update(C.leer(c["tipo"], self.codigo.get("1.0", "end")))
            if self.app.db is not None:
                docs = C.ejecutar(self.app.db, c)
                self.mensaje.config(text=f"✔ Funciona ({len(docs)} documento(s))", foreground="#059669")
            return c
        except Exception as e:  # noqa: BLE001
            self.mensaje.config(text=f"✖ {e}", foreground=ROJO)
            return None

    def guardar(self):
        if not self.titulo.get().strip():
            self.mensaje.config(text="✖ Escribe un título.", foreground=ROJO)
            return
        c = self.probar()
        if c:
            c.update(titulo=self.titulo.get().strip(), descripcion=self.desc.get().strip())
            self.app.agregar(c)
            self.destroy()


if __name__ == "__main__":
    App().mainloop()
