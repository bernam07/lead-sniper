import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def init_driver(headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def get_detail_text(driver, type_data):
    """
    Função auxiliar para encontrar texto dentro do painel de detalhes.
    Tenta várias estratégias para não falhar.
    """
    try:
        if type_data == "phone":
            # Estratégia 1: Botão que tenha o aria-label a começar por "Telefone:"
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Telefone:']")
                return btn.get_attribute("aria-label").replace("Telefone: ", "").strip()
            except:
                pass
            
            # Estratégia 2: Botão com ícone de telefone (data-item-id contém 'phone')
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']")
                return btn.get_attribute("aria-label").replace("Telefone: ", "").strip()
            except:
                return "N/A"

        elif type_data == "website":
            # Estratégia 1: Botão com data-item-id="authority" (Padrão do Google)
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
                return btn.get_attribute("href")
            except:
                return "N/A"
        
        elif type_data == "rating":
            try:
                # Procura o span que tem o role="img" e aria-label com "estrelas"
                span = driver.find_element(By.CSS_SELECTOR, "span[role='img'][aria-label*='estrelas']")
                return span.get_attribute("aria-label")
            except:
                return "N/A"

    except:
        return "N/A"
    return "N/A"

def run_scraper(search_query, max_results, headless=False):
    driver = init_driver(headless)
    results = []
    
    try:
        print("🌍 A abrir Google Maps Oficial...")
        driver.get("https://www.google.com/maps?hl=pt-PT") 
        
        # --- COOKIES ---
        print("🍪 A tratar dos cookies...")
        try:
            wait = WebDriverWait(driver, 5)
            accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button//span[contains(text(), 'Aceitar')]/..")))
            accept_btn.click()
            time.sleep(2) 
        except:
            pass

        # --- PESQUISA ---
        print(f"🔎 A pesquisar por: {search_query}")
        try:
            wait = WebDriverWait(driver, 10)
            input_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
        except:
            input_box = driver.find_element(By.TAG_NAME, "input")

        input_box.clear()
        input_box.send_keys(search_query)
        time.sleep(0.5)
        input_box.send_keys(Keys.ENTER)
        print("✅ Pesquisa enviada. A carregar lista...")
        time.sleep(5) 

        # --- EXTRAÇÃO PROFUNDA ---
        scraped_ids = set()
        
        while len(results) < max_results:
            # Encontra todos os cartões de negócio na lista
            elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
            valid_elements = [el for el in elements if el.get_attribute("aria-label")]
            
            if not valid_elements:
                print("⏳ A carregar mais...")
                time.sleep(2)
            
            found_new = False
            
            for index, el in enumerate(valid_elements):
                if len(results) >= max_results:
                    break
                
                try:
                    link = el.get_attribute("href")
                    name = el.get_attribute("aria-label")
                    
                    if link in scraped_ids:
                        continue
                    
                    found_new = True
                    scraped_ids.add(link)
                    
                    # --- O TRUQUE: CLICAR NO ELEMENTO ---
                    # Fazemos scroll até ele para garantir que é clicável
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                    time.sleep(1)
                    el.click()
                    
                    # Espera o painel lateral carregar os detalhes (Telefone/Site)
                    time.sleep(2.5) 
                    
                    # Extrair Dados
                    phone = get_detail_text(driver, "phone")
                    website = get_detail_text(driver, "website")
                    rating = get_detail_text(driver, "rating")
                    
                    print(f"📍 [{len(results)+1}] {name} | 📞 {phone} | 🌐 {website}")
                    
                    results.append({
                        "Business Name": name,
                        "Phone": phone,
                        "Website": website,
                        "Rating": rating,
                        "Maps Link": link
                    })
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar item: {e}")
                    continue

            # Se chegámos ao fundo dos visíveis, fazer scroll na lista
            try:
                if valid_elements:
                    driver.execute_script("arguments[0].scrollIntoView();", valid_elements[-1])
                else:
                    driver.find_element(By.CSS_SELECTOR, "div[role='feed']").send_keys(Keys.PAGE_DOWN)
            except:
                pass
                
            time.sleep(2)

            if not found_new and len(results) > 0:
                # Tenta esperar um pouco mais
                time.sleep(2)
                check = driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
                if len(check) == len(elements):
                    print("⏹️ Fim da lista.")
                    break

    except Exception as e:
        print(f"❌ Erro: {e}")
        driver.save_screenshot("erro_scraper.png")
    finally:
        driver.quit()
        
    return results