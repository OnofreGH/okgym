import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from messagewhatsapp import send_messages
from PIL import Image, ImageTk

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

def send():
    message = message_text.get("1.0", tk.END).strip()
    if not excel_file or not message:
        messagebox.showerror("Error", "Please provide both an Excel file and a message.")
        return
    try:
        send_messages(excel_file, message)
        messagebox.showinfo("Success", "Messages sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

app = tk.Tk()
app.title("WhatsApp Message Sender")

tk.Label(app, text="Excel File:").pack(pady=5)

# Cargar el logo de Excel
excel_logo_img = Image.open("src/ExcelLogo.png")
excel_logo_img = excel_logo_img.resize((48, 48), Image.LANCZOS)
excel_logo_img = ImageTk.PhotoImage(excel_logo_img)

icon_label = tk.Label(app, text="❌ No importado", font=("Arial", 12))
icon_label.pack(pady=2)
file_name_label = tk.Label(app, text="", font=("Arial", 10))
file_name_label.pack(pady=2)

tk.Button(app, text="Browse", command=browse_file).pack(pady=5)

tk.Label(app, text="Message:").pack(pady=5)
message_text = tk.Text(app, height=10, width=50)
message_text.pack(pady=5)

tk.Button(app, text="Send Messages", command=send).pack(pady=20)

app.mainloop()