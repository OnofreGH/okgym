from tkinter import Tk, Label, Entry, Text, Button, messagebox
import pandas as pd
import webbrowser as web
import pyautogui as pg
import time
import os

def send_messages():
    excel_file = excel_entry.get()
    message_template = message_text.get("1.0", "end-1c")
    
    if not os.path.isfile(excel_file):
        messagebox.showerror("Error", "The specified Excel file does not exist.")
        return
    
    try:
        data = pd.read_excel(excel_file, sheet_name='Ventas')
        for i in range(len(data)):
            celular = data.loc[i, 'Celular'].astype(str)
            nombre = data.loc[i, 'Nombre']
            producto = data.loc[i, 'Producto']
            
            mensaje = message_template.replace("{nombre}", nombre).replace("{producto}", producto)
            
            chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
            web.get(chrome_path).open("https://web.whatsapp.com/send?phone=" + celular + "&text=" + mensaje)
            
            time.sleep(8)
            pg.click(828, 700)
            time.sleep(2)
            pg.press('enter')
            time.sleep(3)
            pg.hotkey('ctrl', 'w')
            time.sleep(2)
        
        messagebox.showinfo("Success", "Messages sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

app = Tk()
app.title("WhatsApp Message Sender")

Label(app, text="Excel File Path:").pack(pady=5)
excel_entry = Entry(app, width=50)
excel_entry.pack(pady=5)

Label(app, text="Message Template:").pack(pady=5)
message_text = Text(app, height=10, width=50)
message_text.pack(pady=5)

Button(app, text="Send Messages", command=send_messages).pack(pady=20)

app.mainloop()