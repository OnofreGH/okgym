from tkinter import Tk, Label, Entry, Text, Button, messagebox
import os
import messagewhatsapp  # asegúrate de que el archivo se llama "messagewhatsapp.py" y está en el mismo directorio

def on_send_click():
    excel_file = excel_entry.get()
    message_template = message_text.get("1.0", "end-1c")
    
    if not os.path.isfile(excel_file):
        messagebox.showerror("Error", "The specified Excel file does not exist.")
        return
    
    try:
        # Llama a la función del otro archivo
        messagewhatsapp.send_messages(excel_file, message_template)
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

Button(app, text="Send Messages", command=on_send_click).pack(pady=20)

app.mainloop()
