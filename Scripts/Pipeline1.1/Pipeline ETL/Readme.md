
# Pipeline de Ingestión de Datos – Concretera

## Descripción

Este proyecto implementa un pipeline de ingestión de datos desarrollado en Python para integrar información proveniente de múltiples archivos Microsoft Excel con estructuras heterogéneas hacia una base de datos PostgreSQL en la capa **RAW**.

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

# Arquitectura General

```text
Excel Operativo
        │
        ▼
 excel_parser
        │
        ▼
 Validaciones
        │
        ▼
 Resolución dinámica de esquema
        │
        ▼
 Generación de Hash
        │
        ▼
 Comparación con RAW
        │
        ├────────► Auditoría de cambios
        │
        ├────────► Control de cambios
        │
        ▼
 PostgreSQL (RAW)
```

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
├── resolve_hash_schema.py
├── sources.py
│
├── docs/
│   ├── README.md
│   ├── excel_parser.md
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

---

## sources

Contiene el catálogo de todas las fuentes de información utilizadas por el pipeline.

Cada fuente define:

* Ruta del archivo.
* Hoja.
* Tabla destino.
* Columnas Hash.
* Llaves de comparación.
* Columna identificadora.

---

# Flujo del Pipeline

Para cada fuente de datos el proceso realiza las siguientes etapas:

1. Extracción del archivo Excel.
2. Normalización de la estructura.
3. Validación de la fuente.
4. Resolución automática de cambios en encabezados.
5. Generación del Hash.
6. Comparación contra la capa RAW.
7. Registro de auditoría.
8. Registro de control de cambios.
9. Inserción incremental de nuevos registros.

---

# Estado del Proyecto

Versión actual: **1.5**

## Componentes implementados

* Ingestión hacia RAW.
* Parser para formatos libres.
* Resolución dinámica del esquema del Hash.
* Auditoría de cambios.
* Control de cambios.
* Carga incremental.

## Próximas etapas

* Construcción de la capa Staging.
* Normalización mediante SQL.
* Construcción del Data Warehouse.
* Automatización de ejecuciones.
* Orquestación del pipeline.
* Incorporación de pruebas automatizadas.

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
