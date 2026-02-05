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

def extract_details(driver):
    """Tenta extrair telefone e site do painel de detalhes aberto"""
    phone = "N/A"
    website = "N/A"
    
    try:
        # Espera o painel carregar um pouco
        time.sleep(1)
        
        # Estratégia: Procurar botões que contêm imagens específicas ou texto
        # O Google muda classes constantemente, o melhor é procurar por atributos
        
        # Tentar achar website (geralmente tem texto "Website" ou ícone de globo)
        try:
            web_btn = driver.find_element(By.CSS_SELECTOR, '[data-item-id="authority"]')
            website = web_btn.get_attribute("href")
            if not website: # Às vezes está no texto
                website = web_btn.text
        except:
            pass

        # Tentar achar telefone (geralmente data-item-id começa com phone ou tem ícone de telefone)
        try:
            # Procura qualquer botão que o texto comece por +351 ou similar, ou pelo ID do elemento
            # Esta classe 'CsEnBe' é comum para linhas de informação, mas pode mudar.
            # Vamos tentar pelo atributo 'aria-label' que costuma dizer "Telefone: ..."
            phone_btn = driver.find_element(By.CSS_SELECTOR, '[data-item-id*="phone"]')
            phone = phone_btn.get_attribute("aria-label").replace("Telefone: ", "").strip()
        except:
            pass
            
    except Exception as e:
        print(f"Erro ao extrair detalhes: {e}")
        
    return phone, website

def run_scraper(search_query, max_results, headless=False):
    driver = init_driver(headless)
    results = []
    
    try:
        driver.get("https://www.google.com/maps")
        time.sleep(3)
        
        # Aceitar Cookies (Botão "Aceitar tudo")
        try:
            driver.find_element(By.XPATH, "//button//span[contains(text(), 'Aceitar tudo')]").click()
            time.sleep(2)
        except:
            pass

        # Pesquisar
        input_box = driver.find_element(By.ID, "searchboxinput")
        input_box.send_keys(search_query)
        input_box.send_keys(Keys.ENTER)
        time.sleep(4)

        print(f"A recolher leads para: {search_query}...")

        # Loop de extração
        scraped_links = set()
        
        while len(results) < max_results:
            # Apanha todos os links visíveis na barra lateral (classe 'hfpxzc' é o link invisível sobre o card)
            elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            
            if not elements:
                print("Nenhum resultado encontrado ou fim da lista.")
                break

            for el in elements:
                if len(results) >= max_results:
                    break
                
                link = el.get_attribute("href")
                if link in scraped_links:
                    continue
                
                scraped_links.add(link)
                
                # Clicar no elemento para abrir detalhes
                driver.execute_script("arguments[0].click();", el)
                time.sleep(2) # Tempo para o painel lateral atualizar
                
                name = el.get_attribute("aria-label")
                phone, website = extract_details(driver)
                
                print(f"✅ {name} | 📞 {phone} | 🌐 {website}")
                
                results.append({
                    "Business Name": name,
                    "Phone": phone,
                    "Website": website,
                    "Google Maps Link": link
                })

            # Scroll para carregar mais (no último elemento encontrado)
            if elements:
                driver.execute_script("arguments[0].scrollIntoView();", elements[-1])
                time.sleep(2)
            else:
                break
                
    except Exception as e:
        print(f"Erro fatal: {e}")
    finally:
        driver.quit()
        
    return results
