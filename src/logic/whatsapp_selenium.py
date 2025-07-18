import time
import os
import platform
import shutil
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class WhatsAppSender:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.is_logged_in = False

    def get_chrome_profile_path(self):
        """Obtiene la ruta del perfil de Chrome predeterminado del usuario"""
        system = platform.system()
        
        if system == "Windows":
            # Ruta típica en Windows
            user_data_dir = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
            profile_dir = "Default"  # Perfil predeterminado
        elif system == "Darwin":  # macOS
            user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            profile_dir = "Default"
        else:  # Linux
            user_data_dir = os.path.expanduser("~/.config/google-chrome")
            profile_dir = "Default"
        
        return user_data_dir, profile_dir

    def setup_driver(self):
        """Configura el driver de Chrome para usar el perfil existente"""
        try:
            print("🔧 Configurando driver de Chrome con perfil existente...")
            chrome_options = webdriver.ChromeOptions()
            
            # Obtener la ruta del perfil de Chrome del usuario
            user_data_dir, profile_dir = self.get_chrome_profile_path()
            
            # Verificar si el perfil existe
            profile_path = os.path.join(user_data_dir, profile_dir)
            if not os.path.exists(profile_path):
                print(f"⚠️ No se encontró el perfil de Chrome en: {profile_path}")
                print("🔄 Usando perfil temporal para WhatsApp...")
                # Fallback: usar perfil temporal
                user_data_dir = os.path.join(os.getcwd(), "whatsapp_profile")
                profile_dir = "Default"
            else:
                print(f"✅ Perfil de Chrome encontrado: {profile_path}")
                # Para usar el perfil existente, usamos una copia temporal
                # para evitar conflictos con Chrome abierto
                temp_profile = os.path.join(os.getcwd(), "chrome_temp_profile")
                if os.path.exists(temp_profile):
                    shutil.rmtree(temp_profile)
                
                print("📋 Copiando sesión de Chrome existente...")
                shutil.copytree(profile_path, os.path.join(temp_profile, "Default"))
                user_data_dir = temp_profile
                profile_dir = "Default"
            
            # Configurar Chrome para usar el perfil
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument(f"--profile-directory={profile_dir}")
            
            # Opciones de estabilidad (SIN remote debugging que causa conflictos)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Cargar más rápido
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Configuraciones para evitar detección
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0
            })
            
            # Instalar ChromeDriver
            print("📥 Descargando/Verificando ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(40)
            
            # Ocultar que es un driver automatizado
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Maximizar ventana para mejor compatibilidad
            self.driver.maximize_window()
            
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ Driver de Chrome configurado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error configurando driver: {e}")
            return self.setup_fallback_driver()

    def setup_fallback_driver(self):
        """Configuración de fallback con perfil temporal limpio"""
        try:
            print("🔄 Intentando con perfil temporal limpio...")
            chrome_options = webdriver.ChromeOptions()
            
            # Usar perfil temporal completamente nuevo
            temp_dir = tempfile.mkdtemp(prefix="whatsapp_")
            chrome_options.add_argument(f"--user-data-dir={temp_dir}")
            
            # Opciones básicas y estables
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(40)
            self.wait = WebDriverWait(self.driver, 20)
            
            print("✅ Driver configurado con perfil temporal limpio")
            return True
            
        except Exception as e:
            print(f"❌ Error crítico configurando driver: {e}")
            import traceback
            traceback.print_exc()
            return False

    def open_whatsapp(self):
        """Abre WhatsApp Web y detecta si ya hay sesión activa"""
        whatsapp_url = "https://web.whatsapp.com"
        try:
            print(f"🌐 Navegando a: {whatsapp_url}")
            self.driver.get(whatsapp_url)
            
            # Verificar si la navegación fue exitosa
            time.sleep(3)
            if "whatsapp.com" not in self.driver.current_url.lower():
                print(f"❌ Error: No se pudo navegar a WhatsApp. URL actual: {self.driver.current_url}")
                return False
            
            print("✅ Navegación a WhatsApp exitosa. Detectando estado de sesión...")
            
            # Selectores para detectar si ya está logueado
            logged_in_selectors = [
                "//div[@id='pane-side']",  # Panel lateral de chats
                "//div[contains(@class, 'two') and contains(@class, '_aigs')]",  # Panel principal
                "//header[contains(@class, '_amid')]",  # Header de WhatsApp
                "//div[@title='New chat']",  # Botón de nuevo chat
                "//div[@data-testid='chat-list']"  # Lista de chats
            ]
            
            # Primero, verificar rápidamente si ya está logueado (5 segundos)
            print("🔍 Verificando sesión existente...")
            for selector in logged_in_selectors:
                try:
                    element = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if element.is_displayed():
                        print("✅ ¡Sesión activa detectada! WhatsApp Web ya está logueado.")
                        self.is_logged_in = True
                        time.sleep(2)  # Esperar a que termine de cargar
                        return True
                except TimeoutException:
                    continue
            
            # Si no se detectó sesión activa, buscar el código QR
            print("📷 No se detectó sesión activa. Buscando código QR...")
            qr_selectors = [
                "//canvas[@aria-label='Scan me!']",
                "//canvas[contains(@aria-label, 'Scan')]",
                "//div[@data-testid='qr-code']",
                "//canvas"
            ]
            
            qr_found = False
            for selector in qr_selectors:
                try:
                    qr_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if qr_element.is_displayed():
                        print("📱 Código QR detectado. Por favor, escanea con tu teléfono.")
                        print("⏳ Tienes hasta 2 minutos para escanear...")
                        qr_found = True
                        break
                except TimeoutException:
                    continue
            
            if qr_found:
                # Esperar a que aparezca la interfaz principal después de escanear
                print("⏳ Esperando login después de escanear QR...")
                for selector in logged_in_selectors:
                    try:
                        WebDriverWait(self.driver, 120).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        print("✅ Login exitoso después de escanear QR.")
                        self.is_logged_in = True
                        time.sleep(2)
                        return True
                    except TimeoutException:
                        continue
                
                print("❌ Timeout: No se completó el login después de escanear QR.")
                return False
            else:
                print("❌ No se detectó código QR ni sesión activa.")
                self.debug_page_state()
                return False

        except WebDriverException as e:
            print(f"❌ Error de WebDriver: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False

    def open_chat_with_link(self, phone_number):
        """Abre un chat directamente usando un enlace"""
        try:
            # El número para el link no debe llevar el '+'
            phone_number_for_link = phone_number.replace('+', '')
            url = f"https://web.whatsapp.com/send?phone={phone_number_for_link}"
            
            print(f"🔗 Abriendo chat con: {url}")
            self.driver.get(url)
            
            # Esperar a que el campo de mensaje esté listo
            message_selectors = [
                "//div[@contenteditable='true'][@data-tab='10']",
                "//div[contains(@aria-label, 'Type a message')]",
                "//div[@title='Type a message']",
                "//div[@role='textbox'][@contenteditable='true']"
            ]
            
            message_box = None
            for selector in message_selectors:
                try:
                    message_box = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not message_box:
                # Verificar si hay algún error de número inválido
                try:
                    invalid_selectors = [
                        "//*[contains(text(), 'phone number is invalid')]",
                        "//*[contains(text(), 'number is invalid')]",
                        "//*[contains(text(), 'inválido')]"
                    ]
                    
                    for invalid_selector in invalid_selectors:
                        invalid_element = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, invalid_selector))
                        )
                        if invalid_element:
                            print(f"❌ El número {phone_number} es inválido según WhatsApp.")
                            return False
                except TimeoutException:
                    pass
                
                print(f"❌ No se pudo abrir el chat para {phone_number}. El campo de mensaje no apareció.")
                return False
            
            print(f"✅ Chat abierto para {phone_number}")
            time.sleep(2)
            return True

        except Exception as e:
            print(f"❌ Error abriendo chat para {phone_number}: {e}")
            return False

    def send_text_message(self, message):
        """Envía un mensaje de texto"""
        try:
            # Múltiples selectores para el campo de mensaje
            message_selectors = [
                "//div[@contenteditable='true'][@data-tab='10']",
                "//div[contains(@aria-label, 'Type a message')]",
                "//div[@role='textbox'][@contenteditable='true'][@data-lexical-editor='true']",
                "//div[contains(@class, 'copyable-text') and @contenteditable='true' and contains(@aria-label, 'message')]",
                "//div[@title='Type a message']"
            ]
            
            message_box = None
            for selector in message_selectors:
                try:
                    message_box = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not message_box:
                print("❌ No se encontró el campo de mensaje")
                return False
            
            # Escribir mensaje
            message_box.click()
            time.sleep(1)
            message_box.clear()
            time.sleep(1)
            message_box.send_keys(message)
            time.sleep(2)
            
            # Enviar mensaje
            message_box.send_keys(Keys.ENTER)
            time.sleep(3)
            
            print("✅ Mensaje de texto enviado")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando mensaje de texto: {e}")
            return False

    def send_files(self, file_paths, file_type="image"):
        """Envía archivos (imágenes o documentos)"""
        try:
            if not file_paths:
                return True
                
            print(f"📎 Enviando {len(file_paths)} archivo(s) de tipo {file_type}")
            
            # Múltiples selectores para el botón de adjuntar
            attach_selectors = [
                "//div[@title='Attach']",
                "//span[@data-icon='plus']/..",
                "//button[contains(@aria-label, 'Attach')]",
                "//div[contains(@aria-label, 'Attach')]"
            ]
            
            attach_button = None
            for selector in attach_selectors:
                try:
                    attach_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not attach_button:
                print("❌ No se encontró el botón de adjuntar")
                return False
            
            attach_button.click()
            time.sleep(2)
            
            # Según el tipo de archivo, buscar el botón correspondiente
            if file_type == "image":
                # Múltiples selectores para imágenes
                file_selectors = [
                    "//span[@data-icon='image']/..",
                    "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']",
                    "//div[contains(@title, 'Photos')]",
                    "//li[contains(@aria-label, 'Photos')]"
                ]
            else:  # document/pdf
                # Múltiples selectores para documentos
                file_selectors = [
                    "//span[@data-icon='document']/..",
                    "//input[@accept='*']",
                    "//div[contains(@title, 'Document')]",
                    "//li[contains(@aria-label, 'Document')]"
                ]
            
            file_input = None
            for selector in file_selectors:
                try:
                    if selector.startswith("//input"):
                        # Si es un input, lo usamos directamente
                        file_input = self.driver.find_element(By.XPATH, selector)
                        break
                    else:
                        file_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        file_button.click()
                        time.sleep(2)
                        # Buscar el input después de hacer clic
                        file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                        break
                except:
                    continue
            
            if not file_input:
                print("❌ No se encontró el input de archivo")
                return False
            
            # Preparar paths absolutos
            absolute_paths = [os.path.abspath(path) for path in file_paths]
            
            # Enviar archivos
            file_input.send_keys('\n'.join(absolute_paths))
            time.sleep(4)
            
            # Buscar y hacer clic en el botón de enviar
            send_selectors = [
                "//span[@data-icon='send']/..",
                "//button[contains(@aria-label, 'Send')]",
                "//div[@title='Send']",
                "//span[contains(@data-icon, 'send')]"
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not send_button:
                print("⚠️ No se encontró el botón de enviar, intentando Enter")
                file_input.send_keys(Keys.ENTER)
            else:
                send_button.click()
            
            time.sleep(4)
            
            print(f"✅ {len(file_paths)} archivo(s) enviado(s)")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando archivos: {e}")
            return False

    def send_complete_message(self, phone_number, message, image_paths=None, pdf_paths=None):
        """Envía un mensaje completo usando un enlace directo para abrir el chat."""
        try:
            # PASO 1: Abrir chat con el enlace directo
            if not self.open_chat_with_link(phone_number):
                return False
            
            # PASO 2: Enviar mensaje de texto
            if message and not self.send_text_message(message):
                print("⚠️ Error enviando texto, pero se continuará con los archivos...")
            
            # PASO 3: Enviar imágenes
            if image_paths:
                if not self.send_files(image_paths, "image"):
                    print("⚠️ Error enviando imágenes.")
            
            # PASO 4: Enviar PDFs
            if pdf_paths:
                if not self.send_files(pdf_paths, "document"):
                    print("⚠️ Error enviando PDFs.")
            
            print("✅ Mensaje completo procesado.")
            return True
            
        except Exception as e:
            print(f"❌ Error crítico enviando mensaje completo a {phone_number}: {e}")
            return False

    def debug_page_state(self):
        """Función para debuggear el estado de la página"""
        try:
            print("🔍 Estado actual de la página:")
            print(f"URL: {self.driver.current_url}")
            print(f"Título: {self.driver.title}")
            
            # Buscar elementos comunes
            elements_to_check = [
                ("Canvas QR", "//canvas"),
                ("Campo búsqueda 1", "//div[@contenteditable='true'][@data-tab='3']"),
                ("Campo búsqueda 2", "//div[@title='Search input textbox']"),
                ("Campo mensaje 1", "//div[@contenteditable='true'][@data-tab='10']"),
                ("Campo mensaje 2", "//div[contains(@aria-label, 'Type a message')]"),
                ("Botón adjuntar", "//div[@title='Attach']")
            ]
            
            for name, xpath in elements_to_check:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    print(f"{name}: {len(elements)} elemento(s) encontrado(s)")
                except Exception as e:
                    print(f"{name}: Error - {e}")
                    
        except Exception as e:
            print(f"Error en debug: {e}")

    def close(self):
        """Cierra el navegador y limpia archivos temporales"""
        try:
            if self.driver:
                self.driver.quit()
                print("🔒 Navegador cerrado")
            
            # Limpiar perfiles temporales
            temp_profiles = ["chrome_temp_profile", "whatsapp_profile"]
            for temp_profile in temp_profiles:
                if os.path.exists(temp_profile):
                    try:
                        shutil.rmtree(temp_profile)
                        print(f"🧹 Perfil temporal {temp_profile} limpiado")
                    except:
                        pass  # Ignorar errores de limpieza
                        
        except Exception as e:
            print(f"⚠️ Error cerrando navegador: {e}")

    def keep_alive(self):
        """Mantiene la sesión activa"""
        try:
            self.driver.execute_script("console.log('keep alive');")
            return True
        except:
            return False
