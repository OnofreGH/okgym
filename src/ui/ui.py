import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import threading

from controller.controller import enviar_mensajes, validar_y_enviar, obtener_mensaje_previsualizacion

# Variables globales
excel_file = None
excel_logo_img = None
image_file = None
pdf_file = None

def update_icon(importado, nombre_archivo=None):
    if importado and nombre_archivo:
        icon_label.config(image=excel_logo_img, text="")
        file_name_label.config(text=os.path.basename(nombre_archivo))
    else:
        icon_label.config(image="", text="No importado")
        file_name_label.config(text="")

def seleccionar_archivo(tipo, extensiones, label, set_var_func):
    file_path = filedialog.askopenfilename(filetypes=[(tipo, extensiones)])
    if file_path:
        set_var_func(file_path)
        nombre_archivo = os.path.basename(file_path)
        label.config(text=f"{nombre_archivo}")
    else:
        set_var_func(None)
        label.config(text=f"Sin {tipo.lower()}")

def crear_seccion_archivo(app, tipo, extensiones, seleccionar_func, quitar_func, label_var):
    tk.Label(app, text=f"{tipo} opcional:").pack(pady=5)
    tk.Button(app, text=f"Seleccionar {tipo.lower()}", command=seleccionar_func).pack(pady=2)
    tk.Button(app, text=f"Quitar {tipo.lower()}", command=quitar_func).pack(pady=1)
    label = tk.Label(app, text=f"Sin {tipo.lower()}", font=("Arial", 10), fg="gray")
    label.pack(pady=3)
    label_var.append(label)

def browse_file():
    global excel_file
    filename = filedialog.askopenfilename(filetypes=[("Archivos de Excel", "*.xls *.xlsx")])
    if filename:
        excel_file = filename
        update_icon(True, filename)
    else:
        excel_file = None
        update_icon(False)

def browse_image():
    seleccionar_archivo("Imagen", "*.png;*.jpg;*.jpeg", image_label, lambda path: globals().__setitem__('image_file', path))

def browse_pdf():
    seleccionar_archivo("PDF", "*.pdf", pdf_label, lambda path: globals().__setitem__('pdf_file', path))

def remove_image():
    globals()['image_file'] = None
    image_label.config(text="Sin imagen")

def remove_pdf():
    globals()['pdf_file'] = None
    pdf_label.config(text="Sin PDF")

def send_in_thread():
    mensaje = message_text.get("1.0", tk.END).strip()
    thread = threading.Thread(
        target=enviar_mensajes,
        args=(excel_file, mensaje, image_file, pdf_file, status_label)
    )
    thread.start()

def send():
    mensaje = message_text.get("1.0", tk.END).strip()
    validar_y_enviar(excel_file, mensaje, status_label, message_text, send_in_thread)

def preview_message():
    if not excel_file:
        messagebox.showwarning("Advertencia", "Por favor selecciona un archivo de Excel primero.")
        return

    mensaje_raw = message_text.get("1.0", tk.END).strip()
    try:
        mensaje_final = obtener_mensaje_previsualizacion(excel_file, mensaje_raw)
        messagebox.showinfo("Vista previa del mensaje", f"Este es el mensaje que se enviará:\n\n{mensaje_final}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo previsualizar el mensaje:\n{e}")

def launch_app():
    global icon_label, file_name_label, message_text, excel_logo_img, status_label
    global image_label, pdf_label, image_file, pdf_file

    image_file = None
    pdf_file = None

    app = tk.Tk()
    app.title("Envío de mensajes por WhatsApp")

    tk.Label(app, text="Archivo Excel:").pack(pady=5)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    logo_path = os.path.join(base_dir, "assets", "ExcelLogo.png")

    try:
        img = Image.open(logo_path)
        img = img.resize((48, 48), Image.LANCZOS)
        excel_logo_img = ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"No se pudo cargar la imagen: {e}")
        excel_logo_img = None

    icon_label = tk.Label(app, text="No importado", font=("Arial", 12))
    icon_label.pack(pady=2)

    file_name_label = tk.Label(app, text="", font=("Arial", 10))
    file_name_label.pack(pady=2)

    tk.Button(app, text="Seleccionar archivo Excel", command=browse_file).pack(pady=5)

    tk.Label(app, text="Mensaje:").pack(pady=5)
    message_text = tk.Text(app, height=10, width=50)
    message_text.pack(pady=5)

    tk.Button(app, text="Previsualizar mensaje", command=preview_message).pack(pady=5)
    tk.Button(app, text="Enviar mensajes", command=send).pack(pady=10)

    image_label_list = []
    crear_seccion_archivo(app, "Imagen", "*.png;*.jpg;*.jpeg", browse_image, remove_image, image_label_list)
    image_label = image_label_list[0]

    pdf_label_list = []
    crear_seccion_archivo(app, "PDF", "*.pdf", browse_pdf, remove_pdf, pdf_label_list)
    pdf_label = pdf_label_list[0]

    status_label = tk.Label(app, text="", font=("Arial", 10), fg="blue")
    status_label.pack(pady=5)

    app.mainloop()
