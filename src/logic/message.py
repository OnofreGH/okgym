import pandas as pd
import pywhatkit
import time
import os
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
                print(f"Enviando imagen a {numero}")
                pywhatkit.sendwhats_image(
                    receiver=numero,
                    img_path=image_path,
                    caption=mensaje,
                    wait_time=10,
                    tab_close=True
                )
                time.sleep(10)

            if pdf_path:
                print(f"Enviando PDF a {numero}")
                time.sleep(3)
                pg.click(705, 975)  # Coordenadas del clip (ajusta según tu pantalla)
                time.sleep(1)
                # Haz clic en el icono de documento (ajusta según tu pantalla)
                pg.click(685, 635)
                time.sleep(1)
                # Escribe el nombre del PDF y presiona Enter
                pg.write(os.path.basename(pdf_path))
                time.sleep(1)
                pg.press('enter')
                time.sleep(3)
                # Enviar el PDF
                pg.press('enter')
                time.sleep(3)
                
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
