import re
import sys
from playwright.sync_api import sync_playwright, Error as PlaywrightError

def find_working_domain(page):
    """
    Verilen aralıkta çalışan, doğru formattaki trgoals domain'ini bulur.
    Zaman aşımı süreleri artırılmış ve bot koruması önlemleri alınmıştır.
    """
    
    # Regex: https veya http, www opsiyonel, trgoals + sayılar + .xyz
    domain_pattern = re.compile(r'https?://(?:www\.)?trgoals[0-9]+\.xyz', re.IGNORECASE)

    # 1. MANUEL KONTROL (Senin çalıştığını bildiğin adres)
    MANUAL_DOMAIN = "https://trgoals1522.xyz/"
    print(f"\n🔍 Öncelikli domain deneniyor: {MANUAL_DOMAIN}")
    
    try:
        # Timeout süresini 20 saniyeye çıkardık (Yavaş siteler için)
        response = page.goto(MANUAL_DOMAIN, timeout=20000, wait_until='domcontentloaded')
        if response and response.ok:
            final_url = page.url.rstrip('/')
            
            if domain_pattern.match(final_url) and "giris" not in final_url:
                print(f"✅ Öncelikli domain aktif: {final_url}")
                return final_url
            else:
                print(f"⚠️ Öncelikli domain reddedildi (Giriş sayfası veya format dışı): {final_url}")
    except PlaywrightError as e:
        print(f"⚠️ Öncelikli domain hatası: {e}")

    # 2. OTOMATİK TARAMA (Geniş Aralık)
    base = "https://trgoals"
    start_range = 1515
    end_range = 1600 # Aralığı 1600'e kadar açtık
    
    print(f"\n🔍 Otomatik arama başlatılıyor: trgoals{start_range}.xyz → trgoals{end_range-1}.xyz")
    
    for i in range(start_range, end_range):
        test_domain = f"{base}{i}.xyz"
        try:
            print(f"   Kontrol: {test_domain}...", end=" ")
            sys.stdout.flush()
            
            try:
                # Timeout 10 saniye yaptık (Hızlı tarama ama sabırlı)
                response = page.goto(test_domain, timeout=10000, wait_until='domcontentloaded')
            except PlaywrightError:
                print("❌ Zaman Aşımı / Ulaşılamadı")
                continue

            final_url = page.url.rstrip('/')
            
            # --- KONTROLLER ---
            if not response.ok:
                print(f"❌ Hata Kodu: {response.status}")
                continue
                
            if "giris" in final_url:
                print(f"⚠️ Giriş Sayfası (Red)")
                continue
                
            if not domain_pattern.match(final_url):
                print(f"⚠️ Alakasız Site: {final_url}")
                continue

            # Eğer buraya geldiyse doğru sitedir
            print(f"✅ BAŞARILI!")
            print(f"   🎯 Tespit Edilen Aktif Domain: {final_url}")
            return final_url
                
        except Exception as e:
            print(f"❌ Hata: {e}")
            continue
            
    return None

def main():
    with sync_playwright() as p:
        print("🚀 Trgoals M3U8 İndirici (V3 - Stealth & Timeout Fix) Başlatılıyor...")
        
        # --- BOT KORUMASINI AŞMA AYARLARI ---
        browser_args = [
            '--autoplay-policy=no-user-gesture-required',
            '--disable-blink-features=AutomationControlled', # En kritik ayar bu
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-infobars',
            '--window-size=1920,1080'
        ]
        
        browser = p.chromium.launch(headless=True, args=browser_args)
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        page = context.new_page()

        # Bot tespitini engellemek için ekstra script
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # 1. ADIM: Domain Bul
        domain = find_working_domain(page)

        if not domain:
            print("\n❌ Kritik Hata: Hiçbir çalışan domain bulunamadı.")
            print("   Lütfen internet bağlantınızı kontrol edin veya VPN kapatıp deneyin.")
            browser.close()
            sys.exit(1)

        # 2. ADIM: Kanal Listesi
        print(f"\n📡 Kanal listesi taranacak...")
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
            "yayinsmarts": ("Smart Sports", "Smart Sports"),
            "yayinsms2": ("Smart Sports 2", "Smart Sports"),
            "yayinnbatv": ("NBA TV", "NBA"),
            "yayinatv": ("ATV", "Ulusal"),
            "yayintv8": ("TV8", "Ulusal"),
            "yayintv85": ("TV8.5", "Ulusal"),
            "yayinas": ("A Spor", "Ulusal"),
            "yayinex1": ("Tâbii 1", "Tabii"),
            "yayineu1": ("Euro Sport 1", "Euro Sport"),
            "yayineu2": ("Euro Sport 2", "Euro Sport"),
        }

        m3u_content = []
        output_filename = "kanallar.m3u8"
        created = 0
        
        # Akıllı Link Bulucu Regex (.sbs linklerini bulur)
        regex_pattern = re.compile(r'["\'](https?://[a-zA-Z0-9.-]+\.sbs/?)["\']', re.IGNORECASE)

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i}/{len(channels)}] {channel_name}...", end=' ')
                sys.stdout.flush() 

                url = f"{domain}/channel.html?id={channel_id}"
                
                try:
                    # Sayfa yükleme süresini de 20sn yaptık
                    page.goto(url, timeout=20000, wait_until='domcontentloaded')
                except:
                    print("-> ❌ Sayfa yüklenemedi (Timeout).")
                    continue
                
                content = page.content()
                match = regex_pattern.search(content)

                if match:
                    baseurl = match.group(1)
                    if not baseurl.endswith('/'): baseurl += '/'
                        
                    direct_url = f"{baseurl}{channel_id}.m3u8"
                    
                    m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                    m3u_content.append(direct_url)
                    
                    print(f"-> ✅ Link: ...{direct_url[-35:]}")
                    created += 1
                else:
                    print("-> ❌ .sbs linki bulunamadı.")
                
            except Exception as e:
                print(f"-> ❌ Hata: {e}")
                continue

        browser.close()

        if created > 0:
            header = f"""#EXTM3U
#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
#EXT-X-REFERER:{domain}/
#EXT-X-ORIGIN:{domain}"""
            
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(header + "\n")
                f.write("\n".join(m3u_content))
            
            print(f"\n🎉 İşlem Tamamlandı! {created} kanal kaydedildi.")
        else:
            print("\n❌ Hiçbir kanal bulunamadı.")

if __name__ == "__main__":
    main()
