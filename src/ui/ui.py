import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import threading
import sys

from controller.controller import enviar_mensajes, validar_y_enviar, obtener_mensaje_previsualizacion

# Variables globales
excel_file = None
excel_logo_img = None
image_file = None
pdf_file = None

image_files = []
pdf_files = []

# Variables para control de envío
app_running = True
current_thread = None
sending_paused = False
last_sent_index = 0  # Índice del último contacto enviado
total_contacts = 0   # Total de contactos válidos
progress_bar = None
progress_label = None
pause_button = None

COLOR_BG = "#e5e7eb"       # gris suave
COLOR_FG = "#1f2937"       # casi negro
COLOR_PRIMARY = "#2563eb"  # azul moderno
COLOR_ACCENT = "#dbeafe"   # fondo de botón activo
FONT_BASE = ("Segoe UI", 10)

def on_closing():
    """Maneja el cierre de la aplicación"""
    global app_running, current_thread
    
    # Preguntar confirmación si hay un hilo ejecutándose
    if current_thread and current_thread.is_alive():
        result = messagebox.askyesno(
            "Confirmar cierre", 
            "Hay un proceso de envío en curso. ¿Estás seguro de que quieres cerrar?\n\nEsto detendrá el envío de mensajes."
        )
        if not result:
            return
    
    # Marcar que la aplicación se está cerrando
    app_running = False
    
    # Intentar terminar hilos activos
    if current_thread and current_thread.is_alive():
        print("🛑 Cerrando aplicación, deteniendo proceso de envío...")
        current_thread.join(timeout=2)
    
    # Cerrar la aplicación
    app.quit()
    app.destroy()
    os._exit(0)

def toggle_pause():
    """Alterna entre pausar y reanudar el envío"""
    global sending_paused
    
    if sending_paused:
        # Reanudar envío
        sending_paused = False
        pause_button.config(text="⏸️ Pausar", bg="#ef4444", activebackground="#fecaca")
        status_label.config(text=f"▶️ Reanudando envío desde contacto {last_sent_index + 1}...")
        # Mantener interfaz bloqueada durante la reanudación
        lock_interface()
    else:
        # Pausar envío - puede permitir edición del mensaje si se desea
        sending_paused = True
        pause_button.config(text="▶️ Reanudar", bg="#10b981", activebackground="#a7f3d0")
        status_label.config(text=f"⏸️ Envío pausado en contacto {last_sent_index}. Haz clic en Reanudar para continuar.")
        # Opcional: desbloquear mensaje durante la pausa para permitir edición
        # unlock_interface()

def update_progress(current, total, contact_name=""):
    """Actualiza la barra de progreso y el contador"""
    global last_sent_index
    
    last_sent_index = current
    progress = (current / total) * 100 if total > 0 else 0
    
    # Actualizar barra de progreso
    if progress_bar:
        progress_bar['value'] = progress
    
    # Actualizar etiqueta de progreso
    if progress_label:
        if contact_name:
            progress_label.config(text=f"📤 Enviando a: {contact_name} ({current}/{total})")
        else:
            progress_label.config(text=f"📊 Progreso: {current}/{total} ({progress:.1f}%)")

def lock_interface():
    """Bloquea la interfaz durante el envío"""
    if message_text:
        message_text.config(state='disabled')
    
    # También bloquear otros controles críticos
    send_button.config(state='disabled')
    browse_button.config(state='disabled')
    preview_button.config(state='disabled')

def unlock_interface():
    """Desbloquea la interfaz después del envío"""
    if message_text:
        message_text.config(state='normal')
    
    # Desbloquear otros controles
    send_button.config(state='normal')
    browse_button.config(state='normal')
    preview_button.config(state='normal')

def disable_all_widgets(parent):
    """Deshabilita recursivamente todos los widgets excepto el botón de pausa"""
    for child in parent.winfo_children():
        if hasattr(child, 'winfo_children'):
            disable_all_widgets(child)
        
        # No deshabilitar el botón de pausa ni la barra de progreso
        if child not in [pause_button, progress_bar, progress_label]:
            try:
                if hasattr(child, 'config'):
                    child.config(state='disabled')
            except tk.TclError:
                pass  # Algunos widgets no tienen estado

def enable_all_widgets(parent):
    """Habilita recursivamente todos los widgets"""
    for child in parent.winfo_children():
        if hasattr(child, 'winfo_children'):
            enable_all_widgets(child)
        
        try:
            if hasattr(child, 'config'):
                child.config(state='normal')
        except tk.TclError:
            pass  # Algunos widgets no tienen estado

def lock_interface_complete():
    """Bloquea completamente la interfaz durante el envío"""
    # Bloquear solo los controles críticos
    if message_text:
        message_text.config(state='disabled')
    
    send_button.config(state='disabled')
    browse_button.config(state='disabled')
    preview_button.config(state='disabled')
    
    # Cambiar cursor para indicar que está ocupado
    app.config(cursor="wait")

def unlock_interface_complete():
    """Desbloquea completamente la interfaz después del envío"""
    if message_text:
        message_text.config(state='normal')
    
    send_button.config(state='normal')
    browse_button.config(state='normal')
    preview_button.config(state='normal')
    
    # Restaurar cursor normal
    app.config(cursor="")

def reset_progress():
    """Resetea el progreso y oculta los controles"""
    global last_sent_index, sending_paused, total_contacts
    
    last_sent_index = 0
    sending_paused = False
    total_contacts = 0
    
    # Usar desbloqueo completo
    unlock_interface_complete()
    
    if progress_bar:
        progress_bar['value'] = 0
        progress_bar.grid_remove()
    
    if progress_label:
        progress_label.config(text="")
        progress_label.grid_remove()
    
    if pause_button:
        pause_button.grid_remove()

def show_progress_controls(total):
    """Muestra los controles de progreso y bloquea la interfaz"""
    global total_contacts
    
    total_contacts = total
    
    # Usar bloqueo completo
    lock_interface_complete()
    
    if progress_bar:
        progress_bar.grid(row=11, column=0, sticky="ew", pady=(5, 0))
    
    if progress_label:
        progress_label.grid(row=12, column=0, sticky="w", pady=(2, 0))
    
    if pause_button:
        pause_button.config(text="⏸️ Pausar", bg="#ef4444", activebackground="#fecaca")
        pause_button.grid(row=13, column=0, sticky="w", pady=(5, 0))

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

    btn_select = tk.Button(btn_frame, text=f"Seleccionar {tipo.lower()}", command=seleccionar_func,
              bg=COLOR_PRIMARY, fg="white", font=FONT_BASE, bd=0, padx=10, pady=4,
              activebackground=COLOR_ACCENT)
    btn_select.pack(side="left", padx=(0, 10))

    btn_remove = tk.Button(btn_frame, text=f"Quitar {tipo.lower()}", command=quitar_func,
              bg="#ef4444", fg="white", font=FONT_BASE, bd=0, padx=10, pady=4,
              activebackground="#fecaca")
    btn_remove.pack(side="left")

    label = tk.Label(section, text=f"Sin {tipo.lower()}", font=("Segoe UI", 9), fg="gray", bg=COLOR_BG, anchor="w")
    label.pack(anchor="w", pady=2, fill="x")
    label_var.append(label)

    return btn_select  # Retorna el botón seleccionar

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
    if image_files:
        pdf_select_button.config(state='disabled')  # Deshabilitar PDF

def browse_pdf():
    seleccionar_archivo(
        "PDF", "*.pdf", pdf_label,
        lambda paths: globals().__setitem__('pdf_files', list(paths) if paths else [])
    )
    if pdf_files:
        image_select_button.config(state='disabled')  # Deshabilitar imagen

def remove_image():
    globals()['image_files'] = []
    image_label.config(text="Sin imagen", fg="gray")
    pdf_select_button.config(state='normal')  # Volver a habilitar PDF

def remove_pdf():
    globals()['pdf_files'] = []
    pdf_label.config(text="Sin PDF", fg="gray")
    image_select_button.config(state='normal')  # Volver a habilitar imagen

    globals()['pdf_files'] = []
    pdf_label.config(text="Sin PDF", fg="gray")

def send_in_thread():
    """Ejecuta el envío en un hilo separado con control de cierre"""
    global current_thread, app_running, sending_paused, last_sent_index
    
    mensaje = message_text.get("1.0", tk.END).strip()
    
    def envio_controlado():
        try:
            # Función que verifica si debe continuar
            def should_continue():
                return app_running and not sending_paused
            
            # Función para actualizar progreso desde el controlador
            def update_progress_callback(current, total, contact_name=""):
                if app_running:
                    app.after(0, lambda: update_progress(current, total, contact_name))
            
            # Pasar todas las funciones de callback al controlador
            enviar_mensajes(
                excel_file, mensaje, image_files, pdf_files, status_label,
                app_running_check=lambda: app_running,
                pause_check=lambda: not sending_paused,
                progress_callback=update_progress_callback,
                start_index=last_sent_index
            )
        except Exception as e:
            if app_running:
                print(f"Error en envío: {e}")
        finally:
            # Limpiar la referencia al hilo y ocultar controles
            if app_running:
                current_thread = None
                app.after(0, reset_progress)
    
    current_thread = threading.Thread(target=envio_controlado, daemon=True)
    current_thread.start()

def send():
    """Validar y enviar mensajes"""
    global current_thread, last_sent_index
    
    # Verificar si ya hay un proceso ejecutándose
    if current_thread and current_thread.is_alive():
        messagebox.showwarning("Proceso en curso", "Ya hay un proceso de envío ejecutándose. Espera a que termine o usa el botón de pausa.")
        return
    
    mensaje = message_text.get("1.0", tk.END).strip()
    
    # Verificar que hay mensaje antes de continuar
    if not mensaje:
        messagebox.showwarning("Mensaje vacío", "Por favor escribe un mensaje antes de enviar.")
        return
    
    # Mostrar información de qué se va a enviar
    archivos_info = []
    if image_files:
        archivos_info.append(f"{len(image_files)} imagen(es)")
    if pdf_files:
        archivos_info.append(f"{len(pdf_files)} PDF(s)")
    
    if archivos_info:
        archivos_texto = " y ".join(archivos_info)
        confirmacion = messagebox.askyesno(
            "Confirmar envío", 
            f"Se enviará:\n• Mensaje de texto\n• {archivos_texto}\n\n¿Continuar con el envío?"
        )
        if not confirmacion:
            return
    
    # Si no es una reanudación, resetear el índice
    if not (current_thread and last_sent_index > 0):
        last_sent_index = 0
    
    validar_y_enviar(excel_file, mensaje, status_label, message_text, send_in_thread, show_progress_controls)

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
    global image_label, pdf_label, image_file, pdf_file, app, app_running
    global progress_bar, progress_label, pause_button
    global send_button, browse_button, preview_button  # Agregar referencias a botones

    # Reiniciar variables de control
    app_running = True
    image_file = None
    pdf_file = None

    app = tk.Tk()
    app.title("WhatsApp Sender")
    app.geometry("1200x800")
    app.configure(bg=COLOR_BG)

    # Configurar el manejo del cierre de ventana
    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.columnconfigure(0, weight=2)
    app.columnconfigure(1, weight=1)
    app.rowconfigure(0, weight=1)

    # --- PANEL PRINCIPAL (IZQUIERDA) ---
    main_frame = tk.Frame(app, bg=COLOR_BG)
    main_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
    for i in range(15):  # Aumentado para acomodar nuevos controles
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
            "• Puedes adjuntar múltiples archivos de cada tipo",
            "• Se pueden enviar imágenes Y PDFs al mismo tiempo"
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

    # --- RESTO DEL CÓDIGO DEL PANEL PRINCIPAL ---
    # Buscar el logo de Excel - compatible con PyInstaller
    try:
        if hasattr(sys, '_MEIPASS'):
            logo_path = os.path.join(sys._MEIPASS, "assets", "ExcelLogo.png")
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            logo_path = os.path.join(base_dir, "assets", "ExcelLogo.png")
        
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            img = img.resize((48, 48), Image.LANCZOS)
            excel_logo_img = ImageTk.PhotoImage(img)
        else:
            excel_logo_img = None
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

    # Guardar referencia al botón de seleccionar archivo
    browse_button = tk.Button(main_frame, text="Seleccionar Excel", command=browse_file,
              bg=COLOR_PRIMARY, fg="white", font=FONT_BASE, bd=0, padx=12, pady=6,
              activebackground=COLOR_ACCENT)
    browse_button.grid(row=4, column=0, sticky="w", pady=5)

    tk.Label(main_frame, text="Mensaje a enviar", font=FONT_BASE, bg=COLOR_BG, fg=COLOR_FG).grid(row=5, column=0, sticky="w", pady=(10, 2))

    # Cuadro de texto del mensaje con configuración inicial
    message_text = tk.Text(main_frame, height=10, font=("Segoe UI", 10), bd=1, relief="flat", wrap="word")
    message_text.grid(row=6, column=0, sticky="nsew")

    # Guardar referencia al botón de previsualizar
    preview_button = tk.Button(main_frame, text="Previsualizar", command=preview_message,
              bg="#6b7280", fg="white", font=FONT_BASE, bd=0, padx=10, pady=5,
              activebackground="#9ca3af")
    preview_button.grid(row=7, column=0, sticky="w", pady=5)

    # Guardar referencia al botón de enviar
    send_button = tk.Button(main_frame, text="Enviar mensajes", command=send,
              bg=COLOR_PRIMARY, fg="white", font=FONT_BASE, bd=0, padx=10, pady=7,
              activebackground=COLOR_ACCENT)
    send_button.grid(row=8, column=0, sticky="w", pady=5)

    frame_extra = tk.Frame(main_frame, bg=COLOR_BG)
    frame_extra.grid(row=9, column=0, sticky="nsew")
    frame_extra.columnconfigure(0, weight=1)
    frame_extra.columnconfigure(1, weight=1)

    image_label_list = []
    btn_img_select = crear_seccion_archivo(frame_extra, "Imagen", "*.png;*.jpg;*.jpeg", browse_image, remove_image, image_label_list, 0, 0)
    image_label = image_label_list[0]

    pdf_label_list = []
    btn_pdf_select = crear_seccion_archivo(frame_extra, "PDF", "*.pdf", browse_pdf, remove_pdf, pdf_label_list, 0, 1)
    pdf_label = pdf_label_list[0]
    
    global image_select_button, pdf_select_button
    image_select_button = btn_img_select
    pdf_select_button = btn_pdf_select
    
    status_label = tk.Label(main_frame, text="", font=("Segoe UI", 9), fg=COLOR_PRIMARY, bg=COLOR_BG)
    status_label.grid(row=10, column=0, sticky="w", pady=10)

    # --- NUEVOS CONTROLES DE PROGRESO ---
    # Barra de progreso (inicialmente oculta)
    progress_bar = ttk.Progressbar(main_frame, mode='determinate', length=400)
    # No hacer grid aquí, se mostrará cuando sea necesario

    # Etiqueta de progreso (inicialmente oculta)
    progress_label = tk.Label(main_frame, text="", font=("Segoe UI", 9), fg=COLOR_FG, bg=COLOR_BG)
    # No hacer grid aquí, se mostrará cuando sea necesario

    # Botón de pausa/reanudar (inicialmente oculto)
    pause_button = tk.Button(main_frame, text="⏸️ Pausar", command=toggle_pause,
                            bg="#ef4444", fg="white", font=FONT_BASE, bd=0, padx=10, pady=5,
                            activebackground="#fecaca")
    # No hacer grid aquí, se mostrará cuando sea necesario

    # Configurar teclas para evitar interferencias (opcional)
    def on_key_press(event):
        """Intercepta teclas durante el envío para evitar interferencias"""
        if message_text.cget('state') == 'disabled':
            # Si el texto está bloqueado, no permitir ninguna tecla
            return "break"
        return None
    
    # Bind del evento de teclado
    app.bind('<Key>', on_key_press)

    # Enfocar el cuadro de mensaje al inicio
    message_text.focus_set()

    app.mainloop()