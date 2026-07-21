
# Pipeline ETL para consolidación de datos operativos

Este proyecto implementa un pipeline ETL orientado a la consolidación de información operativa proveniente de múltiples archivos Excel con estructuras heterogéneas.

El sistema automatiza la extracción, limpieza, validación y carga de datos hacia una base PostgreSQL utilizada como capa RAW, incorporando mecanismos de detección de cambios, evolución del esquema y auditoría de registros.

Actualmente el pipeline procesa información de distintas áreas de una empresa concretera, permitiendo integrar múltiples reportes con estructuras dinámicas sin modificar manualmente el código ante pequeños cambios en las fuentes.

El objetivo principal es establecer una base confiable para la construcción de una arquitectura de datos orientada a Data Engineering, permitiendo posteriormente el desarrollo de las capas **Staging** y **Data Warehouse**.

El pipeline fue diseñado para operar en un entorno donde la información proviene de procesos manuales y archivos Excel con diferentes formatos, encabezados desplazados, tablas auxiliares y criterios de captura distintos entre áreas.

---

# Objetivos

* Centralizar la información operativa de la empresa.
* Automatizar la ingestión de archivos Excel.
* Detectar errores antes de cargar la información.
* Mantener un historial de cambios sobre los registros.
* Preparar una capa RAW íntegra y trazable.
* Reducir el trabajo manual requerido para integrar información.

---
## Características

- Extracción automática de múltiples fuentes Excel.
- Detección automática del encabezado principal.
- Reconstrucción de encabezados distribuidos en varias filas.
- Limpieza automática de columnas y filas residuales.
- Eliminación de columnas fantasma.
- Identificación automática de registros mediante Hash MD5.
- Comparación contra la capa RAW.
- Detección de:
    - Nuevos registros.
    - Cambios.
    - Eliminaciones.
- Registro de auditoría.
- Gestión automática de evolución del esquema (Schema Evolution).
- Alineación automática de columnas (Schema Alignment).
- Corrección automática de cambios en encabezados (Schema Drift Resolution).

# Arquitectura General

Excel
     │
     ▼
Excel Parser
     │
     ▼
Header Detection
     │
     ▼
Header Combination
     │
     ▼
Residual Cleaning
     │
     ▼
Hash Generator
     │
     ▼
Schema Manager
     │
     ▼
Status Detection
     │
     ▼
RAW PostgreSQL
     │
     ├── Auditoría
     └── Control de Cambios
---

# Funcionalidades

El pipeline actualmente permite:

* Lectura automática de archivos Excel.
* Procesamiento de formatos libres.
* Eliminación de encabezados, títulos y resúmenes.
* Reconstrucción de encabezados multinivel.
* Validación de estructura.
* Validación de columnas obligatorias.
* Detección de registros duplicados.
* Adaptación automática cuando cambian los nombres de las columnas.
* Generación de Hash para control de cambios.
* Comparación contra la información almacenada en RAW.
* Detección de registros nuevos.
* Detección de modificaciones.
* Detección de registros eliminados.
* Generación de auditoría.
* Registro estadístico de cada ejecución.
* Carga incremental hacia PostgreSQL.

---

# Estructura del Proyecto

```text
Proyecto/
│
├── pipeline.py
├── excel_parser.py
├── schema_manager.py
├── resolve_hash_schema.py
├── sources.py
│
├── docs/
│   ├── README.md
│   ├── excel_parser.md
│   ├── schema_manager.py
│   ├── resolve_hash_schema.md
│   └── sources.md
│
└── sql/
```

---

# Bibliotecas

## excel_parser

Convierte archivos Excel con formato libre en tablas estructuradas listas para ser procesadas por el pipeline.

Documentación disponible en:

```
docs/excel_parser.md
```

---

## resolve_hash_schema

Actualiza automáticamente la configuración del sistema cuando cambian los nombres de las columnas utilizadas para construir el Hash.

Documentación disponible en:

```
docs/resolve_hash_schema.md
```
## Gestión automática del esquema

El módulo `schema_manager` permite que el pipeline continúe funcionando cuando las estructuras de los archivos cambian entre ejecuciones.

Actualmente soporta tres escenarios:

### Schema Evolution

Detecta columnas nuevas presentes en el archivo fuente y las agrega automáticamente a PostgreSQL.

### Schema Alignment

Cuando una tabla RAW contiene columnas que la fuente actual no posee, estas se agregan temporalmente al DataFrame para mantener la compatibilidad estructural durante la carga.

### Schema Drift Resolution
Cuando un encabezado cambia parcialmente (por ejemplo debido a desplazamientos ocasionados por celdas combinadas), el sistema identifica automáticamente la equivalencia entre columnas y renombra temporalmente el DataFrame para conservar la consistencia histórica del esquema.

---

## sources

Contiene el catálogo de todas las fuentes de información utilizadas por el pipeline.

Cada fuente define:

* Ruta del archivo.
* Hoja.
* Tabla destino.
* Columnas Hash.
* Llaves de comparación.
* Estatus

---

# Flujo del Pipeline

Para cada fuente de datos el proceso realiza las siguientes etapas:

1. Extraer el archivo Excel.
2. Detectar automáticamente el encabezado.
3. Reconstruir encabezados dinámicos.
4. Eliminar columnas residuales.
5. Validar estructura.
6. Configurar Hash.
7. Generar Hash.
8. Consultar RAW.
9. Gestionar cambios de esquema.
10. Detectar nuevos registros.
11. Detectar cambios.
12. Registrar auditoría.
13. Cargar registros nuevos.
14. Actualizar tabla de control.

---

# Estado del Proyecto

Versión actual: **1.6**

## Componentes implementados

* Ingestión hacia RAW.
* Parser para formatos libres.
* Gestión de esquema entre fuentes y destinos.
* Resolución dinámica del esquema del Hash.
* Auditoría de cambios.
* Control de cambios.
* Carga incremental.

## Próximas etapas

* Arquitectura completamente modular.
* Configuración mediante archivos YAML/JSON.
* Procesamiento concurrente.
* Validaciones configurables.
* Registro estructurado (logging).
* Pruebas unitarias.
* Adaptación para procesos ELT.

---

# Tecnologías utilizadas

* Python
* Pandas
* NumPy
* SQLAlchemy
* PostgreSQL

---

# Autor

Proyecto desarrollado como iniciativa de implementación de una arquitectura de datos para una empresa del sector concretero, con enfoque en Data Engineering y automatización de procesos ETL.
Desarrollado por: `Ing. Mauricio Isaias Bolaños Vazquez`
