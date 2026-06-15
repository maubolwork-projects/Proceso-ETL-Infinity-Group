#Esta es la Versión 1.5 del código que pretende ser un proceso ETL el cual extrae datos 
#de diferentes fuentes (en este caso Excel), los procesa, detecta, audita cambios y los carga
# a una base de datos en PostgreSQL. El código es modular, con funciones específicas para cada etapa del proceso.

import datetime
import pandas as pd
import numpy as np
import hashlib
from sqlalchemy import create_engine
import datetime

engine = create_engine("postgresql://postgres:postgres@localhost:5432/raw_prueba")
with engine.connect() as conn:
    print("Conexión exitosa")

def export_to_raw(df, table_name, exist):
    #Esta función toma un dataframe y un nombre de tabla,
    #y lo exporta a una base en PostgreSQL llamada "raw_prueba" utilizando SQLAlchemy
    df.to_sql(name=table_name, con=engine, if_exists=exist, index=False)
    return print(f"Datos exportados a la tabla {table_name} en la base raw_prueba")

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
        export_to_raw( summary_status, "control_de_cambios", "append")
    return df_merge, summary_status

def add_hash (df, columns):
    #Esta función toma un dataframe y una lista de columnas, 
    #crea una clave única concatenando las columnas, 
    #luego genera un hash de esa clave en una nueva columnas
    df_key = df[columns].astype(str).agg("|".join, axis=1)
    df["Hash"] = df_key.apply(lambda x: hashlib.md5(x.encode()).hexdigest())
    return df

def auditory(df, table_origin):
    #Esta función toma un df y crea un df que audita los datos que sufriron cambios o fueron eliminados, agregando la fecha actual
    #Los almacena en una tabla de la base RAW para su posterior análisis
        df_auditoria = df[df["Hash_Match"].isin(["Cambios detectados", "Registro eliminado"])].copy()
        df_auditoria["Fecha_Auditoria"] = execution_date
        df_auditoria["Tabla_Origen"] = table_origin
        if not df_auditoria.empty:
             export_to_raw(df_auditoria, "auditoria_de_cambios", "append")
        return df_auditoria

def get_new_records(df, df_source, table_name):
    #Esta funcion toma un df y devuelve solo los registros que son nuevos(no tienen hash en RAW) y los manda a RAW para su almacenamiento
        df_new_add = df[df["Hash_Match"].isin(["Nuevo registro"])].copy()
        data_new_add = df_new_add["RegistroID"].tolist()
        df_final = df_source 
        df_final = df_final[df_final["RegistroID"].isin(data_new_add)]
        df_final["Fecha_Carga"] = execution_date
        df_final["Tabla_Origen"] = table_name
        if not df_new_add.empty:
             export_to_raw(df_final, table_name, "append")
        return df_final

def get_source_excel(ruta):
    #Esta función toma una ruta de un archivo excel y devuelve un dataframe con los datos del excel
    df = pd.read_excel(ruta)
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

def process_function(source):
    #Esta funcion toma de un diccionario la informacion con cada fuente de informacion
    #procesa los datos de cada fuente utilizando las funciones anteriores, devuelve un df resumen
    #carga los datos sin cambios o errores a raw y los datos con cambios o eliminados a la tabla de auditoria
    df_source = get_source_excel(source["ruta"])
    df_source = df_source.where(pd.notnull(df_source), None)
    df_source = add_hash(df_source, source["hash_columns"])
    df_source_raw = pd.read_sql_table(source["table_name"], con=engine)
    df_status, summary_status = status_test(df_source_raw, df_source, source["key_columns"])
    df_auditoria = auditory(df_status, source["table_name"])
    df_new_records = get_new_records(df_status, source["table_name"])
    return summary_status

def main():

#Extraccion de datos 
    ruta1 = "C:\\Users\\HP\\Documents\\concretera_muestras\\ventas_departamento_100_ciudades_fixed.xlsx"
    #ruta2 = "C:\\Users\\HP\\Documents\\concretera_muestras\\produccion_departamento_100_ciudades_fixed.xlsx"
    df_ventas = get_source_excel(ruta1)

#Agrega la columna de key y hash a ambos dataframes
    df_ventas = add_hash(df_ventas, ["RegistroID", "Fecha", "Material", "Cantidad", "PrecioUnitario", "Total"])
    df_ventas = df_ventas.where(pd.notnull(df_ventas), None)
    df_produccion = add_hash(df_produccion, ["RegistroID", "Fecha", "Material", "Cantidad", "PrecioUnitario", "Total","Sucursal"])
    df_produccion = df_produccion.where(pd.notnull(df_produccion), None)
    #print(df_ventas.head())

#Exportar datos obtenidos de las fuentes en excel sin cambios a la base RAW en postgreSQL
    export_to_raw(df_ventas, "ventas_departamento_100_ciudades")
    export_to_raw(df_produccion, "produccion_departamento_100_ciudades")

#Importar datos desde la base RAW en postgreSQL 
    df_ventas_raw = pd.read_sql_table("ventas_departamento_100_ciudades", con=engine)
    df_produccion_raw = pd.read_sql_table("produccion_departamento_100_ciudades", con=engine)

#Crea un marge para comparar los id y hash de ambos dataframes para detectar cambios, nuevos registros o registros eliminados
#almecena los cambios detectados en un nuevo dataframe de auditoria con la fecha actual y lo envia a raw para su almacenamiento
    df_status = status_test(df_ventas_raw, df_ventas, ["RegistroID", "Hash"])
    df_auditoria = auditory(df_status)
    print(df_auditoria)
if __name__ == "__main__":
    main()