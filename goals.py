import re
import sys
import time
from playwright.sync_api import sync_playwright, Error as PlaywrightError

def find_working_domain(context):
    """
    Çalışan trgoals / taraftarium domain'ini bulur.
    Manuel öncelik + otomatik tarama.
    """
    domain_pattern = re.compile(r'https?://(?:www\.)?trgoals[0-9]+\.xyz', re.IGNORECASE)

    # 1. MANUEL ÖNCELİK (burayı en güncel bildiğin adrese göre değiştir)
    MANUAL_DOMAIN = "https://trgoals1531.xyz/"   # ← Sen burayı güncelleyebilirsin
    print(f"\n🔍 Öncelikli domain deneniyor: {MANUAL_DOMAIN}")
    
    page = context.new_page()
    try:
        response = page.goto(MANUAL_DOMAIN, timeout=10000, wait_until='domcontentloaded')
        if response and response.ok:
            final_url = page.url.rstrip('/')
            if "trgoals" in final_url and "giris" not in final_url.lower():
                print(f"✅ Öncelikli domain aktif: {final_url}")
                page.close()
                return final_url
    except Exception:
        print("⚠️ Öncelikli domain başarısız.")
    finally:
        page.close()

    # 2. OTOMATİK TARAMA (aralığı genişlettim)
    base = "https://trgoals"
    start_range = 1520
    end_range = 1580 
    
    print(f"\n🔍 Otomatik tarama: {start_range} → {end_range}")
    
    for i in range(start_range, end_range):
        test_domain = f"{base}{i}.xyz"
        page = context.new_page()
        try:
            print(f"   Kontrol: {test_domain}...", end=" ")
            sys.stdout.flush()
            
            response = page.goto(test_domain, timeout=8000, wait_until='domcontentloaded')
            final_url = page.url.rstrip('/')

            if not response.ok:
                print(f"❌ {response.status}")
                continue
            if "giris" in final_url.lower():
                print("⚠️ Giriş sayfası")
                continue
            if domain_pattern.match(final_url) or "trgoals" in final_url:
                print("✅ BAŞARILI!")
                return final_url

        except Exception:
            print("❌ Hata")
        finally:
            page.close()
            time.sleep(1.2)  # rate-limit için biraz kısalttım
            
    return None


def main():
    with sync_playwright() as p:
        print("🚀 TRGoals / Taraftarium M3U8 İndirici (V8 - Güncellenmiş) Başlatılıyor...")
        
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
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            ignore_https_errors=True,
            viewport={'width': 1280, 'height': 720}
        )

        # 1. Domain bul
        domain = find_working_domain(context)
        if not domain:
            print("\n❌ Çalışan domain bulunamadı. Manuel olarak güncelle ve tekrar dene.")
            browser.close()
            sys.exit(1)

        print(f"\n📡 Domain kullanıyor: {domain}")

        # Kanal listesi (senin eski listen + taraftarium1041.xyz'den gördüğüm eklemeler)
        channels = {
            "taraftarium": ("BeIN Sports 1", "BeinSports"),
            "b2": ("BeIN Sports 2", "BeinSports"),
            "b3": ("BeIN Sports 3", "BeinSports"),
            "b4": ("BeIN Sports 4", "BeinSports"),
            "b5": ("BeIN Sports 5", "BeinSports"),
            "bm1": ("BeIN Sports 1 Max", "BeinSports"),
            "bm2": ("BeIN Sports 2 Max", "BeinSports"),
            "ss": ("S Sport 1", "S Sports"),
            "ss2": ("S Sport 2", "S Sports"),
            "t1": ("Tivibu Sports 1", "Tivibu"),
            "t2": ("Tivibu Sports 2", "Tivibu"),
            "t3": ("Tivibu Sports 3", "Tivibu"),
            "t4": ("Tivibu Sports 4", "Tivibu"),
            "smarts": ("Smart Spor", "Smart Sports"),
            "sms2": ("Smart Spor 2", "Smart Sports"),
            "trtspor": ("TRT Spor", "TRT"),
            "trtspor2": ("TRT Spor 2", "TRT"),      # yeni ek
            "as": ("A Spor", "Ulusal"),
            "atv": ("ATV", "Ulusal"),
            "tv8": ("TV8", "Ulusal"),
            "tv85": ("TV8.5", "Ulusal"),
            "nbatv": ("NBA TV", "NBA"),
            "eu1": ("Eurosport 1", "Eurosport"),
            # İstersen buraya daha fazla kanal ekleyebilirsin
        }

        m3u_content = []
        output_filename = "kanallar.m3u8"
        created = 0
        debug_saved = False

        # Yeni fallback regex (sbs veya farklı subdomain'ler için)
        regex_fallback = re.compile(r'["\'](https?://[^"\'\s]+?\.(?:sbs|xyz|com|net|org)/?[^"\'\s]*?)["\']', re.IGNORECASE)

        page = context.new_page()

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i}/{len(channels)}] {channel_name} ({channel_id})...", end=' ')
                sys.stdout.flush()

                url = f"{domain.rstrip('/')}/channel.html?id={channel_id}"

                captured_m3u8 = None

                def handle_request(request):
                    nonlocal captured_m3u8
                    req_url = request.url.lower()
                    if ".m3u8" in req_url and ("mono.m3u8" in req_url or "index.m3u8" in req_url or "playlist.m3u8" in req_url):
                        captured_m3u8 = request.url

                page.on("request", handle_request)

                try:
                    page.goto(url, timeout=15000, wait_until='domcontentloaded')
                    
                    # Player'ı tetiklemek için tıklamalar
                    try:
                        page.click('body', timeout=1500)
                        page.wait_for_timeout(800)
                        page.click('iframe', timeout=1500)  # iframe içindeki player için
                    except:
                        pass

                    # m3u8 düşmesi için bekle
                    start_time = time.time()
                    while time.time() - start_time < 8:
                        if captured_m3u8:
                            break
                        page.wait_for_timeout(600)

                    if captured_m3u8:
                        m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                        m3u_content.append(captured_m3u8)
                        print(f"-> ✅ Sniff: ...{captured_m3u8[-50:]}")
                        created += 1
                    else:
                        # Fallback: Sayfa içeriğinde .m3u8 veya .sbs ara
                        content = page.content()
                        match = regex_fallback.search(content)
                        
                        if match:
                            base = match.group(1).rstrip('/')
                            final_stream_url = f"{base}/{channel_id}/mono.m3u8" if not base.endswith('.m3u8') else base
                            
                            m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                            m3u_content.append(final_stream_url)
                            print(f"-> ✅ Regex: ...{final_stream_url[-50:]}")
                            created += 1
                        else:
                            print("-> ❌ Link bulunamadı")
                            if not debug_saved:
                                with open("debug_channel.html", "w", encoding="utf-8") as f:
                                    f.write(content)
                                print("   ℹ️ debug_channel.html kaydedildi (incele)")
                                debug_saved = True

                except Exception as e:
                    print(f"-> ❌ Hata: {e}")
                finally:
                    page.remove_listener("request", handle_request)
                    page.wait_for_timeout(800)

            except Exception as e:
                print(f"-> ❌ Genel hata: {e}")
                continue

        browser.close()

        if created > 0:
            header = f"""#EXTM3U
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36
#EXTVLCOPT:http-referrer={domain}
#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36
#EXT-X-REFERER:{domain}
#EXT-X-ORIGIN:{domain}"""

            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(header + "\n\n")
                f.write("\n".join(m3u_content))
            
            print(f"\n🎉 Tamamlandı! {created} kanal kaydedildi → {output_filename}")
            print(f"   Domain: {domain}")
        else:
            print("\n❌ Hiçbir kanal için link elde edilemedi. debug_channel.html dosyasını inceleyip bana gönderirsen daha iyi yardımcı olurum.")

if __name__ == "__main__":
    main()
