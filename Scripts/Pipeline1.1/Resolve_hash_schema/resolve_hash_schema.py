#resolve_hash_schema.py

#Esta libreria contiene las funciones para procesar las columnas de un dataframe que se utilizan 
#para generar un hash. Reemplaza los headers de las columnas que calculan el hash si cambiaron
#de nombre y reemplaza la columna ID de las key_columns

#====================================
# 1. Funciones Privadas (Uso Interno)
#====================================

def _normalize_text(lista):
    #Esta funcion convierte a minúsculas todos los componentes 
    #de una fila de un dataframe y devuelve una lista

    lower = [str(celda).strip().lower() for celda in lista]
    return lower

def _find_column_name(headers, hash_columns):
    #Esta función encuentra el inidice de las columnas del df original y las compara con
    #las hash_columns, regresa una lista con los nombres de las columnas coincidentes del df original

    norm_headers = _normalize_text(headers)
    norm_headers = list(enumerate(norm_headers))
    norm_hash = _normalize_text(hash_columns)
    coincidencias_hash = []
    indices_consumidos = set()

    for col_buscada in norm_hash:
        for idx, texto_columna in norm_headers:
            
            if idx in indices_consumidos:
                continue
            if col_buscada in texto_columna:
                coincidencias_hash.append(idx)
                indices_consumidos.add(idx)
                break

    nombres_coincidentes = [headers[idx] for idx in coincidencias_hash]
    if len(nombres_coincidentes) != len(hash_columns):
        raise ValueError(
            f"No fue posible localizar todas las hash_columns.\n"
            f"Esperadas: {hash_columns}\n"
            f"Encontradas: {nombres_coincidentes}"
        )

    if nombres_coincidentes and nombres_coincidentes != hash_columns:
        return nombres_coincidentes
    else:
        return None

def _replace_source_keys(lista, key, diccionario):
    # Actualiza una clave del diccionario fuente con los nuevos valores resueltos.
    temporal_dicc = {**diccionario,
                     key :lista}
    return temporal_dicc

def _resolve_key_columns(hash_columns, key_columns):
    #Esta función reemplaza el primer elemento de una lista y regresa la lista modificada
    key_coincidente = _find_column_name(hash_columns, [key_columns[0]])
    new_key_columns = key_columns.copy()
    if key_coincidente and key_coincidente[0] != new_key_columns[0]:
        new_key_columns[0] = key_coincidente[0]
        return new_key_columns
    else:
        return None

#====================================
# 2. Función Pública (Interfaz)
#====================================

def resolve_hash_schema(df, hash_columns, key_columns, dictionary):
    #Esta es la función principal, reemplaza los nombres modificados de las columnas que construyen el hash en el diccionario
    #principal, si es necesario tambien modifica las key columns

    #Parte 1: reemplazo de las columnas hash
    headers = df.columns.tolist()
    nombres_coincidentes = _find_column_name(headers, hash_columns)
    if nombres_coincidentes is not None:
        diccionario_modificado = _replace_source_keys(nombres_coincidentes, "hash_columns", dictionary)
        #Parte 2: reemplazo de las columnas keys
        new_keys = _resolve_key_columns(nombres_coincidentes, key_columns)
        if new_keys is not None:
            diccionario_modificado = _replace_source_keys(new_keys, "key_columns", diccionario_modificado)
        return diccionario_modificado
    else:
        return dictionary

__all__ = ['resolve_hash_schema']
