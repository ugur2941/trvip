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

    # 1. MANUEL KONTROL (Hızlandırmak için çalışan adresi buraya yazın)
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
    start_range = 1530
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
        print("🚀 Trgoals M3U8 İndirici (V7 - Network Sniffing & Auto-Click) Başlatılıyor...")
        
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

        channels = {
            "trgoals": ("beIN Sports 1", "BeinSports"),
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
            "smarts": ("Smart Spor", "Smart Sports"),
            "sms2": ("Smart Spor 2", "Smart Sports"),
            "trtspor": ("TRT Spor", "TRT"),
            "as": ("A Spor", "Ulusal"),
            "atv": ("ATV", "Ulusal"),
            "tv8": ("TV8", "Ulusal"),
            "tv85": ("TV8.5", "Ulusal"),
            "nbatv": ("NBA TV", "NBA"),
            "eu1": ("Eurosport 1", "Euro Sport"),
        }

        m3u_content = []
        output_filename = "kanallar.m3u8"
        created = 0
        debug_saved = False
        
        # Regex: Sadece .sbs ile biten domaini bulmaya çalışır (Yedek Plan)
        # Örnek: https://ofx...sbs/
        regex_fallback = re.compile(r'["\'](https?://[^"\'\s]+\.sbs/?)["\']', re.IGNORECASE)

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i}/{len(channels)}] {channel_name} ({channel_id})...", end=' ')
                sys.stdout.flush() 

                url = f"{domain}/channel.html?id={channel_id}"
                
                # AĞ DİNLEYİCİSİ (SNIFFER)
                captured_m3u8 = None
                def handle_request(request):
                    nonlocal captured_m3u8
                    if ".m3u8" in request.url and "mono.m3u8" in request.url:
                        captured_m3u8 = request.url

                # Sayfa isteği yakalamaya başlasın
                page.on("request", handle_request)
                
                try:
                    page.goto(url, timeout=15000, wait_until='domcontentloaded')
                    
                    # Sayfaya tıkla (Play'i tetiklemek için)
                    try:
                        page.click('body', timeout=2000)
                    except:
                        pass
                    
                    # Linkin düşmesi için bekle
                    start_time = time.time()
                    while time.time() - start_time < 5: # 5 saniye bekle
                        if captured_m3u8:
                            break
                        page.wait_for_timeout(500)

                    # 1. YÖNTEM: AĞDAN YAKALAMA
                    if captured_m3u8:
                        m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                        m3u_content.append(captured_m3u8)
                        print(f"-> ✅ Link (Sniff): ...{captured_m3u8[-40:]}")
                        created += 1
                    else:
                        # 2. YÖNTEM: HTML TARAMA (FALLBACK)
                        content = page.content()
                        match = regex_fallback.search(content)
                        
                        if match:
                            base_url = match.group(1)
                            if not base_url.endswith('/'): base_url += '/'
                            final_stream_url = f"{base_url}{channel_id}/mono.m3u8"
                            
                            m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                            m3u_content.append(final_stream_url)
                            print(f"-> ✅ Link (Regex): ...{final_stream_url[-40:]}")
                            created += 1
                        else:
                            print("-> ❌ Link bulunamadı.")
                            # Hata ayıklama için HTML kaydet (Sadece ilk hata)
                            if not debug_saved:
                                with open("debug_channel.html", "w", encoding="utf-8") as f:
                                    f.write(content)
                                print("   ℹ️ Hata ayıklama için 'debug_channel.html' dosyası oluşturuldu.")
                                debug_saved = True

                except Exception as e:
                    print(f"-> ❌ Hata: {e}")
                finally:
                    page.remove_listener("request", handle_request)
                    
            except Exception as e:
                print(f"-> ❌ Hata: {e}")
                continue

        browser.close()

        if created > 0:
            # Header güncellemesi (Browser loglarına göre)
            header = f"""#EXTM3U
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
#EXTVLCOPT:http-referrer={domain}/
#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
#EXT-X-REFERER:{domain}/
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
