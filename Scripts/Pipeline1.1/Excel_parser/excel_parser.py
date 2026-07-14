#excel_parser.py

# Esta biblioteca versión 1.3 tiene las funciones para convertir archivos Excel con formato libre
# (logos, títulos, encabezados desplazados y resúmenes)
# en una tabla estructurada lista para ser procesada por el pipeline de ingestión.

#====================================
# Importacion De Bibliotecas
#====================================

import pandas as pd
import numpy as np

#====================================
# 1. Funciones Privadas (Uso Interno)
#====================================

def _get_source_excel(ruta, hoja):
    #Esta función toma una ruta de un archivo excel y devuelve un dataframe con los datos del excel
    #además, elimina filas y columnas totalmente vacias
    df = pd.read_excel(ruta, sheet_name=hoja, header=None, dtype_backend='numpy_nullable')
    df = df.dropna(how='all').dropna(how='all', axis=1).copy()
    df = df.reset_index(drop=True)
    return df

def _find_header_row(df, hash_columns, threshold=0.8):
    #Esta funcion busca el encabezado donde se encuentran las columnas principales,
    #y devuelve el indice donde se encuentra.

    start_row = None
    #Localiza en que fila se encuentran las columnas prinicipales
    for i, row in df.iterrows():
        row_values = row.dropna().astype(str).str.strip().tolist()
        matches = sum(1 for col in hash_columns if col in row_values)
        pct = matches / len(hash_columns) if hash_columns else 0
        if pct >= threshold:
            start_row = i
            break
    return start_row

def _assign_headers(headers):
    #Esta función construye los headers cuando estan dispersos en varios renglones, también
    #elimina aquellas columnas que pudieran quedar residuales o con datos nulos
    new_headers = []
    for col in headers.columns:
        pieces = [str(val).strip() for val in headers[col]]
        clean_pieces = []
        for val in pieces:
            if val != "_" and (not clean_pieces or val != clean_pieces[-1]):
                clean_pieces.append(val)

        empty_header = headers[col].iloc[-1] == "_"
        if clean_pieces:
            if empty_header:
                name_column = f"Columna_{col}>" + ">".join(clean_pieces)
            else:
                name_column = ">".join(clean_pieces)
        else:
            name_column = f"Columna_{col}"
        new_headers.append(name_column)
        
    return new_headers

def _clean_garbage_columns(df):
    #Esta función elimina las columnas residuales creadas al concatenar los headers de las columnas
    empty_values = ["_", "", "<NA>", "NaT", None, pd.NA]
    garbage_columns = [col for col in df.columns
    if str(col).startswith("Columna_") and df[col].isin(empty_values).all() | df[col].isna().all()]
    print(garbage_columns)
    df = df.drop(columns=garbage_columns)
    return df

def _assign_index_to_duplicate_columns(df):
    #Si existen nombres de columnas duplicados esta función les asigna un índice para diferenciarlas 
    # y tener una carga correcta a PostgreSQL
    cols = pd.Series(df.columns)
    contador = cols.groupby(cols).cumcount()
    df.columns = [f'{col}_{count + 1}' if count > 0 else col for col,  count in zip(cols, contador)]
    return df

def _remove_header_prefix(df):
    #Esta función elimina el prefijo "Columna_[número]>" asignado al construir el header cuando este no existe
    clean_columns = []

    for col in df.columns:
        col_str = str(col)
        if col_str.startswith("Columna_") and ">" in col_str:
            clean_columns.append(col_str.split(">", 1)[-1])
        else:
            clean_columns.append(col)
    
    df.columns = clean_columns
    return df


def _residual_cleaning_columns(df):
    #Esta función limpia el encabezado de la tabla una vez que se ha encontrado el encabezado principal,
    #Elimina columnas <Nan> y <None> y coloca un índice si hay nombres duplicados
    #Además elimina las columnas que se agregaron por algún dato residual al final del archivo
    df = _clean_garbage_columns(df)
    # Elimina columnas que se llamen 'nan' o tengan valores nulos en el nombre
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, df.columns != 'nan']
    #Elimina prefijos temporales de asignación de los headers
    df = _remove_header_prefix(df)
    #Coloca un indice si por algun motivo sigue habiendo nombres duplicados en las columnas
    df = _assign_index_to_duplicate_columns(df)
    return df

def _has_duplicate_headers(headers):
    #Esta función valida que los encabezados no sean vacíoso nulos, detecta si hay duplicados
    #y devuelve...
    headers_validos = [str(h).strip() for h in headers if str(h).strip() != "" and str(h).lower() != "nan" and str(h) != "none"]
    duplicated = len(headers_validos) != len(set(headers_validos))
    return duplicated
        
def _clean_header(df, hash_columns, threshold=0.8):
    #Esta funcion busca el encabezado de las columnas principales, elimina las filas
    #que estan sobre esta columna y devuelve un df sin encabezado

    start_row = _find_header_row(df, hash_columns, threshold)
    
    #Si encuentra el encabezado elimina las filas superiores a este y lo devuelve limpio
    if start_row is not None:
        new_headers = df.loc[start_row].astype(str).str.strip().tolist()

        #Si hay columnas con headers duplicados, llama a _header_combination
        has_duplicated = _has_duplicate_headers(new_headers)

        if has_duplicated:
            df_clean = _header_combination(df, start_row=start_row)
            
        else:
            df_clean = df.loc[start_row + 1:].copy()
            df_clean.columns = new_headers
            df_clean.reset_index(drop=True, inplace=True)
            # Elimina columnas que se llamen 'nan' o tengan valores nulos en el nombre y pone un ínidice si hay nombres duplicados
            df_clean = _residual_cleaning_columns(df_clean)
        
        return df_clean
    
    return None

def _is_in_tolerance(wide,base_wide, tolerance):
    #Esta funcion verifica si el ancho o meseta de datos está dentro del rango de tolerancia
    lower_bound = base_wide * tolerance
    upper_bound = base_wide * (1 + (1 - tolerance))
    return lower_bound <= wide <= upper_bound

def _find_first_datarow(df, tolerance=0.9, gap=3):
    #Esta funcion calcula la longitud del contenido de cada fila (sin vacios), con ello compara
    #el tamaño en muestras de 3 tres hasta encontrar la meseta que es donde inician los datos reales
    #lo anterior a la meseta de datos pueden ser encabezados o titulos dispersos

    count_row = df.notnull().sum(axis=1).tolist()

    data_init = 0

    for idex in range(len(count_row) - gap):
        actual_wide = count_row[idex]
        if actual_wide <= 1:
            continue

        next_gap = count_row[idex + 1 : idex + 1 + gap]

        is_estable = all(
            _is_in_tolerance(wide, actual_wide, tolerance)
        for wide in next_gap
        )
        if is_estable:
            data_init = idex
            break
    return data_init

def _find_last_datarow(df, start_index, tolerance=0.9, gap=3):
    #Esta funcion calcula la longitud del contenido de cada fila (sin vacios), con ello se compara
    #el tamaño en muestras de 3 tres hasta encontrar la meseta que es donde terminan los datos reales
    #la información posterior pueden ser tablas resumen o datos almacenados al final de una tabla

    count_row = df.notnull().sum(axis=1).tolist()
    total_rows = len(count_row)

    expected_wide = count_row[start_index]
    last_valid_row = start_index

    for idex in range(start_index, total_rows):
        actual_wide = count_row[idex]

        is_part_table = (
            _is_in_tolerance(actual_wide, expected_wide, tolerance)
        )

        if is_part_table:
            last_valid_row = idex

        else:
            next_gap = count_row[idex : idex + gap]
            still_broken = all(
                not (_is_in_tolerance(wide, expected_wide, tolerance))
                for wide in next_gap
            )
            if still_broken:
                return last_valid_row + 1
            
    return total_rows

def _header_combination(df, tolerance=0.9, gap=3, start_row=None):
    
    # Esta función calcula el inidice donde comienzan los datos utilizando la función Find_first_DataRow,
    # Rellena las celdas vacias con "_" y concatena todos los valores de las celdas que esten por encima de los datos
    # crea un nuevo header para las columnas con la informacion calculado para en una etapa posterior limpiarla 
    # sin perder inofrmacion de origen

    if start_row is not None:
        indice = start_row + 1

    else:
        indice = _find_first_datarow(df, tolerance, gap)

    df_headers = df.iloc[:indice].astype(str).fillna("_")
    
    new_headers = _assign_headers(df_headers)

    df = df.iloc[indice :].copy()
    df.columns = new_headers
    df.reset_index(drop=True, inplace=True)
    # Elimina columnas que se llamen 'nan' o tengan valores nulos en el nombre y ponen un ínidce a nombres duplicados
    df = _residual_cleaning_columns(df)
    
    return df


def _clean_tail(df, tolerance=0.95, gap=3):
    #Esta funcion limpia el final de una tabla donde puede haber resumenes o datos dispersos
    f_index = _find_first_datarow(df, tolerance, gap)
    l_index = _find_last_datarow(df, f_index, tolerance, gap)
    df = df.iloc[:l_index].copy()
    return df

#====================================
# 2. Función Pública (Interfaz)
#====================================

def excel_parser(ruta, hoja, hash_columns, threshold=0.8, tolerance=0.5, gap=3):
# Funcion principal donde los insumos principales son la ruta, hoja y columnas principales
# Regresa un DataFrame limpio, con estructura de tabla; eliminado encabezados al inicio
# y resumenes o datos secundarios al final de la tabla.
    df = _get_source_excel(ruta, hoja)
    df_to_clean = df.copy()
    df_to_clean = _clean_header(df_to_clean, hash_columns, threshold)
    if df_to_clean is not None:
        df_to_clean = _clean_tail(df_to_clean, tolerance, gap)
        df_to_clean = _residual_cleaning_columns(df_to_clean)
        print(df_to_clean.head())
        return df_to_clean
    else:
        df_to_combinate = _header_combination(df, tolerance, gap)
        df_to_combinate = _clean_tail(df_to_combinate, tolerance, gap)
        df_to_combinate = _residual_cleaning_columns(df_to_combinate)
        print(df_to_combinate.head())
    return df_to_combinate

__all__ = ['excel_parser']
