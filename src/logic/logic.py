import os
import pandas as pd

def leer_excel(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.xls':
        try:
            return pd.read_excel(path, header=1, engine="xlrd")
        except ImportError:
            raise Exception("Instala xlrd==1.2.0:\npip install xlrd==1.2.0")
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
