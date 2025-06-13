import pandas as pd
import webbrowser as web
import pyautogui as pg
import time
data = pd.read_excel("Clientes.xlsx", sheet_name='Ventas')
data.head(3)

for i in range(len(data)):
    celular = data.loc[i,'Celular'].astype(str)
    nombre = data.loc[i,'Nombre']
    producto = data.loc[i,'Producto']
    
    mensaje = "Hola, " + nombre + "! Gracias por comprar " + producto + " con nosotros"
    
    chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
    web.get(chrome_path).open("https://web.whatsapp.com/send?phone=" + celular + "&text=" + mensaje)
    
    time.sleep(8)          
    pg.click(828,700)     
    time.sleep(2)         
    pg.press('enter')     
    time.sleep(3)       
    pg.hotkey('ctrl', 'w')  
    time.sleep(2)