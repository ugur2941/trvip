import re
import sys
import time
from playwright.sync_api import sync_playwright, Error as PlaywrightError

def find_working_domain(context):
    """
    Sadece verilen yeni domain ile çalışır (V8.3)
    """
    # ====================== YENİ ANA DOMAIN ======================
    MAIN_DOMAIN = "https://taraftarium1041.xyz/"
    
    print(f"\n🔍 Ana domain deneniyor: {MAIN_DOMAIN}")
    
    page = context.new_page()
    try:
        response = page.goto(MAIN_DOMAIN, timeout=15000, wait_until='domcontentloaded')
        
        if response and response.ok:
            final_url = page.url.rstrip('/')
            title = page.title().lower()
            
            # Koruma sayfası kontrolü
            if any(x in title for x in ["giris", "cloudflare", "attention", "just a moment", "dikkat"]):
                print("   ⚠️ Koruma sayfası çıktı (Cloudflare vs.)")
            else:
                print(f"✅ Domain aktif ve kullanılabilir: {final_url}")
                page.close()
                return final_url
        else:
            print("   ⚠️ Domain yanıt vermedi veya hata kodu aldı")
            
    except Exception as e:
        print(f"   ⚠️ Bağlantı hatası: {str(e)[:80]}")
    finally:
        page.close()

    print("\n❌ Ana domain çalışmıyor. Manuel olarak domaini kontrol et ve tekrar dene.")
    return None


def main():
    with sync_playwright() as p:
        print("🚀 Taraftarium1041.xyz M3U8 İndirici (V8.3 - Temizlenmiş) Başlatılıyor...\n")
        
        browser_args = [
            '--autoplay-policy=no-user-gesture-required',
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
        
        browser = p.chromium.launch(headless=True, args=browser_args)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            ignore_https_errors=True,
            viewport={'width': 1366, 'height': 768}
        )

        # 1. Domain kontrolü (sadece yeni domain)
        domain = find_working_domain(context)
        
        if not domain:
            print("\n❌ https://taraftarium1041.xyz/ şu anda çalışmıyor.")
            print("   Lütfen tarayıcıdan manuel olarak siteye girip kontrol et.")
            print("   Çalışıyorsa X'ten (@TRSportHD) güncel linki alıp bana söyle.")
            browser.close()
            sys.exit(1)

        print(f"\n📡 Kullanılan Domain: {domain}\n")

        # Kanal listesi
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
            "trtspor2": ("TRT Spor 2", "TRT"),
            "as": ("A Spor", "Ulusal"),
            "atv": ("ATV", "Ulusal"),
            "tv8": ("TV8", "Ulusal"),
            "tv85": ("TV8.5", "Ulusal"),
            "nbatv": ("NBA TV", "NBA"),
            "eu1": ("Eurosport 1", "Eurosport"),
        }

        m3u_content = []
        output_filename = "kanallar.m3u8"
        created = 0
        debug_saved = False

        regex_fallback = re.compile(r'["\'](https?://[^"\'\s]+?\.(?:sbs|xyz|com|net)/?[^"\'\s]*?(?:mono|index|playlist)\.m3u8[^"\'\s]*)["\']', re.IGNORECASE)

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
                    if ".m3u8" in req_url and any(x in req_url for x in ["mono", "index", "playlist"]):
                        captured_m3u8 = request.url

                page.on("request", handle_request)

                try:
                    page.goto(url, timeout=18000, wait_until='domcontentloaded')
                    page.wait_for_timeout(1200)

                    # Player'ı tetikle
                    try:
                        page.click('body', timeout=1500)
                        page.wait_for_timeout(800)
                        page.click('iframe', timeout=1500)
                    except:
                        pass

                    # m3u8 bekle
                    start_time = time.time()
                    while time.time() - start_time < 10:
                        if captured_m3u8:
                            break
                        page.wait_for_timeout(700)

                    if captured_m3u8:
                        m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                        m3u_content.append(captured_m3u8)
                        print(f"-> ✅ Sniff: ...{captured_m3u8[-60:]}")
                        created += 1
                    else:
                        content = page.content()
                        match = regex_fallback.search(content)
                        if match:
                            stream_url = match.group(1)
                            m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                            m3u_content.append(stream_url)
                            print(f"-> ✅ Regex: ...{stream_url[-60:]}")
                            created += 1
                        else:
                            print("-> ❌ Link bulunamadı")
                            if not debug_saved:
                                with open("debug_channel.html", "w", encoding="utf-8") as f:
                                    f.write(content)
                                print("   ℹ️ debug_channel.html kaydedildi")
                                debug_saved = True

                except Exception as e:
                    print(f"-> ❌ Hata: {str(e)[:70]}")
                finally:
                    page.remove_listener("request", handle_request)

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
            
            print(f"\n🎉 Başarılı! {created} kanal kaydedildi → {output_filename}")
            print(f"   Domain: {domain}")
        else:
            print("\n❌ Hiçbir m3u8 linki yakalanamadı.")
            print("   debug_channel.html dosyasını inceleyip buraya önemli kısımlarını yapıştır.")

if __name__ == "__main__":
    main()
