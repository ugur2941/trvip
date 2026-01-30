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
    MANUAL_DOMAIN = "https://trgoals1522.xyz/" 
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
        page.close() # Sayfayı mutlaka kapat

    # 2. OTOMATİK TARAMA
    base = "https://trgoals"
    start_range = 1515
    end_range = 1550 
    
    print(f"\n🔍 Otomatik arama başlatılıyor: {start_range} -> {end_range}")
    
    for i in range(start_range, end_range):
        test_domain = f"{base}{i}.xyz"
        
        # Her domain denemesi için YENİ bir sayfa açıyoruz (Kritik Nokta)
        page = context.new_page()
        
        try:
            print(f"   Kontrol: {test_domain}...", end=" ")
            sys.stdout.flush()
            
            try:
                # 8 saniye yeterli, çok beklemeye gerek yok
                response = page.goto(test_domain, timeout=8000, wait_until='domcontentloaded')
            except PlaywrightError:
                print("❌ Zaman Aşımı")
                continue

            final_url = page.url.rstrip('/')
            
            # --- KONTROLLER ---
            if not response.ok:
                print(f"❌ Hata Kodu: {response.status}")
                continue
                
            if "giris" in final_url:
                print(f"⚠️ Giriş Sayfası")
                continue
                
            if not domain_pattern.match(final_url):
                print(f"⚠️ Alakasız Site")
                continue

            # BAŞARILI
            print(f"✅ BAŞARILI!")
            print(f"   🎯 Tespit Edilen Aktif Domain: {final_url}")
            return final_url

        except Exception as e:
            print(f"❌ Hata")
        finally:
            # İşimiz bitince sayfayı kapatıp hafızayı temizliyoruz
            page.close()
            # Bot korumasına yakalanmamak için 1.5 saniye bekle
            time.sleep(1.5)
            
    return None

def main():
    with sync_playwright() as p:
        print("🚀 Trgoals M3U8 İndirici (V4 - Anti-Detect Modu) Başlatılıyor...")
        
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

        # 1. ADIM: Domain Bul (Artık context gönderiyoruz)
        domain = find_working_domain(context)

        if not domain:
            print("\n❌ Hata: Çalışan domain bulunamadı.")
            browser.close()
            sys.exit(1)

        # 2. ADIM: Kanal Listesi
        print(f"\n📡 Kanal listesi taranacak...")
        
        # Kanal işlemleri için tek bir sayfa yeterli
        page = context.new_page()

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
        
        # Akıllı Link Bulucu (.sbs linklerini yakalar)
        regex_pattern = re.compile(r'["\'](https?://[a-zA-Z0-9.-]+\.sbs/?)["\']', re.IGNORECASE)

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i}/{len(channels)}] {channel_name}...", end=' ')
                sys.stdout.flush() 

                url = f"{domain}/channel.html?id={channel_id}"
                
                try:
                    page.goto(url, timeout=15000, wait_until='domcontentloaded')
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
                        print("-> ❌ Link bulunamadı.")
                except:
                    print("-> ❌ Zaman aşımı.")
                    
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
