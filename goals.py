import re
import sys
from playwright.sync_api import sync_playwright, Error as PlaywrightError

def find_working_domain(page):
    """Verilen aralıkta çalışan ve doğru formattaki trgoals domain'ini bulur."""
    
    # Manuel kontrol (Hız için)
    MANUAL_DOMAIN = "https://trgoals1495.xyz/"
    print(f"\n🔍 Öncelikli domain deneniyor: {MANUAL_DOMAIN}")
    try:
        response = page.goto(MANUAL_DOMAIN, timeout=10000, wait_until='domcontentloaded')
        if response and response.ok:
            final_url = page.url.rstrip('/')
            print(f"✅ Öncelikli domain aktif: {final_url}")
            return final_url
    except PlaywrightError:
        print(f"⚠️ Öncelikli domain yanıt vermedi.")

    base = "https://trgoals"
    start_range = 1490
    end_range = 1530
    domain_pattern = re.compile(r'https://trgoals[0-9]+\.xyz')

    print(f"\n🔍 Otomatik arama: trgoals{start_range}.xyz → trgoals{end_range-1}.xyz")
    for i in range(start_range, end_range):
        test_domain = f"{base}{i}.xyz"
        try:
            print(f"   Kontrol ediliyor: {test_domain}...", end="\r")
            response = page.goto(test_domain, timeout=5000, wait_until='domcontentloaded')
            final_url = page.url.rstrip('/')
            
            if response and response.ok and domain_pattern.match(final_url):
                print(f"\n✅ Domain bulundu: {final_url}")
                return final_url
        except PlaywrightError:
            continue
            
    return None

def main():
    with sync_playwright() as p:
        print("🚀 Trgoals M3U8 İndirici (Akıllı Link Tarama Modu) Başlatılıyor...")
        
        browser_args = [
            '--autoplay-policy=no-user-gesture-required',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
        
        browser = p.chromium.launch(headless=True, args=browser_args)
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            ignore_https_errors=True
        )
        page = context.new_page()

        domain = find_working_domain(page)

        if not domain:
            print("\n❌ Hata: Çalışan domain bulunamadı.")
            browser.close()
            sys.exit(1)

        print(f"\n📡 Kanal listesi taranacak...")
        channels = {
            # BeinSports Kategorisi
            "yayinzirve": ("beIN Sports 1 ☪️", "BeinSports"),
            "yayininat": ("beIN Sports 1 ⭐", "BeinSports"),
            "yayin1": ("beIN Sports 1 ♾️", "BeinSports"),
            "yayinb2": ("beIN Sports 2", "BeinSports"),
            "yayinb3": ("beIN Sports 3", "BeinSports"),
            "yayinb4": ("beIN Sports 4", "BeinSports"),
            "yayinb5": ("beIN Sports 5", "BeinSports"),
            "yayinbm1": ("beIN Sports 1 Max", "BeinSports"),
            "yayinbm2": ("beIN Sports 2 Max", "BeinSports"),
            # S Sports Kategorisi
            "yayinss": ("Saran Sports 1", "S Sports"),
            "yayinss2": ("Saran Sports 2", "S Sports"),
            # Tivibu Kategorisi
            "yayint1": ("Tivibu Sports 1", "Tivibu"),
            "yayint2": ("Tivibu Sports 2", "Tivibu"),
            "yayint3": ("Tivibu Sports 3", "Tivibu"),
            # Smart Sports
            "yayinsmarts": ("Smart Sports", "Smart Sports"),
            "yayinsms2": ("Smart Sports 2", "Smart Sports"),
            # NBA
            "yayinnbatv": ("NBA TV", "NBA"),
            # Ulusal
            "yayinatv": ("ATV", "Ulusal"),
            "yayintv8": ("TV8", "Ulusal"),
            "yayintv85": ("TV8.5", "Ulusal"),
            "yayinas": ("A Spor", "Ulusal"),
            # Tabii
            "yayinex1": ("Tâbii 1", "Tabii"),
            # Euro Sport
            "yayineu1": ("Euro Sport 1", "Euro Sport"),
            "yayineu2": ("Euro Sport 2", "Euro Sport"),
        }

        m3u_content = []
        output_filename = "kanallar.m3u8"
        created = 0
        
        # --- AKILLI REGEX (UNIVERSAL PATTERN) ---
        # Bu Regex şunu der:
        # 1. Tırnak işareti (") veya (') ile başlayan,
        # 2. https:// ile devam eden,
        # 3. Arada harf/sayı olan,
        # 4. Ve kesinlikle ".sbs/" ile biten bir şey bul.
        # Değişken adı (B_URL, config, zart, zurt) umrumuzda değil.
        regex_pattern = re.compile(r'["\'](https?://[a-zA-Z0-9.-]+\.sbs/?)["\']', re.IGNORECASE)

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i}/{len(channels)}] {channel_name}...", end=' ')
                sys.stdout.flush() 

                url = f"{domain}/channel.html?id={channel_id}"
                page.goto(url, timeout=15000, wait_until='domcontentloaded')
                
                content = page.content()
                match = regex_pattern.search(content)

                if match:
                    baseurl = match.group(1)
                    # Site bazen sonuna / koymayı unutursa biz tamamlayalım
                    if not baseurl.endswith('/'):
                        baseurl += '/'
                        
                    direct_url = f"{baseurl}{channel_id}.m3u8"
                    
                    m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                    m3u_content.append(direct_url)
                    
                    print(f"-> ✅ Link: {direct_url[-35:]}...")
                    created += 1
                else:
                    print("-> ❌ .sbs uzantılı yayın linki bulunamadı.")
                
            except PlaywrightError:
                print("-> ❌ Sayfaya ulaşılamadı.")
                continue

        browser.close()

        if created > 0:
            header = f"""#EXTM3U
#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36
#EXT-X-REFERER:{domain}/
#EXT-X-ORIGIN:{domain}"""
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(header + "\n")
                f.write("\n".join(m3u_content))
            print(f"\n📂 Dosya hazır: {output_filename} ({created} kanal)")
        else:
            print("\n❌ Hiçbir kanal bulunamadı.")

if __name__ == "__main__":
    main()
