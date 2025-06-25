import threading
from tkinter import messagebox

from logic.logic import leer_excel, validar_numeros
from logic.message import send_messages
from logic.utils import normalizar_numero

def enviar_mensajes(excel_file, mensaje, image_path, pdf_path, status_label):
    try:
        status_label.config(text="Enviando mensajes...")
        status_label.update_idletasks()

        enviados = send_messages(
            excel_file,
            mensaje,
            image_path=image_path,
            pdf_path=pdf_path
        )

        status_label.config(text="Envío completado")
        messagebox.showinfo("Éxito", f"Se enviaron {enviados} mensajes exitosamente.")
    except Exception as e:
        status_label.config(text="Error durante el envío")
        messagebox.showerror("Error", str(e))

def validar_y_enviar(excel_file, mensaje, status_label, message_text, iniciar_hilo):
    if not excel_file or not mensaje.strip():
        messagebox.showerror("Error", "Selecciona un archivo de Excel y escribe un mensaje.")
        return

    try:
        df = leer_excel(excel_file)
        validos = validar_numeros(df, normalizar_numero)

        if validos == 0:
            messagebox.showwarning("Advertencia", "No se encontró ningún número válido con formato peruano.")
            return

        messagebox.showinfo("Validación exitosa", f"Se detectaron {validos} números válidos. Iniciando envío...")
        iniciar_hilo()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo validar el archivo:\n{e}")

def obtener_mensaje_previsualizacion(excel_file, mensaje_raw):
    df = leer_excel(excel_file)
    if df.empty:
        raise ValueError("El archivo Excel está vacío.")

    nombre = str(df.loc[0, 'NOMBRES'])
    celular = str(df.loc[0, 'CELULAR'])
    fecha_fin = str(df.loc[0, 'FECHA FIN'])
    return mensaje_raw.format(nombre=nombre, celular=celular, fecha_fin=fecha_fin)
