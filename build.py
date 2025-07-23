import os
import subprocess
import sys
import shutil
from pathlib import Path
import time

def try_direct_pyinstaller():
    """Intenta usar PyInstaller directamente sin verificar la importación"""
    
    python_candidates = [
        "python",
        "py", 
        sys.executable,
        "C:\\Python313\\python.exe",
    ]
    
    print("Probando PyInstaller directamente...")
    
    for python_exe in python_candidates:
        try:
            print(f"   Probando: {python_exe}")
            
            result = subprocess.run([
                python_exe, "-m", "PyInstaller", "--version"
            ], capture_output=True, text=True, check=True, timeout=10)
            
            if result.returncode == 0:
                print(f"   PyInstaller funciona: {result.stdout.strip()}")
                return python_exe
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"   No funciona: {e}")
    
    return None

def build_executable():
    """Crea el ejecutable portable de WhatsApp Sender - VERSIÓN CORREGIDA"""
    
    print("Construyendo WhatsApp Sender (Version Corregida)...")
    
    # Buscar PyInstaller
    python_exe = try_direct_pyinstaller()
    
    if not python_exe:
        print("\nNo se encontro PyInstaller funcional")
        print("Instala con: pip install pyinstaller")
        return False
    
    # Verificar estructura del proyecto
    required_files = [
        'src/main.py',
        'src/ui/ui.py', 
        'src/logic/whatsapp_selenium.py'
    ]
    
    print("\nVerificando archivos del proyecto...")
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   OK: {file_path}")
        else:
            print(f"   FALTANTE: {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\nFaltan archivos criticos: {missing_files}")
        return False
    
    # Buscar icono
    icon_path = None
    for icon_file in ['src/assets/icon.ico', 'assets/icon.ico', 'icon.ico']:
        if os.path.exists(icon_file):
            icon_path = icon_file
            print(f"Icono encontrado: {icon_file}")
            break
    
    if not icon_path:
        print("No se encontro icono")
    
    # Limpiar builds anteriores
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"{folder} anterior eliminado")
    
    try:
        # COMANDO CORREGIDO (sin --optimize que no existe en PyInstaller 5.13.2)
        cmd = [
            python_exe, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name", "WhatsAppSender",
            "--clean",
            "--noconfirm",
            # Removido: "--optimize", "2",  # No existe en esta versión
            
            # DEPENDENCIAS REALES de tu proyecto:
            "--hidden-import", "selenium",
            "--hidden-import", "selenium.webdriver",
            "--hidden-import", "selenium.webdriver.chrome",
            "--hidden-import", "selenium.webdriver.chrome.service",
            "--hidden-import", "selenium.webdriver.chrome.options",
            "--hidden-import", "selenium.webdriver.common.by",
            "--hidden-import", "selenium.webdriver.common.keys",
            "--hidden-import", "selenium.webdriver.support",
            "--hidden-import", "selenium.webdriver.support.ui",
            "--hidden-import", "selenium.webdriver.support.expected_conditions",
            "--hidden-import", "selenium.common.exceptions",
            
            # Pandas y Excel
            "--hidden-import", "pandas",
            "--hidden-import", "openpyxl",
            "--hidden-import", "openpyxl.reader.excel",
            "--hidden-import", "xlrd",
            "--hidden-import", "xlsxwriter",
            
            # Tkinter (UI)
            "--hidden-import", "tkinter",
            "--hidden-import", "tkinter.filedialog",
            "--hidden-import", "tkinter.messagebox",
            "--hidden-import", "tkinter.ttk",
            "--hidden-import", "tkinter.scrolledtext",
            
            # PIL para imágenes
            "--hidden-import", "PIL",
            "--hidden-import", "PIL.Image",
            "--hidden-import", "PIL.ImageTk",
            "--hidden-import", "PIL.ImageDraw",
            
            # Otras dependencias importantes
            "--hidden-import", "pyperclip",
            "--hidden-import", "threading",
            "--hidden-import", "webbrowser",
            "--hidden-import", "tempfile",
            "--hidden-import", "shutil",
            "--hidden-import", "os",
            "--hidden-import", "sys",
            "--hidden-import", "time",
            "--hidden-import", "datetime",
            "--hidden-import", "pathlib",
            
            # INCLUIR TUS MODULOS PERSONALIZADOS:
            "--hidden-import", "ui.ui",
            "--hidden-import", "logic.whatsapp_selenium",
            
            # INCLUIR CARPETAS DE CODIGO:
            "--add-data", "src/ui;ui",
            "--add-data", "src/logic;logic",
            
            # Excluir módulos pesados innecesarios
            "--exclude-module", "matplotlib",
            "--exclude-module", "scipy",
            "--exclude-module", "numpy.tests",
            "--exclude-module", "pandas.tests",
            "--exclude-module", "test",
            "--exclude-module", "unittest",
        ]
        
        # Agregar icono si existe
        if icon_path:
            cmd.extend(["--icon", icon_path])
        
        # Agregar assets si existen
        if os.path.exists('src/assets'):
            cmd.extend(["--add-data", "src/assets;assets"])
            print("Incluyendo carpeta assets")
        
        cmd.append("src/main.py")
        
        print(f"\nEjecutando PyInstaller...")
        print(f"Usando Python: {python_exe}")
        print(f"Comando: {' '.join(cmd[:8])} ... [muchas opciones] ... src/main.py")
        
        # Ejecutar con progreso mejorado
        start_time = time.time()
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True, 
            universal_newlines=True
        )
        
        print("\nProgreso del build:")
        important_lines = []
        
        for line in process.stdout:
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in [
                "info:", "analyzing", "building", "collecting", "processing",
                "warning:", "error:", "completed successfully", "building exe"
            ]):
                print(f"   {line}")
                important_lines.append(line)
                
                # Detectar errores críticos
                if "error:" in line.lower() and "critical" in line.lower():
                    print(f"ERROR CRITICO DETECTADO")
        
        process.wait()
        build_time = time.time() - start_time
        
        if process.returncode == 0:
            # Verificar ejecutable
            exe_path = Path("dist/WhatsAppSender.exe")
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                
                print(f"\nBUILD EXITOSO!")
                print(f"Ejecutable: {exe_path.absolute()}")
                print(f"Tamaño: {size_mb:.1f} MB")
                print(f"Tiempo: {build_time:.1f} segundos")
                
                if icon_path:
                    print(f"Icono aplicado: {icon_path}")
                
                # Crear distribución portable
                create_portable_distribution(exe_path, icon_path)
                
                return True
            else:
                print("El ejecutable no se creo")
                return False
        else:
            print(f"\nPyInstaller FALLO (codigo {process.returncode})")
            print("\nUltimas lineas importantes:")
            for line in important_lines[-10:]:
                print(f"   {line}")
            return False
            
    except Exception as e:
        print(f"Error inesperado durante el build: {e}")
        return False

def create_portable_distribution(exe_path, icon_path):
    """Crea una carpeta de distribución lista para usar"""
    
    dist_folder = Path("WhatsAppSender_Portable")
    
    print(f"\nCreando distribucion portable...")
    
    # Limpiar distribución anterior
    if dist_folder.exists():
        shutil.rmtree(dist_folder)
    
    dist_folder.mkdir()
    
    # Copiar ejecutable
    shutil.copy2(exe_path, dist_folder / "WhatsAppSender.exe")
    print(f"Ejecutable copiado")
    
    # Copiar icono si existe
    if icon_path and os.path.exists(icon_path):
        shutil.copy2(icon_path, dist_folder / "icon.ico")
        print(f"Icono copiado")
    
    # Crear archivos de documentación (sin Excel de ejemplo)
    create_readme(dist_folder)
    create_troubleshooting_guide(dist_folder)
    
    print(f"Distribucion creada: {dist_folder.absolute()}")
    
    # Intentar abrir carpeta
    try:
        if os.name == 'nt':
            os.startfile(str(dist_folder))
            print(f"Carpeta abierta automaticamente")
    except Exception:
        print(f"Abre manualmente: {dist_folder.absolute()}")

def create_readme(dist_folder):
    """Crear README completo"""
    readme_content = """# WhatsApp Sender - Aplicacion Portable

## INICIO RAPIDO

1. **Ejecutar:** Doble clic en `WhatsAppSender.exe`
2. **Preparar Excel:** Crear archivo con columnas NOMBRES, CELULAR, FECHA FIN
3. **Enviar:** Seleccionar archivo -> Escribir mensaje -> Enviar

## FORMATO EXCEL REQUERIDO

| NOMBRES          | CELULAR   | FECHA FIN  |
|------------------|-----------|------------|
| Juan Perez       | 987654321 | 31/12/2024 |
| Maria Gonzalez   | 976543210 | 15/01/2025 |

**IMPORTANTE:**
- Numeros de **9 digitos** (sin +51, sin espacios)
- Fechas en formato **DD/MM/YYYY**
- Columnas exactas: **NOMBRES**, **CELULAR**, **FECHA FIN**

## MENSAJE CON VARIABLES

Usa estas variables en tu mensaje:
- `{nombre}` -> Se reemplaza por el nombre de la persona
- `{fecha_fin}` -> Se reemplaza por la fecha de vencimiento

**Ejemplo:**
```
Hola {nombre}, tu membresia vence el {fecha_fin}. 
Renueva ahora para no perder el acceso!
```

## ARCHIVOS ADJUNTOS

- **Imagenes:** JPG, PNG, GIF (maximo 10MB cada una)
- **PDFs:** Evita acentos en el nombre del archivo
- **Limite:** 10 archivos por envio

## REQUISITOS TECNICOS

- Windows 10/11
- 4GB RAM minimo
- Conexion a internet estable
- WhatsApp activo en el telefono
- Navegador moderno (Chrome, Edge, Firefox)

## INSTRUCCIONES IMPORTANTES

### Durante el envio:
- **NO muevas el mouse** ni uses el teclado
- Manten WhatsApp Web abierto en el navegador
- No abras otras aplicaciones pesadas
- Asegurate de tener buena conexion a internet

### Antes de enviar:
- Verifica que todos los numeros sean validos
- Prueba con 1-2 contactos primero
- Ten preparados los archivos a adjuntar

## SOLUCION DE PROBLEMAS

**El programa no abre:**
- Ejecutar como administrador (clic derecho -> "Ejecutar como administrador")
- Desactivar antivirus temporalmente
- Verificar que no este bloqueado por Windows Defender

**WhatsApp no se conecta:**
- Abrir WhatsApp Web manualmente en el navegador
- Escanear codigo QR con el telefono
- Verificar conexion a internet

**Numeros invalidos:**
- Verificar formato de 9 digitos
- Sin +51, sin guiones, sin espacios
- Ejemplo correcto: 987654321

**Archivos no se envian:**
- PDFs: renombrar sin acentos (ñ, a, e, i, o, u)
- Verificar tamaño < 10MB por archivo
- Verificar que los archivos existan

## CONTACTO Y SOPORTE

Si tienes problemas persistentes:
1. Leer `solucion_problemas.txt`
2. Verificar todos los requisitos
3. Reiniciar la aplicacion
4. Contactar al desarrollador

---
**Version:** 1.0 | **Desarrollado para:** Envio masivo responsable de WhatsApp
**Advertencia:** Respeta las politicas de WhatsApp y no hagas spam
"""
    
    with open(dist_folder / "LEEME.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)

def create_troubleshooting_guide(dist_folder):
    """Crear guia detallada de solucion de problemas"""
    guide_content = """# Guia de Solucion de Problemas

## PROBLEMAS COMUNES Y SOLUCIONES

### 1. EL PROGRAMA NO ABRE

**Sintomas:** Doble clic no hace nada, o aparece error inmediatamente

**Soluciones:**
1. **Ejecutar como administrador**
   - Clic derecho en WhatsAppSender.exe
   - Seleccionar "Ejecutar como administrador"

2. **Desbloquear archivo**
   - Clic derecho en WhatsAppSender.exe -> Propiedades
   - En "Seguridad" marcar "Desbloquear" -> Aplicar

3. **Antivirus bloqueando**
   - Agregar excepcion en Windows Defender
   - Desactivar antivirus temporalmente

4. **Falta Visual C++ Redistributable**
   - Descargar de Microsoft.com
   - Instalar version 2015-2022 x64

### 2. WHATSAPP WEB NO FUNCIONA

**Sintomas:** No se abre navegador, o codigo QR no aparece

**Soluciones:**
1. **Abrir WhatsApp Web manualmente**
   - Ir a web.whatsapp.com en Chrome/Edge
   - Escanear codigo QR con el telefono
   - Dejar abierto, luego ejecutar la aplicacion

2. **Limpiar cache del navegador**
   - Chrome: Ctrl+Shift+Del -> Borrar datos
   - Reiniciar navegador

3. **Verificar conexion**
   - Telefono y PC en la misma red WiFi
   - WhatsApp actualizado en el telefono

### 3. NUMEROS NO VALIDOS

**Sintomas:** "Numero invalido", mensajes no se envian

**Soluciones:**
1. **Formato correcto**
   - Solo 9 digitos: 987654321
   - Sin +51, sin espacios, sin guiones
   - Sin parentesis, sin puntos

2. **Verificar numeros reales**
   - Probar llamando desde otro telefono
   - Numeros deben estar registrados en WhatsApp

### 4. ARCHIVOS NO SE ENVIAN

**Sintomas:** Error al adjuntar PDFs o imagenes

**Soluciones:**
1. **PDFs con acentos**
   - Renombrar archivo sin ñ, a, e, i, o, u
   - Ejemplo: "facturacion.pdf" -> "facturacion.pdf"

2. **Tamaño de archivos**
   - Maximo 10MB por archivo
   - Comprimir imagenes si es necesario

3. **Rutas con espacios**
   - Evitar carpetas con nombres muy largos
   - Mover archivos a carpeta simple (ej: C:\\temp\\)

### 5. PROGRAMA SE CIERRA INESPERADAMENTE

**Sintomas:** Se cierra durante el envio

**Soluciones:**
1. **Liberar memoria**
   - Cerrar otras aplicaciones
   - Reiniciar PC si es necesario

2. **No mover el mouse**
   - Mantener manos alejadas durante envio
   - No usar otras aplicaciones

3. **Conexion estable**
   - Usar cable Ethernet si es posible
   - Cerrar descargas/streaming

### 6. MENSAJES SE ENVIAN MUY LENTO

**Sintomas:** Demora mucho entre mensajes

**Esto es NORMAL por seguridad:**
- WhatsApp detecta envio masivo
- Se agregan pausas automaticas
- Es para evitar bloqueos de cuenta

**No hay solucion rapida** - Respeta los tiempos

## SI NADA FUNCIONA

1. **Reiniciar completamente:**
   - Cerrar WhatsApp Sender
   - Cerrar navegador
   - Reiniciar PC
   - Abrir WhatsApp Web primero
   - Luego abrir WhatsApp Sender

2. **Verificar requisitos:**
   - Windows 10/11 actualizado
   - 4GB RAM libre
   - Navegador actualizado
   - Internet estable

3. **Contactar soporte:**
   - Anotar mensaje de error exacto
   - Describir pasos que realizaste
   - Incluir version de Windows

## ADVERTENCIAS IMPORTANTES

- **No hagas spam:** Respeta a tus contactos
- **Limites de WhatsApp:** Maximo 50-100 mensajes por dia
- **Cuenta comercial:** Considera WhatsApp Business API para volumenes altos
- **Backup:** Siempre respalda tu lista de contactos

---
**Tip:** Siempre prueba con 1-2 contactos antes de envio masivo
"""
    
    with open(dist_folder / "solucion_problemas.txt", 'w', encoding='utf-8') as f:
        f.write(guide_content)

if __name__ == "__main__":
    print("=" * 70)
    print("BUILD CORREGIDO - WhatsApp Sender")
    print("=" * 70)
    
    success = build_executable()
    
    if success:
        print("\nBUILD COMPLETADO EXITOSAMENTE")
        print("Tu aplicacion portable esta lista para distribuir")
        print("Revisa los archivos de documentacion incluidos")
    else:
        print("\nBUILD FALLO")
        print("Revisa los errores mostrados arriba")
        print("Verifica que todas las dependencias esten instaladas")
    
    input("\nPresiona Enter para salir...")