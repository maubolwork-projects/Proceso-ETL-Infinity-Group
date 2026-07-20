# schema_manager.py

""" Esta librería contiene funciones que ayudan a alinear las estructuras de las tablas entre las fuentes
    y las existentes en la base RAW, para en un proceso posterior poder cargarlas a RAW sin desfases.
    V 1.2, Se agregan funciones para alinear las columnas con algun cambio en el header.
    Soluciona 3 problemas: Schema evolution (columnas nuevas), Schema alignment (columnas faltantes),
    Schema drift resolution (cambios en nombres).
"""

#====================================
# 1. Funciones Privadas (Uso Interno)
#====================================
from sqlalchemy import text
import pandas as pd

def _normalize_schema_headers(df):
    # Esta función recorta los headers cuando son demasiado largos y toma solo las dos cadenas unidas
    # por ">", ejemplo: material>cemento
    df_copy = df.copy()
    # EXPRESIÓN REGULAR: Sin espacios internos y con soporte para espacios opcionales alrededor del '>'
    patron = r'([^>]+(?:\s*>\s*)[^>]+)$'
    
    series_columns = df_copy.columns.to_series().reset_index(drop=True)
    # Extraemos las últimas dos secciones y rellenamos con la original si no hay cambios
    cutting_headers = series_columns.astype(str).str.extract(patron, expand=False).fillna(series_columns)
    df_copy.columns = cutting_headers.str.strip().values
    return df_copy

def _extra_columns(df_source, df_raw):
    #Compara el nombre de las columnas de la fuente contra las registradas en la base RAW.
    #Primero corta la cadena hasta las últimas dos cadenas que construyen el header despues,
    #las agrupa en conjuntos y se obtienen las columnas extra en la nueva fuente.
    df_source = _normalize_schema_headers(df_source)
    name_headers_source = set(df_source.columns)
    df_raw = _normalize_schema_headers(df_raw)
    name_headers_raw = set(df_raw.columns)
    extra_columns_excel = list(name_headers_source - name_headers_raw)
    extra_columns_raw = list(name_headers_raw - name_headers_source)
    return extra_columns_excel, extra_columns_raw

def _recover_original_headers(df, pieces_list):
    #Devuelve una lista con los nombres originales de las columnas  que coinciden con la lista de fragmentos proporcionada.
    
    original_indices = [i for i, col in enumerate(df.columns) if any(col.endswith(f) for f in pieces_list)]
    original_headers = list(df.columns[original_indices])
    return original_headers

def _create_new_raw_columns(headers, table_name, engine):
    #Esta función agrega las columnas nuevas extraidas del DF proveniente de Excel a la base RAW
    with engine.begin() as conexion:
        for col in headers:
            querry_sql = text(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{col}" VARCHAR;')

            conexion.execute(querry_sql)
    return None

def _align_dataframe_schema(df, raw_headers):
    #Esta función agrega las columnas que tenga faltantes con respecto a RAW y las agrega para cuadrar la carga
    df_copy = df.copy()
    for col in raw_headers:
        if col not in df_copy.columns:
            df_copy[col] = pd.Series(pd.NA, index=df_copy.index, dtype="string")
    return df_copy

def _misaligned_name_columns(df_enriched, df_raw):
    #Compara el nombre de las columnas de la fuente contra las registradas en la base RAW.
    #Primero corta la cadena hasta las últimas dos cadenas que construyen el header despues,
    #las agrupa en conjuntos y se obtienen las columnas extra en la nueva fuente.
    
    name_headers_source = set(df_enriched.columns)
    
    name_headers_raw = set(df_raw.columns)
    misaligned_excel = list(name_headers_source - name_headers_raw)
    misaligned_raw = list(name_headers_raw - name_headers_source)
    return misaligned_excel, misaligned_raw

def _substitution_dict(columns_df, columns_raw, patterns):
    # Esta función construye un diccionario que relaciona las columnas desalineadas del DF y de RAW
    # utilizando un conjunto de patrones normalizados con las dos últimas partes de la cadena que
    # conforma el header (string2>string1), las cuales son más significativas
    automatic_dict = {}
    clean_patterns = [str(p).strip().lower() for p in patterns]

    indice ={}
    for col in columns_raw:
            clean_col_raw = str(col).strip().lower()
            for pattern in clean_patterns:
                if clean_col_raw.endswith(pattern):
                    indice[pattern] = col
                    break

    for col in columns_df:
            clean_col_df = str(col).strip().lower()
            for pattern in clean_patterns:
                if clean_col_df.endswith(pattern):
                    if pattern in indice:
                        automatic_dict[col] = indice[pattern]
                        break

    return automatic_dict

def _rename_df_columns(df, sub_dict):
    #Esta función reemplaza los nombres de las columnas del dataframe que coinciden en sus 
    # dos últimos bloques (string1 > string2) con la tabla en RAW para tener una carga uniforme

    df_copy = df.copy()
    df_copy = df_copy.drop(columns=sub_dict.values(), errors="ignore")
    df_copy = df_copy.rename(columns=sub_dict)

    return df_copy

#====================================
# 2. Función Pública (Interfaz)
#====================================

def schema_manager(df_source, df_raw, table_name, engine):
    #Esta función detecta si hay columnas nuevas en el df proveniente de Excel, si las hay las agrega
    #  a la base RAW, importa las columnas faltantes que existen en RAW y devuelve un DF enriquecido
    # para su posterior carga a RAW
    df_enriched = df_source.copy()
    # 1. Detecta si existen columnas extra en el DF nuevo y en la base RAW
    unmatched_columns, unmatched_raw = _extra_columns(df_enriched, df_raw)
    # 2. Si existen nuevas columnas en el DF las carga a RAW
    if unmatched_columns:
        original_headers = _recover_original_headers(df_enriched, unmatched_columns)
        _create_new_raw_columns(original_headers, table_name, engine)
    # 3. Si existen columnas adicionales en RAW las agrega al DF 
    if unmatched_raw:
        original_raw = _recover_original_headers(df_raw, unmatched_raw)
        df_enriched = _align_dataframe_schema(df_enriched, original_raw)

    # 4. Detecta las columnas desalineadas en ambas fuentes DF y RAW, esto quiere decir,
    # son iguales pero los nombres no coinciden en niveles del header menos significativos
    misaligned_df, misaligned_raw = _misaligned_name_columns(df_enriched, df_raw)

    if misaligned_df and misaligned_raw:
        # 5. Normaliza los headers de las columnas desalineadas en DF encuentra los nombres 
        # equivalentes en RAW
        norm_ma_df = _normalize_schema_headers(df_enriched.loc[:, misaligned_df]).columns.tolist()
        raw_equivalent_headers = _recover_original_headers(df_raw, norm_ma_df)

        # 6. Crea un diccionario que empareja los headers coinicidentes completos entre el DF y RAW
        eq_dict = _substitution_dict(misaligned_df, raw_equivalent_headers, norm_ma_df)

        # 7. Cambia el nombre de las colummas desalineadas del DF por el nombre que tienen en RAW
        df_enriched = _rename_df_columns(df_enriched, eq_dict)
        return df_enriched
    else:
        return df_enriched

__all__ = ['schema_manager']
