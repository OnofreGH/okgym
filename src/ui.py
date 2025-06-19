import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import re
import os
import time
import webbrowser as web
import pyautogui as pg
from urllib.parse import quote
from utils import normalizar_numero

# Variables globales
excel_file = None
excel_logo_img = None
image_file = None  # Global

# Actualiza el ícono y el nombre del archivo seleccionado
def update_icon(importado, nombre_archivo=None):
    if importado and nombre_archivo:
        icon_label.config(image=excel_logo_img, text="")  # Muestra imagen
        # Muestra solo el nombre del archivo (sin la ruta completa)
        file_name_label.config(text=nombre_archivo.split("/")[-1] or nombre_archivo.split("\\")[-1])
    else:
        icon_label.config(image="", text="❌ No importado")  # Muestra texto por defecto
        file_name_label.config(text="")  # Limpia el texto del nombre del archivo

# Permite al usuario seleccionar un archivo Excel
def browse_file():
    global excel_file
    filename = filedialog.askopenfilename(filetypes=[("Archivos de Excel", "*.xlsx")])
    if filename:
        excel_file = filename
        update_icon(True, filename)
    else:
        excel_file = None
        update_icon(False)

# Selecciona una imagen para enviar junto con el mensaje
def browse_image():
    global image_file
    file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
    if file_path:
        image_file = file_path
        image_label.config(text=f"📷 Imagen seleccionada: {file_path.split('/')[-1]}")
    else:
        image_file = None
        image_label.config(text="Sin imagen")

# Elimina la imagen seleccionada
def remove_image():
    global image_file
    image_file = None
    image_label.config(text="Sin imagen")

# Envía los mensajes en un hilo separado para no congelar la interfaz
def send_in_thread():
    try:
        df = pd.read_excel(excel_file, header=1)
        mensaje = message_text.get("1.0", tk.END).strip()
        total = len(df)
        enviados = 0

        for i in range(total):
            celular_raw = df.loc[i, 'CELULAR']
            celular = normalizar_numero(celular_raw)
            if not celular:
                continue

            nombre = str(df.loc[i, 'NOMBRES']).strip()
            fecha_fin = str(df.loc[i, 'FECHA FIN']).strip()

            try:
                mensaje_formateado = mensaje.format(nombre=nombre, fecha_fin=fecha_fin, celular=celular)
            except Exception as e:
                print(f"[⚠️ Formato inválido en fila {i+2}]: {e}")
                continue

            # Actualiza estado en la UI
            status_label.config(text=f"Enviando mensaje {enviados + 1} de {total}...")
            status_label.update_idletasks()

            # Abre WhatsApp Web con el mensaje
            url = f"https://web.whatsapp.com/send?phone={celular}&text={quote(mensaje_formateado)}"
            web.open(url)
            time.sleep(10)  # Espera que cargue la conversación

            # Envía imagen si fue seleccionada
            if image_file:
                try:
                    pg.click(1220, 980)  # Haz clic en el ícono de adjuntar (ajusta según tu resolución)
                    time.sleep(2)
                    pg.write(image_file)  # Ruta de la imagen
                    pg.press('enter')
                    time.sleep(3)
                except Exception as e:
                    print(f"[❌ Error al adjuntar imagen]: {e}")

            pg.press('enter')  # Enviar mensaje
            time.sleep(3)
            pg.hotkey('ctrl', 'w')  # Cierra la pestaña
            time.sleep(2)

            enviados += 1

        status_label.config(text="✅ Envío completado")
        messagebox.showinfo("Éxito", f"Se enviaron {enviados} mensajes exitosamente.")

    except Exception as e:
        status_label.config(text="❌ Error durante el envío")
        messagebox.showerror("Error", str(e))

# Valida los datos y lanza el hilo de envío
def send():
    if not excel_file or not message_text.get("1.0", tk.END).strip():
        messagebox.showerror("Error", "Por favor selecciona un archivo de Excel y escribe un mensaje.")
        return

    try:
        df = pd.read_excel(excel_file, header=1)  # Usa la fila 2 como encabezado

        validos = 0  # Contador de celulares válidos

        for i in range(len(df)):
            celular = df.loc[i, 'CELULAR']
            celular_normalizado = normalizar_numero(celular)
            
            print(f"[DEBUG] Fila {i+2} - Celular bruto: {celular}")
            print(f"[DEBUG] Celular normalizado: {celular_normalizado}")

            if celular_normalizado:
                validos += 1  # Aquí debería aumentar correctamente

        print(f"[DEBUG] Total válidos: {validos}")

        if validos == 0:
            messagebox.showwarning("Advertencia", "No se encontró ningún número válido con formato peruano.")
            return
        else:
            messagebox.showinfo("Validación exitosa", f"Se detectaron {validos} números válidos. Iniciando envío...")

        # Si hay válidos, ejecutamos el envío
        thread = threading.Thread(target=send_in_thread)
        thread.start()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo validar el archivo:\n{e}")

# Muestra una previsualización del mensaje con los datos del primer registro
def preview_message():
    if not excel_file:
        messagebox.showwarning("Advertencia", "Por favor selecciona un archivo de Excel primero.")
        return

    try:
        # Lee el archivo Excel (primera hoja o puedes especificar)
        df = pd.read_excel(excel_file, header=1)

        if df.empty:
            messagebox.showwarning("Advertencia", "El archivo Excel está vacío.")
            return

        # Extrae datos del primer registro
        nombre = str(df.loc[0, 'NOMBRES'])
        celular = str(df.loc[0, 'CELULAR'])
        fecha_fin = str(df.loc[0, 'FECHA FIN'])
        # Obtiene el mensaje escrito por el usuario
        mensaje_raw = message_text.get("1.0", tk.END).strip()
        # Intenta formatear el mensaje con los valores del Excel
        mensaje_final = mensaje_raw.format(nombre=nombre, celular=celular, fecha_fin=fecha_fin)

        # Muestra el mensaje de ejemplo
        messagebox.showinfo("Vista previa del mensaje", f"Este es el mensaje que se enviará:\n\n{mensaje_final}")

    except KeyError as e:
        messagebox.showerror("Error", f"La columna '{e}' no se encontró en el Excel.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo previsualizar el mensaje:\n{e}")

# Lanza la ventana principal de la aplicación
def launch_app():
    global icon_label, file_name_label, message_text, excel_logo_img, image_status_label, status_label, image_file

    image_file = None  # Inicializa la variable de imagen

    app = tk.Tk()
    app.title("Envío de mensajes por WhatsApp")

    # Etiqueta para seleccionar archivo Excel
    tk.Label(app, text="Archivo Excel:").pack(pady=5)

    # Carga del logo de Excel
    logo_path = "src/ExcelLogo.png"
    try:
        img = Image.open(logo_path)
        img = img.resize((48, 48), Image.LANCZOS)
        excel_logo_img = ImageTk.PhotoImage(img)
    except:
        excel_logo_img = None

    # Muestra el estado del archivo (importado o no)
    icon_label = tk.Label(app, text="❌ No importado", font=("Arial", 12))
    icon_label.pack(pady=2)

    # Nombre del archivo cargado
    file_name_label = tk.Label(app, text="", font=("Arial", 10))
    file_name_label.pack(pady=2)

    # Botón para buscar archivo Excel
    tk.Button(app, text="Seleccionar archivo Excel", command=browse_file).pack(pady=5)

    # Área de texto para el mensaje
    tk.Label(app, text="Mensaje:").pack(pady=5)
    message_text = tk.Text(app, height=10, width=50)
    message_text.pack(pady=5)

    # Botón para previsualizar el mensaje
    tk.Button(app, text="Previsualizar mensaje", command=preview_message).pack(pady=5)

    # Botón para enviar mensajes
    tk.Button(app, text="Enviar mensajes", command=send).pack(pady=10)

    # Sección para imagen adjunta
    tk.Label(app, text="Imagen opcional:").pack(pady=5)

    frame_imagen = tk.Frame(app)
    frame_imagen.pack(pady=5)

    # Botones y estado de imagen
    tk.Button(app, text="Seleccionar imagen", command=browse_image).pack(pady=5)
    tk.Button(app, text="Quitar imagen", command=remove_image).pack(pady=1)

    global image_label
    image_label = tk.Label(app, text="Sin imagen", font=("Arial", 10), fg="gray")
    image_label.pack(pady=3)

    # Etiqueta para mostrar estado del envío
    status_label = tk.Label(app, text="", font=("Arial", 10), fg="blue")
    status_label.pack(pady=5)

    app.mainloop()
