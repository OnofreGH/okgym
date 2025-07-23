import threading
from tkinter import messagebox
from datetime import datetime

from logic.logic import leer_excel, validar_numeros
from logic.message import send_messages
from logic.utils import normalizar_numero

def format_fecha_preview(fecha_str):
    """Convierte fecha de formato YYYY-MM-DD HH:MM:SS a DD/MM/YYYY para preview"""
    try:
        # Si viene como string, convertir a datetime
        if isinstance(fecha_str, str):
            # Extraer solo la parte de la fecha (sin hora)
            fecha_parte = fecha_str.split(' ')[0]
            fecha_obj = datetime.strptime(fecha_parte, '%Y-%m-%d')
        elif isinstance(fecha_str, datetime):
            fecha_obj = fecha_str
        else:
            # Si es otro tipo, convertir a string y procesar
            fecha_obj = datetime.strptime(str(fecha_str).split(' ')[0], '%Y-%m-%d')
        
        # Formatear a DD/MM/YYYY
        return fecha_obj.strftime('%d/%m/%Y')
    except Exception as e:
        print(f"Error formateando fecha para preview '{fecha_str}': {e}")
        return str(fecha_str)  # Retornar original si hay error

def enviar_mensajes(excel_file, mensaje, image_path, pdf_path, status_label, 
                   app_running_check=None, pause_check=None, progress_callback=None, start_index=0):
    """
    Envía mensajes con verificación de si la aplicación sigue ejecutándose
    app_running_check: función que retorna True si la app sigue ejecutándose
    pause_check: función que retorna True si no está pausado
    progress_callback: función para actualizar progreso (current, total, contact_name)
    start_index: índice desde donde empezar el envío
    """
    if not excel_file:
        if app_running_check and app_running_check():
            status_label.config(text="Por favor selecciona un archivo de Excel")
        return

    if not mensaje:
        if app_running_check and app_running_check():
            status_label.config(text="Por favor escribe un mensaje")
        return

    try:
        # Verificar si la app sigue ejecutándose antes de continuar
        if app_running_check and not app_running_check():
            return

        if app_running_check and app_running_check():
            status_label.config(text="Leyendo archivo Excel...")

        df = leer_excel(excel_file)
        
        # Verificar nuevamente
        if app_running_check and not app_running_check():
            return

        if app_running_check and app_running_check():
            status_label.config(text="Validando números...")

        validos = validar_numeros(df, normalizar_numero)
        total = len(df)

        # Verificar antes de mostrar estadísticas
        if app_running_check and not app_running_check():
            return

        if app_running_check and app_running_check():
            status_label.config(text=f"Números válidos: {validos}/{total}")

        if validos == 0:
            if app_running_check and app_running_check():
                status_label.config(text="No hay números válidos para enviar")
            return

        # Verificar antes de iniciar envío
        if app_running_check and not app_running_check():
            return

        # Mostrar controles de progreso si hay callback
        if progress_callback:
            progress_callback(start_index, validos)

        if app_running_check and app_running_check():
            if start_index > 0:
                status_label.config(text=f"Reanudando envío desde contacto {start_index + 1}...")
            else:
                status_label.config(text="Iniciando envío de mensajes...")

        # Pasar todas las funciones de verificación al módulo de envío
        enviados = send_messages(
            excel_file, mensaje, image_path, pdf_path, 
            app_running_check, pause_check, progress_callback, start_index
        )

        # Verificar antes de mostrar resultado final
        if app_running_check and not app_running_check():
            return

        if app_running_check and app_running_check():
            if enviados > 0:
                status_label.config(text=f"Mensajes enviados: {enviados}/{validos}")
            else:
                status_label.config(text="No se pudieron enviar mensajes")

    except Exception as e:
        if app_running_check and app_running_check():
            status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error al enviar mensajes:\n{str(e)}")

def validar_y_enviar(excel_file, mensaje, status_label, message_text, iniciar_hilo, show_progress_callback=None):
    if not excel_file:
        messagebox.showerror("Error", "Selecciona un archivo de Excel")
        return

    try:
        df = leer_excel(excel_file)
        validos = validar_numeros(df, normalizar_numero)

        if validos == 0:
            messagebox.showwarning("Advertencia", "No se encontro ningun numero valido con formato peruano.")
            return

        # Mostrar controles de progreso antes de iniciar
        if show_progress_callback:
            show_progress_callback(validos)

        messagebox.showinfo("Validacion exitosa", f"Se detectaron {validos} numeros válidos. Iniciando envío...")
        iniciar_hilo()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo validar el archivo:\n{e}")

def obtener_mensaje_previsualizacion(excel_file, mensaje_raw):
    from logic.message import normalize_text, format_fecha  # Importar funciones
    
    df = leer_excel(excel_file)
    if df.empty:
        raise ValueError("El archivo Excel esta vacio.")

    nombre_raw = str(df.loc[0, 'NOMBRES'])
    celular = str(df.loc[0, 'CELULAR'])
    fecha_fin_raw = df.loc[0, 'FECHA FIN']
    
    # Normalizar nombre para evitar problemas de codificacion
    nombre = normalize_text(nombre_raw)
    
    # Formatear la fecha para preview
    fecha_fin = format_fecha(fecha_fin_raw)
    
    # CORRECCION: Usar replace en lugar de format
    return mensaje_raw.replace("{nombre}", nombre).replace("{fecha_fin}", fecha_fin)
