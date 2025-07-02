import os
import subprocess
import sys
import shutil
from pathlib import Path

def try_direct_pyinstaller():
    """Intenta usar PyInstaller directamente sin verificar la importación"""
    
    # Priorizar instalaciones que probablemente funcionan
    python_candidates = [
        "python",  # Python en PATH (este parece funcionar)
        "py",      # Python Launcher
        sys.executable,  # Python actual
        "C:\\Python313\\python.exe",  # Python del sistema
    ]
    
    print("🔧 Probando PyInstaller directamente...")
    
    for python_exe in python_candidates:
        try:
            print(f"   Probando: {python_exe}")
            
            # Intentar ejecutar PyInstaller directamente
            result = subprocess.run([
                python_exe, "-m", "PyInstaller", "--version"
            ], capture_output=True, text=True, check=True, timeout=10)
            
            if result.returncode == 0:
                print(f"PyInstaller funciona: {result.stdout.strip()}")
                return python_exe
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"No funciona: {e}")
    
    return None

def build_executable():
    """Crea el ejecutable portable de WhatsApp Sender"""
    
    print("🔨 Construyendo WhatsApp Sender...")
    
    # Buscar PyInstaller usando ejecución directa
    python_exe = try_direct_pyinstaller()
    
    if not python_exe:
        print("\nNo se encontró PyInstaller funcional")
        return
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('src/main.py'):
        print("No se encontró src/main.py")
        print("Ejecuta este script desde la raíz del proyecto (okgym/)")
        return
    
    # Verificar icono
    icon_path = None
    for icon_file in ['src/assets/icon.ico', 'src/assets/icon.png']:
        if os.path.exists(icon_file):
            icon_path = icon_file
            print(f"Icono encontrado: {icon_file}")
            break
    
    if not icon_path:
        print("No se encontró icono, creando ejecutable sin icono")
    
    # Limpiar builds anteriores
    if os.path.exists('build'):
        shutil.rmtree('build')
        print("Build anterior eliminado")
    
    if os.path.exists('dist'):
        shutil.rmtree('dist')
        print("Dist anterior eliminado")
    
    try:
        # Comando de PyInstaller
        cmd = [
            python_exe, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name", "WhatsAppSender",
            "--clean",
            "--noconfirm",
            # Agregar imports ocultos importantes
            "--hidden-import", "pywhatkit",
            "--hidden-import", "pyautogui",
            "--hidden-import", "pandas",
            "--hidden-import", "pyexcel",
            "--hidden-import", "pyexcel.plugins.xls",
            "--hidden-import", "pyexcel.plugins.xlsx",
            "--hidden-import", "PIL.Image",
            "--hidden-import", "PIL.ImageTk",
            "--hidden-import", "openpyxl",
            "--hidden-import", "xlrd",
            "--hidden-import", "tkinter",
            "--hidden-import", "threading",
            "--hidden-import", "webbrowser",
        ]
        
        # Agregar icono si se encontró
        if icon_path:
            cmd.extend(["--icon", icon_path])
            print(f"Agregando icono: {icon_path}")
        
        # Agregar assets si existen
        if os.path.exists('src/assets'):
            cmd.extend(["--add-data", "src/assets;assets"])
            print("Incluyendo carpeta assets")
        
        cmd.append("src/main.py")
        
        print("Ejecutando PyInstaller...")
        print(f"Usando Python: {python_exe}")
        print(f"Comando: {' '.join(cmd[:6])} ... src/main.py")
        
        # Ejecutar PyInstaller y mostrar progreso
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, universal_newlines=True)
        
        print("\nSalida de PyInstaller:")
        # Mostrar salida en tiempo real
        for line in process.stdout:
            # Filtrar líneas importantes para mostrar progreso
            if any(keyword in line for keyword in [
                "INFO:", "WARNING:", "ERROR:", "Building", "Analyzing", 
                "Collecting", "Processing", "completed successfully"
            ]):
                print(f"   {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            # Verificar que el ejecutable se creó
            exe_path = Path("dist/WhatsAppSender.exe")
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"\nEjecutable creado exitosamente!")
                print(f"Ubicación: {exe_path.absolute()}")
                print(f"Tamaño: {size_mb:.1f} MB")
                
                if icon_path:
                    print(f"Icono aplicado: {icon_path}")
                
                # Crear carpeta de distribución
                dist_folder = Path("WhatsAppSender_Portable")
                if dist_folder.exists():
                    shutil.rmtree(dist_folder)
                
                dist_folder.mkdir()
                shutil.copy2(exe_path, dist_folder / "WhatsAppSender.exe")
                
                # Crear README para el usuario
                create_readme(dist_folder)
                
                print(f"Versión portable creada en: {dist_folder.absolute()}")
                
                # Abrir carpeta del ejecutable (Windows)
                if os.name == 'nt':
                    try:
                        os.startfile(str(dist_folder))
                    except Exception:
                        print(f"Abre manualmente: {dist_folder.absolute()}")
            else:
                print("El ejecutable no se creó correctamente")
        else:
            print(f"PyInstaller falló con código: {process.returncode}")
            
    except Exception as e:
        print(f"Error inesperado: {e}")

def create_readme(dist_folder):
    """Crea un archivo README para el usuario final"""
    readme_content = """# WhatsApp Sender - Versión Portable

## Instrucciones de uso:

1. **Ejecutar el programa:**
   - Doble clic en WhatsAppSender.exe
   - No requiere instalación

2. **Preparar archivo Excel:**
   - Columnas requeridas: NOMBRES, CELULAR, FECHA FIN
   - Formatos soportados: .xls, .xlsx
   - Números de 9 dígitos (formato peruano)

3. **Usar el programa:**
   - Seleccionar archivo Excel
   - Escribir mensaje (usa {nombre}, {fecha_fin})
   - Adjuntar imágenes/PDFs (opcional)
   - Previsualizar mensaje
   - Enviar mensajes

## Requisitos:
- Windows 10/11
- Conexión a internet (para WhatsApp Web)
- Navegador moderno (Chrome, Edge, Firefox)

## Notas importantes:
- Mantén WhatsApp Web abierto durante el envío
- No muevas el mouse mientras se envían mensajes
- Los números inválidos se omiten automáticamente

## Soporte:
Si tienes problemas, verifica que:
- WhatsApp Web esté funcionando en tu navegador
- Los números estén en formato correcto
- Tengas permisos para escribir archivos temporales
"""
    
    readme_path = dist_folder / "LEEME.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

if __name__ == "__main__":
    build_executable()