import pandas as pd
import pywhatkit
import time
import os
import pygetwindow as gw
import pyautogui as pg
from logic.utils import normalizar_numero

def send_messages(excel_file, message_template, image_path=None, pdf_path=None):
    df = pd.read_excel(excel_file, header=1)
    enviados = 0

    for i in range(len(df)):
        try:
            celular = normalizar_numero(df.loc[i, 'CELULAR'])
            if not celular:
                continue

            nombre = str(df.loc[i, 'NOMBRES']).strip()
            fecha_fin = str(df.loc[i, 'FECHA FIN']).strip()
            mensaje = message_template.format(nombre=nombre, fecha_fin=fecha_fin)
            numero = f"+{celular}"

            if image_path:
                if isinstance(image_path, str):
                    image_path = [image_path]

                print(f"Enviando {len(image_path)} imagen(es) a {numero}")

                # Abre el chat con el mensaje usando pywhatkit
                pywhatkit.sendwhatmsg_instantly(
                    phone_no=numero,
                    message=mensaje,
                    wait_time=10,
                    tab_close=False
                )
                time.sleep(10)

                # Activar ventana de WhatsApp Web
                try:
                    window = gw.getWindowsWithTitle("WhatsApp")[0]
                    window.activate()
                    time.sleep(1)
                except Exception:
                    print("No se pudo activar la ventana de WhatsApp Web")

                # Clic en ícono de clip (adjuntar)
                pg.click(x=485, y=700)  # Actualiza según tu pantalla
                time.sleep(1)

                # Clic en ícono de imagen
                pg.click(x=470, y=455)  # Actualiza según tu pantalla
                time.sleep(2)

                # Escribir paths separados por espacio y entre comillas
                all_paths = " ".join(f'"{os.path.abspath(p)}"' for p in image_path)
                pg.write(all_paths)
                time.sleep(2)

                pg.press('enter')  # Abrir imágenes
                time.sleep(3)

                pg.press('enter')  # Enviar mensaje con imágenes
                time.sleep(4)

                # Cierra la pestaña de WhatsApp Web
                pg.hotkey('ctrl', 'w')
                print("Ventana de WhatsApp cerrada.")

            elif pdf_path:
                if isinstance(pdf_path, str):
                    pdf_path = [pdf_path]

                print(f"Enviando {len(pdf_path)} PDF(s) a {numero}")

                # Abre el chat con el mensaje usando pywhatkit
                pywhatkit.sendwhatmsg_instantly(
                    phone_no=numero,
                    message=mensaje,
                    wait_time=10,
                    tab_close=False
                )
                time.sleep(10)

                # Activar ventana de WhatsApp Web
                try:
                    window = gw.getWindowsWithTitle("WhatsApp")[0]
                    window.activate()
                    time.sleep(1)
                except Exception:
                    print("No se pudo activar la ventana de WhatsApp Web")

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

                pg.press('enter')  # Abrir los PDFs
                time.sleep(3)

                pg.press('enter')  # Enviar los PDFs
                time.sleep(4)

                # Cerrar la pestaña de WhatsApp Web
                pg.hotkey('ctrl', 'w')
                print("Ventana de WhatsApp cerrada.")

            else:
                print(f"Enviando texto a {numero}")
                pywhatkit.sendwhatmsg_instantly(
                    phone_no=numero,
                    message=mensaje,
                    wait_time=10,
                    tab_close=True
                )

            enviados += 1
            time.sleep(5)  # Intervalo entre envíos

        except Exception as e:
            print(f"Error con el número en fila {i+2}: {type(e).__name__}: {e}")

    return enviados
