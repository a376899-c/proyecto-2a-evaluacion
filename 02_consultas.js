// BDAutos - consultas (generado desde consultas.json)
// Correr en mongosh:  mongosh 02_consultas.js

db = db.getSiblingDB('BDAutos');

// 1. Autos 2024 en adelante con al menos 35 mpg, de mayor a menor rendimiento
print('\n===== Consulta 1 =====');
printjson(db.cars.find(
  { year: { $gte: 2024 }, 'specs.mpg': { $gte: 35 } },
  { _id: 0, descr: 1, year: 1, 'specs.mpg': 1 }
).sort({ 'specs.mpg': -1 }).toArray());

// 2. Autos de fabricantes europeos, 4 cilindros y al menos 250 hp
print('\n===== Consulta 2 =====');
printjson(db.cars.find(
  {
    'maker.continent': 'europe',
    'specs.cylinders': 4,
    'specs.horsepower': { $gte: 250 }
  },
  { _id: 0, descr: 1, 'maker.country': 1, 'specs.horsepower': 1 }
).sort({ 'specs.horsepower': -1 }).toArray());

// 3. Cuántos autos de fabricantes japoneses son turbo (descripción termina en cilindrada + 't')
print('\n===== Consulta 3 =====');
printjson(db.cars.countDocuments({ 'maker.country': 'japan', descr: /\d\.\dt$/ }));

// 4. Autos ligeros y rápidos (< 3000 lb y < 9 s) o de 8+ cilindros con al menos 19 mpg
print('\n===== Consulta 4 =====');
printjson(db.cars.find(
  {
    $or: [
      { 'specs.weight': { $lt: 3000 }, 'specs.accel': { $lt: 9 } },
      { 'specs.cylinders': { $gte: 8 }, 'specs.mpg': { $gte: 19 } }
    ]
  },
  {
    _id: 0,
    descr: 1,
    'specs.weight': 1,
    'specs.accel': 1,
    'specs.cylinders': 1,
    'specs.mpg': 1
  }
).toArray());

// 5. Fabricantes que comercializan más de una marca: nombre, país y modelos
print('\n===== Consulta 5 =====');
printjson(db.makers.find(
  { 'models.1': { $exists: true } },
  { _id: 0, name: 1, 'country.name': 1, 'models.name': 1 }
).toArray());

// 6. Autos cuya marca (model.name) es distinta del nombre del fabricante (maker.name)
print('\n===== Consulta 6 =====');
printjson(db.cars.find(
  { $expr: { $ne: ['$model.name', '$maker.name'] } },
  { _id: 0, descr: 1, 'model.name': 1, 'maker.name': 1 }
).toArray());

// 7. Por país: número de autos, rendimiento y potencia promedio
print('\n===== Consulta 7 =====');
printjson(db.cars.aggregate([
  {
    $group: {
      _id: '$maker.country',
      autos: { $sum: 1 },
      mpgProm: { $avg: '$specs.mpg' },
      hpProm: { $avg: '$specs.horsepower' }
    }
  },
  {
    $project: {
      _id: 0,
      pais: '$_id',
      autos: '$autos',
      mpgProm: { $round: ['$mpgProm', 1] },
      hpProm: { $round: ['$hpProm', 1] }
    }
  },
  { $sort: { autos: -1, pais: 1 } }
]).toArray());

// 8. Por fabricante: número de autos, marcas distintas y potencia promedio
print('\n===== Consulta 8 =====');
printjson(db.cars.aggregate([
  {
    $group: {
      _id: '$maker.name',
      autos: { $sum: 1 },
      marcas: { $addToSet: '$model.name' },
      hpProm: { $avg: '$specs.horsepower' }
    }
  },
  {
    $project: {
      _id: 0,
      fabricante: '$_id',
      autos: '$autos',
      marcasDistintas: { $size: '$marcas' },
      hpProm: { $round: ['$hpProm', 1] }
    }
  },
  { $sort: { autos: -1, fabricante: 1 } }
]).toArray());

// 9. Cuántos modelos (marcas) hay por continente
print('\n===== Consulta 9 =====');
printjson(db.makers.aggregate([
  {
    $group: { _id: '$country.continent', modelos: { $sum: { $size: '$models' } } }
  },
  { $project: { _id: 0, continente: '$_id', modelos: '$modelos' } },
  { $sort: { modelos: -1 } }
]).toArray());

// 10. Autos por rango de rendimiento (mpg) y su peso promedio
print('\n===== Consulta 10 =====');
printjson(db.cars.aggregate([
  {
    $bucket: {
      groupBy: '$specs.mpg',
      boundaries: [0, 20, 25, 30, 35, 40],
      default: '40 o más',
      output: { autos: { $sum: 1 }, pesoProm: { $avg: '$specs.weight' } }
    }
  },
  {
    $project: {
      _id: 0,
      rango: {
        $switch: {
          branches: [
            { case: { $eq: ['$_id', 0] }, then: '[0, 20)' },
            { case: { $eq: ['$_id', 20] }, then: '[20, 25)' },
            { case: { $eq: ['$_id', 25] }, then: '[25, 30)' },
            { case: { $eq: ['$_id', 30] }, then: '[30, 35)' },
            { case: { $eq: ['$_id', 35] }, then: '[35, 40)' }
          ],
          default: '40 o más'
        }
      },
      autos: '$autos',
      pesoProm: { $round: ['$pesoProm', 1] }
    }
  }
]).toArray());

// 11. Top 5 fabricantes con mayor rendimiento promedio (con al menos 8 autos)
print('\n===== Consulta 11 =====');
printjson(db.cars.aggregate([
  {
    $group: {
      _id: '$maker.name',
      autos: { $sum: 1 },
      mpgProm: { $avg: '$specs.mpg' }
    }
  },
  { $match: { autos: { $gte: 8 } } },
  { $sort: { mpgProm: -1 } },
  { $limit: 5 },
  {
    $project: {
      _id: 0,
      fabricante: '$_id',
      autos: '$autos',
      mpgProm: { $round: ['$mpgProm', 1] }
    }
  }
]).toArray());

// 12. Autos por continente y categoría de rendimiento (Alta / Media / Baja)
print('\n===== Consulta 12 =====');
printjson(db.cars.aggregate([
  {
    $project: {
      continente: '$maker.continent',
      categoria: {
        $switch: {
          branches: [
            { case: { $gte: ['$specs.mpg', 30] }, then: 'Alta' },
            { case: { $gte: ['$specs.mpg', 20] }, then: 'Media' }
          ],
          default: 'Baja'
        }
      }
    }
  },
  {
    $group: {
      _id: { continente: '$continente', categoria: '$categoria' },
      autos: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      continente: '$_id.continente',
      categoria: '$_id.categoria',
      autos: '$autos'
    }
  },
  { $sort: { continente: 1, categoria: 1 } }
]).toArray());

// 13. Desde makers: cuántos autos tiene cada fabricante (incluidos los que tienen cero)
print('\n===== Consulta 13 =====');
printjson(db.makers.aggregate([
  {
    $lookup: {
      from: 'cars',
      localField: '_id',
      foreignField: 'maker._id',
      as: 'autos'
    }
  },
  { $project: { _id: 0, fabricante: '$name', autos: { $size: '$autos' } } },
  { $sort: { autos: -1, fabricante: 1 } }
]).toArray());

// 14. Modelos del catálogo sin ningún auto registrado
print('\n===== Consulta 14 =====');
printjson(db.makers.aggregate([
  { $unwind: '$models' },
  {
    $lookup: {
      from: 'cars',
      localField: 'models._id',
      foreignField: 'model._id',
      as: 'autos'
    }
  },
  { $match: { autos: { $size: 0 } } },
  { $project: { _id: 0, modelo: '$models.name', fabricante: '$name' } }
]).toArray());

// 15. Los 5 autos más potentes con el nombre completo de su fabricante
print('\n===== Consulta 15 =====');
printjson(db.cars.aggregate([
  { $sort: { 'specs.horsepower': -1 } },
  { $limit: 5 },
  {
    $lookup: {
      from: 'makers',
      localField: 'maker._id',
      foreignField: '_id',
      as: 'fab'
    }
  },
  { $unwind: '$fab' },
  {
    $project: {
      _id: 0,
      descr: '$descr',
      horsepower: '$specs.horsepower',
      fullName: '$fab.fullName'
    }
  }
]).toArray());

// 16. Por continente, los 3 autos con mayor rendimiento
print('\n===== Consulta 16 =====');
printjson(db.cars.aggregate([
  { $sort: { 'specs.mpg': -1, descr: 1 } },
  {
    $group: {
      _id: '$maker.continent',
      autos: { $push: { descr: '$descr', mpg: '$specs.mpg' } }
    }
  },
  {
    $project: { _id: 0, continente: '$_id', top3: { $slice: ['$autos', 3] } }
  },
  { $sort: { continente: 1 } }
]).toArray());

// 17. Fabricantes con más de un modelo: cuál de sus modelos tiene más autos
print('\n===== Consulta 17 =====');
printjson(db.makers.aggregate([
  { $match: { 'models.1': { $exists: true } } },
  { $unwind: '$models' },
  {
    $lookup: {
      from: 'cars',
      localField: 'models._id',
      foreignField: 'model._id',
      as: 'autos'
    }
  },
  {
    $group: {
      _id: '$name',
      modelos: { $push: { modelo: '$models.name', autos: { $size: '$autos' } } },
      maxAutos: { $max: { $size: '$autos' } }
    }
  },
  {
    $project: {
      _id: 0,
      fabricante: '$_id',
      autos: '$maxAutos',
      modeloConMasAutos: {
        $map: {
          input: {
            $filter: {
              input: '$modelos',
              as: 'm',
              cond: { $eq: ['$$m.autos', '$maxAutos'] }
            }
          },
          as: 'm',
          in: '$$m.modelo'
        }
      }
    }
  },
  { $sort: { fabricante: 1 } }
]).toArray());

// 18. Porcentaje de autos de cada continente sobre el total
print('\n===== Consulta 18 =====');
printjson(db.cars.aggregate([
  { $group: { _id: '$maker.continent', autos: { $sum: 1 } } },
  {
    $group: {
      _id: null,
      total: { $sum: '$autos' },
      continentes: { $push: { continente: '$_id', autos: '$autos' } }
    }
  },
  { $unwind: '$continentes' },
  {
    $project: {
      _id: 0,
      continente: '$continentes.continente',
      autos: '$continentes.autos',
      porcentaje: {
        $round: [
          { $multiply: [{ $divide: ['$continentes.autos', '$total'] }, 100] },
          2
        ]
      }
    }
  },
  { $sort: { porcentaje: -1 } }
]).toArray());

// 19. 5 autos que más superan el rendimiento promedio de su número de cilindros
print('\n===== Consulta 19 =====');
printjson(db.cars.aggregate([
  {
    $setWindowFields: {
      partitionBy: '$specs.cylinders',
      output: { mpgPromCil: { $avg: '$specs.mpg' } }
    }
  },
  {
    $project: {
      _id: 0,
      descr: '$descr',
      cilindros: '$specs.cylinders',
      mpg: '$specs.mpg',
      mpgPromCil: { $round: ['$mpgPromCil', 1] },
      diferencia: { $round: [{ $subtract: ['$specs.mpg', '$mpgPromCil'] }, 1] }
    }
  },
  { $sort: { diferencia: -1 } },
  { $limit: 5 }
]).toArray());

// 20. Por continente: autos, cuántos tienen 8+ cilindros y su porcentaje
print('\n===== Consulta 20 =====');
printjson(db.cars.aggregate([
  {
    $group: {
      _id: '$maker.continent',
      autos: { $sum: 1 },
      ochoOMas: { $sum: { $cond: [{ $gte: ['$specs.cylinders', 8] }, 1, 0] } }
    }
  },
  {
    $project: {
      _id: 0,
      continente: '$_id',
      autos: '$autos',
      ochoOMas: '$ochoOMas',
      porcentaje: {
        $round: [{ $multiply: [{ $divide: ['$ochoOMas', '$autos'] }, 100] }, 1]
      }
    }
  },
  { $sort: { autos: -1 } }
]).toArray());

// 21. Top 10 autos por potencia por cada 1000 lb de peso, con su país
print('\n===== Consulta 21 =====');
printjson(db.cars.aggregate([
  {
    $project: {
      _id: 0,
      descr: '$descr',
      pais: '$maker.country',
      hpPor1000lb: {
        $round: [
          {
            $multiply: [{ $divide: ['$specs.horsepower', '$specs.weight'] }, 1000]
          },
          1
        ]
      }
    }
  },
  { $sort: { hpPor1000lb: -1 } },
  { $limit: 10 }
]).toArray());

// 22. Por fabricante, solo los modelos con nombre distinto al del fabricante
print('\n===== Consulta 22 =====');
printjson(db.makers.aggregate([
  {
    $project: {
      _id: 0,
      fabricante: '$name',
      modelos: {
        $map: {
          input: {
            $filter: {
              input: '$models',
              as: 'm',
              cond: { $ne: ['$$m.name', '$name'] }
            }
          },
          as: 'm',
          in: '$$m.name'
        }
      }
    }
  },
  { $match: { 'modelos.0': { $exists: true } } },
  { $sort: { fabricante: 1 } }
]).toArray());

// 23. En una sola consulta: autos por continente, autos por cilindros y estadísticas de mpg
print('\n===== Consulta 23 =====');
printjson(db.cars.aggregate([
  {
    $facet: {
      porContinente: [
        { $group: { _id: '$maker.continent', autos: { $sum: 1 } } },
        { $sort: { autos: -1 } }
      ],
      porCilindros: [
        { $group: { _id: '$specs.cylinders', autos: { $sum: 1 } } },
        { $sort: { _id: 1 } }
      ],
      estadisticasMpg: [
        {
          $group: {
            _id: null,
            min: { $min: '$specs.mpg' },
            max: { $max: '$specs.mpg' },
            promedio: { $avg: '$specs.mpg' }
          }
        },
        {
          $project: { _id: 0, min: 1, max: 1, promedio: { $round: ['$promedio', 2] } }
        }
      ]
    }
  }
]).toArray());

// 24. Autos alemanes: posición por potencia dentro de su país (5 primeros)
print('\n===== Consulta 24 =====');
printjson(db.cars.aggregate([
  { $match: { 'maker.country': 'germany' } },
  {
    $setWindowFields: {
      partitionBy: '$maker.country',
      sortBy: { 'specs.horsepower': -1 },
      output: { posicion: { $rank: {} } }
    }
  },
  { $match: { posicion: { $lte: 5 } } },
  {
    $project: {
      _id: 0,
      posicion: '$posicion',
      descr: '$descr',
      fabricante: '$maker.name',
      horsepower: '$specs.horsepower'
    }
  }
]).toArray());

// 25. Para cada fabricante europeo, su auto más eficiente (mayor mpg)
print('\n===== Consulta 25 =====');
printjson(db.cars.aggregate([
  { $match: { 'maker.continent': 'europe' } },
  { $sort: { 'specs.mpg': -1, descr: 1 } },
  {
    $group: {
      _id: '$maker.name',
      descr: { $first: '$descr' },
      mpg: { $first: '$specs.mpg' },
      pais: { $first: '$maker.country' }
    }
  },
  {
    $project: {
      _id: 0,
      fabricante: '$_id',
      pais: '$pais',
      descr: '$descr',
      mpg: '$mpg'
    }
  },
  { $sort: { mpg: -1 } }
]).toArray());
