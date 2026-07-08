#ingestion_pipeline.py

#Versión 1.0 del código que pretende ser un proceso ETL el cual extrae datos 
#de diferentes fuentes (en este caso Excel): comprueba la validez del archivo (vacio, faltantes, duplicados) y,
#detiene el proceso si no es valido; procesa los datos y asigna un hash a cada fila, audita cambios, eliminados
#y nuevos, reporta los cambios en una tabla y aisla las filas con cambios en otra (auditoria), los nuevos los carga
# a una base de datos en PostgreSQL. El código es modular, con funciones específicas para cada etapa del proceso.

#Versión 1.1 funciona con datos reales, con archivos de una estructura adecuada, se utilizaron 4 fuentes bien estructuradas
# No hubo cambios en el Pipeline original V1.0

#Versión 1.2 Se incorpora la biblioteca y función "excel_parser" la cual convierte archivos Excel con formato libre 
# en tablas estructuradas listas para un pipeline ETL.

#Versión 1.3 Se agrega la biblioteca "source" que contiene el diccionario con las caracteristicas de las fuentes de datos

#Versión 1.4 Se adiciona una biblioteca "resolve_hash_schema" que es capaz de detectar los cambios en el nombre de las columnas, si los hay
# sustituye las hash_columns y key_columns

#Versión 1.4.1 Se modificó la funcion _auditory para que reportara los siguientes datos "Tabla_Origen", "Renglon_Cambio", "Hash_Match",
#  "Fecha_Auditoria". ya que antoriormente tomamba la fila completa y eso causaba error debido a los diferentes formatos de las tablas

#Versión 1.5 Se sustituyo el método de ejecución de la función process_source en la funcion __main__ por un ciclo for y un if que 
# evaluan y comparan la función para cada registro en sources.

#====================================
# Importacion De Bibliotecas
#====================================

import datetime
import pandas as pd
import numpy as np
import hashlib
from sqlalchemy import create_engine, inspect
#Bibliotecas propias
from excel_parser import excel_parser
from resolve_hash_schema import resolve_hash_schema
from sources import SOURCES 

#====================================
# 1. Variables globales
#====================================

engine = create_engine("postgresql://postgres:postgres@localhost:5432/RAW_Concretera")
#INSPECTOR = inspect(ENGINE)
EXECUTION_DATE = datetime.datetime.now()

#====================================
# 2. Funciones Privadas (Uso Interno)
#====================================

def _export_to_raw(df, table_name):
    #Esta función toma un dataframe y un nombre de tabla,
    #y lo exporta a una base en PostgreSQL llamada "raw_prueba" utilizando SQLAlchemy
    df.to_sql(name=table_name, con=engine, if_exists="append", index=False) 

def _validate_source(df, columns):
     #Esta función valida si la fuente de datos en excel es valida, esto quiere 
     #decir que no tiene los siguientes errores: a) el archivo está completamente
     #vacio. b) Tiene estructura (Columnas) pero no tiene datos. c) Tiene algunas
     #columnas eliminadas

     if len(df.columns) == 0:
          raise ValueError("Archivo vacío : no contiene columnas")
     
     if df.empty:
          raise ValueError(f"Advertencia : Archivo sin registros en las columnas : {columns}")

     missing_columns = [col for col in columns
                        if col not in df.columns]
     
     if missing_columns:
          raise ValueError(f"Columnas faltantes : {missing_columns}")
     
     return True
    
def _validate_duplicated(df, ID_Column):
     #Esta función detecta si hay valores duplicados y detiene la ejecución si los hay
     duplicados = df[df.duplicated(subset=[ID_Column[0]], keep=False)]
     if not duplicados.empty:
          raise ValueError(f"Tabla con valores duplicados en : {duplicados[ID_Column[0]].unique().tolist()}")

def _status_test(df1, df2, key_columns, table_origin):
    #Esta funcion toma el df de la base RAW y el df de produccion y los columnas a comparar,
    #hace un merge para comparar los hash, agrega una columna con el resultado de la comparación
    # Agrega estas líneas justo antes del df_merge = ...

    df_merge = df1.merge(df2[[key_columns[0], key_columns[1]]], on=key_columns[0], how="outer", suffixes=("_Old", "_New"))

    Condiciones =[df_merge["Hash_Old"] == df_merge["Hash_New"], 
                    df_merge["Hash_Old"].isnull(), 
                    df_merge["Hash_New"].isnull()]
    Elecciones = ["Sin cambios", "Nuevo registro", "Registro eliminado"]
    df_merge["Hash_Match"] = np.select(Condiciones, Elecciones, default="Cambios detectados")
    summary_status = df_merge.groupby("Hash_Match").size().reset_index(name="Total_Registros")
    summary_status["Fecha_Resumen"] = EXECUTION_DATE
    summary_status["Tabla_Origen"] = table_origin
    if not summary_status.empty:
        _export_to_raw( summary_status, "Control_De_Cambios")
    return df_merge, summary_status

def _add_hash (df, columns):
    #Esta función toma un dataframe y una lista de columnas, 
    #crea una clave única concatenando las columnas, 
    #luego genera un hash de esa clave en una nueva columnas
    df_hash = df.copy()
    df_hash = df_hash.astype("string")
    df_hash = df_hash.dropna(how="all")
    df_hash = df_hash.fillna("__NULL__")
    df_key = df_hash[columns].agg("|".join, axis=1)
    df["Hash"] = df_key.apply(lambda x: hashlib.md5(x.encode()).hexdigest())
    df["Fecha_Carga"] = EXECUTION_DATE
    return df

def _auditory(df, table_origin):
    #Esta función toma un df y crea un df que audita los datos que sufriron cambios o fueron eliminados, agregando la fecha actual
    #Los almacena en una tabla de la base RAW para su posterior análisis
        df_auditoria = df[df["Hash_Match"].isin(["Cambios detectados", "Registro eliminado"])]#.copy()

        if not df_auditoria.empty:
            df_auditoria["Fecha_Auditoria"] = EXECUTION_DATE
            df_auditoria["Tabla_Origen"] = table_origin
            df_auditoria["Renglon_Cambio"] = df_auditoria.index + 2
            columnas_fijas = ["Tabla_Origen", "Renglon_Cambio", "Hash_Match", "Fecha_Auditoria"]
        
            df_auditoria = df_auditoria[columnas_fijas]
        
            _export_to_raw(df_auditoria, "Auditoria_De_Cambios")
        return df_auditoria

def _get_new_records(df, df_source, table_name, column_id):
    #Esta funcion toma un df y devuelve solo los registros que son nuevos(no tienen hash en RAW) y los manda a RAW para su almacenamiento
        df_new_add = df[df["Hash_Match"].isin(["Nuevo registro"])]#.copy()
        data_new_add = df_new_add[column_id].tolist()
        df_final = df_source 
        df_final = df_final[df_final[column_id].isin(data_new_add)]
        if not df_new_add.empty:
             _export_to_raw(df_final, table_name)
        return df_final

def _get_source_sql(table_name):
    #Esta función toma el nombre de una tabla en la base RAW y devuelve un dataframe con los datos de esa tabla
    df = pd.read_sql_table(table_name, con=engine)
    return df

#====================================
# 3. Función Pública (Interfaz)
#====================================

def process_source(source):
    #Esta funcion toma de un diccionario la informacion con cada fuente de informacion
    #procesa los datos de cada fuente utilizando las funciones privadas, devuelve un df resumen
    #carga los datos sin cambios o errores a raw y los datos con cambios o eliminados a la tabla de auditoria

    #Parte 1. Extracción y formato de la fuente de datos
    df_source = excel_parser(source["ruta"], source["sheet_name"], source["hash_columns"])

    #Parte 2. Validación de la fuente de datos
    _validate_source(df_source, source["hash_columns"])
    _validate_duplicated(df_source, source["key_columns"])

    #Parte 3. Si es necesario se reconfigura el sistema de key columns y generación de hash
    source = resolve_hash_schema(df_source, source["hash_columns"], source["key_columns"], source)
    
    #Parte 4. Se agrega el hash de seguimiento de cambios
    df_source = _add_hash(df_source, source["hash_columns"])

    #Parte 5. Si la tabla existe en RAW, se carga el estatus de los datos, se agregan a la tabla auditoria
    # y se agregan los datos nuevos
    inspector = inspect(engine)
    if inspector.has_table(source["table_name"]):
        df_source_raw = _get_source_sql(source["table_name"])
        df_status, summary_status = _status_test(df_source_raw, df_source, source["key_columns"], source["table_name"])
        _auditory(df_status, source["table_name"])
        _get_new_records(df_status, df_source, source["table_name"], source["key_columns"][0])
        return summary_status
    else:
    #Parte 6. Si no existe la tabla en RAW, se carga completa 
        _export_to_raw(df_source, source["table_name"])
    
def main():
    # Función principal del pipeline de ingestión.

    # Recorre todas las fuentes definidas en SOURCES y ejecuta el proceso ETL para cada una de ellas. El proceso incluye:
    # 1. Extracción y normalización del archivo Excel mediante excel_parser.
    # 2. Validación de estructura, columnas obligatorias y registros duplicados.
    # 3. Resolución automática de cambios en los encabezados (hash schema).
    # 4. Generación del hash de seguimiento para cada registro.
    # 5. Comparación contra la capa RAW.
    # 6. Detección de nuevos registros, cambios y eliminaciones.
    # 7. Registro de auditoría y control de cambios.
    # 8. Carga incremental de nuevos registros a PostgreSQL.
    Sources = SOURCES
    for source_name, source in Sources.items():
         if not source.get("enabled", True):
              print(f"Fuente no conciderada: {source_name}\nMotivo: {source.get("coment")}\n")
              continue
         process_source(source)

if __name__ == "__main__":
    main()
