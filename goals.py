from playwright.sync_api import sync_playwright
import time

# Hedef site
URL = "https://taraftarium24.xyz/"

def save_page_source():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Siteye gidiliyor: {URL}")
        page.goto(URL, timeout=60000)
        
        # Sayfanın tam yüklenmesi için biraz bekle
        print("Sayfa yükleniyor...")
        time.sleep(5)
        
        # Tüm HTML içeriğini al
        content = page.content()
        
        # Dosyaya kaydet
        with open("sayfa_kaynagi.txt", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("✅ Kaynak kodları 'sayfa_kaynagi.txt' dosyasına kaydedildi.")
        print("Lütfen bu dosyanın içeriğini kopyalayıp yapıştır.")
        
        browser.close()

if __name__ == "__main__":
    save_page_source()
