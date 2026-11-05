# BDAutos en MongoDB — Proyecto 1 (Base de Datos II)

## Forma rápida (Windows)
Doble clic en `instalar_y_correr.bat`: instala lo que falte (Python y pymongo), crea la base, corre las 25 consultas y abre la app. Deja el registro en `log_ejecucion.txt` y los resultados en `resultados_consultas.txt`.

## Archivos
- `conexion.py` — conexión con PyMongo: `get_db(uri, db_name)`.
- `crear_bd.py` — crea la base BDAutos desde Python (`create_collection`, `insert_many`, `create_index`).
- `01_crear_bdautos.js` — lo mismo pero para mongosh / Compass.
- `consultas.py` — las 25 consultas escritas con diccionarios de PyMongo y las funciones para ejecutarlas.
- `02_consultas.js` — las mismas 25 consultas en sintaxis mongosh.
- `app_consultas.py` / `abrir_app.bat` — la interfaz.
- `Proyecto 1 - Modelado BDAutos en MongoDB` (.docx / .pdf) y los diagramas `er_original.png`, `modelo_mongodb.png`.

## Cómo correrlo a mano
1. MongoDB encendido (localhost:27017).
2. `pip install pymongo`
3. `python crear_bd.py`        (crea la base)
4. `python consultas.py`       (muestra las 25 consultas y sus resultados; `python consultas.py 7` solo la 7)
5. `python app_consultas.py`   (abre la app)

## La app
- Arriba se elige la consulta; abajo se ve su código PyMongo y su resultado.
- **Ejecutar** (o F5) la vuelve a correr.
- **+ Nueva**: título, colección, tipo (`aggregate`, `find`, `count_documents`) y la consulta escrita con diccionarios de Python, igual que en PyMongo. **Probar** la ejecuta; **Guardar** solo guarda si funciona.
- **Eliminar** (pide confirmación) y **Restaurar 25** (recupera las originales borradas).
- Las consultas se guardan en `mis_consultas.json`; la base de datos no se modifica.
