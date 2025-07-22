import pandas as pd
import time
import os
import sys
import unicodedata
from datetime import datetime
from logic.utils import normalizar_numero
from logic.whatsapp_selenium import WhatsAppSender

def normalize_text(text):
    """Normaliza texto removiendo acentos y caracteres problematicos"""
    try:
        # Normalizar Unicode (NFD: Normalization Form Decomposed)
        normalized = unicodedata.normalize('NFD', str(text))
        # Remover los caracteres de acento (categoria 'Mn': Nonspacing_Mark)
        without_accents = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
        return without_accents
    except Exception:
        # Si falla, intentar reemplazos manuales basicos
        replacements = {
            'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a',
            'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
            'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i',
            'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o',
            'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u',
            'ñ': 'n',
            'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A',
            'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E',
            'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I',
            'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O',
            'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U',
            'Ñ': 'N'
        }
        
        result = str(text)
        for accented, plain in replacements.items():
            result = result.replace(accented, plain)
        return result

def safe_print(message):
    """Imprime mensajes de forma segura evitando errores de codificacion"""
    try:
        print(message)
    except UnicodeEncodeError:
        try:
            # Intentar con encoding Latin-1
            print(message.encode('latin-1', 'ignore').decode('latin-1'))
        except:
            try:
                # Ultimo recurso: ASCII
                print(message.encode('ascii', 'ignore').decode('ascii'))
            except:
                print("[Mensaje con caracteres especiales - no se puede mostrar]")

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
        safe_print(f"Error formateando fecha '{fecha_str}': {e}")
        return str(fecha_str)  # Retornar original si hay error

def send_messages(excel_file, message_template, image_path=None, pdf_path=None, 
                 app_running_check=None, pause_check=None, progress_callback=None, start_index=0):
    """
    Envia mensajes con verificacion de interrupcion y progreso usando Selenium
    app_running_check: funcion que retorna True si la app sigue ejecutandose
    pause_check: funcion que retorna True si no esta pausado
    progress_callback: funcion para actualizar progreso (current, total, contact_name)
    start_index: indice desde donde empezar el envio
    """
    # Configurar la codificacion de la consola para Windows
    if sys.platform.startswith('win'):
        try:
            # Intentar configurar UTF-8 para la consola
            os.system('chcp 65001 > nul')
        except:
            pass
    
    df = pd.read_excel(excel_file, header=1)
    enviados = 0
    contactos_validos = []
    
    # Primero, crear lista de contactos validos
    for i in range(len(df)):
        celular = normalizar_numero(df.loc[i, 'CELULAR'])
        if celular:
            # Formatear la fecha al extraer los datos
            fecha_fin_raw = df.loc[i, 'FECHA FIN']
            fecha_fin_formateada = format_fecha(fecha_fin_raw)
            
            # NORMALIZAR TEXTO: Remover acentos problematicos
            nombre_raw = str(df.loc[i, 'NOMBRES']).strip()
            nombre_limpio = normalize_text(nombre_raw)
            
            contactos_validos.append({
                'index': i,
                'celular': celular,
                'nombre': nombre_limpio,  # Texto normalizado
                'nombre_original': nombre_raw,  # Conservar original para logs
                'fecha_fin': fecha_fin_formateada
            })
    
    total_validos = len(contactos_validos)
    
    # Inicializar WhatsApp Selenium
    whatsapp_sender = WhatsAppSender()
    
    try:
        # Inicializar el driver y abrir WhatsApp Web
        if not whatsapp_sender.setup_driver():
            safe_print("Error al inicializar WhatsApp Web")
            return 0
        
        # Esperar hasta que el usuario escanee el codigo QR si es necesario
        safe_print("Esperando autenticacion en WhatsApp Web...")
        if not whatsapp_sender.open_whatsapp():
            safe_print("Error: No se pudo autenticar en WhatsApp Web")
            whatsapp_sender.close()
            return 0
        
        safe_print("WhatsApp Web autenticado correctamente")
        
        # Empezar desde el indice especificado
        for contacto_idx in range(start_index, total_validos):
            try:
                # Verificar si la aplicacion sigue ejecutandose
                if app_running_check and not app_running_check():
                    safe_print("Envio interrumpido por cierre de aplicacion")
                    break
                
                # Verificar si esta pausado - esperar hasta que se reanude
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        whatsapp_sender.close()
                        return enviados
                    time.sleep(0.5)  # Esperar medio segundo antes de verificar de nuevo
                
                contacto = contactos_validos[contacto_idx]
                celular = contacto['celular']
                nombre = contacto['nombre']  # Ya normalizado
                nombre_original = contacto['nombre_original']
                fecha_fin = contacto['fecha_fin']
                
                # Actualizar progreso con nombre del contacto
                if progress_callback:
                    progress_callback(contacto_idx + 1, total_validos, nombre_original)
                
                # Personalizar mensaje con texto normalizado
                mensaje_personalizado = message_template.replace("{nombre}", nombre).replace("{fecha_fin}", fecha_fin)
                
                safe_print(f"Enviando mensaje a {nombre_original} ({celular})")
                safe_print(f"Fecha formateada: {fecha_fin}")
                
                # CORRECCION: Preparar archivos para envio correctamente
                image_paths = None
                pdf_paths = None
                
                # Verificar y preparar imagen
                if image_path:
                    if isinstance(image_path, str):
                        if os.path.exists(image_path):
                            image_paths = [image_path]
                        else:
                            safe_print(f"Imagen no encontrada: {image_path}")
                    elif isinstance(image_path, list):
                        valid_images = []
                        for img in image_path:
                            if isinstance(img, str) and os.path.exists(img):
                                valid_images.append(img)
                        if valid_images:
                            image_paths = valid_images
                
                # Verificar y preparar PDF
                if pdf_path:
                    if isinstance(pdf_path, str):
                        if os.path.exists(pdf_path):
                            pdf_paths = [pdf_path]
                        else:
                            safe_print(f"PDF no encontrado: {pdf_path}")
                    elif isinstance(pdf_path, list):
                        valid_pdfs = []
                        for pdf in pdf_path:
                            if isinstance(pdf, str) and os.path.exists(pdf):
                                valid_pdfs.append(pdf)
                        if valid_pdfs:
                            pdf_paths = valid_pdfs
                
                # Debug para verificar los tipos
                safe_print(f"DEBUG - Enviando con image_paths: {image_paths}, pdf_paths: {pdf_paths}")
                
                # Enviar mensaje completo con archivos
                if whatsapp_sender.send_complete_message(celular, mensaje_personalizado, image_paths, pdf_paths):
                    enviados += 1
                    safe_print(f"Mensaje enviado exitosamente a {nombre_original}")
                else:
                    safe_print(f"Error: No se pudo enviar el mensaje a {celular}")
                    continue
                
                # Esperar un poco entre mensajes para evitar ser detectado como spam
                time.sleep(2)
                
            except Exception as e:
                # Manejo seguro de errores
                try:
                    nombre_para_log = contacto.get('nombre_original', 'contacto desconocido')
                    safe_print(f"Error al enviar mensaje a {nombre_para_log}: {str(e)}")
                except:
                    safe_print(f"Error al enviar mensaje: Error de codificacion")
                continue
        
    except Exception as e:
        # Manejar errores de codificacion de manera segura
        safe_print(f"Error general en envio de mensajes: {str(e)}")
    finally:
        # Cerrar el driver de Selenium
        whatsapp_sender.close()
    
    safe_print(f"Proceso completado. Se enviaron {enviados} de {total_validos} mensajes.")
    return enviados