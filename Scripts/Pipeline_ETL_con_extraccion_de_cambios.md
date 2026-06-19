# Pipeline ETL con extracción de cambios

### Descripción
Este proyecto implementa un proceso ETL desarrollado en Python, el cual se divide en los siguientes pasos: Extracción, importa archivos de excel y valida que tenga la estructura correcta para su procesamiento (sin registros, vacío, incompleto o duplicado) de no cumplirlo detiene el proceso, si cumple con la anterior pasa a un proceso básico de limpieza eliminando filas en blanco, después hace un mini proceso CDC agregando un hash, el cual es auditable y pasa a un proceso SDC tipo 2, reportando en dos tablas diferentes los cambios y las datos cambiadosc, finalmente solo carga los datos nuevos a una base de datos RAW en PostgreSQL.

### Tecnologías
- Python
- Pandas
- Numpy
- SQLAlchemy
- PostgreSQL
- Excel

### Funcionalidades
_Extracción :_
- Lectura de archivos de Excel
- Soporte para múltiples fuentes con configuración centralizada

_Validación :_
- Archivos Vacío
- Sin Registros
- Columnas obligatorias faltantes
- Duplicados

_Transformación :_
- Generación de Hash con MD5 utilizando como fuente las columnas más importante de negocio
- Normalización de valores nulos

_Detección de cambios :_
- Eliminados
- Cambio histórico
- Nuevo registro
- Sin cambios

_Auditoria :_
Los registros modificados y eliminados son almacenados en una tabla para su posterior análisis.

_Carga Incremental :_
Solo se insertan registros nuevos a la base de datos RAW

_Control de ejecución :_
Los cambios se registran en una tabla por cada ejecución.

### Flujo general

Excel -> Validación -> Hash -> Auditoria -> Control -> RAW

### Tablas utilizadas

**RAW**
Base de datos principal donde llegan los datos sin modificar de producción.

**Auditoria**
Base en la cual se registran los datos con cambios o eliminados.

**Control de cambios**
Guarda la cantidad de datos sin cambios, modificados o eliminados en una ejecución.

### Estado del Proyecto

_Versión 1.0 estable._
Funcionalidades implementadas:

- Carga de datos
- Detección de cambios
- Auditoria
- Control de ejecución
- Validación de fuentes

