excel_parser.py

Propósito
---------
Biblioteca para convertir archivos Excel con formato libre
en tablas estructuradas listas para un pipeline ETL.

Problemas que resuelve
----------------------

✔ Encabezados desplazados

✔ Encabezados multinivel

✔ Celdas combinadas

✔ Logos y títulos

✔ Filas vacías

✔ Resúmenes al final

Entradas
---------

ruta
hoja
hash_columns

Salida
------

DataFrame listo para el proceso de ingestión.

Ejemplo
-------

from excel_parser import excel_parser

df = excel_parser(...)
