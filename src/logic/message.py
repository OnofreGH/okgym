import pandas as pd
import time
import os
import sys
from logic.utils import normalizar_numero
from logic.whatsapp_selenium import WhatsAppSender

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
            contactos_validos.append({
                'index': i,
                'celular': celular,
                'nombre': str(df.loc[i, 'NOMBRES']).strip(),
                'fecha_fin': str(df.loc[i, 'FECHA FIN']).strip()
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
                fecha_fin = contacto['fecha_fin']
                
                # Actualizar progreso con nombre del contacto
                if progress_callback:
                    progress_callback(contacto_idx + 1, total_validos, nombre)
                
                # Personalizar mensaje
                mensaje_personalizado = message_template.replace("[NOMBRE]", nombre).replace("[FECHA FIN]", fecha_fin)
                
                print(f"Enviando mensaje a {nombre} ({celular})")
                
                # Preparar archivos para envío
                image_paths = [image_path] if image_path and os.path.exists(image_path) else None
                pdf_paths = [pdf_path] if pdf_path and os.path.exists(pdf_path) else None
                
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