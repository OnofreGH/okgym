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
            user_data_dir = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
            profile_dir = "Default"
        elif system == "Darwin":  # macOS
            user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            profile_dir = "Default"
        else:  # Linux
            user_data_dir = os.path.expanduser("~/.config/google-chrome")
            profile_dir = "Default"
        
        return user_data_dir, profile_dir

    def copy_essential_session_files(self, source_profile, dest_profile):
        """Copia solo los archivos esenciales de la sesión, no todo el perfil"""
        essential_files = [
            "Cookies",
            "Local Storage",
            "Session Storage", 
            "Web Data",
            "Login Data",
            "Preferences"
        ]
        
        try:
            os.makedirs(dest_profile, exist_ok=True)
            
            for file_name in essential_files:
                source_path = os.path.join(source_profile, file_name)
                dest_path = os.path.join(dest_profile, file_name)
                
                if os.path.exists(source_path):
                    if os.path.isdir(source_path):
                        if os.path.exists(dest_path):
                            shutil.rmtree(dest_path)
                        shutil.copytree(source_path, dest_path)
                    else:
                        shutil.copy2(source_path, dest_path)
                    print(f"Copiado: {file_name}")
                else:
                    print(f"No encontrado: {file_name}")
            
            return True
        except Exception as e:
            print(f"Error copiando archivos de sesion: {e}")
            return False

    def setup_driver(self):
        """Configura el driver de Chrome con una estrategia optimizada"""
        try:
            print("Configurando driver de Chrome...")
            chrome_options = webdriver.ChromeOptions()
            
            # ESTRATEGIA 1: Intentar usar perfil temporal con sesión copiada
            user_data_dir, profile_dir = self.get_chrome_profile_path()
            profile_path = os.path.join(user_data_dir, profile_dir)
            
            use_copied_session = False
            
            if os.path.exists(profile_path):
                print(f"Perfil de Chrome encontrado: {profile_path}")
                
                # Crear perfil temporal solo con archivos esenciales
                temp_profile = os.path.join(os.getcwd(), "chrome_temp_profile")
                if os.path.exists(temp_profile):
                    shutil.rmtree(temp_profile)
                
                print("Copiando archivos esenciales de sesion (rapido)...")
                temp_profile_default = os.path.join(temp_profile, "Default")
                
                if self.copy_essential_session_files(profile_path, temp_profile_default):
                    chrome_options.add_argument(f"--user-data-dir={temp_profile}")
                    chrome_options.add_argument(f"--profile-directory=Default")
                    use_copied_session = True
                    print("Usando sesion copiada optimizada")
                else:
                    print("Fallo la copia, usando perfil temporal limpio")
            
            if not use_copied_session:
                # ESTRATEGIA 2: Perfil temporal completamente limpio
                print("Usando perfil temporal limpio...")
                temp_dir = tempfile.mkdtemp(prefix="whatsapp_")
                chrome_options.add_argument(f"--user-data-dir={temp_dir}")
            
            # Opciones de estabilidad y velocidad
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Cargar más rápido
            chrome_options.add_argument("--disable-javascript")  # Solo para cargar inicial
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Configuraciones para evitar detección
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0
            })
            
            # Instalar ChromeDriver con timeout más corto
            print("Configurando ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)  # Reducido de 40 a 30
            
            # Ocultar que es un driver automatizado
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Maximizar ventana
            self.driver.maximize_window()
            
            self.wait = WebDriverWait(self.driver, 15)  # Reducido de 20 a 15
            print("Driver de Chrome configurado correctamente")
            return True
            
        except Exception as e:
            print(f"Error configurando driver: {e}")
            return self.setup_fallback_driver()

    def setup_fallback_driver(self):
        """Configuración de fallback completamente básica"""
        try:
            print("Usando configuracion basica de emergencia...")
            chrome_options = webdriver.ChromeOptions()
            
            # Solo opciones básicas
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--start-maximized")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 15)
            
            print("Driver configurado con opciones basicas")
            return True
            
        except Exception as e:
            print(f"Error critico configurando driver: {e}")
            return False

    def dismiss_welcome_popups(self):
        """Cierra ventanas emergentes de bienvenida que aparecen después del primer login - VERSIÓN OPTIMIZADA"""
        try:
            print("Verificando ventanas de bienvenida...")
            
            # Verificación rápida inicial - si no hay diálogos, salir inmediatamente
            try:
                dialogs = self.driver.find_elements(By.XPATH, "//div[@role='dialog']")
                if not any(d.is_displayed() for d in dialogs):
                    print("No hay ventanas emergentes visibles")
                    return True
            except:
                print("No hay ventanas emergentes")
                return True
            
            print("Ventana emergente detectada, cerrando...")
            
            # Selectores ordenados por prioridad y frecuencia
            quick_selectors = [
                "//button[contains(text(), 'Continuar')]",
                "//button[contains(text(), 'Continue')]", 
                "//span[@data-icon='x']/..",
                "//div[@role='dialog']//button[1]"  # Primer botón del diálogo
            ]
            
            # Solo 1 intento rápido
            for selector in quick_selectors:
                try:
                    popup_button = WebDriverWait(self.driver, 0.5).until(  # Timeout muy corto
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    if popup_button.is_displayed():
                        popup_button.click()
                        print("Ventana emergente cerrada")
                        time.sleep(0.5)  # Pausa mínima
                        return True
                        
                except TimeoutException:
                    continue
                except Exception:
                    continue
            
            # Si no funcionó, intentar ESC como último recurso
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                print("ESC enviado para cerrar ventanas")
                time.sleep(0.5)
                return True
            except:
                pass
                
            print("Verificación completada")
            return True
            
        except Exception as e:
            print(f"Error en dismiss_welcome_popups: {e}")
            return False

    def open_whatsapp(self):
        """Abre WhatsApp Web y detecta si ya hay sesión activa"""
        whatsapp_url = "https://web.whatsapp.com"
        try:
            print(f"Navegando a: {whatsapp_url}")
            self.driver.get(whatsapp_url)
            
            # Verificar si la navegación fue exitosa
            time.sleep(5)  # Aumentado para dar más tiempo inicial
            if "whatsapp.com" not in self.driver.current_url.lower():
                print(f"Error: No se pudo navegar a WhatsApp. URL actual: {self.driver.current_url}")
                return False
            
            print("Navegación a WhatsApp exitosa. Detectando estado de sesión...")
            
            # Selectores más amplios para detectar diferentes estados
            logged_in_selectors = [
                "//div[@id='pane-side']",  # Panel lateral de chats
                "//div[contains(@class, 'two') and contains(@class, '_aigs')]",  # Panel principal
                "//header[contains(@class, '_amid')]",  # Header de WhatsApp
                "//div[@title='New chat']",  # Botón de nuevo chat
                "//div[@data-testid='chat-list']",  # Lista de chats
                "//span[@data-icon='new-chat-outline']/..",  # Botón nuevo chat (alternativo)
                "//div[contains(@aria-label, 'Chat list')]",  # Lista de chats (alternativo)
                "//div[@role='button'][contains(@title, 'New chat')]"  # Nuevo chat (más general)
            ]
            
            # Detectar estados intermedios (cuando está cargando después del QR)
            intermediate_selectors = [
                "//div[@contenteditable='true'][@data-tab='3']",  # Campo de búsqueda
                "//div[contains(@aria-label, 'Search input')]",  # Campo de búsqueda alternativo
                "//div[@title='Search input textbox']"  # Campo de búsqueda (más específico)
            ]
            
            # PASO 1: Verificar si ya está completamente logueado
            print("Verificando sesión existente...")
            for attempt in range(3):
                print(f"Intento {attempt + 1} de verificar sesión completa...")
                
                for selector in logged_in_selectors:
                    try:
                        element = WebDriverWait(self.driver, 6).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if element.is_displayed():
                            print("Sesión activa detectada. WhatsApp Web ya está logueado.")
                            self.is_logged_in = True
                            self.dismiss_welcome_popups()
                            return True
                    except TimeoutException:
                        continue
                
                # Si no está completamente logueado, verificar estado intermedio
                intermediate_found = False
                for selector in intermediate_selectors:
                    try:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if element.is_displayed():
                            print(f"Estado intermedio detectado (intento {attempt + 1}). WhatsApp está cargando...")
                            intermediate_found = True
                            break
                    except TimeoutException:
                        continue
                
                if intermediate_found:
                    # Está en estado intermedio, cerrar popups y esperar más
                    print("Cerrando posibles ventanas emergentes...")
                    self.dismiss_welcome_popups()
                    
                    # Esperar más tiempo para que WhatsApp termine de cargar
                    print("Esperando a que WhatsApp termine de cargar completamente...")
                    time.sleep(15)  # Espera extendida
                    
                    # Continuar con el siguiente intento
                    continue
                else:
                    # No hay estado intermedio, salir del bucle para buscar QR
                    break
            
            # PASO 2: Si después de los intentos no está logueado, buscar QR
            print("No se detectó sesión activa. Verificando si se requiere login...")
            qr_selectors = [
                "//canvas[@aria-label='Scan me!']",
                "//canvas[contains(@aria-label, 'Scan')]",
                "//div[@data-testid='qr-code']",
                "//canvas",
                "//div[contains(@class, 'qr')]"
            ]
            
            qr_found = False
            for selector in qr_selectors:
                try:
                    qr_element = WebDriverWait(self.driver, 8).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if qr_element.is_displayed():
                        print("Código QR detectado - Se requiere autenticación inicial.")
                        print("Escanea el código QR con tu teléfono para autenticarte.")
                        print("Tienes hasta 2 minutos para completar el proceso...")
                        qr_found = True
                        break
                except TimeoutException:
                    continue
            
            if qr_found:
                # PASO 3: Esperar autenticación después del QR con manejo de ventanas emergentes
                print("Esperando autenticación...")
                
                # Primero esperar a que desaparezca el QR
                try:
                    print("Esperando a que desaparezca el QR...")
                    WebDriverWait(self.driver, 120).until_not(
                        EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
                    )
                    print("QR escaneado, procesando autenticación...")
                except TimeoutException:
                    print("Timeout esperando escaneo de QR")
                    return False
                
                # Esperar y manejar ventanas emergentes inmediatamente después del QR
                for post_qr_attempt in range(5):  # Hasta 5 intentos post-QR
                    print(f"Post-QR intento {post_qr_attempt + 1}: Cerrando ventanas emergentes...")
                    self.dismiss_welcome_popups()
                    time.sleep(3)
                    
                    # Verificar si ya apareció la interfaz principal
                    session_ready = False
                    for selector in logged_in_selectors:
                        try:
                            element = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            if element.is_displayed():
                                print("Interfaz principal detectada después del QR")
                                session_ready = True
                                break
                        except TimeoutException:
                            continue
                    
                    if session_ready:
                        print("Autenticación completada exitosamente.")
                        self.is_logged_in = True
                        
                        # Una última verificación de popups
                        print("Limpieza final de ventanas emergentes...")
                        self.dismiss_welcome_popups()
                        time.sleep(2)
                        return True
                    
                    # Si no está listo, verificar si sigue en estado intermedio
                    intermediate_still_there = False
                    for selector in intermediate_selectors:
                        try:
                            element = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            if element.is_displayed():
                                print(f"Aún en estado intermedio (post-QR intento {post_qr_attempt + 1})")
                                intermediate_still_there = True
                                break
                        except TimeoutException:
                            continue
                    
                    if not intermediate_still_there:
                        print("WhatsApp no está en estado esperado, haciendo debug...")
                        self.debug_page_state()
                        break
                    
                    # Esperar antes del siguiente intento
                    print("Esperando más tiempo para estabilización...")
                    time.sleep(10)
                
                print("Timeout: No se completó la autenticación correctamente.")
                return False
            else:
                # PASO 4: No hay QR, verificar si hay estados especiales o errores
                print("Estado inesperado: No se detectó QR ni sesión activa.")
                
                # Verificar errores específicos
                error_selectors = [
                    "//*[contains(text(), 'Unable to connect')]",
                    "//*[contains(text(), 'Computer not connected')]", 
                    "//*[contains(text(), 'Phone not connected')]",
                    "//*[contains(text(), 'Loading')]",
                    "//*[contains(text(), 'Cargando')]"
                ]
                
                for error_selector in error_selectors:
                    try:
                        error_element = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, error_selector))
                        )
                        if error_element.is_displayed():
                            print(f"Error detectado: {error_element.text}")
                            return False
                    except TimeoutException:
                        continue
                
                # Si está en estado intermedio sin QR, intentar esperar más
                intermediate_found = False
                for selector in intermediate_selectors:
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        if element.is_displayed():
                            print("Estado intermedio sin QR detectado. Esperando estabilización...")
                            intermediate_found = True
                            break
                    except:
                        continue
                
                if intermediate_found:
                    # Intentar cerrar popups y esperar
                    self.dismiss_welcome_popups()
                    time.sleep(15)
                    
                    # Verificar una vez más
                    for selector in logged_in_selectors:
                        try:
                            element = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            if element.is_displayed():
                                print("Sesión estabilizada después de espera adicional")
                                self.is_logged_in = True
                                return True
                        except TimeoutException:
                            continue
                
                self.debug_page_state()
                return False

        except WebDriverException as e:
            print(f"Error de WebDriver: {e}")
            return False
        except Exception as e:
            print(f"Error inesperado: {e}")
            return False

    def dismiss_dialogs(self):
        """Cierra cualquier diálogo o popup que pueda estar bloqueando la interfaz"""
        try:
            # Lista de selectores para cerrar diálogos comunes
            close_selectors = [
                "//button[@aria-label='Cerrar']",
                "//button[@aria-label='Close']",
                "//span[@data-icon='x']/..",
                "//div[@role='button'][contains(@aria-label, 'Close')]",
                "//button[contains(@class, 'close')]",
                "//div[@data-testid='modal-header-close-btn']",
                "//button[contains(text(), 'Not now')]",
                "//button[contains(text(), 'Ahora no')]",
                "//button[contains(text(), 'Maybe later')]",
                "//button[contains(text(), 'Skip')]"
            ]
            
            for selector in close_selectors:
                try:
                    close_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    close_button.click()
                    print("Diálogo cerrado")
                    time.sleep(1)
                    return True
                except TimeoutException:
                    continue
            
                
            return False
            
        except Exception as e:
            print(f"Error cerrando diálogos: {e}")
            return False

    def wait_for_page_load(self):
        """Espera a que la página esté completamente cargada"""
        try:
            # Esperar a que desaparezcan los spinners de carga
            WebDriverWait(self.driver, 5).until_not(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'spinner')]"))
            )
        except TimeoutException:
            pass  # Es normal que no haya spinners
        
    def open_chat_with_link(self, phone_number):
        """Abre un chat directamente usando un enlace"""
        try:
            # El número para el link no debe llevar el '+'
            phone_number_for_link = phone_number.replace('+', '')
            url = f"https://web.whatsapp.com/send?phone={phone_number_for_link}"
            
            print(f"Abriendo chat con: {url}")
            self.driver.get(url)
            
            # Esperar a que la página cargue completamente
            self.wait_for_page_load()
            
            # Cerrar cualquier diálogo que pueda aparecer
            self.dismiss_dialogs()
            
            # Esperar a que el campo de mensaje esté listo
            message_selectors = [
                "//div[@contenteditable='true'][@data-tab='10']",
                "//div[contains(@aria-label, 'Type a message')]",
                "//div[@title='Type a message']",
                "//div[@role='textbox'][@contenteditable='true']",
                "//div[contains(@class, 'copyable-text') and @contenteditable='true']"
            ]
            
            message_box = None
            for selector in message_selectors:
                try:
                    message_box = WebDriverWait(self.driver, 5).until(
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
                            print(f"El número {phone_number} es inválido según WhatsApp.")
                            return False
                except TimeoutException:
                    pass
                
                print(f"No se pudo abrir el chat para {phone_number}. El campo de mensaje no apareció.")
                # Hacer debug para ver qué está pasando
                self.debug_page_state()
                return False
            
            print(f"Chat abierto para {phone_number}")
            return True

        except Exception as e:
            print(f"Error abriendo chat para {phone_number}: {e}")
            return False

    def send_text_message(self, message):
        """Envía un mensaje de texto con manejo mejorado de errores"""
        try:
            # Primero, cerrar cualquier diálogo que pueda estar abierto
            self.dismiss_dialogs()
            
            # Múltiples selectores para el campo de mensaje
            message_selectors = [
                "//div[@contenteditable='true'][@data-tab='10']",
                "//div[contains(@aria-label, 'Type a message')]",
                "//div[@role='textbox'][@contenteditable='true'][@data-lexical-editor='true']",
                "//div[contains(@class, 'copyable-text') and @contenteditable='true' and contains(@aria-label, 'message')]",
                "//div[@title='Type a message']",
                "//div[@data-testid='conversation-compose-box-input']"
            ]
            
            message_box = None
            for attempt in range(3):  # Intentar hasta 3 veces
                print(f"Intento {attempt + 1} de encontrar campo de mensaje...")
                
                for selector in message_selectors:
                    try:
                        message_box = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        print(f"Campo de mensaje encontrado con selector: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if message_box:
                    break
                
                # Si no se encontró, intentar cerrar diálogos y refrescar
                print("Campo de mensaje no encontrado, intentando cerrar diálogos...")
                self.dismiss_dialogs()
                time.sleep(2)
            
            if not message_box:
                print("No se encontró el campo de mensaje después de varios intentos")
                return False
            
            # Hacer scroll al elemento si es necesario
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", message_box)
                time.sleep(1)
            except:
                pass
            
            # Intentar hacer clic de manera más robusta
            try:
                # Usar JavaScript para hacer clic si el clic normal falla
                self.driver.execute_script("arguments[0].click();", message_box)
                time.sleep(1)
            except:
                try:
                    message_box.click()
                    time.sleep(1)
                except:
                    print("No se pudo hacer clic en el campo de mensaje")
                    return False

            # Limpiar el campo y escribir mensaje
            try:
                # Borrar cualquier texto anterior
                message_box.send_keys(Keys.CONTROL + "a")
                time.sleep(0.5)
                message_box.send_keys(Keys.DELETE)
                time.sleep(0.5)

                # Escribir el mensaje
                message_box.send_keys(message)
                time.sleep(2)

                # Enviar mensaje
                message_box.send_keys(Keys.ENTER)
                time.sleep(3)

                print("Mensaje de texto enviado correctamente")
                return True
                
            except Exception as e:
                print(f"Error al escribir/enviar mensaje: {e}")
                return False

        except Exception as e:
            print(f"Error enviando mensaje de texto: {e}")
            return False

    def send_files(self, file_paths, file_type="image"):
        """Envía archivos (imágenes o documentos)"""
        try:
            if not file_paths:
                return True
                
            print(f"Enviando {len(file_paths)} archivo(s) de tipo {file_type}")
            
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
                print("No se encontró el botón de adjuntar")
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
                print("No se encontró el input de archivo")
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
                print("No se encontró el botón de enviar, intentando Enter")
                file_input.send_keys(Keys.ENTER)
            else:
                send_button.click()
            
            time.sleep(4)
            
            print(f"{len(file_paths)} archivo(s) enviado(s)")
            return True
            
        except Exception as e:
            print(f"Error enviando archivos: {e}")
            return False

    def send_complete_message(self, phone_number, message, image_paths=None, pdf_paths=None):
        """Envía un mensaje completo usando un enlace directo para abrir el chat."""
        try:
            # PASO 1: Abrir chat con el enlace directo
            if not self.open_chat_with_link(phone_number):
                return False
            
            # PASO 2: Enviar mensaje de texto
            if message and not self.send_text_message(message):
                print("Error enviando texto, pero se continuará con los archivos...")
            
            # PASO 3: Enviar imágenes
            if image_paths:
                if not self.send_files(image_paths, "image"):
                    print("Error enviando imágenes.")
            
            # PASO 4: Enviar PDFs
            if pdf_paths:
                if not self.send_files(pdf_paths, "document"):
                    print("Error enviando PDFs.")
            
            print("Mensaje completo procesado.")
            return True
            
        except Exception as e:
            print(f"Error crítico enviando mensaje completo a {phone_number}: {e}")
            return False

    def debug_page_state(self):
        """Función para debuggear el estado de la página"""
        try:
            print("Estado actual de la página:")
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
                print("Navegador cerrado")
            
            # Limpiar perfiles temporales
            temp_profiles = ["chrome_temp_profile", "whatsapp_profile"]
            for temp_profile in temp_profiles:
                if os.path.exists(temp_profile):
                    try:
                        shutil.rmtree(temp_profile)
                        print(f"Perfil temporal {temp_profile} limpiado")
                    except:
                        pass  # Ignorar errores de limpieza
                        
        except Exception as e:
            print(f"Error cerrando navegador: {e}")

    def keep_alive(self):
        """Mantiene la sesión activa"""
        try:
            self.driver.execute_script("console.log('keep alive');")
            return True
        except:
            return False
