import sys
import os

# Configuracion de codificacion para Windows
if sys.platform.startswith('win'):
    try:
        # Configurar UTF-8 para la consola
        os.system('chcp 65001 > nul')
        # Configurar stdout para UTF-8 con manejo de errores
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

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