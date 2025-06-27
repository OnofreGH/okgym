import os
import pandas as pd
import pyexcel

def convertir_xls_a_xlsx(path_xls):
    """Convierte un archivo .xls a .xlsx usando pyexcel y retorna la nueva ruta con nombre único"""
    try:
        # Step 2: Obtener la hoja del archivo .xls
        sheet0 = pyexcel.get_sheet(file_name=path_xls, name_columns_by_row=0)
        
        # Step 3: Crear array desde el contenido
        xlsarray = sheet0.to_array()
        
        # Step 4: Verificar contenido del array (opcional, para debug)
        print(f"📊 Filas leídas: {len(xlsarray)}")
        
        # Step 5: Pasar el array a una nueva hoja de trabajo
        sheet1 = pyexcel.Sheet(xlsarray)
        
        # Step 6: Crear la nueva ruta con nombre único para evitar interferencias
        nombre_base = os.path.splitext(os.path.basename(path_xls))[0]
        directorio = os.path.dirname(path_xls)
        path_xlsx = os.path.join(directorio, f"{nombre_base}_converted.xlsx")
        
        sheet1.save_as(path_xlsx)
        
        print(f"✅ Archivo convertido: {os.path.basename(path_xlsx)}")
        return path_xlsx
        
    except Exception as e:
        raise Exception(f"Error al convertir archivo: {e}")

def leer_excel(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.xls':
        try:
            # Convertir .xls a .xlsx automáticamente
            path_xlsx = convertir_xls_a_xlsx(path)
            return pd.read_excel(path_xlsx, header=1)
        except ImportError:
            raise Exception("Instala xlrd==1.2.0 y openpyxl:\npip install xlrd==1.2.0 openpyxl")
    elif ext == '.xlsx':
        try:
            return pd.read_excel(path, header=1, engine="openpyxl")
        except ImportError:
            raise Exception("Instala openpyxl:\npip install openpyxl")
    else:
        raise Exception("Formato no soportado: solo .xls y .xlsx")

def validar_numeros(df, normalizar_func):
    validos = 0
    for i in range(len(df)):
        celular = df.loc[i, 'CELULAR']
        celular_normalizado = normalizar_func(celular)
        if celular_normalizado:
            validos += 1
    return validos
