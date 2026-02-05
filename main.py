import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÃO ---
SEARCH_QUERY = "Restaurantes em Braga"
TOTAL_RESULTS = 10  # Quantos queres sacar (para teste mete baixo)
HEADLESS = False    # Mete True para não abrir o browser visualmente

def init_driver():
    options = webdriver.ChromeOptions()
    if HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    # Truques para evitar detecção básica
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_gmaps():
    driver = init_driver()
    driver.get("https://www.google.com/maps")
    time.sleep(3)

    # 1. Aceitar Cookies (Google EU) - Tenta clicar se aparecer
    try:
        driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Aceitar tudo')]").click()
        time.sleep(2)
    except:
        pass

    # 2. Pesquisar
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.send_keys(SEARCH_QUERY)
    search_box.send_keys(Keys.ENTER)
    time.sleep(5)

    # 3. Scroll Infinito (O Segredo)
    # Precisamos de encontrar o painel lateral que tem o scroll
    print("A iniciar extração...")
    
    scraped_data = []
    
    # Loop para garantir que carregamos X resultados
    # Nota: O Google Maps é complexo, classes mudam. Usamos seletores genéricos.
    while len(scraped_data) < TOTAL_RESULTS:
        # Encontrar os cartões de negócio visíveis (classe 'hfpxzc' é o link do negócio geralmente)
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        
        # Scroll down no painel lateral
        if elements:
            driver.execute_script("arguments[0].scrollIntoView();", elements[-1])
            time.sleep(2)
        
        # Se chegarmos ao fim da lista disponível ou não houver mais
        current_len = len(elements)
        if current_len == len(scraped_data):
            break # Não carregou mais nada

        # Vamos iterar sobre o que já carregou
        # ATENÇÃO: Num scraper real para venda, entraríamos em cada link para sacar telefone/site.
        # Aqui fazemos o básico: Nome e Link.
        
        # Para evitar duplicados, pegamos tudo de novo e filtramos
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        
        for el in elements:
            link = el.get_attribute("href")
            name = el.get_attribute("aria-label")
            
            if link and name and link not in [x['link'] for x in scraped_data]:
                if len(scraped_data) >= TOTAL_RESULTS:
                    break
                    
                print(f"Encontrado: {name}")
                scraped_data.append({
                    "name": name,
                    "link": link,
                    # Futuramente: Clicar no link para sacar telefone e website
                })

    driver.quit()
    return scraped_data

if __name__ == "__main__":
    data = scrape_gmaps()
    
    # Guardar em Excel/CSV (o que as empresas querem)
    df = pd.DataFrame(data)
    filename = "leads_output.csv"
    df.to_csv(filename, index=False)
    print(f"Sucesso! {len(data)} leads guardadas em {filename}")
