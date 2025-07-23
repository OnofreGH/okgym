import sys
import os

# Configuración para PyInstaller
if hasattr(sys, '_MEIPASS'):
    # Si se ejecuta desde PyInstaller
    base_path = sys._MEIPASS
    sys.path.insert(0, base_path)
else:
    # Si se ejecuta desde código fuente
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, current_dir)

try:
    from ui.ui import launch_app
    
    if __name__ == "__main__":
        try:
            launch_app()
        except Exception as e:
            # Mostrar error en ventana si falla (solo en modo ejecutable)
            if hasattr(sys, '_MEIPASS'):
                import tkinter as tk
                from tkinter import messagebox
                
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "Error al iniciar", 
                    f"Error al iniciar la aplicacion:\n\n{type(e).__name__}: {e}\n\nContacta al desarrollador si el problema persiste."
                )
                root.destroy()
            else:
                print(f"[ERROR]: {type(e).__name__} - {e}")
                
except ImportError as e:
    print(f"[ERROR IMPORT]: {e}")
    print("Algunos modulos no estan disponibles")
    if not hasattr(sys, '_MEIPASS'):
        print("Ejecuta: pip install -r requirements.txt")
        input("Presiona Enter para salir...")