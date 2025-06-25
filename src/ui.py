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
import pyperclip
from urllib.parse import quote
from utils import normalizar_numero

# Variables globales
excel_file = None
excel_logo_img = None
image_file = None
pdf_file = None

def update_icon(importado, nombre_archivo=None):
    if importado and nombre_archivo:
        icon_label.config(image=excel_logo_img, text="")
        file_name_label.config(text=nombre_archivo.split("/")[-1] or nombre_archivo.split("\\")[-1])
    else:
        icon_label.config(image="", text="❌ No importado")
        file_name_label.config(text="")

def browse_file():
    global excel_file
    # ✅ Ahora acepta tanto .xls como .xlsx
    filename = filedialog.askopenfilename(filetypes=[("Archivos de Excel", "*.xls *.xlsx")])
    if filename:
        excel_file = filename
        update_icon(True, filename)
    else:
        excel_file = None
        update_icon(False)

def browse_pdf():
    global pdf_file
    file_path = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
    if file_path:
        pdf_file = file_path
        pdf_label.config(text=f"📄 PDF seleccionado {os.path.basename(file_path)}")
    else:
        pdf_file = None
        pdf_label.config(text="Sin PDF")

def browse_image():
    global image_file
    file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
    if file_path:
        image_file = file_path
        image_label.config(text=f"📷 Imagen seleccionada {os.path.basename(file_path)}")
    else:
        image_file = None
        image_label.config(text="Sin imagen")

def remove_image():
    global image_file
    image_file = None
    image_label.config(text="Sin imagen")

def remove_pdf():
    global pdf_file
    pdf_file = None
    pdf_label.config(text="Sin PDF")

def leer_excel(path):
    ext = os.path.splitext(path)[1].lower()  # convertimos a minúsculas para evitar errores con mayúsculas
    if ext == '.xls':
        try:
            df = pd.read_excel(path, header=1, engine="xlrd")
        except ImportError:
            raise Exception("Para leer archivos .xls necesitas instalar xlrd versión 1.2.0:\npip install xlrd==1.2.0")
        except Exception as e:
            raise e
    elif ext == '.xlsx':
        try:
            df = pd.read_excel(path, header=1, engine="openpyxl")
        except ImportError:
            raise Exception("Para leer archivos .xlsx necesitas tener instalado openpyxl:\npip install openpyxl")
        except Exception as e:
            raise e
    else:
        raise Exception("Formato de archivo no soportado. Solo se aceptan archivos .xls y .xlsx.")
    
    return df


def send_in_thread():
    try:
        df = leer_excel(excel_file)
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

            status_label.config(text=f"Enviando mensaje {enviados + 1} de {total}...")
            status_label.update_idletasks()
            
            url = f"https://web.whatsapp.com/send?phone={celular}&text={quote(mensaje_formateado)}"
            web.open(url)
            time.sleep(10)
                

            #if i == 0:
            #    url = f"https://web.whatsapp.com/send?phone={celular}&text={quote(mensaje_formateado)}"
            #    web.open(url)
            #    time.sleep(10)
            #pyperclip.copy(mensaje_formateado)
            #pg.click(900, 975)
            #time.sleep(1)
            #pg.hotkey('ctrl', 'v')
            #time.sleep(1)


            if image_file:
                try:
                    time.sleep(3)
                    pg.click(705, 975)
                    time.sleep(2)
                    pg.click(685, 595)
                    time.sleep(1)
                    pg.write(os.path.basename(image_file))
                    time.sleep(1)
                    pg.press('enter')
                    time.sleep(3)
                    pg.press('enter')
                    time.sleep(3)
                except Exception as e:
                    print(f"[❌ Error al adjuntar imagen]: {e}")
            
            if pdf_file:
                try:
                    time.sleep(3)
                    pg.click(705, 975)
                    time.sleep(2)
                    pg.click(685, 540)
                    time.sleep(1)
                    pg.write(os.path.basename(pdf_file))
                    time.sleep(1)
                    pg.press('enter')
                    time.sleep(3)
                    pg.press('enter')
                    time.sleep(3)
                except Exception as e:
                    print(f"[❌ Error al adjuntar PDF]: {e}")

            pg.press('enter')
            time.sleep(3)
            pg.hotkey('ctrl', 'w')
            time.sleep(2)

            enviados += 1

        status_label.config(text="✅ Envío completado")
        messagebox.showinfo("Éxito", f"Se enviaron {enviados} mensajes exitosamente.")

    except Exception as e:
        status_label.config(text="❌ Error durante el envío")
        messagebox.showerror("Error", str(e))

def send():
    if not excel_file or not message_text.get("1.0", tk.END).strip():
        messagebox.showerror("Error", "Por favor selecciona un archivo de Excel y escribe un mensaje.")
        return

    try:
        df = leer_excel(excel_file)
        validos = 0

        for i in range(len(df)):
            celular = df.loc[i, 'CELULAR']
            celular_normalizado = normalizar_numero(celular)
            print(f"[DEBUG] Fila {i+2} - Celular bruto: {celular}")
            print(f"[DEBUG] Celular normalizado: {celular_normalizado}")
            if celular_normalizado:
                validos += 1

        print(f"[DEBUG] Total válidos: {validos}")

        if validos == 0:
            messagebox.showwarning("Advertencia", "No se encontró ningún número válido con formato peruano.")
            return
        else:
            messagebox.showinfo("Validación exitosa", f"Se detectaron {validos} números válidos. Iniciando envío...")

        thread = threading.Thread(target=send_in_thread)
        thread.start()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo validar el archivo:\n{e}")

def preview_message():
    if not excel_file:
        messagebox.showwarning("Advertencia", "Por favor selecciona un archivo de Excel primero.")
        return

    try:
        df = leer_excel(excel_file)

        if df.empty:
            messagebox.showwarning("Advertencia", "El archivo Excel está vacío.")
            return

        nombre = str(df.loc[0, 'NOMBRES'])
        celular = str(df.loc[0, 'CELULAR'])
        fecha_fin = str(df.loc[0, 'FECHA FIN'])
        mensaje_raw = message_text.get("1.0", tk.END).strip()
        mensaje_final = mensaje_raw.format(nombre=nombre, celular=celular, fecha_fin=fecha_fin)

        messagebox.showinfo("Vista previa del mensaje", f"Este es el mensaje que se enviará:\n\n{mensaje_final}")

    except KeyError as e:
        messagebox.showerror("Error", f"La columna '{e}' no se encontró en el Excel.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo previsualizar el mensaje:\n{e}")

def launch_app():
    global icon_label, file_name_label, message_text, excel_logo_img, image_status_label, status_label, image_label, pdf_label, image_file, pdf_file

    image_file = None
    pdf_file = None

    app = tk.Tk()
    app.title("Envío de mensajes por WhatsApp")

    tk.Label(app, text="Archivo Excel:").pack(pady=5)

    logo_path = "src/ExcelLogo.png"
    try:
        img = Image.open(logo_path)
        img = img.resize((48, 48), Image.LANCZOS)
        excel_logo_img = ImageTk.PhotoImage(img)
    except:
        excel_logo_img = None

    icon_label = tk.Label(app, text="❌ No importado", font=("Arial", 12))
    icon_label.pack(pady=2)

    file_name_label = tk.Label(app, text="", font=("Arial", 10))
    file_name_label.pack(pady=2)

    tk.Button(app, text="Seleccionar archivo Excel", command=browse_file).pack(pady=5)

    tk.Label(app, text="Mensaje:").pack(pady=5)
    message_text = tk.Text(app, height=10, width=50)
    message_text.pack(pady=5)

    tk.Button(app, text="Previsualizar mensaje", command=preview_message).pack(pady=5)
    tk.Button(app, text="Enviar mensajes", command=send).pack(pady=10)

    tk.Label(app, text="Imagen opcional:").pack(pady=5)

    frame_imagen = tk.Frame(app)
    frame_imagen.pack(pady=5)

    tk.Button(app, text="Seleccionar imagen", command=browse_image).pack(pady=5)
    tk.Button(app, text="Quitar imagen", command=remove_image).pack(pady=1)

    image_label = tk.Label(app, text="Sin imagen", font=("Arial", 10), fg="gray")
    image_label.pack(pady=3)

    tk.Label(app, text="PDF opcional:").pack(pady=5)

    frame_pdf = tk.Frame(app)
    frame_pdf.pack(pady=5)

    tk.Button(app, text="Seleccionar PDF (opcional)", command=browse_pdf).pack(pady=5)
    tk.Button(app, text="Quitar PDF", command=remove_pdf).pack(pady=1)

    pdf_label = tk.Label(app, text="Sin PDF", font=("Arial", 10), fg="gray")
    pdf_label.pack(pady=3)

    status_label = tk.Label(app, text="", font=("Arial", 10), fg="blue")
    status_label.pack(pady=5)

    app.mainloop()