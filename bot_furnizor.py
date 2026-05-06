import os
import pandas as pd
from playwright.sync_api import Playwright, sync_playwright

# Codul citește variabilele din sistemul GitHub (Secrets)
DAINESE_USER = os.environ.get('DAINESE_USER')
DAINESE_PASS = os.environ.get('DAINESE_PASS')

def run(playwright: Playwright) -> None:
    # Pe server folosim headless=True pentru că nu există monitor
    browser = playwright.chromium.launch(headless=True) 
    context = browser.new_context()
    page = context.new_page()
    
    try:
        print("🚀 Pasul 1: Logare pe Dainese...")
        page.goto("https://dainese.elasticsuite.com/")
        page.locator('input[name="username"]').fill(DAINESE_USER)
        page.locator('input[name="password"]').fill(DAINESE_PASS)
        page.get_by_role("button", name="Login").click()
        
        print("⌛ Pasul 2: Navigare către catalog...")
        page.wait_for_selector(".sc-cbkKFq.eUtQjk", timeout=30000)
        page.locator(".sc-cbkKFq.eUtQjk").first.click()
        page.wait_for_timeout(5000)
        
        print("🖱️ Pasul 3: Export XLSX...")
        page.get_by_role("button").nth(4).click()
        page.locator("span").filter(has_text="●Menu").nth(4).click()
        page.get_by_label("●Menu ●").get_by_text("Export XLSX").click()
        page.get_by_role("radio", name="Full Catalog").check()
        page.get_by_role("radio", name="All Product Data").check()
        
        print("📥 Pasul 4: Descărcare...")
        with page.expect_download(timeout=120000) as download_info:
            page.locator("span").filter(has_text="●Export XLSX").nth(1).click()
        
        download = download_info.value
        temp_path = "temp_raw.xlsx"
        download.save_as(temp_path)

        # --- PRELUCRARE TABEL ---
        print("📊 Pasul 5: Eliminare coloană Compatibility...")
        df = pd.read_excel(temp_path)
        if 'Compatibility' in df.columns:
            df.drop(columns=['Compatibility'], inplace=True)
            print("🗑️ Succes: Coloana a fost ștearsă.")

        # Salvăm fișierul final chiar aici, în folderul de bază
        df.to_excel("feed_dainese_final.xlsx", index=False)
        print("✨ GATA! Fișierul a fost creat pe server.")

    except Exception as e:
        print(f"❌ Eroare în timpul rulării: {e}")
        exit(1)
    finally:
        if os.path.exists("temp_raw.xlsx"):
            os.remove("temp_raw.xlsx")
        context.close()
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
