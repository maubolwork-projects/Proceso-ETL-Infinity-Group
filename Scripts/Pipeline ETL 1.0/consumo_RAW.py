#Esta es la Versión 1.0 del código que pretende ser un proceso ETL el cual extrae datos 
#de diferentes fuentes (en este caso Excel): comprueba la validez del archivo (vacio, faltantes, duplicados) y,
#detiene el proceso si no es valido; procesa los datos y asigna un hash a cada fila, audita cambios, eliminados
#y nuevos, reporta los cambios en una tabla y aisla las filas con cambios en otra (auditoria), los nuevos los carga
# a una base de datos en PostgreSQL. El código es modular, con funciones específicas para cada etapa del proceso.

import datetime
import pandas as pd
import numpy as np
import hashlib
from sqlalchemy import create_engine, inspect

engine = create_engine("postgresql://postgres:postgres@localhost:5432/raw_prueba")

def export_to_raw(df, table_name):
    #Esta función toma un dataframe y un nombre de tabla,
    #y lo exporta a una base en PostgreSQL llamada "raw_prueba" utilizando SQLAlchemy
    df.to_sql(name=table_name, con=engine, if_exists="append", index=False) 

def validate_source(df, columns):
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
    
def validate_duplicated(df, ID_Column):
     #Esta función detecta si hay valores duplicados y detiene la ejecución si los hay
     duplicados = df[df.duplicated(subset=[ID_Column[0]], keep=False)]
     if not duplicados.empty:
          raise ValueError(f"Tabla con valores duplicados en : {duplicados[ID_Column[0]].unique().tolist()}")

def status_test(df1, df2, key_columns):
    #Esta funcion toma el df de la base RAW y el df de produccion y los columnas a comparar,
    #hace un merge para comparar los hash, agrega una columna con el resultado de la comparación
    df_merge = df1.merge(df2[[key_columns[0], key_columns[1]]], on=key_columns[0], how="outer", suffixes=("_Old", "_New"))
    Condiciones =[df_merge["Hash_Old"] == df_merge["Hash_New"], 
                    df_merge["Hash_Old"].isnull(), 
                    df_merge["Hash_New"].isnull()]
    Elecciones = ["Sin cambios", "Nuevo registro", "Registro eliminado"]
    df_merge["Hash_Match"] = np.select(Condiciones, Elecciones, default="Cambios detectados")
    summary_status = df_merge.groupby("Hash_Match").size().reset_index(name="Total_Registros")
    summary_status["Fecha_Resumen"] = execution_date
    if not summary_status.empty:
        export_to_raw( summary_status, "control_de_cambios")
    return df_merge, summary_status

def add_hash (df, columns):
    #Esta función toma un dataframe y una lista de columnas, 
    #crea una clave única concatenando las columnas, 
    #luego genera un hash de esa clave en una nueva columnas
    df_hash = df.copy()
    df_hash = df_hash.astype("string")
    df_hash = df_hash.dropna(how="all")
    df_hash = df_hash.fillna("__NULL__")
    df_key = df_hash[columns].agg("|".join, axis=1)
    df["Hash"] = df_key.apply(lambda x: hashlib.md5(x.encode()).hexdigest())
    df["Fecha_Carga"] = execution_date
    return df

def auditory(df, table_origin):
    #Esta función toma un df y crea un df que audita los datos que sufriron cambios o fueron eliminados, agregando la fecha actual
    #Los almacena en una tabla de la base RAW para su posterior análisis
        df_auditoria = df[df["Hash_Match"].isin(["Cambios detectados", "Registro eliminado"])].copy()
        df_auditoria["Fecha_Auditoria"] = execution_date
        df_auditoria["Tabla_Origen"] = table_origin
        if not df_auditoria.empty:
             export_to_raw(df_auditoria, "auditoria_de_cambios")
        return df_auditoria

def get_new_records(df, df_source, table_name):
    #Esta funcion toma un df y devuelve solo los registros que son nuevos(no tienen hash en RAW) y los manda a RAW para su almacenamiento
        df_new_add = df[df["Hash_Match"].isin(["Nuevo registro"])].copy()
        data_new_add = df_new_add["RegistroID"].tolist()
        df_final = df_source 
        df_final = df_final[df_final["RegistroID"].isin(data_new_add)]
        if not df_new_add.empty:
             export_to_raw(df_final, table_name)
        return df_final

def get_source_excel(ruta):
    #Esta función toma una ruta de un archivo excel y devuelve un dataframe con los datos del excel
    df = pd.read_excel(ruta, dtype_backend='numpy_nullable')
    return df

def get_source_sql(table_name):
    #Esta función toma el nombre de una tabla en la base RAW y devuelve un dataframe con los datos de esa tabla
    df = pd.read_sql_table(table_name, con=engine)
    return df

Sources = {
     "ventas": {
          "ruta" : "C:\\Users\\HP\\Documents\\concretera_muestras\\ventas_departamento_100_ciudades_fixed.xlsx",
          "table_name" : "ventas_departamento_100_ciudades",
          "hash_columns" : ["RegistroID", "Fecha", "Material", "Cantidad", "PrecioUnitario", "Total"],
          "key_columns" : ["RegistroID", "Hash"]
          },
    "produccion": {
          "ruta" : "C:\\Users\\HP\\Documents\\concretera_muestras\\produccion_departamento_100_ciudades_fixed.xlsx",
          "table_name" : "produccion_departamento_100_ciudades",
          "hash_columns" : ["RegistroID", "Fecha", "Material", "Cantidad", "PrecioUnitario", "Total","Sucursal"],
          "key_columns" : ["RegistroID", "Hash"]
           }
}
execution_date = datetime.datetime.now()

def process_source(source):
    #Esta funcion toma de un diccionario la informacion con cada fuente de informacion
    #procesa los datos de cada fuente utilizando las funciones anteriores, devuelve un df resumen
    #carga los datos sin cambios o errores a raw y los datos con cambios o eliminados a la tabla de auditoria
    df_source = get_source_excel(source["ruta"])
    validate_source(df_source, source["hash_columns"])
    validate_duplicated(df_source, source["key_columns"])
    df_source = add_hash(df_source, source["hash_columns"])    
    inspector = inspect(engine)
    if inspector.has_table(source["table_name"]):
        df_source_raw = get_source_sql(source["table_name"])
        df_status, summary_status = status_test(df_source_raw, df_source, source["key_columns"])
        auditory(df_status, source["table_name"])
        get_new_records(df_status, df_source, source["table_name"])
        return summary_status
    else:
        export_to_raw(df_source, source["table_name"])
    

def main():

    #Esta es la función principal que ejecuta el proceso ETL para cada fuente de información almacenada en Sources
    #En este ejemplo extrae los datos de dos fuentes de excel (ventas y producción), agrega un hash unico para cada
    #registro; a partrir de ahí compara los datos almacenados en la base de datos RAW y los extraidos de las otras 
    #fuentes; detecta cambios, nuevos registros y eliminados, almacena los datos nuevos en una tabla de la base RAW
    #los cambios en una tabla de auditoria y un resumen con la cantidad de estados detectados en otra tabla.

    proceso_ventas = process_source(Sources["ventas"])
    

if __name__ == "__main__":
    main()
