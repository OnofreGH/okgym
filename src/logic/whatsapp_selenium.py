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
    # Constantes para timeouts
    NAVIGATION_TIMEOUT = 20
    QR_TIMEOUT = 120
    ELEMENT_TIMEOUT = 8
    MESSAGE_TIMEOUT = 5
    
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
        elif  system == "Darwin":  # macOS
            user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            profile_dir = "Default"
        else:  # Linux
            user_data_dir = os.path.expanduser("~/.config/google-chrome")
            profile_dir = "Default"
        
        return user_data_dir, profile_dir

    def copy_essential_session_files(self, source_profile, dest_profile):
        """Copia solo los archivos esenciales de la sesion, no todo el perfil"""
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
        """Configura el driver de Chrome con configuracion optimizada"""
        try:
            print("Configurando driver de Chrome...")
            chrome_options = webdriver.ChromeOptions()
            
            # Perfil temporal limpio (mas rapido que copiar archivos)
            temp_dir = tempfile.mkdtemp(prefix="whatsapp_")
            chrome_options.add_argument(f"--user-data-dir={temp_dir}")
            
            # Opciones optimizadas para velocidad
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            
            # Configuraciones anti-deteccion
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 1  # Deshabilitar imagenes
            })
            
            # User-Agent actualizado
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(20)  # Reducido
            
            # Configuraciones post-inicializacion
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.maximize_window()
            
            self.wait = WebDriverWait(self.driver, 10)  # Reducido de 15
            print("Driver configurado correctamente")
            return True
            
        except Exception as e:
            print(f"Error configurando driver: {e}")
            return False

    def setup_fallback_driver(self):
        """Configuracion de fallback completamente basica"""
        try:
            print("Usando configuracion basica de emergencia...")
            chrome_options = webdriver.ChromeOptions()
            
            # Solo opciones basicas
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
        """Cierra ventanas emergentes de forma optimizada"""
        try:
            # Verificacion rapida sin timeouts largos
            dialogs = self.driver.find_elements(By.XPATH, "//div[@role='dialog']")
            if not dialogs or not any(d.is_displayed() for d in dialogs):
                return True
            
            print("Cerrando ventana emergente...")
            
            # Selectores mas especificos y comunes
            selectors = [
                "//button[text()='Continuar']",
                "//button[text()='Continue']", 
                "//button[text()='OK']",
                "//span[@data-icon='x']/.."
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(self.driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    print("Ventana emergente cerrada")
                    time.sleep(1)
                    return True
                except TimeoutException:
                    continue
            
            # ESC como fallback
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                return True
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"Error cerrando ventanas: {e}")
            return False

    def open_whatsapp(self):
        """Abre WhatsApp Web de forma optimizada"""
        try:
            print("Navegando a WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            
            # Espera inicial reducida
            time.sleep(3)
            
            # Detectar QR o sesion activa
            qr_present = self.driver.find_elements(By.XPATH, "//canvas[@aria-label='Scan me!']")
            
            if qr_present and qr_present[0].is_displayed():
                print("Codigo QR detectado - Escanea para autenticarte")
                
                # Esperar hasta que desaparezca el QR
                try:
                    WebDriverWait(self.driver, 120).until_not(
                        EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
                    )
                    print("QR escaneado correctamente")
                except TimeoutException:
                    print("Timeout escaneando QR")
                    return False
        
            # Validar sesion activa
            session_selectors = [
                "//div[@id='pane-side']",
                "//div[@title='New chat']",
                "//div[@data-testid='chat-list']"
            ]
            
            for attempt in range(3):
                for selector in session_selectors:
                    try:
                        element = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if element.is_displayed():
                            print("Sesion validada - WhatsApp listo")
                            self.is_logged_in = True
                            self.dismiss_welcome_popups()
                            return True
                    except TimeoutException:
                        continue
                
                if attempt < 2:
                    time.sleep(5)
            
            print("No se pudo validar la sesion")
            return False
            
        except Exception as e:
            print(f"Error abriendo WhatsApp: {e}")
            return False

    def wait_for_page_load(self):
        """Espera a que la pagina este completamente cargada"""
        try:
            # Esperar a que desaparezcan los spinners de carga
            WebDriverWait(self.driver, 1).until_not(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'spinner')]"))
            )
        except TimeoutException:
            pass  # Es normal que no haya spinners
        
    def open_chat_with_link(self, phone_number):
        """Abre chat de forma optimizada con filtrado de campo de busqueda"""
        try:
            # PASO 1: Navegar a WhatsApp Web base para resetear estado
            print("Reseteando estado de WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            time.sleep(2)

            # PASO 2: Abrir chat específico
            url = f"https://web.whatsapp.com/send?phone={phone_number.replace('+', '')}"
            print(f"Abriendo chat: {phone_number}")
            
            self.driver.get(url)
            time.sleep(5)
            
            # PASO 3: Verificar campo de mensaje con estrategias múltiples
            message_selectors = [
                # PRIORIDAD 1: Campo específico de mensaje (data-tab='10')
                "//div[@contenteditable='true'][@data-tab='10']",
                # PRIORIDAD 2: Campo moderno de mensaje con data-lexical-editor EN FOOTER
                "//footer//div[@role='textbox'][@contenteditable='true'][@data-lexical-editor='true']",
                # PRIORIDAD 3: Campo de mensaje por aria-label
                "//div[contains(@aria-label, 'Type a message')][@contenteditable='true']",
                # PRIORIDAD 4: Campo de mensaje por título
                "//div[@title='Type a message'][@contenteditable='true']",
                # PRIORIDAD 5: Campo genérico en footer
                "//footer//div[@contenteditable='true']"
            ]
            
            for attempt in range(3):  # Hasta 3 intentos
                print(f"Intento {attempt + 1} de encontrar campo de mensaje...")
                
                for selector in message_selectors:
                    try:
                        candidates = self.driver.find_elements(By.XPATH, selector)
                        
                        for candidate in candidates:
                            # FILTRADO MEJORADO: Verificar que NO sea campo de búsqueda
                            data_tab = candidate.get_attribute('data-tab')
                            
                            # Excluir específicamente campos de búsqueda
                            if data_tab == '3':
                                print(f"Campo de búsqueda excluido (data-tab=3): {selector}")
                                continue
                            
                            # Para campos con data-lexical-editor, verificar ubicación
                            if candidate.get_attribute('data-lexical-editor'):
                                # Verificar que esté en footer (área de mensaje)
                                in_footer = candidate.find_elements(By.XPATH, "./ancestor::footer")
                                in_search = candidate.find_elements(By.XPATH, "./ancestor::*[contains(@class, 'search') or contains(@data-testid, 'search')]")
                                
                                if in_search and not in_footer:
                                    print(f"Campo lexical en área de búsqueda excluido: {selector}")
                                    continue
                            
                            # Verificar que el elemento esté visible y clickeable
                            if candidate.is_displayed():
                                try:
                                    WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable(candidate)
                                    )
                                    print(f"Chat abierto correctamente con: {selector}")
                                    return True
                                except TimeoutException:
                                    continue
                    
                    except Exception as e:
                        print(f"Error con selector {selector}: {e}")
                        continue
                
                # Si no encontró nada, esperar y reintentar
                if attempt < 2:
                    print("Campo no encontrado, esperando y reintentando...")
                    time.sleep(3)
                    # Refrescar página en segundo intento
                    if attempt == 1:
                        print("Refrescando página...")
                        self.driver.refresh()
                        time.sleep(5)
            
            # Verificar número inválido
            invalid_indicators = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'phone number is invalid')]"
            )
            
            if invalid_indicators:
                print(f"Número inválido: {phone_number}")
                return False
            
            print(f"No se pudo abrir chat después de 3 intentos: {phone_number}")
            return False
            
        except Exception as e:
            print(f"Error abriendo chat {phone_number}: {e}")
            return False

    def send_text_message(self, message):
        """Envia mensaje de texto con priorizacion de data-tab='10' y filtrado de busqueda"""
        try:
            # PASO 1: Encontrar campo de mensaje con filtrado mejorado
            selectors = [
                # PRIORIDAD 1: Campo específico de mensaje (data-tab='10')
                "//div[@contenteditable='true'][@data-tab='10']",
                # PRIORIDAD 2: Campo moderno EN FOOTER específicamente
                "//footer//div[@role='textbox'][@data-lexical-editor='true']",
                # PRIORIDAD 3: Campo por aria-label
                "//div[contains(@aria-label, 'Type a message')][@contenteditable='true']",
                # PRIORIDAD 4: Campo genérico en footer
                "//footer//div[@contenteditable='true']"
            ]
            
            message_box = None
            for selector in selectors:
                try:
                    candidates = self.driver.find_elements(By.XPATH, selector)
                    
                    for candidate in candidates:
                        # FILTRADO: Excluir explicitamente campos de busqueda
                        data_tab = candidate.get_attribute('data-tab')

                        # Excluir campos de búsqueda
                        if data_tab == '3':
                            print(f"Campo de busqueda excluido en envio: {selector}")
                            continue
                        
                        # Para campos lexical, verificar ubicación estricta
                        if candidate.get_attribute('data-lexical-editor'):
                            # DEBE estar en footer
                            in_footer = candidate.find_elements(By.XPATH, "./ancestor::footer")
                            if not in_footer:
                                print(f"Campo lexical fuera de footer excluido: {selector}")
                                continue

                        # Verificar que es un campo valido para mensajes
                        if candidate.is_displayed():
                            try:
                                WebDriverWait(self.driver, 2).until(
                                    EC.element_to_be_clickable(candidate)
                                )
                                message_box = candidate
                                print(f"Campo de mensaje encontrado: {selector}")
                                break
                            except TimeoutException:
                                continue
                
                except Exception as e:
                    print(f"Error con selector {selector}: {e}")
                    continue
        
            if not message_box:
                print("Campo de mensaje no encontrado")
                return False
            
            # PASO 2: Enviar mensaje con limpieza previa
            try:
                # Click y limpieza
                self.driver.execute_script("arguments[0].focus();", message_box)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", message_box)
                time.sleep(0.5)
                
                # Limpiar campo completamente
                message_box.send_keys(Keys.CONTROL + "a")
                time.sleep(0.2)
                message_box.send_keys(Keys.DELETE)
                time.sleep(0.5)
                
                # Escribir mensaje
                message_box.send_keys(message)
                time.sleep(1)
                
                # Enviar
                message_box.send_keys(Keys.ENTER)
                time.sleep(3)  # Tiempo aumentado para confirmación
                
                print("Mensaje enviado")
                return True
                
            except Exception as e:
                print(f"Error enviando mensaje: {e}")
                return False
            
        except Exception as e:
            print(f"Error en send_text_message: {e}")
            return False

    def _debug_message_fields_simple(self):
        """Debug simplificado para campos de mensaje"""
        try:
            print("=== DEBUG SIMPLE: Campos disponibles ===")
            
            # Buscar todos los campos editables
            editable_fields = self.driver.find_elements(By.XPATH, "//div[@contenteditable='true'] | //div[@role='textbox']")
            
            print(f"Total campos editables: {len(editable_fields)}")
            
            for i, field in enumerate(editable_fields[:5], 1):  # Solo primeros 5
                try:
                    data_tab = field.get_attribute('data-tab') or 'N/A'
                    aria_label = field.get_attribute('aria-label') or 'N/A'
                    data_lexical = 'SI' if field.get_attribute('data-lexical-editor') else 'NO'
                    visible = field.is_displayed()
                    
                    # Verificar si está en footer
                    in_footer = len(field.find_elements(By.XPATH, "./ancestor::footer")) > 0
                    
                    print(f"  Campo {i}: data-tab={data_tab}, lexical={data_lexical}, visible={visible}, footer={in_footer}")
                    
                except Exception as e:
                    print(f"  Campo {i}: Error - {e}")
            
            print("=== FIN DEBUG ===")
            
        except Exception as e:
            print(f"Error en debug: {e}")

    def _wait_for_message_load(self):
        """Espera a que se cargue completamente la interfaz de mensajes"""
        try:
            print("Esperando carga completa de interfaz...")
            
            # Esperar que desaparezcan indicadores de carga
            try:
                WebDriverWait(self.driver, 5).until_not(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'loading')]"))
                )
            except TimeoutException:
                pass  # No hay indicadores de carga
            
            # Esperar que aparezca el footer (área de mensaje)
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, "//footer"))
                )
            except TimeoutException:
                print("Footer no encontrado en tiempo esperado")
            
            time.sleep(2)  # Tiempo adicional para estabilización
            print("Interfaz cargada")
            return True
            
        except Exception as e:
            print(f"Error esperando carga: {e}")
            return False
    
    def send_files(self, file_paths, file_type="image"):
        """Envia archivos con logica optimizada y manejo robusto de errores"""
        try:
            if not file_paths:
                print("No hay archivos para enviar")
                return True
                
            print(f"Enviando {len(file_paths)} archivo(s) de tipo {file_type}")
            
            # PASO 1: Validar archivos antes de intentar enviarlos
            valid_paths = self._validate_file_paths(file_paths)
            if not valid_paths:
                print("ERROR: No hay archivos validos para enviar")
                return False
            
            # PASO 2: Buscar y hacer clic en boton de adjuntar
            attach_button = self._find_attach_button()
            if not attach_button:
                return False
            
            if not self._click_attach_button(attach_button):
                return False
            
            # PASO 3: Buscar input de archivo o boton especifico del tipo
            file_input = self._find_file_input(file_type)
            if not file_input:
                return False
            
            # PASO 4: Enviar archivos al input
            if not self._send_files_to_input(file_input, valid_paths):
                return False
            
            # PASO 5: Buscar y hacer clic en boton de enviar
            return self._send_files_final()
            
        except Exception as e:
            print(f"ERROR critico en send_files: {e}")
            return False

    def _validate_file_paths(self, file_paths):
        """Valida que los archivos existan y sean accesibles"""
        valid_paths = []
        
        for path in file_paths:
            try:
                abs_path = os.path.abspath(path)
                
                if os.path.exists(abs_path) and os.path.isfile(abs_path):
                    valid_paths.append(abs_path)
                    print(f"Archivo valido: {os.path.basename(abs_path)}")
                else:
                    print(f"Archivo no encontrado: {path}")
                    
            except Exception as e:
                print(f"Error validando archivo {path}: {e}")
    
        return valid_paths
 
    def _find_attach_button(self):
        """Busca el boton de adjuntar con estrategia optimizada"""
        print("Buscando boton de adjuntar...")
        
        # Selectores actualizados: Agregue selectores mas modernos y genericos
        selectors = [
            # Selectores especificos originales
            "//div[@title='Attach']",
            "//span[@data-icon='attach-menu-plus']/..",
            "//span[@data-icon='plus']/..",
            "//span[@data-icon='clip']/..",
            "//div[@role='button'][contains(@aria-label, 'Attach')]",
            
            # Selectores actualizados mas modernos y genericos
            "//button[@title='Attach' or @title='Adjuntar']",
            "//div[@role='button'][contains(@aria-label, 'Adjuntar')]",
            "//span[@data-icon='attach']/..",
            "//div[@role='button'][contains(@title, 'ttach')]",
            "//span[contains(@data-icon, 'plus')]/..",
            "//span[contains(@data-icon, 'clip')]/..",
            "//span[contains(@data-icon, 'attach')]/..",
            "//div[@role='button'][contains(@class, 'x1c4vz4f')]",  # Clase comun de botones WA
            "//footer//div[@role='button'][position()=1]",  # Primer boton en footer
            "//div[contains(@class, '_amie')]//div[@role='button'][1]"  # Area de input
        ]
        
        # Intentos con timeouts progresivos
        timeouts = [2, 3, 5]
        
        for attempt, timeout in enumerate(timeouts, 1):
            print(f"Intento {attempt} con timeout {timeout}s...")
            
            for i, selector in enumerate(selectors):
                try:
                    elements = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"Boton de adjuntar encontrado: selector {i+1}")
                            return element   
                                                    
                except TimeoutException:
                    continue
                except Exception as e:
                    print(f"Error con selector {i+1}: {e}")
                    continue
        
        # Entre intentos, hacer scroll y esperar
        if attempt < len(timeouts):
            print("Haciendo scroll y esperando...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
    
        # Debug si no se encuentra
        self._debug_attach_button()
        return None

    def _debug_attach_button(self):
        """Debug especifico para el boton de adjuntar"""
        try:
            print("=== DEBUG: Boton de adjuntar ===")
            
            # Buscar botones genericos
            buttons = self.driver.find_elements(By.XPATH, "//div[@role='button'] | //button")
            attach_candidates = []
            
            for btn in buttons:
                try:
                    title = btn.get_attribute('title') or ''
                    aria_label = btn.get_attribute('aria-label') or ''
                    class_name = btn.get_attribute('class') or ''
                    
                    combined_text = (title + aria_label + class_name).lower()
                    
                    if any(keyword in combined_text for keyword in ['attach', 'adjuntar', 'clip']):
                        attach_candidates.append({
                            'element': btn,
                            'title': title,
                            'aria_label': aria_label,
                            'visible': btn.is_displayed(),
                            'enabled': btn.is_enabled()
                        })
                except:
                    continue
            
            print(f"Candidatos para boton adjuntar: {len(attach_candidates)}")
            for i, candidate in enumerate(attach_candidates[:5]):  # Solo primeros 5
                print(f"  {i+1}. title='{candidate['title']}', aria='{candidate['aria_label']}', "
                      f"visible={candidate['visible']}, enabled={candidate['enabled']}")
            
            print("=== FIN DEBUG ===")
            
        except Exception as e:
            print(f"Error en debug: {e}")

    def _click_attach_button(self, button):
        """Hace clic en el boton de adjuntar de forma robusta"""
        try:
            print("Haciendo clic en boton de adjuntar...")
            
            # Asegurar que el elemento este visible
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(0.5)
            
            # Intentar clic normal primero
            try:
                button.click()
                print("Clic normal exitoso")
            except Exception:
                # Fallback con JavaScript
                print("Intentando clic con JavaScript...")
                self.driver.execute_script("arguments[0].click();", button)
                print("Clic JavaScript exitoso")
            
            # Esperar a que aparezca el menu
            time.sleep(3)
            
            # Verificar que el menu aparecio
            menu_indicators = [
                "//span[@data-icon='image']",
                "//span[@data-icon='document']",
                "//input[@type='file']",
                "//div[contains(@aria-label, 'Photos')]",
                "//div[contains(@aria-label, 'Document')]"
            ]
            
            for indicator in menu_indicators:
                if self.driver.find_elements(By.XPATH, indicator):
                    print("Menu de adjuntar aparecio")
                    return True
            
            print("Menu de adjuntar no detectado, continuando...")
            return True
            
        except Exception as e:
            print(f"Error haciendo clic en boton adjuntar: {e}")
            return False

    def _find_file_input(self, file_type):
        """Busca el input de archivo segun el tipo especificado"""
        print(f"Buscando input para {file_type}...")
        
        if file_type == "image":
            strategies = [
                # Estrategia 1: Buscar input de imagen directamente
                ("Input imagen directo", [
                    "//input[contains(@accept, 'image')]",  # Corregido: removed * 
                    "//input[@type='file'][contains(@accept, 'image')]"
                ]),
                # Estrategia 2: Hacer clic en boton de fotos
                ("Boton Photos/Fotos", [
                    "//span[@data-icon='image']/..",
                    "//div[contains(@title, 'Photos') or contains(@title, 'Fotos')]",
                    "//div[contains(@aria-label, 'Photos') or contains(@aria-label, 'Fotos')]"
                ])
            ]
        else:  # document/pdf
            strategies = [
                # Estrategia 1: Input generico
                ("Input documento directo", [
                    "//input[@type='file']"
                ]),
                # Estrategia 2: Hacer clic en boton de documentos
                ("Boton Document/Documento", [
                    "//span[@data-icon='document']/..",
                    "//div[contains(@title, 'Document') or contains(@title, 'Documento')]",
                    "//div[contains(@aria-label, 'Document') or contains(@aria-label, 'Documento')]"
                ])
            ]
        
        # Ejecutar estrategias
        for strategy_name, selectors in strategies:
            print(f"Probando estrategia: {strategy_name}")
            
            for selector in selectors:
                try:
                    if selector.startswith("//input"):
                        # Input directo
                        inputs = self.driver.find_elements(By.XPATH, selector)
                        for inp in inputs:
                            if inp.is_displayed() or inp.get_attribute('type') == 'file':
                                print(f"Input encontrado: {selector}")
                                return inp
                    else:
                        # Boton que activa input
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                try:
                                    WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable(element)
                                    )
                                    print(f"Haciendo clic en: {selector}")
                                    self.driver.execute_script("arguments[0].click();", element)
                                    time.sleep(2)
                                    
                                    # Buscar input despues del clic
                                    file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                                    print("Input encontrado despues del clic")
                                    return file_input
                                    
                                except Exception as e:
                                    print(f"Error con elemento: {e}")
                                    continue
                                    
                except Exception as e:
                    print(f"Error con selector {selector}: {e}")
                    continue
    
        print(f"No se encontro input para {file_type}")
        return None

    def _send_files_to_input(self, file_input, file_paths):
        """Envia archivos al input CON MANEJO DE UNICODE"""
        try:
            print(f"Enviando {len(file_paths)} archivo(s) al input...")
            
            # SOLUCION: Preparar rutas con manejo de codificación
            safe_paths = []
            for path in file_paths:
                try:
                    # Asegurar que la ruta esté en formato correcto para Selenium
                    if os.name == 'nt':  # Windows
                        # Convertir a ruta absoluta y normalizar
                        normalized_path = os.path.normpath(os.path.abspath(path))
                        safe_paths.append(normalized_path)
                    else:
                        safe_paths.append(path)
                except Exception as e:
                    print(f"Error normalizando ruta {path}: {e}")
                    continue
            
            if not safe_paths:
                print("ERROR: No hay rutas válidas después de normalización")
                return False
            
            # Preparar string de rutas (separadas por \n para múltiples archivos)
            try:
                paths_string = '\n'.join(safe_paths)
                print(f"Rutas preparadas: {len(safe_paths)} archivos")
                
                # Enviar rutas al input con manejo de errores
                file_input.send_keys(paths_string)
                print("Archivos enviados al input exitosamente")
                
            except UnicodeEncodeError as unicode_error:
                print(f"Error de Unicode enviando rutas: {unicode_error}")
                
                # FALLBACK: Enviar archivos uno por uno
                print("Intentando envío individual de archivos...")
                for i, path in enumerate(safe_paths):
                    try:
                        if i > 0:
                            file_input.send_keys('\n')  # Separador para múltiples archivos
                        file_input.send_keys(path)
                        print(f"Archivo {i+1} enviado individualmente")
                    except Exception as individual_error:
                        print(f"Error enviando archivo individual {path}: {individual_error}")
                        continue
            
            # Esperar tiempo adaptativo según cantidad de archivos
            wait_time = min(3 + len(safe_paths), 10)  # Entre 3 y 10 segundos
            print(f"Esperando {wait_time}s para carga de archivos...")
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            print(f"Error enviando archivos al input: {e}")
            return False
    
    def _send_files_final(self):
        """Envia los archivos haciendo clic en el boton de enviar"""
        print("Buscando boton de enviar...")
        
        send_selectors = [
            "//span[@data-icon='send']/..",
            "//div[@role='button'][@aria-label='Send' or @aria-label='Enviar']",
            "//button[contains(@aria-label, 'Send') or contains(@aria-label, 'Enviar')]",
            "//div[@title='Send' or @title='Enviar']",
            # Agregue mas selectores especificos para el boton enviar
            "//span[@data-icon='send-light']/..",
            "//button[@aria-label='Send']",
            "//button[@aria-label='Enviar']",
            "//div[contains(@class, 'send') and @role='button']",
            "//footer//button[last()]",  # Ultimo boton en footer
            "//div[@role='button'][contains(@class, '_4sWnG')]"  # Clase comun del boton enviar
        ]
        
        # Buscar boton de enviar con timeout mas largo
        for selector in send_selectors:
            try:
                print(f"Probando selector: {selector}")
                candidates = WebDriverWait(self.driver, 8).until(  # Aumente timeout
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                
                for candidate in candidates:
                    if candidate.is_displayed():
                        try:
                            WebDriverWait(self.driver, 5).until(  # Aumente timeout
                                EC.element_to_be_clickable(candidate)
                            )
                            print("Boton enviar encontrado y clickeable")
                            
                            # Hacer clic con scroll previo
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", candidate)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", candidate)
                            print("Archivos enviados exitosamente")
                            
                            time.sleep(4)  # Esperar confirmacion mas tiempo
                            return True
                            
                        except TimeoutException:
                            print(f"Elemento no clickeable: {selector}")
                            continue
                        
            except TimeoutException:
                print(f"Timeout en selector: {selector}")
                continue
            except Exception as e:
                print(f"Error con selector enviar: {e}")
                continue
        
        # Fallback mejorado: buscar input file y enviar Enter
        print("Boton enviar no encontrado, buscando input file para Enter...")
        try:
            # Buscar el input file que usamos antes
            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            for file_input in file_inputs:
                try:
                    # Verificar que el input este asociado con archivos cargados
                    files_value = file_input.get_attribute('files')
                    if files_value or file_input.get_attribute('value'):
                        print("Input file con archivos encontrado, enviando Enter...")
                        file_input.send_keys(Keys.ENTER)
                        time.sleep(4)
                        print("Enter enviado al input file")
                        return True
                except Exception as e:
                    print(f"Error con input file: {e}")
                    continue
        except Exception as e:
            print(f"Error buscando input file: {e}")
    
        # Ultimo fallback: Enter en body
        print("Ultimo recurso: Enter en body...")
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ENTER)
            time.sleep(4)
            print("Enter enviado en body")
            return True
        except Exception as e:
            print(f"Error enviando Enter en body: {e}")
            return False
        
    def send_complete_message(self, phone_number, message, image_paths=None, pdf_paths=None):
        """Envía un mensaje completo"""
        try:
            # PASO 1: Abrir chat con el enlace directo
            if not self.open_chat_with_link(phone_number):
                return False
            
            # PASO 2: Esperar carga completa antes de proceder
            self._wait_for_message_load()
            
            # PASO 3: Enviar mensaje de texto
            if message and not self.send_text_message(message):
                print("Error enviando texto, pero se continuará con los archivos...")
            
            # PASO 4: Enviar imágenes
            if image_paths:
                print("Preparando envío de imágenes...")
                time.sleep(2)
                if not self.send_files(image_paths, "image"):
                    print("Error enviando imágenes.")
                else:
                    time.sleep(3)
                    # Resetear estado del DOM después de imágenes
                    self._reset_dom_state()

            # PASO 5: Enviar PDFs (SIN pre-procesamiento)
            if pdf_paths:
                print("Preparando envío de PDFs...")
                time.sleep(2)
                if not self.send_files(pdf_paths, "document"):
                    print("Error enviando PDFs.")
            
            print("Mensaje completo procesado.")
            return True
            
        except Exception as e:
            print(f"Error crítico enviando mensaje completo a {phone_number}: {e}")
            return False
        
    def _reset_dom_state(self):
        """Resetea el estado del DOM después de enviar archivos"""
        try:
            print("Reseteando estado del DOM...")
            
            # Hacer scroll para refrescar elementos
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Forzar reflow del DOM
            self.driver.execute_script("""
                var elements = document.querySelectorAll('input[type="file"]');
                elements.forEach(function(el) {
                    if (el.offsetParent === null) {
                        el.style.display = 'none';
                        el.offsetHeight; // trigger reflow
                        el.style.display = '';
                    }
                });
            """)
            
            time.sleep(2)
            print("Estado del DOM reseteado")
            
        except Exception as e:
            print(f"Error reseteando DOM: {e}")

    def _send_files_to_input(self, file_input, file_paths):
        """Envía archivos al input de forma simple"""
        try:
            print(f"Enviando {len(file_paths)} archivo(s) al input...")
            
            # Preparar rutas simples
            safe_paths = []
            for path in file_paths:
                try:
                    if os.name == 'nt':  # Windows
                        normalized_path = os.path.normpath(os.path.abspath(path))
                        safe_paths.append(normalized_path)
                    else:
                        safe_paths.append(path)
                except Exception as e:
                    print(f"Error normalizando ruta {path}: {e}")
                    continue
            
            if not safe_paths:
                print("ERROR: No hay rutas válidas después de normalización")
                return False
            
            # Envío directo sin manejo de Unicode especial
            try:
                paths_string = '\n'.join(safe_paths)
                print(f"Rutas preparadas: {len(safe_paths)} archivos")
                
                # Enviar rutas al input
                file_input.send_keys(paths_string)
                print("Archivos enviados al input exitosamente")
                
            except Exception as send_error:
                print(f"Error enviando archivos: {send_error}")
                return False
            
            # Esperar tiempo adaptativo según cantidad de archivos
            wait_time = min(3 + len(safe_paths), 10)
            print(f"Esperando {wait_time}s para carga de archivos...")
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            print(f"Error enviando archivos al input: {e}")
            return False
    
    def debug_page_state(self):
        """Funcion para debuggear el estado de la pagina"""
        try:
            print("Estado actual de la pagina:")
            print(f"URL: {self.driver.current_url}")
            print(f"Titulo: {self.driver.title}")
            
            # Buscar elementos comunes
            elements_to_check = [
                ("Canvas QR", "//canvas"),
                ("Campo busqueda 1", "//div[@contenteditable='true'][@data-tab='3']"),
                ("Campo busqueda 2", "//div[@title='Search input textbox']"),
                ("Campo mensaje 1", "//div[@contenteditable='true'][@data-tab='10']"),
                ("Campo mensaje 2", "//div[contains(@aria-label, 'Type a message')]"),
                ("Boton adjuntar", "//div[@title='Attach']")
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
        """Cierra el navegador"""
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
        """Mantiene la sesion activa"""
        try:
            self.driver.execute_script("console.log('keep alive');")
            return True
        except Exception:
            return False
