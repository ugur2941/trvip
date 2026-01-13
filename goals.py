import re
import sys
import time
from playwright.sync_api import sync_playwright, Error as PlaywrightError

def find_working_domain(page):
    """Verilen aralıkta çalışan ve doğru formattaki trgoals domain'ini bulur."""
    MANUAL_DOMAIN = "https://trgoals1495.xyz/"
    print(f"\n🔍 Öncelikli domain deneniyor: {MANUAL_DOMAIN}")
    try:
        response = page.goto(MANUAL_DOMAIN, timeout=20000, wait_until='domcontentloaded')
        if response and response.ok:
            final_url = page.url.rstrip('/')
            print(f"✅ Öncelikli domain başarıyla bulundu: {final_url}")
            return final_url
    except PlaywrightError:
        print(f"⚠️ Öncelikli domain'e bağlanılamadı. Otomatik arama başlatılacak...")

    base = "https://trgoals"
    start_range = 1495
    end_range = 2500
    domain_pattern = re.compile(r'https://trgoals[0-9]+\.xyz')

    print(f"\n🔍 Otomatik arama: trgoals{start_range}.xyz → trgoals{end_range-1}.xyz")
    for i in range(start_range, end_range):
        test_domain = f"{base}{i}.xyz"
        try:
            response = page.goto(test_domain, timeout=10000, wait_until='domcontentloaded')
            final_url = page.url.rstrip('/')
            if response and response.ok and domain_pattern.match(final_url):
                print(f"✅ Otomatik arama ile domain bulundu: {final_url}")
                return final_url
        except PlaywrightError:
            continue
    return None

def main():
    with sync_playwright() as p:
        print("🚀 Playwright ile Akıllı Ağ Dinleyici (Sniffer) Başlatılıyor...")
        
        # GitHub Actions ortamı için gerekli argümanlar
        browser_args = [
            '--autoplay-policy=no-user-gesture-required', # Otomatik oynatma izni buraya taşındı
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]

        # Headless mode CI ortamında True olmalıdır
        browser = p.chromium.launch(headless=True, args=browser_args)
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            ignore_https_errors=True
        )
        
        # Hata veren satır kaldırıldı: context.grant_permissions(['autoplay']) 
        
        page = context.new_page()

        domain = find_working_domain(page)
        if not domain:
            print("❌ UYARI: Hiçbir geçerli domain bulunamadı - işlem sonlandırılacak.")
            browser.close()
            sys.exit(1)

        channels = {
            "yayinzirve": ("beIN Sports 1 ☪️", "BeinSports"),
            "yayininat": ("beIN Sports 1 ⭐", "BeinSports"),
            "yayin1": ("beIN Sports 1 ♾️", "BeinSports"),
            "yayinb2": ("beIN Sports 2", "BeinSports"),
            "yayinb3": ("beIN Sports 3", "BeinSports"),
            "yayinb4": ("beIN Sports 4", "BeinSports"),
            "yayinb5": ("beIN Sports 5", "BeinSports"),
            "yayinbm1": ("beIN Sports 1 Max", "BeinSports"),
            "yayinbm2": ("beIN Sports 2 Max", "BeinSports"),
            "yayinss": ("Saran Sports 1", "S Sports"),
            "yayinss2": ("Saran Sports 2", "S Sports"),
            "yayint1": ("Tivibu Sports 1", "Tivibu"),
            "yayint2": ("Tivibu Sports 2", "Tivibu"),
            "yayint3": ("Tivibu Sports 3", "Tivibu"),
            "yayint4": ("Tivibu Sports 4", "Tivibu"),
            "yayinsmarts": ("Smart Sports", "Smart Sports"),
            "yayinsms2": ("Smart Sports 2", "Smart Sports"),
            "yayinnbatv": ("NBA TV", "NBA"),
            "yayinatv": ("ATV", "Ulusal"),
            "yayintv8": ("TV8", "Ulusal"),
            "yayintv85": ("TV8.5", "Ulusal"),
            "yayinas": ("A Spor", "Ulusal"),
            "yayinex1": ("Tâbii 1", "Tabii"),
            "yayinex2": ("Tâbii 2", "Tabii"),
            "yayinex3": ("Tâbii 3", "Tabii"),
            "yayinex4": ("Tâbii 4", "Tabii"),
            "yayinex5": ("Tâbii 5", "Tabii"),
            "yayinex6": ("Tâbii 6", "Tabii"),
            "yayinex7": ("Tâbii 7", "Tabii"),
            "yayinex8": ("Tâbii 8", "Tabii"),
            "yayintrt1": ("TRT 1", "TRT"),
            "yayintrtspor": ("TRT Spor", "TRT"),
            "yayintrtspor2": ("TRT Spor 2", "TRT"),
            "yayineu1": ("Euro Sport 1", "Euro Sport"),
            "yayineu2": ("Euro Sport 2", "Euro Sport"),
        }

        m3u_content = []
        output_filename = "kanallar.m3u8"
        created = 0
        
        print(f"\n📺 {len(channels)} kanal taranıyor (Ağ İzleme Modu)...")

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            print(f"[{i}/{len(channels)}] {channel_name}...", end=' ')
            sys.stdout.flush() # Logların anlık düşmesi için
            
            found_m3u8 = None

            def handle_request(request):
                nonlocal found_m3u8
                try:
                    if ".m3u8" in request.url and found_m3u8 is None:
                        found_m3u8 = request.url
                except:
                    pass

            # Listener ekle
            page.on("request", handle_request)

            try:
                url = f"{domain}/channel.html?id={channel_id}"
                # Sayfaya git
                page.goto(url, timeout=20000, wait_until='domcontentloaded')
                
                # Linkin ağa düşmesi için bekle (Maksimum 8 saniye)
                start_time = time.time()
                while time.time() - start_time < 8:
                    if found_m3u8:
                        break
                    page.wait_for_timeout(250)

                # Temizlik
                page.remove_listener("request", handle_request)

                if found_m3u8:
                    print("-> ✅ YAKALANDI")
                    m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                    m3u_content.append(found_m3u8)
                    created += 1
                else:
                    print("-> ❌ Link bulunamadı.")

            except Exception as e:
                page.remove_listener("request", handle_request)
                print(f"-> ❌ Hata: {str(e)[:50]}...")
                continue

        browser.close()

        if created > 0:
            header = f"""#EXTM3U
#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36
#EXT-X-REFERER:{domain}/
#EXT-X-ORIGIN:{domain}"""
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(header)
                f.write("\n") 
                f.write("\n".join(m3u_content))
            print(f"\n📂 {created} kanal başarıyla '{output_filename}' dosyasına kaydedildi.")
        else:
            print("\nℹ️  Hiçbir m3u8 bağlantısı yakalanamadı.")

if __name__ == "__main__":
    main()
