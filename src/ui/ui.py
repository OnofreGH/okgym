import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import threading
import sys
import signal
import time

from controller.controller import enviar_mensajes, validar_y_enviar, obtener_mensaje_previsualizacion

# Variables globales optimizadas
class AppState:
    def __init__(self):
        self.excel_file = None
        self.excel_logo_img = None
        self.image_files = []
        self.pdf_files = []
        self.app_running = True
        self.current_thread = None
        self.sending_paused = False
        self.last_sent_index = 0
        self.total_contacts = 0
        
        # Referencias a widgets
        self.progress_bar = None
        self.progress_label = None
        self.pause_button = None
        self.send_button = None
        self.browse_button = None
        self.preview_button = None
        self.message_text = None
        self.status_label = None
        self.image_label = None
        self.pdf_label = None
        self.icon_label = None
        self.file_name_label = None
        self.image_select_button = None
        self.pdf_select_button = None
        self.app = None

# Instancia global del estado
state = AppState()

# Constantes de estilo
COLORS = {
    'bg': "#e5e7eb",
    'fg': "#1f2937", 
    'primary': "#2563eb",
    'accent': "#dbeafe",
    'error': "#ef4444",
    'success': "#10b981"
}

FONTS = {
    'base': ("Segoe UI", 10),
    'title': ("Segoe UI", 14, "bold"),
    'small': ("Segoe UI", 9)
}

def kill_chrome_processes():
    """Mata todos los procesos de Chrome de forma agresiva"""
    try:
        import subprocess
        import psutil
        
        print("Matando procesos de Chrome...")
        
        # Obtener todos los procesos
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
                
                # Identificar procesos de Chrome relacionados con WhatsApp
                if any(keyword in proc_name for keyword in ['chrome', 'chromium']):
                    if any(keyword in cmdline for keyword in ['whatsapp', 'web.whatsapp', 'user-data-dir']):
                        print(f"Matando proceso Chrome: {proc.info['pid']}")
                        proc.terminate()
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Esperar un momento y forzar kill si es necesario
        time.sleep(1)
        
        # Segunda pasada mas agresiva
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()
            except:
                continue
                
    except ImportError:
        # Si psutil no esta disponible, usar comandos del sistema
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], capture_output=True)
                subprocess.run(['taskkill', '/f', '/im', 'chromedriver.exe'], capture_output=True)
            else:  # Linux/Mac
                subprocess.run(['pkill', '-f', 'chrome'], capture_output=True)
                subprocess.run(['pkill', '-f', 'chromedriver'], capture_output=True)
        except:
            pass
    except Exception as e:
        print(f"Error matando procesos Chrome: {e}")

def emergency_cleanup():
    """Limpieza de emergencia mas agresiva"""
    print("Ejecutando limpieza de emergencia...")
    
    # 1. Marcar que la app se esta cerrando
    state.app_running = False
    
    # 2. Matar procesos de Chrome
    kill_chrome_processes()
    
    # 3. Limpiar archivos temporales
    try:
        import tempfile
        import shutil
        
        temp_dirs = [
            os.path.join(tempfile.gettempdir(), d) 
            for d in os.listdir(tempfile.gettempdir()) 
            if d.startswith('whatsapp_') or d.startswith('chrome_temp_')
        ]
        
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                print(f"Limpiado directorio temporal: {temp_dir}")
            except:
                pass
    except:
        pass

def force_exit():
    """Fuerza la salida completa del programa con timeout"""
    print("Forzando salida del programa...")
    
    def emergency_exit():
        """Salida de emergencia despues de timeout"""
        time.sleep(2)  # Esperar 2 segundos
        print("EMERGENCIA: Forzando salida inmediata")
        os._exit(1)  # Salida forzada
    
    # Iniciar hilo de emergencia
    emergency_thread = threading.Thread(target=emergency_exit, daemon=True)
    emergency_thread.start()
    
    try:
        if state.app:
            state.app.quit()
            state.app.destroy()
    except:
        pass
    
    # Salida normal
    os._exit(0)

def cleanup_whatsapp():
    """Limpia recursos de WhatsApp con timeout"""
    try:
        print("Limpiando WhatsApp...")
        
        # Importar y cerrar con timeout
        def cleanup_with_timeout():
            try:
                from logic.whatsapp_selenium import WhatsAppSender
                temp_sender = WhatsAppSender()
                if hasattr(temp_sender, 'driver') and temp_sender.driver:
                    temp_sender.close()
                print("WhatsApp cerrado correctamente")
            except Exception as e:
                print(f"Error cerrando WhatsApp: {e}")
        
        # Ejecutar limpieza en hilo con timeout
        cleanup_thread = threading.Thread(target=cleanup_with_timeout, daemon=True)
        cleanup_thread.start()
        cleanup_thread.join(timeout=1.0)  # Esperar maximo 1 segundo
        
        if cleanup_thread.is_alive():
            print("Timeout en limpieza de WhatsApp, continuando...")
            
    except Exception as e:
        print(f"Error en cleanup_whatsapp: {e}")

def on_closing():
    """Maneja el cierre de la aplicacion con limpieza agresiva"""
    print("Iniciando cierre de aplicacion...")
    
    # Deshabilitar la ventana inmediatamente
    try:
        if state.app:
            state.app.withdraw()  # Ocultar ventana
            state.app.update()
    except:
        pass
    
    # Ejecutar limpieza completa en hilo separado con timeout
    def complete_cleanup():
        try:
            # 1. Marcar cierre
            state.app_running = False
            
            # 2. Terminar hilo de envio (timeout muy corto)
            if state.current_thread and state.current_thread.is_alive():
                print("Terminando hilo de envio...")
                state.current_thread.join(timeout=0.1)  # Solo 0.1 segundos
            
            # 3. Limpieza de WhatsApp (con timeout)
            cleanup_whatsapp()
            
            # 4. Limpieza de emergencia
            emergency_cleanup()
            
        except Exception as e:
            print(f"Error en limpieza: {e}")
        finally:
            print("Limpieza completada, cerrando...")
    
    # Ejecutar limpieza en hilo separado
    cleanup_thread = threading.Thread(target=complete_cleanup, daemon=True)
    cleanup_thread.start()
    
    # Esperar un maximo de 1.5 segundos para la limpieza
    cleanup_thread.join(timeout=1.5)
    
    # Forzar salida independientemente del estado de la limpieza
    force_exit()

def signal_handler(signum, frame):
    """Maneja señales del sistema para cierre forzado"""
    print(f"Señal recibida: {signum}")
    emergency_cleanup()
    os._exit(1)

def toggle_pause():
    """Alterna pausa/reanudacion del envio"""
    state.sending_paused = not state.sending_paused
    
    if state.sending_paused:
        state.pause_button.config(text="▶️ Reanudar", bg=COLORS['success'])
        state.status_label.config(text=f"Envio pausado en contacto {state.last_sent_index}")
    else:
        state.pause_button.config(text="⏸️ Pausar", bg=COLORS['error'])
        state.status_label.config(text=f"Reanudando envio desde contacto {state.last_sent_index + 1}...")

def update_progress(current, total, contact_name=""):
    """Actualiza progreso de forma optimizada"""
    state.last_sent_index = current
    progress = (current / total) * 100 if total > 0 else 0
    
    if state.progress_bar:
        state.progress_bar['value'] = progress
    
    if state.progress_label:
        text = f"Enviando a: {contact_name} ({current}/{total})" if contact_name else f"Progreso: {current}/{total} ({progress:.1f}%)"
        state.progress_label.config(text=text)

def set_interface_state(enabled=True):
    """Controla el estado de la interfaz de forma centralizada"""
    widget_state = 'normal' if enabled else 'disabled'
    cursor = "" if enabled else "wait"
    
    widgets_to_control = [
        state.message_text, state.send_button, 
        state.browse_button, state.preview_button
    ]
    
    for widget in widgets_to_control:
        if widget:
            try:
                widget.config(state=widget_state)
            except tk.TclError:
                pass
    
    if state.app:
        state.app.config(cursor=cursor)

def reset_progress():
    """Resetea progreso y restaura interfaz"""
    state.last_sent_index = 0
    state.sending_paused = False
    state.total_contacts = 0
    
    set_interface_state(True)
    
    for widget in [state.progress_bar, state.progress_label, state.pause_button]:
        if widget:
            widget.grid_remove()

def show_progress_controls(total):
    """Muestra controles de progreso"""
    state.total_contacts = total
    set_interface_state(False)
    
    if state.progress_bar:
        state.progress_bar.grid(row=11, column=0, sticky="ew", pady=(5, 0))
    
    if state.progress_label:
        state.progress_label.grid(row=12, column=0, sticky="w", pady=(2, 0))
    
    if state.pause_button:
        state.pause_button.config(text="⏸️ Pausar", bg=COLORS['error'])
        state.pause_button.grid(row=13, column=0, sticky="w", pady=(5, 0))

def update_icon(imported, filename=None):
    """Actualiza icono de archivo Excel"""
    if imported and filename:
        state.icon_label.config(image=state.excel_logo_img, text="")
        state.file_name_label.config(text=os.path.basename(filename))
    else:
        state.icon_label.config(image="", text="No importado")
        state.file_name_label.config(text="")

def handle_file_selection(file_type, extensions, is_multiple=True):
    """Maneja seleccion de archivos de forma unificada"""
    file_dialog = filedialog.askopenfilenames if is_multiple else filedialog.askopenfilename
    file_paths = file_dialog(filetypes=[(file_type, extensions)])
    
    if not file_paths:
        return None
    
    return list(file_paths) if is_multiple else file_paths

def update_file_label(label, file_type, files):
    """Actualiza etiquetas de archivos seleccionados"""
    if not files:
        label.config(text=f"Sin {file_type.lower()}", fg="gray")
        return
    
    if isinstance(files, list) and len(files) > 1:
        count = len(files)
        names = "\n".join(os.path.basename(f) for f in files)
        plural = file_type.lower() + ("es" if file_type.lower().endswith("f") else "s")
        label.config(text=f"{count} {plural} seleccionados:\n{names}", fg=COLORS['fg'])
    else:
        filename = files[0] if isinstance(files, list) else files
        label.config(text=os.path.basename(filename), fg=COLORS['fg'])

def browse_file():
    """Selecciona archivo Excel con conversion automatica"""
    filename = filedialog.askopenfilename(filetypes=[("Archivos de Excel", "*.xls *.xlsx")])
    if not filename:
        state.excel_file = None
        update_icon(False)
        return
    
    if filename.lower().endswith('.xls'):
        try:
            from logic.logic import convertir_xls_a_xlsx
            messagebox.showinfo("Conversion", "Convirtiendo archivo .xls a .xlsx...")
            
            converted_file = convertir_xls_a_xlsx(filename)
            state.excel_file = converted_file
            update_icon(True, converted_file)
            messagebox.showinfo("Exito", f"Archivo convertido: {os.path.basename(converted_file)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo convertir el archivo:\n{e}")
            state.excel_file = None
            update_icon(False)
    else:
        state.excel_file = filename
        update_icon(True, filename)

def browse_image():
    """Selecciona imagenes"""
    files = handle_file_selection("Imagen", "*.png;*.jpg;*.jpeg")
    if files:
        state.image_files = files
        update_file_label(state.image_label, "Imagen", files)
    else:
        remove_image()

def browse_pdf():
    """Selecciona PDFs"""
    files = handle_file_selection("PDF", "*.pdf")
    if files:
        state.pdf_files = files
        update_file_label(state.pdf_label, "PDF", files)
    else:
        remove_pdf()

def remove_image():
    """Remueve imagenes seleccionadas"""
    state.image_files = []
    update_file_label(state.image_label, "Imagen", [])

def remove_pdf():
    """Remueve PDFs seleccionados"""
    state.pdf_files = []
    update_file_label(state.pdf_label, "PDF", [])

def send_in_thread():
    """Ejecuta envio en hilo separado optimizado"""
    mensaje = state.message_text.get("1.0", tk.END).strip()
    
    def envio_controlado():
        try:
            def update_progress_callback(current, total, contact_name=""):
                if state.app_running:
                    state.app.after(0, lambda: update_progress(current, total, contact_name))
            
            enviar_mensajes(
                state.excel_file, mensaje, state.image_files, state.pdf_files, 
                state.status_label,
                app_running_check=lambda: state.app_running,
                pause_check=lambda: not state.sending_paused,
                progress_callback=update_progress_callback,
                start_index=state.last_sent_index
            )
        except Exception as e:
            if state.app_running:
                print(f"Error en envio: {e}")
        finally:
            if state.app_running:
                state.current_thread = None
                state.app.after(0, reset_progress)
    
    state.current_thread = threading.Thread(target=envio_controlado, daemon=True)
    state.current_thread.start()

def validate_and_send():
    """Valida datos y confirma envio"""
    if state.current_thread and state.current_thread.is_alive():
        messagebox.showwarning("Proceso en curso", "Ya hay un envio en progreso.")
        return
    
    mensaje = state.message_text.get("1.0", tk.END).strip()
    if not mensaje:
        messagebox.showwarning("Mensaje vacio", "Escribe un mensaje antes de enviar.")
        return
    
    # Confirmar envio con archivos - MEJORADO para mostrar ambos tipos
    files_info = []
    if state.image_files:
        files_info.append(f"{len(state.image_files)} imagen(es)")
    if state.pdf_files:
        files_info.append(f"{len(state.pdf_files)} PDF(s)")
    
    if files_info:
        archivos_texto = " y ".join(files_info)
        confirmation = messagebox.askyesno(
            "Confirmar envio", 
            f"Se enviara:\n• Mensaje de texto\n• {archivos_texto}\n\n"
            f"NOTA: Se enviaran primero las imagenes, luego los PDFs\n\nContinuar?"
        )
        if not confirmation:
            return
    
    if not (state.current_thread and state.last_sent_index > 0):
        state.last_sent_index = 0
    
    validar_y_enviar(state.excel_file, mensaje, state.status_label, 
                    state.message_text, send_in_thread, show_progress_controls)

def preview_message():
    """Previsualiza mensaje con datos del Excel"""
    if not state.excel_file:
        messagebox.showwarning("Advertencia", "Selecciona un archivo Excel primero.")
        return
    
    mensaje_raw = state.message_text.get("1.0", tk.END).strip()
    try:
        mensaje_final = obtener_mensaje_previsualizacion(state.excel_file, mensaje_raw)
        messagebox.showinfo("Vista previa", f"Mensaje que se enviara:\n\n{mensaje_final}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo previsualizar:\n{e}")

def create_file_section(parent, file_type, extensions, browse_func, remove_func, row, col):
    """Crea seccion de archivos de forma optimizada"""
    section = tk.Frame(parent, bg=COLORS['bg'])
    section.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
    
    # Titulo
    tk.Label(section, text=f"{file_type} opcional", font=FONTS['base'], 
             bg=COLORS['bg'], fg=COLORS['fg']).pack(anchor="w")
    
    # Botones
    btn_frame = tk.Frame(section, bg=COLORS['bg'])
    btn_frame.pack(anchor="w", pady=2, fill="x")
    
    select_btn = tk.Button(btn_frame, text=f"Seleccionar {file_type.lower()}", 
                          command=browse_func, bg=COLORS['primary'], fg="white", 
                          font=FONTS['base'], bd=0, padx=10, pady=4)
    select_btn.pack(side="left", padx=(0, 10))
    
    remove_btn = tk.Button(btn_frame, text=f"Quitar {file_type.lower()}", 
                          command=remove_func, bg=COLORS['error'], fg="white", 
                          font=FONTS['base'], bd=0, padx=10, pady=4)
    remove_btn.pack(side="left")
    
    # Etiqueta de archivo
    label = tk.Label(section, text=f"Sin {file_type.lower()}", font=FONTS['small'], 
                    fg="gray", bg=COLORS['bg'], anchor="w")
    label.pack(anchor="w", pady=2, fill="x")
    
    return select_btn, label

def create_instructions_panel(parent):
    """Crea panel de instrucciones optimizado"""
    frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
    
    # Titulo
    tk.Label(frame, text="Como usar el programa", font=("Segoe UI", 12, "bold"),
             bg="white", fg=COLORS['fg']).pack(pady=10, padx=10, anchor="w")
    
    # Canvas con scroll
    canvas = tk.Canvas(frame, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    content = tk.Frame(canvas, bg="white")
    
    content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Instrucciones ACTUALIZADAS
    instructions = [
        ("1. Seleccionar Excel", ["Archivo .xls o .xlsx", "Conversion automatica"]),
        ("2. Escribir mensaje", ["Variables: {nombre}, {fecha_fin}", "Ejemplo incluido"]),
        ("3. Adjuntar archivos", [
            "Imagenes (.png, .jpg, .jpeg)", 
            "PDFs (.pdf)", 
            "Multiples archivos de cada tipo",
            "SE PUEDEN ENVIAR AMBOS TIPOS JUNTOS"  # NUEVA LINEA
        ]),
        ("4. Previsualizar", ["Verificar mensaje", "Comprobar variables"]),
        ("5. Enviar", ["WhatsApp Web automatico", "No tocar durante envio"])
    ]
    
    for title, steps in instructions:
        tk.Label(content, text=title, font=("Segoe UI", 10, "bold"),
                bg="white", fg=COLORS['primary']).pack(anchor="w", padx=10, pady=(10, 5))
        
        for step in steps:
            tk.Label(content, text=f"• {step}", font=FONTS['small'],
                    bg="white", fg=COLORS['fg'], wraplength=250, 
                    justify="left").pack(anchor="w", padx=20, pady=1)
    
    canvas.pack(side="left", fill="both", expand=True, padx=(0, 10))
    scrollbar.pack(side="right", fill="y")
    
    return frame

def load_excel_logo():
    """Carga logo de Excel optimizado"""
    try:
        if hasattr(sys, '_MEIPASS'):
            logo_path = os.path.join(sys._MEIPASS, "assets", "ExcelLogo.png")
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            logo_path = os.path.join(base_dir, "assets", "ExcelLogo.png")
        
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            img = img.resize((48, 48), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"No se pudo cargar logo: {e}")
    
    return None

def launch_app():
    """Lanza la aplicacion optimizada"""
    # Configurar manejadores de señales
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except:
        pass  # Señales no disponibles en Windows
    
    # Reiniciar estado
    state.__init__()
    
    # Crear ventana principal
    state.app = tk.Tk()
    state.app.title("WhatsApp Sender")
    state.app.geometry("1200x800")
    state.app.configure(bg=COLORS['bg'])
    state.app.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Configurar grid
    state.app.columnconfigure(0, weight=2)
    state.app.columnconfigure(1, weight=1)
    state.app.rowconfigure(0, weight=1)
    
    # Panel principal
    main_frame = tk.Frame(state.app, bg=COLORS['bg'])
    main_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
    for i in range(15):
        main_frame.rowconfigure(i, weight=1)
    main_frame.columnconfigure(0, weight=1)
    
    # Panel de instrucciones
    instructions_frame = create_instructions_panel(state.app)
    instructions_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
    
    # Cargar logo
    state.excel_logo_img = load_excel_logo()
    
    # Titulo
    tk.Label(main_frame, text="Enviar mensajes por WhatsApp", font=FONTS['title'],
             bg=COLORS['bg'], fg=COLORS['fg']).grid(row=0, column=0, sticky="w")
    
    # Seccion Excel
    tk.Label(main_frame, text="Archivo Excel", font=FONTS['base'], 
             bg=COLORS['bg'], fg=COLORS['fg']).grid(row=1, column=0, sticky="w")
    
    state.icon_label = tk.Label(main_frame, text="No importado", font=FONTS['base'], 
                               bg=COLORS['bg'], fg="gray")
    state.icon_label.grid(row=2, column=0, sticky="w")
    
    state.file_name_label = tk.Label(main_frame, text="", font=FONTS['small'], 
                                    bg=COLORS['bg'], fg="gray")
    state.file_name_label.grid(row=3, column=0, sticky="w")
    
    state.browse_button = tk.Button(main_frame, text="Seleccionar Excel", command=browse_file,
                                   bg=COLORS['primary'], fg="white", font=FONTS['base'], 
                                   bd=0, padx=12, pady=6)
    state.browse_button.grid(row=4, column=0, sticky="w", pady=5)
    
    # Seccion mensaje
    tk.Label(main_frame, text="Mensaje a enviar", font=FONTS['base'], 
             bg=COLORS['bg'], fg=COLORS['fg']).grid(row=5, column=0, sticky="w", pady=(10, 2))
    
    state.message_text = tk.Text(main_frame, height=10, font=("Segoe UI", 10), 
                                bd=1, relief="flat", wrap="word")
    state.message_text.grid(row=6, column=0, sticky="nsew")
    
    # Botones de accion
    state.preview_button = tk.Button(main_frame, text="Previsualizar", command=preview_message,
                                    bg="#6b7280", fg="white", font=FONTS['base'], 
                                    bd=0, padx=10, pady=5)
    state.preview_button.grid(row=7, column=0, sticky="w", pady=5)
    
    state.send_button = tk.Button(main_frame, text="Enviar mensajes", command=validate_and_send,
                                 bg=COLORS['primary'], fg="white", font=FONTS['base'], 
                                 bd=0, padx=10, pady=7)
    state.send_button.grid(row=8, column=0, sticky="w", pady=5)
    
    # Seccion archivos
    files_frame = tk.Frame(main_frame, bg=COLORS['bg'])
    files_frame.grid(row=9, column=0, sticky="nsew")
    files_frame.columnconfigure(0, weight=1)
    files_frame.columnconfigure(1, weight=1)
    
    state.image_select_button, state.image_label = create_file_section(
        files_frame, "Imagen", "*.png;*.jpg;*.jpeg", browse_image, remove_image, 0, 0)
    
    state.pdf_select_button, state.pdf_label = create_file_section(
        files_frame, "PDF", "*.pdf", browse_pdf, remove_pdf, 0, 1)
    
    # Status y controles de progreso
    state.status_label = tk.Label(main_frame, text="", font=FONTS['small'], 
                                 fg=COLORS['primary'], bg=COLORS['bg'])
    state.status_label.grid(row=10, column=0, sticky="w", pady=10)
    
    # Controles de progreso (ocultos inicialmente)
    state.progress_bar = ttk.Progressbar(main_frame, mode='determinate', length=400)
    state.progress_label = tk.Label(main_frame, text="", font=FONTS['small'], 
                                   fg=COLORS['fg'], bg=COLORS['bg'])
    state.pause_button = tk.Button(main_frame, text="Pausar", command=toggle_pause,
                                  bg=COLORS['error'], fg="white", font=FONTS['base'], 
                                  bd=0, padx=10, pady=5)
    
    # Eventos de teclado
    def on_key_press(event):
        if state.message_text and state.message_text.cget('state') == 'disabled':
            return "break"
        return None
    
    state.app.bind('<Key>', on_key_press)
    
    # Configurar foco inicial
    if state.message_text:
        state.message_text.focus_set()
    
    # Iniciar aplicacion
    try:
        state.app.mainloop()
    except KeyboardInterrupt:
        print("Interrupcion de teclado detectada")
        on_closing()
    except Exception as e:
        print(f"Error en mainloop: {e}")
        on_closing()