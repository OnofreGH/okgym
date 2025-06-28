import pandas as pd
import pywhatkit
import time
import os
import pygetwindow as gw
import pyautogui as pg
from logic.utils import normalizar_numero

def send_messages(excel_file, message_template, image_path=None, pdf_path=None, 
                 app_running_check=None, pause_check=None, progress_callback=None, start_index=0):
    """
    Envía mensajes con verificación de interrupción y progreso
    app_running_check: función que retorna True si la app sigue ejecutándose
    pause_check: función que retorna True si no está pausado
    progress_callback: función para actualizar progreso (current, total, contact_name)
    start_index: índice desde donde empezar el envío
    """
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
    
    # Empezar desde el índice especificado
    for contacto_idx in range(start_index, total_validos):
        try:
            # Verificar si la aplicación sigue ejecutándose
            if app_running_check and not app_running_check():
                print("🛑 Envío interrumpido por cierre de aplicación")
                break
            
            # Verificar si está pausado - esperar hasta que se reanude
            while pause_check and not pause_check():
                if app_running_check and not app_running_check():
                    return enviados
                time.sleep(0.5)  # Esperar medio segundo antes de verificar de nuevo
            
            contacto = contactos_validos[contacto_idx]
            celular = contacto['celular']
            nombre = contacto['nombre']
            fecha_fin = contacto['fecha_fin']
            
            # Actualizar progreso con nombre del contacto
            if progress_callback:
                progress_callback(contacto_idx + 1, total_validos, nombre)
            
            mensaje = message_template.format(nombre=nombre, fecha_fin=fecha_fin)
            numero = f"+{celular}"

            print(f"📤 Enviando mensaje {contacto_idx + 1}/{total_validos} a {nombre} ({numero})")

            # Verificar antes de cada operación importante
            if app_running_check and not app_running_check():
                break

            if image_path:
                if isinstance(image_path, str):
                    image_path = [image_path]

                print(f"Enviando {len(image_path)} imagen(es) a {numero}")

                # Verificar pausa antes de abrir WhatsApp
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)

                # Abre el chat con el mensaje usando pywhatkit
                pywhatkit.sendwhatmsg_instantly(
                    phone_no=numero,
                    message=mensaje,
                    wait_time=10,
                    tab_close=False
                )
                
                # Verificar durante la espera con posibilidad de pausa
                for _ in range(10):
                    while pause_check and not pause_check():
                        if app_running_check and not app_running_check():
                            return enviados
                        time.sleep(0.5)
                    
                    if app_running_check and not app_running_check():
                        break
                    time.sleep(1)
                
                if app_running_check and not app_running_check():
                    break

                # Activar ventana de WhatsApp Web
                try:
                    window = gw.getWindowsWithTitle("WhatsApp")[0]
                    window.activate()
                    time.sleep(1)
                except Exception:
                    print("No se pudo activar la ventana de WhatsApp Web")

                # Verificar pausa antes de continuar
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)

                if app_running_check and not app_running_check():
                    break

                # Clic en ícono de clip (adjuntar)
                pg.click(x=485, y=700)  # Actualiza según tu pantalla
                time.sleep(1)
                
                # Verificar pausa
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)

                # Clic en ícono de imagen
                pg.click(x=470, y=455)  # Actualiza según tu pantalla
                time.sleep(2)

                # Escribir paths separados por espacio y entre comillas
                all_paths = " ".join(f'"{os.path.abspath(p)}"' for p in image_path)
                pg.write(all_paths)
                time.sleep(2)

                # Verificar pausa antes de enviar
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)

                pg.press('enter')  # Abrir imágenes
                time.sleep(3)

                pg.press('enter')  # Enviar mensaje con imágenes
                time.sleep(4)

                # Cierra la pestaña de WhatsApp Web
                pg.hotkey('ctrl', 'w')
                print("Ventana de WhatsApp cerrada.")

            elif pdf_path:
                # Lógica similar para PDFs con verificaciones de pausa
                if isinstance(pdf_path, str):
                    pdf_path = [pdf_path]

                print(f"Enviando {len(pdf_path)} PDF(s) a {numero}")

                # Verificar pausa
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)

                pywhatkit.sendwhatmsg_instantly(
                    phone_no=numero,
                    message=mensaje,
                    wait_time=10,
                    tab_close=False
                )
                
                # Verificar durante la espera con posibilidad de pausa
                for _ in range(10):
                    while pause_check and not pause_check():
                        if app_running_check and not app_running_check():
                            return enviados
                        time.sleep(0.5)
                    
                    if app_running_check and not app_running_check():
                        break
                    time.sleep(1)

                if app_running_check and not app_running_check():
                    break

                # Activar ventana de WhatsApp Web
                try:
                    window = gw.getWindowsWithTitle("WhatsApp")[0]
                    window.activate()
                    time.sleep(1)
                except Exception:
                    print("No se pudo activar la ventana de WhatsApp Web")

                # Verificaciones de pausa en cada paso...
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)

                # Clic en ícono de clip (adjuntar)
                pg.click(x=485, y=700)  # Actualiza según tu pantalla
                time.sleep(1)
                # Clic en ícono de documento
                pg.click(x=470, y=424)  # Actualiza según tu pantalla
                time.sleep(2)

                # Escribir paths separados por espacio y entre comillas
                all_paths = " ".join(f'"{os.path.abspath(p)}"' for p in pdf_path)
                pg.write(all_paths)
                time.sleep(2)

                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)

                pg.press('enter')  # Abrir los PDFs
                time.sleep(3)
                pg.press('enter')  # Enviar los PDFs
                time.sleep(4)
                pg.hotkey('ctrl', 'w')
                print("Ventana de WhatsApp cerrada.")

            else:
                print(f"Enviando texto a {numero}")
                
                # Verificar pausa antes de enviar texto
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)

                pywhatkit.sendwhatmsg_instantly(
                    phone_no=numero,
                    message=mensaje,
                    wait_time=10,
                    tab_close=True
                )

            enviados += 1
            
            # Verificar antes del intervalo entre envíos
            if app_running_check and not app_running_check():
                break

            # Intervalo entre envíos con verificación de pausa
            for _ in range(5):
                while pause_check and not pause_check():
                    if app_running_check and not app_running_check():
                        return enviados
                    time.sleep(0.5)
                
                if app_running_check and not app_running_check():
                    break
                time.sleep(1)

        except Exception as e:
            print(f"Error con el contacto {contacto_idx + 1}: {type(e).__name__}: {e}")
            # Continuar con el siguiente contacto

    return enviados
