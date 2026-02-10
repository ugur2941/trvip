import re
import sys
import time
from playwright.sync_api import sync_playwright, Error as PlaywrightError

def find_working_domain(context):
    """
    Verilen aralıkta çalışan domain'i bulur.
    Her deneme için yeni sayfa açarak bot korumasını (rate limit) atlatır.
    """
    
    # Regex: https/http, www opsiyonel, trgoals + sayılar + .xyz
    domain_pattern = re.compile(r'https?://(?:www\.)?trgoals[0-9]+\.xyz', re.IGNORECASE)

    # 1. MANUEL KONTROL
    # En son çalışan adresi buraya yazmak işlemi hızlandırır.
    MANUAL_DOMAIN = "https://trgoals1531.xyz/" 
    print(f"\n🔍 Öncelikli domain deneniyor: {MANUAL_DOMAIN}")
    
    page = context.new_page()
    try:
        response = page.goto(MANUAL_DOMAIN, timeout=10000, wait_until='domcontentloaded')
        if response and response.ok:
            final_url = page.url.rstrip('/')
            if domain_pattern.match(final_url) and "giris" not in final_url:
                print(f"✅ Öncelikli domain aktif: {final_url}")
                page.close()
                return final_url
            else:
                print(f"⚠️ Öncelikli domain reddedildi: {final_url}")
    except Exception as e:
        print(f"⚠️ Öncelikli domain başarısız.")
    finally:
        page.close()

    # 2. OTOMATİK TARAMA
    base = "https://trgoals"
    start_range = 1528
    end_range = 1560 
    
    print(f"\n🔍 Otomatik arama başlatılıyor: {start_range} -> {end_range}")
    
    for i in range(start_range, end_range):
        test_domain = f"{base}{i}.xyz"
        page = context.new_page()
        try:
            print(f"   Kontrol: {test_domain}...", end=" ")
            sys.stdout.flush()
            try:
                response = page.goto(test_domain, timeout=8000, wait_until='domcontentloaded')
            except PlaywrightError:
                print("❌ Zaman Aşımı")
                continue

            final_url = page.url.rstrip('/')
            
            if not response.ok:
                print(f"❌ Hata Kodu: {response.status}")
                continue
            if "giris" in final_url:
                print(f"⚠️ Giriş Sayfası")
                continue
            if not domain_pattern.match(final_url):
                print(f"⚠️ Alakasız Site")
                continue

            print(f"✅ BAŞARILI!")
            print(f"   🎯 Tespit Edilen Aktif Domain: {final_url}")
            return final_url

        except Exception as e:
            print(f"❌ Hata")
        finally:
            page.close()
            time.sleep(1.5)
            
    return None

def main():
    with sync_playwright() as p:
        print("🚀 Trgoals M3U8 İndirici (V6 - Dinamik Link Oluşturucu) Başlatılıyor...")
        
        browser_args = [
            '--autoplay-policy=no-user-gesture-required',
            '--disable-blink-features=AutomationControlled', 
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-infobars'
        ]
        
        browser = p.chromium.launch(headless=True, args=browser_args)
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            ignore_https_errors=True
        )

        # 1. ADIM: Domain Bul
        domain = find_working_domain(context)

        if not domain:
            print("\n❌ Hata: Çalışan domain bulunamadı.")
            browser.close()
            sys.exit(1)

        # 2. ADIM: Kanal Listesi
        print(f"\n📡 Kanal listesi taranacak...")
        page = context.new_page()

        # GÜNCELLENMİŞ KANAL LISTESI (Senin verdiğin yeni formatlara göre)
        # ID'ler artık linkteki klasör ismidir. Örn: .../b2/mono.m3u8 için ID "b2" dir.
        channels = {
            "trgoals": ("beIN Sports 1", "BeinSports"),  # Link yapısı: .../trgoals/mono.m3u8
            "b2": ("beIN Sports 2", "BeinSports"),
            "b3": ("beIN Sports 3", "BeinSports"),
            "b4": ("beIN Sports 4", "BeinSports"),
            "b5": ("beIN Sports 5", "BeinSports"),
            "bm1": ("beIN Sports 1 Max", "BeinSports"),
            "bm2": ("beIN Sports 2 Max", "BeinSports"),
            
            "ss": ("S Sport 1", "S Sports"),
            "ss2": ("S Sport 2", "S Sports"),
            
            "t1": ("Tivibu Sports 1", "Tivibu"),
            "t2": ("Tivibu Sports 2", "Tivibu"),
            "t3": ("Tivibu Sports 3", "Tivibu"),
            "t4": ("Tivibu Sports 4", "Tivibu"),
            "t5": ("Tivibu Sports 5", "Tivibu"),
            "t6": ("Tivibu Sports 6", "Tivibu"),
            
            "smarts": ("Smart Spor", "Smart Sports"),
            "sms2": ("Smart Spor 2", "Smart Sports"),
            
            "trt1": ("TRT 1", "TRT"),
            "trtspor": ("TRT Spor", "TRT"),
            "trtspor2": ("TRT Spor 2", "TRT"),
            
            "as": ("A Spor", "Ulusal"),
            "atv": ("ATV", "Ulusal"),
            "tv8": ("TV8", "Ulusal"),
            "tv85": ("TV8.5", "Ulusal"),
            
            "nbatv": ("NBA TV", "NBA"),
            "eu1": ("Eurosport 1", "Euro Sport"),
            "eu2": ("Eurosport 2", "Euro Sport"),
        }

        m3u_content = []
        output_filename = "kanallar.m3u8"
        created = 0
        
        # Regex: Sadece B_URL değişkenini yakalar (https://....sbs/)
        regex_pattern = re.compile(r'B_URL\s*=\s*["\'](https?://[^"\']+\.sbs/?)["\']', re.IGNORECASE)

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i}/{len(channels)}] {channel_name} ({channel_id})...", end=' ')
                sys.stdout.flush() 

                # Siteye giderken kanal ID'sini parametre olarak ekliyoruz
                url = f"{domain}/channel.html?id={channel_id}"
                
                try:
                    page.goto(url, timeout=15000, wait_until='domcontentloaded')
                    content = page.content()
                    
                    # Sayfadan B_URL'i (Base URL) çekiyoruz
                    match = regex_pattern.search(content)

                    if match:
                        base_url = match.group(1)
                        if not base_url.endswith('/'): base_url += '/'
                        
                        # LİNK OLUŞTURMA: Base URL + Kanal ID + /mono.m3u8
                        # Örn: https://ofx...sbs/ + b2 + /mono.m3u8
                        final_stream_url = f"{base_url}{channel_id}/mono.m3u8"
                        
                        m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                        m3u_content.append(final_stream_url)
                        print(f"-> ✅ Link: ...{final_stream_url[-40:]}")
                        created += 1
                    else:
                        print("-> ❌ B_URL bulunamadı.")
                except:
                    print("-> ❌ Zaman aşımı.")
                    
            except Exception as e:
                print(f"-> ❌ Hata: {e}")
                continue

        browser.close()

        if created > 0:
            # Header'lar (ExoPlayer için gerekli olanlar dahil)
            header = f"""#EXTM3U
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
#EXTVLCOPT:http-referrer={domain}/channel.html
#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
#EXT-X-REFERER:{domain}/channel.html
#EXT-X-ORIGIN:{domain}
#EXT-X-HEADER:Sec-Fetch-Dest=empty
#EXT-X-HEADER:Sec-Fetch-Mode=cors
#EXT-X-HEADER:Sec-Fetch-Site=cross-site"""
            
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(header + "\n")
                f.write("\n".join(m3u_content))
            
            print(f"\n🎉 İşlem Tamamlandı! {created} kanal kaydedildi.")
        else:
            print("\n❌ Hiçbir kanal bulunamadı.")

if __name__ == "__main__":
    main()
