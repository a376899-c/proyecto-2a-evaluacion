"""Las 25 consultas de BDAutos escritas con PyMongo (diccionarios de Python).

Cada consulta tiene:
  coleccion   -> "cars" o "makers"
  tipo        -> "find", "count_documents" o "aggregate"
  filtro, proyeccion, orden   (para find / count_documents)
  pipeline                    (para aggregate)

Uso por consola:
  python consultas.py        corre las 25 y muestra los resultados
  python consultas.py 7      corre solo la consulta 7
"""
import ast
import json
import sys

CONSULTAS = [
    {
        "num": 1,
        "titulo": "Autos 2024 en adelante con al menos 35 mpg, de mayor a menor rendimiento",
        "descripcion": "Obtener los autos de modelo 2024 en adelante con rendimiento de al menos 35 mpg. Mostrar solo la descripción, el año y el rendimiento, ordenados de mayor a menor rendimiento.",
        "coleccion": "cars",
        "tipo": "find",
        "filtro": {"year": {"$gte": 2024}, "specs.mpg": {"$gte": 35}},
        "proyeccion": {"_id": 0, "descr": 1, "year": 1, "specs.mpg": 1},
        "orden": {"specs.mpg": -1},
    },
    {
        "num": 2,
        "titulo": "Autos de fabricantes europeos, 4 cilindros y al menos 250 hp",
        "descripcion": "Listar los autos de fabricantes europeos con motor de 4 cilindros y al menos 250 hp, mostrando descripción, país y potencia, ordenados por potencia descendente.",
        "coleccion": "cars",
        "tipo": "find",
        "filtro": {
            "maker.continent": "europe",
            "specs.cylinders": 4,
            "specs.horsepower": {"$gte": 250}
        },
        "proyeccion": {"_id": 0, "descr": 1, "maker.country": 1, "specs.horsepower": 1},
        "orden": {"specs.horsepower": -1},
    },
    {
        "num": 3,
        "titulo": "Cuántos autos de fabricantes japoneses son turbo (descripción termina en cilindrada + 't')",
        "descripcion": "Contar cuántos autos de fabricantes japoneses tienen motor turbo, es decir, cuya descripción termina con la cilindrada seguida de \"t\" (por ejemplo \"1.5t\").",
        "coleccion": "cars",
        "tipo": "count_documents",
        "filtro": {"maker.country": "japan", "descr": {"$regex": "\\d\\.\\dt$"}},
    },
    {
        "num": 4,
        "titulo": "Autos ligeros y rápidos (< 3000 lb y < 9 s) o de 8+ cilindros con al menos 19 mpg",
        "descripcion": "Encontrar los autos que cumplan cualquiera de estas condiciones: (a) pesan menos de 3000 lb y aceleran de 0 a 60 mph en menos de 9 s, o (b) tienen 8 o más cilindros y rinden al menos 19 mpg.",
        "coleccion": "cars",
        "tipo": "find",
        "filtro": {
            "$or": [
                {"specs.weight": {"$lt": 3000}, "specs.accel": {"$lt": 9}},
                {"specs.cylinders": {"$gte": 8}, "specs.mpg": {"$gte": 19}}
            ]
        },
        "proyeccion": {
            "_id": 0,
            "descr": 1,
            "specs.weight": 1,
            "specs.accel": 1,
            "specs.cylinders": 1,
            "specs.mpg": 1
        },
    },
    {
        "num": 5,
        "titulo": "Fabricantes que comercializan más de una marca: nombre, país y modelos",
        "descripcion": "Obtener los fabricantes que comercializan más de una marca o línea de modelo, mostrando nombre, país y modelos.",
        "coleccion": "makers",
        "tipo": "find",
        "filtro": {"models.1": {"$exists": True}},
        "proyeccion": {"_id": 0, "name": 1, "country.name": 1, "models.name": 1},
    },
    {
        "num": 6,
        "titulo": "Autos cuya marca (model.name) es distinta del nombre del fabricante (maker.name)",
        "descripcion": "Encontrar los autos cuya marca (model.name) es distinta del nombre de su grupo fabricante (maker.name). Mostrar descripción, marca y fabricante.",
        "coleccion": "cars",
        "tipo": "find",
        "filtro": {"$expr": {"$ne": ["$model.name", "$maker.name"]}},
        "proyeccion": {"_id": 0, "descr": 1, "model.name": 1, "maker.name": 1},
    },
    {
        "num": 7,
        "titulo": "Por país: número de autos, rendimiento y potencia promedio",
        "descripcion": "Calcular por país el número de autos, el rendimiento promedio y la potencia promedio (redondeados a 1 decimal), ordenado por número de autos.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$group": {
                    "_id": "$maker.country",
                    "autos": {"$sum": 1},
                    "mpgProm": {"$avg": "$specs.mpg"},
                    "hpProm": {"$avg": "$specs.horsepower"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "pais": "$_id",
                    "autos": "$autos",
                    "mpgProm": {"$round": ["$mpgProm", 1]},
                    "hpProm": {"$round": ["$hpProm", 1]}
                }
            },
            {"$sort": {"autos": -1, "pais": 1}}
        ],
    },
    {
        "num": 8,
        "titulo": "Por fabricante: número de autos, marcas distintas y potencia promedio",
        "descripcion": "Calcular para cada grupo fabricante el número de autos, el número de marcas distintas con autos registrados y la potencia promedio (redondeada a 1 decimal), ordenado por número de autos.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$group": {
                    "_id": "$maker.name",
                    "autos": {"$sum": 1},
                    "marcas": {"$addToSet": "$model.name"},
                    "hpProm": {"$avg": "$specs.horsepower"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "fabricante": "$_id",
                    "autos": "$autos",
                    "marcasDistintas": {"$size": "$marcas"},
                    "hpProm": {"$round": ["$hpProm", 1]}
                }
            },
            {"$sort": {"autos": -1, "fabricante": 1}}
        ],
    },
    {
        "num": 9,
        "titulo": "Cuántos modelos (marcas) hay por continente",
        "descripcion": "Contar cuántos modelos (marcas) hay por continente.",
        "coleccion": "makers",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$group": {
                    "_id": "$country.continent",
                    "modelos": {"$sum": {"$size": "$models"}}
                }
            },
            {"$project": {"_id": 0, "continente": "$_id", "modelos": "$modelos"}},
            {"$sort": {"modelos": -1}}
        ],
    },
    {
        "num": 10,
        "titulo": "Autos por rango de rendimiento (mpg) y su peso promedio",
        "descripcion": "Clasificar los autos en rangos de rendimiento [0,20), [20,25), [25,30), [30,35), [35,40) y 40 o más, contando cuántos hay en cada rango y su peso promedio.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$bucket": {
                    "groupBy": "$specs.mpg",
                    "boundaries": [0, 20, 25, 30, 35, 40],
                    "default": "40 o más",
                    "output": {"autos": {"$sum": 1}, "pesoProm": {"$avg": "$specs.weight"}}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "rango": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$_id", 0]}, "then": "[0, 20)"},
                                {"case": {"$eq": ["$_id", 20]}, "then": "[20, 25)"},
                                {"case": {"$eq": ["$_id", 25]}, "then": "[25, 30)"},
                                {"case": {"$eq": ["$_id", 30]}, "then": "[30, 35)"},
                                {"case": {"$eq": ["$_id", 35]}, "then": "[35, 40)"}
                            ],
                            "default": "40 o más"
                        }
                    },
                    "autos": "$autos",
                    "pesoProm": {"$round": ["$pesoProm", 1]}
                }
            }
        ],
    },
    {
        "num": 11,
        "titulo": "Top 5 fabricantes con mayor rendimiento promedio (con al menos 8 autos)",
        "descripcion": "Obtener los 5 fabricantes con mayor rendimiento promedio, considerando solo aquellos con al menos 8 autos registrados.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$group": {
                    "_id": "$maker.name",
                    "autos": {"$sum": 1},
                    "mpgProm": {"$avg": "$specs.mpg"}
                }
            },
            {"$match": {"autos": {"$gte": 8}}},
            {"$sort": {"mpgProm": -1}},
            {"$limit": 5},
            {
                "$project": {
                    "_id": 0,
                    "fabricante": "$_id",
                    "autos": "$autos",
                    "mpgProm": {"$round": ["$mpgProm", 1]}
                }
            }
        ],
    },
    {
        "num": 12,
        "titulo": "Autos por continente y categoría de rendimiento (Alta / Media / Baja)",
        "descripcion": "Clasificar cada auto como \"Alta\" (mpg ≥ 30), \"Media\" (20 ≤ mpg < 30) o \"Baja\" (mpg < 20) y contar cuántos autos hay por continente y categoría.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$project": {
                    "continente": "$maker.continent",
                    "categoria": {
                        "$switch": {
                            "branches": [
                                {
                                    "case": {"$gte": ["$specs.mpg", 30]},
                                    "then": "Alta"
                                },
                                {
                                    "case": {"$gte": ["$specs.mpg", 20]},
                                    "then": "Media"
                                }
                            ],
                            "default": "Baja"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": {"continente": "$continente", "categoria": "$categoria"},
                    "autos": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "continente": "$_id.continente",
                    "categoria": "$_id.categoria",
                    "autos": "$autos"
                }
            },
            {"$sort": {"continente": 1, "categoria": 1}}
        ],
    },
    {
        "num": 13,
        "titulo": "Desde makers: cuántos autos tiene cada fabricante (incluidos los que tienen cero)",
        "descripcion": "Desde la colección makers, obtener cuántos autos tiene registrados cada fabricante (incluidos los que tienen cero).",
        "coleccion": "makers",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$lookup": {
                    "from": "cars",
                    "localField": "_id",
                    "foreignField": "maker._id",
                    "as": "autos"
                }
            },
            {
                "$project": {"_id": 0, "fabricante": "$name", "autos": {"$size": "$autos"}}
            },
            {"$sort": {"autos": -1, "fabricante": 1}}
        ],
    },
    {
        "num": 14,
        "titulo": "Modelos del catálogo sin ningún auto registrado",
        "descripcion": "Encontrar los modelos del catálogo que no tienen ningún auto registrado.",
        "coleccion": "makers",
        "tipo": "aggregate",
        "pipeline": [
            {"$unwind": "$models"},
            {
                "$lookup": {
                    "from": "cars",
                    "localField": "models._id",
                    "foreignField": "model._id",
                    "as": "autos"
                }
            },
            {"$match": {"autos": {"$size": 0}}},
            {
                "$project": {"_id": 0, "modelo": "$models.name", "fabricante": "$name"}
            }
        ],
    },
    {
        "num": 15,
        "titulo": "Los 5 autos más potentes con el nombre completo de su fabricante",
        "descripcion": "Para los 5 autos más potentes, obtener su descripción, potencia y el nombre completo (fullName) de su fabricante.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {"$sort": {"specs.horsepower": -1}},
            {"$limit": 5},
            {
                "$lookup": {
                    "from": "makers",
                    "localField": "maker._id",
                    "foreignField": "_id",
                    "as": "fab"
                }
            },
            {"$unwind": "$fab"},
            {
                "$project": {
                    "_id": 0,
                    "descr": "$descr",
                    "horsepower": "$specs.horsepower",
                    "fullName": "$fab.fullName"
                }
            }
        ],
    },
    {
        "num": 16,
        "titulo": "Por continente, los 3 autos con mayor rendimiento",
        "descripcion": "Obtener, para cada continente, los 3 autos con mayor rendimiento (descripción y mpg).",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {"$sort": {"specs.mpg": -1, "descr": 1}},
            {
                "$group": {
                    "_id": "$maker.continent",
                    "autos": {"$push": {"descr": "$descr", "mpg": "$specs.mpg"}}
                }
            },
            {
                "$project": {"_id": 0, "continente": "$_id", "top3": {"$slice": ["$autos", 3]}}
            },
            {"$sort": {"continente": 1}}
        ],
    },
    {
        "num": 17,
        "titulo": "Fabricantes con más de un modelo: cuál de sus modelos tiene más autos",
        "descripcion": "Para cada fabricante con más de un modelo, determinar cuál de sus modelos tiene más autos registrados.",
        "coleccion": "makers",
        "tipo": "aggregate",
        "pipeline": [
            {"$match": {"models.1": {"$exists": True}}},
            {"$unwind": "$models"},
            {
                "$lookup": {
                    "from": "cars",
                    "localField": "models._id",
                    "foreignField": "model._id",
                    "as": "autos"
                }
            },
            {
                "$group": {
                    "_id": "$name",
                    "modelos": {
                        "$push": {"modelo": "$models.name", "autos": {"$size": "$autos"}}
                    },
                    "maxAutos": {"$max": {"$size": "$autos"}}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "fabricante": "$_id",
                    "autos": "$maxAutos",
                    "modeloConMasAutos": {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$modelos",
                                    "as": "m",
                                    "cond": {"$eq": ["$$m.autos", "$maxAutos"]}
                                }
                            },
                            "as": "m",
                            "in": "$$m.modelo"
                        }
                    }
                }
            },
            {"$sort": {"fabricante": 1}}
        ],
    },
    {
        "num": 18,
        "titulo": "Porcentaje de autos de cada continente sobre el total",
        "descripcion": "Calcular el porcentaje que representa cada continente sobre el total de autos, con 2 decimales.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {"$group": {"_id": "$maker.continent", "autos": {"$sum": 1}}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$autos"},
                    "continentes": {"$push": {"continente": "$_id", "autos": "$autos"}}
                }
            },
            {"$unwind": "$continentes"},
            {
                "$project": {
                    "_id": 0,
                    "continente": "$continentes.continente",
                    "autos": "$continentes.autos",
                    "porcentaje": {
                        "$round": [
                            {
                                "$multiply": [{"$divide": ["$continentes.autos", "$total"]}, 100]
                            },
                            2
                        ]
                    }
                }
            },
            {"$sort": {"porcentaje": -1}}
        ],
    },
    {
        "num": 19,
        "titulo": "5 autos que más superan el rendimiento promedio de su número de cilindros",
        "descripcion": "Listar los 5 autos que más superan el rendimiento promedio de los autos con su mismo número de cilindros, mostrando ese promedio y la diferencia.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$setWindowFields": {
                    "partitionBy": "$specs.cylinders",
                    "output": {"mpgPromCil": {"$avg": "$specs.mpg"}}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "descr": "$descr",
                    "cilindros": "$specs.cylinders",
                    "mpg": "$specs.mpg",
                    "mpgPromCil": {"$round": ["$mpgPromCil", 1]},
                    "diferencia": {"$round": [{"$subtract": ["$specs.mpg", "$mpgPromCil"]}, 1]}
                }
            },
            {"$sort": {"diferencia": -1}},
            {"$limit": 5}
        ],
    },
    {
        "num": 20,
        "titulo": "Por continente: autos, cuántos tienen 8+ cilindros y su porcentaje",
        "descripcion": "Calcular, por continente, el número de autos, cuántos tienen 8 o más cilindros y el porcentaje que representan (1 decimal).",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$group": {
                    "_id": "$maker.continent",
                    "autos": {"$sum": 1},
                    "ochoOMas": {"$sum": {"$cond": [{"$gte": ["$specs.cylinders", 8]}, 1, 0]}}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "continente": "$_id",
                    "autos": "$autos",
                    "ochoOMas": "$ochoOMas",
                    "porcentaje": {
                        "$round": [
                            {
                                "$multiply": [{"$divide": ["$ochoOMas", "$autos"]}, 100]
                            },
                            1
                        ]
                    }
                }
            },
            {"$sort": {"autos": -1}}
        ],
    },
    {
        "num": 21,
        "titulo": "Top 10 autos por potencia por cada 1000 lb de peso, con su país",
        "descripcion": "Calcular la potencia por cada 1000 lb de peso y mostrar los 10 autos con mayor valor, junto con su país.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$project": {
                    "_id": 0,
                    "descr": "$descr",
                    "pais": "$maker.country",
                    "hpPor1000lb": {
                        "$round": [
                            {
                                "$multiply": [
                                    {
                                        "$divide": ["$specs.horsepower", "$specs.weight"]
                                    },
                                    1000
                                ]
                            },
                            1
                        ]
                    }
                }
            },
            {"$sort": {"hpPor1000lb": -1}},
            {"$limit": 10}
        ],
    },
    {
        "num": 22,
        "titulo": "Por fabricante, solo los modelos con nombre distinto al del fabricante",
        "descripcion": "Para cada fabricante, mostrar solo los modelos cuyo nombre es distinto al nombre del fabricante, descartando a los fabricantes que no tengan ninguno.",
        "coleccion": "makers",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$project": {
                    "_id": 0,
                    "fabricante": "$name",
                    "modelos": {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$models",
                                    "as": "m",
                                    "cond": {"$ne": ["$$m.name", "$name"]}
                                }
                            },
                            "as": "m",
                            "in": "$$m.name"
                        }
                    }
                }
            },
            {"$match": {"modelos.0": {"$exists": True}}},
            {"$sort": {"fabricante": 1}}
        ],
    },
    {
        "num": 23,
        "titulo": "En una sola consulta: autos por continente, autos por cilindros y estadísticas de mpg",
        "descripcion": "En una sola consulta, obtener: (a) el número de autos por continente, (b) el número de autos por cilindros y (c) las estadísticas globales de mpg (mínimo, máximo y promedio).",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {
                "$facet": {
                    "porContinente": [
                        {
                            "$group": {"_id": "$maker.continent", "autos": {"$sum": 1}}
                        },
                        {"$sort": {"autos": -1}}
                    ],
                    "porCilindros": [
                        {
                            "$group": {"_id": "$specs.cylinders", "autos": {"$sum": 1}}
                        },
                        {"$sort": {"_id": 1}}
                    ],
                    "estadisticasMpg": [
                        {
                            "$group": {
                                "_id": None,
                                "min": {"$min": "$specs.mpg"},
                                "max": {"$max": "$specs.mpg"},
                                "promedio": {"$avg": "$specs.mpg"}
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "min": 1,
                                "max": 1,
                                "promedio": {"$round": ["$promedio", 2]}
                            }
                        }
                    ]
                }
            }
        ],
    },
    {
        "num": 24,
        "titulo": "Autos alemanes: posición por potencia dentro de su país (5 primeros)",
        "descripcion": "Asignar a cada auto alemán su posición por potencia dentro de su país y mostrar los 5 primeros.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {"$match": {"maker.country": "germany"}},
            {
                "$setWindowFields": {
                    "partitionBy": "$maker.country",
                    "sortBy": {"specs.horsepower": -1},
                    "output": {"posicion": {"$rank": {}}}
                }
            },
            {"$match": {"posicion": {"$lte": 5}}},
            {
                "$project": {
                    "_id": 0,
                    "posicion": "$posicion",
                    "descr": "$descr",
                    "fabricante": "$maker.name",
                    "horsepower": "$specs.horsepower"
                }
            }
        ],
    },
    {
        "num": 25,
        "titulo": "Para cada fabricante europeo, su auto más eficiente (mayor mpg)",
        "descripcion": "Obtener para cada fabricante europeo su auto más eficiente.",
        "coleccion": "cars",
        "tipo": "aggregate",
        "pipeline": [
            {"$match": {"maker.continent": "europe"}},
            {"$sort": {"specs.mpg": -1, "descr": 1}},
            {
                "$group": {
                    "_id": "$maker.name",
                    "descr": {"$first": "$descr"},
                    "mpg": {"$first": "$specs.mpg"},
                    "pais": {"$first": "$maker.country"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "fabricante": "$_id",
                    "pais": "$pais",
                    "descr": "$descr",
                    "mpg": "$mpg"
                }
            },
            {"$sort": {"mpg": -1}}
        ],
    },
]


def ejecutar(db, c):
    """Corre la consulta con PyMongo y regresa una lista de documentos."""
    coleccion = db[c["coleccion"]]
    if c["tipo"] == "count_documents":
        return [{"total": coleccion.count_documents(c.get("filtro", {}))}]
    if c["tipo"] == "find":
        cursor = coleccion.find(c.get("filtro", {}), c.get("proyeccion"))
        if c.get("orden"):
            cursor = cursor.sort(list(c["orden"].items()))
        return list(cursor)
    return list(coleccion.aggregate(c["pipeline"]))


def _py(v, sangria=0, ancho=70):
    """Escribe un valor como código Python (comillas dobles, True/False/None)."""
    if v is None or v is True or v is False:
        return str(v)
    if isinstance(v, str):
        if "\\" in v and '"' not in v:
            return f'r"{v}"'                    # texto con \ (expresión regular): r"..."
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, dict):
        partes = [f"{json.dumps(k, ensure_ascii=False)}: {_py(x, sangria + 4, ancho)}" for k, x in v.items()]
        a, z = "{", "}"
    else:
        partes = [_py(x, sangria + 4, ancho) for x in v]
        a, z = "[", "]"
    corto = a + ", ".join(partes) + z
    if len(corto) + sangria <= ancho or not partes:
        return corto
    pad = " " * (sangria + 4)
    return a + "\n" + ",\n".join(pad + p for p in partes) + "\n" + " " * sangria + z


def codigo(c):
    """Texto del código PyMongo de la consulta (lo que se muestra en la app)."""
    col = f"db.{c['coleccion']}"
    if c["tipo"] == "aggregate":
        etapas = ",\n".join("    " + _py(e, 4) for e in c["pipeline"])
        return f"pipeline = [\n{etapas}\n]\n\nresultado = list({col}.aggregate(pipeline))"
    if c["tipo"] == "count_documents":
        return f"resultado = {col}.count_documents({_py(c.get('filtro', {}))})"
    texto = f"filtro = {_py(c.get('filtro', {}))}\n"
    args = "filtro"
    if c.get("proyeccion"):
        texto += f"proyeccion = {_py(c['proyeccion'])}\n"
        args += ", proyeccion"
    texto += f"\nresultado = list({col}.find({args})"
    for campo, sentido in (c.get("orden") or {}).items():
        texto += f'.sort("{campo}", {sentido})'
    return texto + ")"


def leer(tipo, texto):
    """Convierte lo que escribe el usuario (diccionarios de Python) en las partes de la consulta.

    aggregate        ->  [ {"$match": ...}, {"$group": ...} ]
    find             ->  {filtro}   o   {filtro}, {proyeccion}   o   {filtro}, {proyeccion}, {orden}
    count_documents  ->  {filtro}
    """
    try:
        valor = ast.literal_eval(texto.strip())  # lee texto de Python de forma segura (solo datos)
    except (ValueError, SyntaxError):
        raise ValueError("Sintaxis inválida. Revisa llaves { }, corchetes [ ], comas, comillas dobles "
                         "y que True/False/None vayan con mayúscula.") from None
    if tipo == "aggregate":
        if not isinstance(valor, list) or not all(isinstance(e, dict) for e in valor):
            raise ValueError("El pipeline debe ser una lista de etapas: [ {...}, {...} ]")
        return {"pipeline": valor}
    partes = valor if isinstance(valor, tuple) else (valor,)
    if not all(isinstance(p, dict) for p in partes):
        raise ValueError("Escribe diccionarios: { ... }")
    if tipo == "count_documents":
        return {"filtro": partes[0]}
    nombres = ("filtro", "proyeccion", "orden")
    return {nombre: parte for nombre, parte in zip(nombres, partes)}


if __name__ == "__main__":
    from conexion import get_db
    db = get_db("mongodb://localhost:27017", "BDAutos")
    nums = [int(a) for a in sys.argv[1:] if a.isdigit()] or [c["num"] for c in CONSULTAS]
    for c in CONSULTAS:
        if c["num"] in nums:
            print(f"\n{'=' * 70}\n{c['num']}. {c['titulo']}\n{'-' * 70}")
            print(codigo(c))
            resultado = ejecutar(db, c)
            print(f"--- {len(resultado)} documento(s) ---")
            for doc in resultado:
                print(doc)
