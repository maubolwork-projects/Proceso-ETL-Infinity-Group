# Arquitectura Pipeline ETL

## Objetivo
Desarrollar un pipeline que satisfaga las necesidades del negocio el cual debera cumplir con metodos de validación de fuentes, 
inspección de duplicados, auditoria y carga incremental. Los cuales serán almacenados en una Base RAW.

## Fuentes
Archivos de Excel de diferentes áreas emuladas de una concretera.

## Motor ETL
### Implementado en Python, donde las funciones principales son:
- get_source_excel()
- validate_source()
- validate_duplicated()
- export_to_raw()
- add_hash ()
- get_source_sql()- 
- status_test()
- auditory()
- get_new_records()

## Base de datos PostgreSQL
Se utilizan tres tablas en la base de datos RAW:

### Tablas RAW
Almacena los datos tal cual se obtienen de producción, solamente añadiendo una columna Hash.
### Tabla de control de eventos
Tabla reporte que registra el tipo y la cantidad de eventos por ejecución.
### Tabla de auditoria
Registra los datos modificados o eliminados por ejecución.

## Estrategia de detección de cambios
la comparación se realiza monitoreando dos columnas
_Registro_ID + Hash_

### Generador de hash
El hash se calcula concatenando columnas de negocio:

RegistroID | Fecha | Material | Cantidad | PrecioUnitario | Total

Posteriormente se genera un MD5.

### Reglas de negocio
_Sin cambios :_ El hash almacenado en RAW es igual al de Excel.
Acción: no hacer nada

_Con cambios :_ El hash almacenado en RAW es diferente al de Excel.
Acción: No modifica RAW, se agrega registro a Auditoria y se reporta en control de cambios.

_Eliminado :_ El hash existe en RAW, pero no es encontrado en Excel.
Acción: No elimina en RAW, se agrega el registro en auditoria y se reporta en control de cambios.

_Nuevo Registro :_ El hash existe en Excel pero no se encuentra en RAW.
Acción: Se actualiza la tabla RAW con los nuevos datos.

## Flujo de ejecución
- Lectura de Excel
- Validación de estructura
- Validación de duplicados
- Generar Hash
- Validar existencia en RAW
- Comparar Hash
- Generar auditoria
- Cargar nuevos registros
- Generar tabla de control

## Casos validados
- Archivo vacio
- Archivo sin datos
- Columnas relevantes eliminadas
- Datos duplicados
- Filas en blanco
- Filas eliminadas
- Celdas en blanco
- Celdas eliminadas
- Sin cambios
- Cambios historicos
- Nuevos Registros
- Primera carga
