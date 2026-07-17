# schema_validation

## Descripción

`schema_validation` es una biblioteca encargada de validar y alinear el esquema (estructura de columnas) entre una fuente
de datos y su tabla correspondiente en la base de datos RAW.

Su objetivo es permitir que el pipeline continúe funcionando cuando una fuente incorpora nuevas columnas o cuando 
la estructura de la tabla RAW contiene columnas que ya no aparecen en la fuente actual.

La biblioteca realiza únicamente modificaciones sobre el esquema de las columnas; no altera los datos ni realiza 
transformaciones sobre los registros.

---

## Problema que resuelve

En los archivos operativos de la empresa es común que la estructura de las tablas cambie con el tiempo.

Entre los cambios más frecuentes se encuentran:

- Incorporación de nuevas columnas.
- Eliminación temporal de columnas.
- Cambio en la posición de las columnas.
- Encabezados jerárquicos con diferentes niveles de profundidad.

Cuando esto ocurre, una carga directa hacia PostgreSQL produce errores debido a que el esquema del DataFrame ya no coincide con el esquema existente en RAW.

Esta biblioteca detecta dichas diferencias y alinea ambas estructuras antes de realizar la carga.

---

## Flujo de trabajo

El proceso sigue la siguiente secuencia:

1. Normaliza temporalmente los nombres de las columnas para facilitar la comparación.
2. Detecta columnas nuevas presentes en la fuente pero inexistentes en RAW.
3. Agrega automáticamente esas columnas a la tabla correspondiente de PostgreSQL.
4. Detecta columnas que existen en RAW pero no en la fuente actual.
5. Agrega dichas columnas al DataFrame utilizando valores nulos (`pd.NA`).
6. Devuelve un DataFrame con una estructura compatible con la tabla RAW.

---

## Funciones privadas

### `_cut_headers()`

Reduce temporalmente los nombres de columnas conservando únicamente los dos últimos niveles del encabezado jerárquico.

Esta representación simplificada únicamente se utiliza para comparar estructuras.

---

### `_extra_columns()`

Compara los encabezados de la fuente y de RAW utilizando conjuntos (`set`) y determina:

- columnas nuevas provenientes de Excel;
- columnas que existen únicamente en RAW.

---

### `_recover_original_headers()`

Recupera el nombre completo del encabezado original a partir de la versión simplificada utilizada durante la comparación.

Esto permite conservar los nombres reales al modificar la estructura de la base de datos.

---

### `_create_new_raw_columns()`

Agrega automáticamente nuevas columnas a la tabla RAW mediante instrucciones SQL: **ALTER TABLE**
Cada columna nueva se crea únicamente si aún no existe.

---

### `_align_dataframe_schema()`

Agrega al DataFrame todas las columnas existentes en RAW que no aparecen en la fuente actual.

Las columnas agregadas contienen valores nulos (`pd.NA`) para mantener la compatibilidad estructural durante la carga.

---

## Función pública

### `schema_validation()`

Coordina todo el proceso de validación del esquema.

### Entradas

- DataFrame proveniente de la fuente.
- DataFrame obtenido desde RAW.
- Nombre de la tabla.
- Motor SQLAlchemy.

### Salida

Devuelve un DataFrame cuya estructura es compatible con la tabla existente en PostgreSQL.

Si existen columnas nuevas:

- actualiza automáticamente el esquema de RAW.

Si existen columnas faltantes:

- las agrega al DataFrame antes de la carga.

---

## Integración con el pipeline

Dentro del pipeline esta biblioteca se ejecuta después de validar la fuente y antes de generar el hash de cada registro.

```
Excel
      │
      ▼
excel_parser
      │
      ▼
Validaciones
      │
      ▼
resolve_hash_schema
      │
      ▼
schema_validation
      │
      ▼
Generación de Hash
      │
      ▼
Comparación con RAW
```

---

## Consideraciones

- No modifica el contenido de los registros.
- No elimina columnas de la base RAW.
- Sólo incorpora nuevas columnas cuando aparecen en la fuente.
- Las columnas faltantes se agregan temporalmente al DataFrame mediante valores nulos.
- La comparación de esquemas utiliza versiones simplificadas de los encabezados para tolerar cambios menores en encabezados
  jerárquicos.

---

## Objetivo dentro del proyecto

Esta biblioteca permite que el pipeline continúe funcionando aun cuando la estructura de los archivos evoluciona con el 
tiempo, evitando modificaciones manuales del esquema de PostgreSQL y reduciendo interrupciones durante la carga de datos.
