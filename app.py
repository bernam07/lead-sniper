import customtkinter as ctk
import pandas as pd
import threading
from datetime import datetime
from scraper_engine import run_scraper 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GMapScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("G-Maps Lead Extractor Pro")
        self.geometry("600x450")
        self.resizable(False, False)
        self.label_title = ctk.CTkLabel(self, text="📍 G-Maps Lead Extractor", font=("Roboto", 24, "bold"))
        self.label_title.pack(pady=20)
        self.entry_query = ctk.CTkEntry(self, placeholder_text="Ex: Restaurantes em Lisboa", width=400)
        self.entry_query.pack(pady=10)
        self.label_limit = ctk.CTkLabel(self, text="Quantidade de Leads:")
        self.label_limit.pack()
        self.slider_limit = ctk.CTkSlider(self, from_=5, to=50, number_of_steps=9, width=400)
        self.slider_limit.set(10)
        self.slider_limit.pack(pady=5)
        self.checkbox_headless = ctk.CTkCheckBox(self, text="Modo Invisível (Headless)")
        self.checkbox_headless.pack(pady=10)
        self.btn_start = ctk.CTkButton(self, text="INICIAR EXTRAÇÃO", command=self.start_thread, height=40, font=("Roboto", 14, "bold"))
        self.btn_start.pack(pady=20)
        self.textbox_log = ctk.CTkTextbox(self, width=500, height=100)
        self.textbox_log.pack(pady=10)
        self.textbox_log.insert("0.0", "Pronto para iniciar...\n")

    def log(self, message):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")

    def start_thread(self):
        threading.Thread(target=self.run_process).start()

    def run_process(self):
        query = self.entry_query.get()
        limit = int(self.slider_limit.get())
        headless = self.checkbox_headless.get()

        if not query:
            self.log("❌ Erro: Insira um termo de pesquisa!")
            return

        self.btn_start.configure(state="disabled", text="A extrair... Aguarde")
        self.log(f"🔎 A iniciar pesquisa por: {query} (Max: {limit})")

        try:
            data = run_scraper(query, limit, headless)
            
            if data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"leads_{timestamp}.csv"
                df = pd.DataFrame(data)
                filename = f"leads_{timestamp}.xlsx"
                df.to_excel(filename, index=False)
                self.log(f"✅ Sucesso! {len(data)} leads guardadas em:")
                self.log(f"📂 {filename}")
            else:
                self.log("⚠️ Nenhum dado encontrado.")

        except Exception as e:
            self.log(f"❌ Erro: {str(e)}")
        
        self.btn_start.configure(state="normal", text="INICIAR EXTRAÇÃO")

if __name__ == "__main__":
    app = GMapScraperApp()
    app.mainloop()
