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

image_files = []
pdf_files = []

COLOR_BG = "#e5e7eb"       # gris suave
COLOR_FG = "#1f2937"       # casi negro
COLOR_PRIMARY = "#2563eb"  # azul moderno
COLOR_ACCENT = "#dbeafe"   # fondo de botón activo
FONT_BASE = ("Segoe UI", 10)

def update_icon(importado, nombre_archivo=None):
    if importado and nombre_archivo:
        icon_label.config(image=excel_logo_img, text="")
        file_name_label.config(text=os.path.basename(nombre_archivo))
    else:
        icon_label.config(image="", text="No importado")
        file_name_label.config(text="")

def seleccionar_archivo(tipo, extensiones, label, set_var_func):
    multiple = tipo.lower().startswith("imagen") or tipo.lower().startswith("pdf")
    
    if multiple:
        file_paths = filedialog.askopenfilenames(filetypes=[(tipo, extensiones)])
    else:
        file_paths = filedialog.askopenfilename(filetypes=[(tipo, extensiones)])

    if file_paths:
        set_var_func(file_paths)
        if multiple:
            count = len(file_paths)
            nombres = "\n".join(os.path.basename(p) for p in file_paths)
            plural_tipo = tipo.lower() + ("es" if tipo.lower().endswith("f") else "s")
            label.config(
                text=f"{count} {plural_tipo} seleccionad{'as' if tipo.lower() == 'imagen' else 'os'}:\n{nombres}",
                foreground=COLOR_FG
            )
        else:
            label.config(text=os.path.basename(file_paths), foreground=COLOR_FG)
    else:
        set_var_func([] if multiple else None)
        label.config(text=f"Sin {tipo.lower()}", foreground="gray")

def crear_seccion_archivo(frame, tipo, extensiones, seleccionar_func, quitar_func, label_var, row, column):
    section = tk.Frame(frame, bg=COLOR_BG)
    section.grid(row=row, column=column, padx=10, pady=5, sticky="nsew")

    tk.Label(section, text=f"{tipo} opcional", font=FONT_BASE, bg=COLOR_BG, fg=COLOR_FG).pack(anchor="w")

    btn_frame = tk.Frame(section, bg=COLOR_BG)
    btn_frame.pack(anchor="w", pady=2, fill="x")

    tk.Button(btn_frame, text=f"Seleccionar {tipo.lower()}", command=seleccionar_func,
              bg=COLOR_PRIMARY, fg="white", font=FONT_BASE, bd=0, padx=10, pady=4,
              activebackground=COLOR_ACCENT).pack(side="left", padx=(0, 10))

    tk.Button(btn_frame, text=f"Quitar {tipo.lower()}", command=quitar_func,
              bg="#ef4444", fg="white", font=FONT_BASE, bd=0, padx=10, pady=4,
              activebackground="#fecaca").pack(side="left")

    label = tk.Label(section, text=f"Sin {tipo.lower()}", font=("Segoe UI", 9), fg="gray", bg=COLOR_BG, anchor="w")
    label.pack(anchor="w", pady=2, fill="x")
    label_var.append(label)

def browse_file():
    global excel_file
    filename = filedialog.askopenfilename(filetypes=[("Archivos de Excel", "*.xls *.xlsx")])
    if filename:
        # Verificar si es .xls y convertir automáticamente
        if filename.lower().endswith('.xls'):
            try:
                from logic.logic import convertir_xls_a_xlsx
                messagebox.showinfo("Conversión", "Archivo .xls detectado. Convirtiendo automáticamente a .xlsx...")
                
                # Convertir el archivo y actualizar la variable excel_file
                archivo_convertido = convertir_xls_a_xlsx(filename)
                excel_file = archivo_convertido
                
                # Actualizar la interfaz con el archivo convertido
                update_icon(True, archivo_convertido)
                messagebox.showinfo("Éxito", f"Archivo convertido exitosamente:\n{os.path.basename(archivo_convertido)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo convertir el archivo:\n{e}")
                excel_file = None
                update_icon(False)
        else:
            # Si es .xlsx, usar directamente
            excel_file = filename
            update_icon(True, filename)
    else:
        excel_file = None
        update_icon(False)

def browse_image():
    seleccionar_archivo(
        "Imagen", "*.png;*.jpg;*.jpeg", image_label,
        lambda paths: globals().__setitem__('image_files', list(paths) if paths else [])
    )

def browse_pdf():
    seleccionar_archivo(
        "PDF", "*.pdf", pdf_label,
        lambda paths: globals().__setitem__('pdf_files', list(paths) if paths else [])
    )

def remove_image():
    globals()['image_files'] = []
    image_label.config(text="Sin imagen", fg="gray")

def remove_pdf():
    globals()['pdf_files'] = []
    pdf_label.config(text="Sin PDF", fg="gray")

def send_in_thread():
    mensaje = message_text.get("1.0", tk.END).strip()
    thread = threading.Thread(
        target=enviar_mensajes,
        args=(excel_file, mensaje, image_files, pdf_files, status_label)
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
    app.title("WhatsApp Sender")
    app.geometry("1200x800")  # Aumentar ancho para el panel de instrucciones
    app.configure(bg=COLOR_BG)

    app.columnconfigure(0, weight=2)  # Columna principal (más ancha)
    app.columnconfigure(1, weight=1)  # Columna de instrucciones (menos ancha)
    app.rowconfigure(0, weight=1)

    # --- PANEL PRINCIPAL (IZQUIERDA) ---
    main_frame = tk.Frame(app, bg=COLOR_BG)
    main_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
    for i in range(10):
        main_frame.rowconfigure(i, weight=1)
    main_frame.columnconfigure(0, weight=1)

    # --- PANEL DE INSTRUCCIONES (DERECHA) ---
    instructions_frame = tk.Frame(app, bg="white", relief="solid", bd=1)
    instructions_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
    instructions_frame.columnconfigure(0, weight=1)

    # Título del panel de instrucciones
    tk.Label(instructions_frame, text="📋 Cómo usar el programa", 
             font=("Segoe UI", 12, "bold"), bg="white", fg=COLOR_FG).pack(pady=10, padx=10, anchor="w")

    # Crear un frame con scroll para las instrucciones
    canvas = tk.Canvas(instructions_frame, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(instructions_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Instrucciones paso a paso
    instrucciones = [
        (" 1 Seleccionar archivo Excel", [
            "• Ingresa un archivo Excel (.xls o .xlsx) se convierte automáticamente."
            "• Verifica que aparezca el ícono ✅"
        ]),
        (" 2 Escribir mensaje", [
            "• Escribe tu mensaje en el cuadro de texto",
            "• Usa variables: {nombre}, {fecha_fin}",
            "• Ejemplo: 'Hola {nombre}, tu membresía vence el {fecha_fin}'"
        ]),
        (" 3 Adjuntar archivos (opcional)", [
            "• Selecciona imágenes (.png, .jpg, .jpeg)",
            "• Selecciona PDFs si necesitas",
            "• Puedes adjuntar múltiples archivos"
        ]),
        (" 4 Previsualizar", [
            "• Haz clic en 'Previsualizar'",
            "• Revisa cómo se verá el mensaje",
            "• Verifica que las variables se muestren correctamente"
        ]),
        (" 5 Enviar mensajes", [
            "• Haz clic en 'Enviar mensajes'",
            "• Se abrirá WhatsApp Web automáticamente",
            "• IMPORTANTE: Tener WhatsApp Web abierto con la cuenta de la empresa",
            "• Espera a que se envíen todos los mensajes",
        ])
    ]

    for titulo, pasos in instrucciones:
        # Título de cada sección
        titulo_label = tk.Label(scrollable_frame, text=titulo, 
                               font=("Segoe UI", 10, "bold"), bg="white", fg=COLOR_PRIMARY)
        titulo_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Pasos de cada sección
        for paso in pasos:
            paso_label = tk.Label(scrollable_frame, text=paso, 
                                 font=("Segoe UI", 9), bg="white", fg=COLOR_FG, 
                                 wraplength=250, justify="left")
            paso_label.pack(anchor="w", padx=20, pady=1)

    # Notas importantes
    tk.Label(scrollable_frame, text="⚠️ Notas importantes", 
             font=("Segoe UI", 10, "bold"), bg="white", fg="#ef4444").pack(anchor="w", padx=10, pady=(15, 5))

    notas = [
        "• Mantén WhatsApp Web abierto durante el envío",
        "• No uses el mouse mientras se envían mensajes",
        "• Los números inválidos se omiten automáticamente",
        "• Archivos .xls se convierten a .xlsx automáticamente"
    ]

    for nota in notas:
        nota_label = tk.Label(scrollable_frame, text=nota, 
                             font=("Segoe UI", 9), bg="white", fg="#ef4444", 
                             wraplength=250, justify="left")
        nota_label.pack(anchor="w", padx=20, pady=1)

    canvas.pack(side="left", fill="both", expand=True, padx=(0, 10))
    scrollbar.pack(side="right", fill="y")

    # --- RESTO DEL CÓDIGO DEL PANEL PRINCIPAL (sin cambios) ---
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    logo_path = os.path.join(base_dir, "assets", "ExcelLogo.png")

    try:
        img = Image.open(logo_path)
        img = img.resize((48, 48), Image.LANCZOS)
        excel_logo_img = ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"No se pudo cargar la imagen: {e}")
        excel_logo_img = None

    tk.Label(main_frame, text="Enviar mensajes por WhatsApp", font=("Segoe UI", 14, "bold"),
             bg=COLOR_BG, fg=COLOR_FG).grid(row=0, column=0, sticky="w")

    tk.Label(main_frame, text="Archivo Excel", font=FONT_BASE, bg=COLOR_BG, fg=COLOR_FG).grid(row=1, column=0, sticky="w")
    icon_label = tk.Label(main_frame, text="No importado", font=FONT_BASE, bg=COLOR_BG, fg="gray")
    icon_label.grid(row=2, column=0, sticky="w")
    file_name_label = tk.Label(main_frame, text="", font=("Segoe UI", 9), bg=COLOR_BG, fg="gray")
    file_name_label.grid(row=3, column=0, sticky="w")

    tk.Button(main_frame, text="Seleccionar Excel", command=browse_file,
              bg=COLOR_PRIMARY, fg="white", font=FONT_BASE, bd=0, padx=12, pady=6,
              activebackground=COLOR_ACCENT).grid(row=4, column=0, sticky="w", pady=5)

    tk.Label(main_frame, text="Mensaje a enviar", font=FONT_BASE, bg=COLOR_BG, fg=COLOR_FG).grid(row=5, column=0, sticky="w", pady=(10, 2))

    message_text = tk.Text(main_frame, height=10, font=("Segoe UI", 10), bd=1, relief="flat", wrap="word")
    message_text.grid(row=6, column=0, sticky="nsew")

    tk.Button(main_frame, text="Previsualizar", command=preview_message,
              bg="#6b7280", fg="white", font=FONT_BASE, bd=0, padx=10, pady=5,
              activebackground="#9ca3af").grid(row=7, column=0, sticky="w", pady=5)

    tk.Button(main_frame, text="Enviar mensajes", command=send,
              bg=COLOR_PRIMARY, fg="white", font=FONT_BASE, bd=0, padx=10, pady=7,
              activebackground=COLOR_ACCENT).grid(row=8, column=0, sticky="w", pady=5)

    frame_extra = tk.Frame(main_frame, bg=COLOR_BG)
    frame_extra.grid(row=9, column=0, sticky="nsew")
    frame_extra.columnconfigure(0, weight=1)
    frame_extra.columnconfigure(1, weight=1)

    image_label_list = []
    crear_seccion_archivo(frame_extra, "Imagen", "*.png;*.jpg;*.jpeg", browse_image, remove_image, image_label_list, 0, 0)
    image_label = image_label_list[0]

    pdf_label_list = []
    crear_seccion_archivo(frame_extra, "PDF", "*.pdf", browse_pdf, remove_pdf, pdf_label_list, 0, 1)
    pdf_label = pdf_label_list[0]

    status_label = tk.Label(main_frame, text="", font=("Segoe UI", 9), fg=COLOR_PRIMARY, bg=COLOR_BG)
    status_label.grid(row=10, column=0, sticky="w", pady=10)

    app.mainloop()