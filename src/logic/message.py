import pandas as pd
import time
import os
import sys
from datetime import datetime
from logic.utils import normalizar_numero
from logic.whatsapp_selenium import WhatsAppSender

def format_fecha(fecha_str):
    """Convierte fecha de formato YYYY-MM-DD HH:MM:SS a DD/MM/YYYY"""
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
        print(f"Error formateando fecha '{fecha_str}': {e}")
        return str(fecha_str)  # Retornar original si hay error

def send_messages(excel_file, message_template, image_path=None, pdf_path=None, 
                 app_running_check=None, pause_check=None, progress_callback=None, start_index=0):
    """
    Envía mensajes con verificación de interrupción y progreso usando Selenium
    app_running_check: función que retorna True si la app sigue ejecutándose
    pause_check: función que retorna True si no está pausado
    progress_callback: función para actualizar progreso (current, total, contact_name)
    start_index: índice desde donde empezar el envío
    """
    # Configurar la codificación de la consola para Windows
    if sys.platform.startswith('win'):
        try:
            # Intentar configurar UTF-8 para la consola
            os.system('chcp 65001 > nul')
        except:
            pass
    
    df = pd.read_excel(excel_file, header=1)
    enviados = 0
    contactos_validos = []
    
    # Primero, crear lista de contactos válidos
    for i in range(len(df)):
        celular = normalizar_numero(df.loc[i, 'CELULAR'])
        if celular:
            # Formatear la fecha al extraer los datos
            fecha_fin_raw = df.loc[i, 'FECHA FIN']
            fecha_fin_formateada = format_fecha(fecha_fin_raw)
            
            contactos_validos.append({
                'index': i,
                'celular': celular,
                'nombre': str(df.loc[i, 'NOMBRES']).strip(),
                'fecha_fin': fecha_fin_formateada  # Ya formateada
            })
    
    total_validos = len(contactos_validos)
    
    # Inicializar WhatsApp Selenium
    whatsapp_sender = WhatsAppSender()
    
    try:
        # Inicializar el driver y abrir WhatsApp Web
        if not whatsapp_sender.setup_driver():
            print("Error al inicializar WhatsApp Web")
            return 0
        
        # Esperar hasta que el usuario escanee el código QR si es necesario
        print("Esperando autenticacion en WhatsApp Web...")
        if not whatsapp_sender.open_whatsapp():
            print("Error: No se pudo autenticar en WhatsApp Web")
            whatsapp_sender.close()
            return 0
        
        print("WhatsApp Web autenticado correctamente")
        
        # Empezar desde el índice especificado
        for contacto_idx in range(start_index, total_validos):
            try:
                # Verificar si la aplicación sigue ejecutándose
                if app_running_check and not app_running_check():
                    print("Envio interrumpido por cierre de aplicacion")
                    break
                
                # Verificar si está pausado - esperar hasta que se reanude
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        whatsapp_sender.close()
                        return enviados
                    time.sleep(0.5)  # Esperar medio segundo antes de verificar de nuevo
                
                contacto = contactos_validos[contacto_idx]
                celular = contacto['celular']
                nombre = contacto['nombre']
                fecha_fin = contacto['fecha_fin']  # Ya está formateada como DD/MM/YYYY
                
                # Actualizar progreso con nombre del contacto
                if progress_callback:
                    progress_callback(contacto_idx + 1, total_validos, nombre)
                
                # Personalizar mensaje con fecha ya formateada
                mensaje_personalizado = message_template.replace("{nombre}", nombre).replace("{fecha_fin}", fecha_fin)
                
                print(f"Enviando mensaje a {nombre} ({celular})")
                print(f"Fecha formateada: {fecha_fin}")  # Debug
                
                # CORRECCIÓN: Preparar archivos para envío correctamente
                image_paths = None
                pdf_paths = None
                
                # Verificar y preparar imagen
                if image_path:
                    if isinstance(image_path, str):
                        # Si es string, verificar que existe y crear lista
                        if os.path.exists(image_path):
                            image_paths = [image_path]
                        else:
                            print(f"Imagen no encontrada: {image_path}")
                    elif isinstance(image_path, list):
                        # Si es lista, verificar cada elemento
                        valid_images = []
                        for img in image_path:
                            if isinstance(img, str) and os.path.exists(img):
                                valid_images.append(img)
                        if valid_images:
                            image_paths = valid_images
                
                # Verificar y preparar PDF
                if pdf_path:
                    if isinstance(pdf_path, str):
                        # Si es string, verificar que existe y crear lista
                        if os.path.exists(pdf_path):
                            pdf_paths = [pdf_path]
                        else:
                            print(f"PDF no encontrado: {pdf_path}")
                    elif isinstance(pdf_path, list):
                        # Si es lista, verificar cada elemento
                        valid_pdfs = []
                        for pdf in pdf_path:
                            if isinstance(pdf, str) and os.path.exists(pdf):
                                valid_pdfs.append(pdf)
                        if valid_pdfs:
                            pdf_paths = valid_pdfs
                
                # Debug para verificar los tipos
                print(f"DEBUG - Enviando con image_paths: {image_paths}, pdf_paths: {pdf_paths}")
                
                # Enviar mensaje completo con archivos
                if whatsapp_sender.send_complete_message(celular, mensaje_personalizado, image_paths, pdf_paths):
                    enviados += 1
                    print(f"Mensaje enviado exitosamente a {nombre}")
                else:
                    print(f"Error: No se pudo enviar el mensaje a {celular}")
                    continue
                
                # Esperar un poco entre mensajes para evitar ser detectado como spam
                time.sleep(2)
                
            except Exception as e:
                # Usar representación segura del error para evitar problemas de codificación
                error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                print(f"Error al enviar mensaje a {contacto.get('nombre', 'contacto desconocido')}: {error_msg}")
                continue
        
    except Exception as e:
        # Manejar errores de codificación de manera segura
        try:
            print(f"Error general en envio de mensajes: {str(e)}")
        except UnicodeEncodeError:
            # Si hay problemas con caracteres especiales, usar representación ASCII
            error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            print(f"Error general en envio de mensajes: {error_msg}")
    finally:
        # Cerrar el driver de Selenium
        whatsapp_sender.close()
    
    print(f"Proceso completado. Se enviaron {enviados} de {total_validos} mensajes.")
    return enviados