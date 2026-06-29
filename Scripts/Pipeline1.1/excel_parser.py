#excel_parser.py

# Esta biblioteca tiene las funciones para convertir archivos Excel con formato libre
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
    return df

def _clean_header(df, hash_columns, threshold=0.8):
    #Esta funcion busca el encabezado de las columnas principales, elimina las filas
    #que estan sobre esta columna y devuelve un df sin encabezado
    start_row = None

    for i, row in df.iterrows():
        row_values = row.dropna().astype(str).str.strip().tolist()
        matches = sum(1 for col in hash_columns if col in row_values)
        pct = matches / len(hash_columns) if hash_columns else 0
        if pct >= threshold:
            start_row = i
            break

    if start_row is not None:
        new_headers = df.iloc[start_row].tolist()
        df_clean = df.iloc[start_row + 1:].copy()
        df_clean.columns = new_headers
        df_clean.reset_index(drop=True, inplace=True)
        return df_clean
    
    return None

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
            (wide >= actual_wide * tolerance) and 
            (wide <= actual_wide * (1 + (1 - tolerance)))
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
            (actual_wide >= expected_wide * tolerance) and
            (actual_wide <= expected_wide * (1 + (1 - tolerance)))
        )

        if is_part_table:
            last_valid_row = idex

        else:
            next_gap = count_row[idex : idex + gap]
            still_broken = all(
                not ((wide >= expected_wide * tolerance) and (wide <= expected_wide * (1 + (1 - tolerance))))
                for wide in next_gap
            )
            if still_broken:
                return last_valid_row + 1
            
    return total_rows

def _header_combination(df, tolerance=0.9, gap=3):
    # Esta función calcula el inidice donde comienzan los datos utilizando la función Find_first_DataRow,
    # Rellena las celdas vacias con "_" y concatena todos los valores de las celdas que esten por encima de los datos
    # crea un nuevo header para las columnas con la informacion calculado para en una etapa posterior limpiarla 
    # sin perder inofrmacion de origen

    indice = _find_first_datarow(df, tolerance, gap)

    df_headers = df.iloc[:indice].fillna("_")
    new_headers = []
    for col in df_headers.columns:
        pieces = [str(val).strip() for val in df_headers[col]]
        clean_pieces = []
        for val in pieces:
            if val != "_" and (not clean_pieces or val != clean_pieces[-1]):
                clean_pieces.append(val)

        name_column = ">".join(clean_pieces) if clean_pieces else f"Columna_{col}"
        new_headers.append(name_column) 
    df = df.iloc[indice :].copy()
    df.columns = new_headers
    df.reset_index(drop=True, inplace=True)
    return df

def _clean_tail(df, tolerance=0.9, gap=3):
    #Esta funcion limpia el final de una tabla donde puede haber resumenes o datos dispersos
    f_index = _find_first_datarow(df, tolerance, gap)
    l_index = _find_last_datarow(df, f_index, tolerance, gap)
    df = df.iloc[:l_index].copy()

    return df

#====================================
# 2. Función Pública (Interfaz)
#====================================

def Excel_Parser(ruta, hoja, hash_columns, threshold=0.8, tolerance=0.5, gap=3):
# Funcion principal donde los insumos principales son la ruta, hoja y columnas principales
# Regresa un DataFrame limpio, con estructura de tabla; eliminado encabezados al inicio
# y resumenes o datos secundarios al final de la tabla.
    df = _get_source_excel(ruta, hoja)
    df1 = df.copy()
    df1 = _clean_header(df1, hash_columns, threshold)
    if df1 is not None:
        df1 = _clean_tail(df1, tolerance, gap)
        return df1
    else:
        df = _header_combination(df, tolerance, gap)
        df = _clean_tail(df, tolerance, gap)

    return df

__all__ = ['excel_parser']
