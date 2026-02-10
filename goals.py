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
    # Test için burayı bilerek 1512 yapabilirsin, kod aşağıda doğrusunu bulmalı.
    # Güncel çalışan adresi biliyorsan buraya yazmak işlemi hızlandırır.
    MANUAL_DOMAIN = "https://trgoals1529.xyz/" 
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
    start_range = 1525 # Güncel aralıklara yakın başlatalım
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
        print("🚀 Trgoals M3U8 İndirici (V5 - Yeni URL Yapısı /mono.m3u8) Başlatılıyor...")
        
        # Gizlilik ayarları
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

        # Kanal listesi (ID'ler aynı kalabilir, çünkü site ID'ye göre yönlendirme yapıyor)
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
            "yayineu1": ("Euro Sport 1", "Euro Sport"),
            "yayineu2": ("Euro Sport 2", "Euro Sport"),
            "yayintrt1": ("TRT 1", "TRT"),
            "yayintrtspor": ("TRT Spor", "TRT"),
            "yayintrtspor2": ("TRT Spor 2", "TRT")
        }

        m3u_content = []
        output_filename = "kanallar.m3u8"
        created = 0
        
        # --- KRİTİK DEĞİŞİKLİK ---
        # Eski Regex: Sadece base domain'i (.sbs) buluyordu.
        # Yeni Regex: .sbs ile başlayan ve .m3u8 ile biten TAM linki bulur.
        # Örnek yakalama: https://ofx.d72577a9dd0ec26.sbs/b2/mono.m3u8
        regex_pattern = re.compile(r'["\'](https?://[a-zA-Z0-9.-]+\.sbs/[^"\']*?\.m3u8)["\']', re.IGNORECASE)

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i}/{len(channels)}] {channel_name}...", end=' ')
                sys.stdout.flush() 

                url = f"{domain}/channel.html?id={channel_id}"
                
                try:
                    page.goto(url, timeout=15000, wait_until='domcontentloaded')
                    content = page.content()
                    
                    # Regex ile tam linki ara
                    match = regex_pattern.search(content)

                    if match:
                        # Artık linki kendimiz oluşturmuyoruz, doğrudan sayfadan çekiyoruz.
                        full_video_url = match.group(1)
                        
                        m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                        m3u_content.append(full_video_url)
                        print(f"-> ✅ Link: ...{full_video_url[-40:]}") # Linkin son kısmını göster
                        created += 1
                    else:
                        print("-> ❌ Link bulunamadı.")
                except:
                    print("-> ❌ Zaman aşımı.")
                    
            except Exception as e:
                print(f"-> ❌ Hata: {e}")
                continue

        browser.close()

        if created > 0:
            # Header'ları da güncelledik (Önceki konuşmamızdaki düzeltmelerle birlikte)
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
