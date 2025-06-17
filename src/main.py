import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
from messagewhatsapp import send_messages

excel_file = None
excel_logo_img = None

def update_icon(imported, filename=None):
    if imported and filename:
        icon_label.config(image=excel_logo_img, text="")
        file_name_label.config(text=filename.split("/")[-1] or filename.split("\\")[-1])
    else:
        icon_label.config(image="", text="❌ No importado")
        file_name_label.config(text="")

def browse_file():
    global excel_file
    filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if filename:
        excel_file = filename
        update_icon(True, filename)
    else:
        excel_file = None
        update_icon(False)

def send_in_thread():
    try:
        send_messages(excel_file, message_text.get("1.0", tk.END).strip())
        messagebox.showinfo("Success", "Messages sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def send():
    if not excel_file or not message_text.get("1.0", tk.END).strip():
        messagebox.showerror("Error", "Please provide both an Excel file and a message.")
        return
    
    thread = threading.Thread(target=send_in_thread)
    thread.start()

def preview_message():
    if not excel_file:
        messagebox.showwarning("Warning", "Please select an Excel file first.")
        return
    
    try:
        df = pd.read_excel(excel_file, sheet_name='Ventas')
        if df.empty:
            messagebox.showwarning("Warning", "The Excel file is empty.")
            return

        # Usamos el primer registro
        nombre = str(df.loc[0, 'Nombre'])
        producto = str(df.loc[0, 'Producto'])

        # Formateamos el mensaje
        mensaje_raw = message_text.get("1.0", tk.END).strip()
        mensaje_final = mensaje_raw.format(nombre=nombre, producto=producto)

        messagebox.showinfo("Mensaje de Ejemplo", f"Este es el mensaje que se enviará:\n\n{mensaje_final}")
    
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo previsualizar el mensaje:\n{e}")

app = tk.Tk()
app.title("WhatsApp Message Sender")

tk.Label(app, text="Excel File:").pack(pady=5)

logo_path = "src/ExcelLogo.png"
try:
    img = Image.open(logo_path)
    img = img.resize((48, 48), Image.LANCZOS)
    excel_logo_img = ImageTk.PhotoImage(img)
except:
    excel_logo_img = None

icon_label = tk.Label(app, text="❌ No importado", font=("Arial", 12))
icon_label.pack(pady=2)
file_name_label = tk.Label(app, text="", font=("Arial", 10))
file_name_label.pack(pady=2)

tk.Button(app, text="Browse", command=browse_file).pack(pady=5)

tk.Label(app, text="Message:").pack(pady=5)
message_text = tk.Text(app, height=10, width=50)
message_text.pack(pady=5)

# Botón de previsualización
tk.Button(app, text="Previsualizar Mensaje", command=preview_message).pack(pady=5)

# Botón de envío
tk.Button(app, text="Send Messages", command=send).pack(pady=10)

app.mainloop()
