# Video Kurgu Dili, Hibrit Model Akışı ve Doğrulama Rehberi

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o satır aralığını okuyun.

## Alfabetik Bölüm ve Metot Fihristi (A-Z)
| Başlık | Satır Aralığı | İçerik Özeti |
| :--- | :--- | :--- |
| [A. Akış ve Hibrit Model İş Bölümü (Argon Planlar, Flash Uygular)](#a-akış-ve-hibrit-model-iş-bölümü-argon-planlar-flash-uygular) | L16-L30 | Kota dostu 5 adımlı analiz, plan.json, doğrulama, önizleme ve master akışı |
| [B. Bağlam Koruması ve Flash Uzun İş Protokolü](#b-bağlam-koruması-ve-flash-uzun-iş-protokolü) | L32-L41 | durum.md kaydı, adım kapısı, plan kilidi ve 2 tur devre kesici kuralı |
| [C. Çizelge ve plan.json Şema Standardı](#c-çizelge-ve-planjson-şema-standardı) | L43-L77 | Sahne alanları, odak koordinatları, şablon yuva kontrolü ve müzik tanımı |
| [D. Doğrulama ve Kurgu Dili (9 Altın Kural)](#d-doğrulama-ve-kurgu-dili-9-altın-kural) | L79-L93 | Hook, vuruşta kesim (<=0.12s), geçiş kilidi, 1:1 taş netliği ve yama yasağı |
| [E. Ekran Kanıtı ve Tek-Segment Revizyon Döngüsü](#e-ekran-kanıtı-ve-tek-segment-revizyon-döngüsü) | L95-L104 | _kareler.jpg incelemesi, SHA-256 segment önbelleği ve Sarman makbuzu kanıtları |

---

## A. Akış ve Hibrit Model İş Bölümü (Argon Planlar, Flash Uygular)

Video kurguda estetik karar ile mekanik işlem birbirinden ayrılır; FFmpeg filtre zinciri asla sıfırdan elle yazılmaz:

| Adım | Komut / İşlem | Sorumlu Model | Kota ve Çıktı |
| :--- | :--- | :--- | :--- |
| **1. Ön Analiz** | `python tools/video/analiz.py <kaynak> --muzik <muzik>` | **Gemini 3.8 Flash** | `analiz.json`, `_kontak_videolar.jpg`, `_kontak_gorseller.jpg` (0 Argon kotası) |
| **2. Kurgu Planı** | Kontak görselleri (`read_file`) + `analiz.json` okunarak `plan.json` yazımı | **Gemini 4 Argon** / **Sonnet 5.5** / **Opus 5.5** | Ham video yerine yalnız özet JSON + kontak sayfası okunur (tek çağrı) |
| **3. Doğrulama & Önizleme** | `python tools/video/plan_render.py plan.json --dogrula --onizleme` | **Gemini 3.8 Flash** | `540x960` hızlı MP4 ve sahne orta karelerinden `_kareler.jpg` |
| **4. Görsel Kontrol** | `_kareler.jpg` dosyasının `read_file` ile incelenmesi | **Flash** (Estetik sorun varsa **Argon**) | Kusurlu sahne varsa yalnız o sahne `plan.json`'da düzeltilir |
| **5. Master & XML** | `python tools/video/plan_render.py plan.json --master` | **Gemini 3.8 Flash** | `1080x1920` CRF 17 MP4, `_premiere.xml` ve master `_kareler.jpg` |

> **Yedek Kuralı:** Argon/Sonnet/Opus kotası tamamen doluysa `plan.json` dosyasını Flash yazar ancak teslim raporunda *"Kurgu planı kota nedeniyle Flash ile oluşturuldu"* şerhini düşer.

---

## B. Bağlam Koruması ve Flash Uzun İş Protokolü

Hafif modellerin (Flash) uzun işlerde bağlamı unutmaması ve kısayola kaçmaması için 4 katı kural uygulanır:

1. **Durum Kaydı (`_calisma/durum.md`):** Her adım bittiğinde tamamlanan dosya yolu, doğrulama çıktısı ve sıradaki adım `_calisma/durum.md` içine 5–10 satırla yazılır.
2. **Adım Kapısı (Kanıtsız İlerleme Yasağı):** `_kontak_videolar.jpg` ve `_kontak_gorseller.jpg` `read_file` ile görülmeden `plan.json` yazılamaz; `--dogrula` hatasız geçmeden ve `_kareler.jpg` `read_file` ile görülmeden kullanıcıya "bitti" denilemez.
3. **Plan Kilidi:** Onaylanmış `plan.json` içindeki sahne sırası, süreler ve geçişler Cihan istemedikçe render sırasında değiştirilemez.
4. **2 Tur Devre Kesici:** Bir teknik hata veya doğrulama uyarısı 2 denemede çözülemezse deneme durdurulur; hata çıktısıyla birlikte üst modele veya Tekir'e devredilir.

---

## C. Çizelge ve plan.json Şema Standardı

`tools/video/plan_render.py` tarafından işlenen `plan.json` şeması:

```json
{
  "genislik": 1080,
  "yukseklik": 1920,
  "fps": 30,
  "hedef_sure_sn": 60.0,
  "analiz_json": "analiz.json",
  "muzik": "muzik.mp3",
  "muzik_baslangic_sn": 0.0,
  "sabit_katman_png": "filigran_seffaf.png",
  "cikti_mp4": "video_kurgu_master.mp4",
  "sahneler": [
    {
      "kaynak": "../01_video.mp4",
      "baslangic": 1.2,
      "sure": 2.8,
      "hiz": 1.0,
      "mod": "kirp_9_16",
      "odak_x": 0.5,
      "odak_y": 0.35,
      "gecis": "fade",
      "gecis_sure": 0.40,
      "katman_png": "01_baslik_seffaf.png",
      "yuva_kontrol": [{"cx": 330, "cy": 1050, "r": 185}],
      "neden": "Hook: en net kadrajla ilk 2.8 saniyede ürün taş parlamasını göster"
    }
  ]
}
```

---

## D. Doğrulama ve Kurgu Dili (9 Altın Kural)

`plan_render.py --dogrula` tarafından denetlenen kurgu ilkeleri:

1. **Hook (İlk 3 Saniye):** İlk sahne `1.2 – 3.0 sn` arasında olmalı ve en yüksek netlik (`Laplacian`) skoruna sahip hareketli/çarpıcı kareden seçilmelidir.
2. **Sahne Süresi Sınırları:** Tek bir sahne `1.0 sn`'den kısa veya `5.5 sn`'den uzun olamaz (ideal aralık: `2.4 – 4.2 sn`).
3. **Vuruşta Kesim (Beat Sync):** Her sahne geçişi (`net_kesim_sn`), müziğin gerçek enerji tepelerinden (`vuruslar_sn`) birine en fazla `≤ 0.12 sn` uzaklıkta olmalıdır.
4. **Boş `neden` Yasağı:** Her sahnede o karenin neden seçildiğini açıklayan anlamlı bir `neden` alanı zorunludur.
5. **Geçiş Kısıtı:** Göz yoran `slideleft`, `wipeleft`, `circleopen` gibi geçişler yasaktır; yalnızca `cut` (`kesme`) ve `0.35 – 0.45 sn` yumuşak optik `fade` (`erime`) kullanılır.
6. **1:1 Ürün/Taş Netliği ve PiP/Grid Yasağı:** Taş, strass, sim ve nakış detaylı görsellerde küçük PiP kutusu, 4'lü grid veya `3:4` görseli `9:16`'ya sündürme yasaktır; `kirp_9_16` modu (`Lanczos` + `UnsharpMask`) kullanılır.
7. **Sıfır-Titreme (Tamsayı Crop Pan Yasağı):** Sabit görsellerde `crop=x0+dx*t` ile kaydırma yapmak 1 piksellik sıçrama (takılma) yarattığından yasaktır; görseller `%100` sabit tutulur.
8. **Dikey 4K Telefon Videoları (`displaymatrix`):** `-noautorotate` kullanılmaz; `plan_render.py` her segment sonrası `-display_rotation 0` ile döndürme yan verisini otomatik temizler.
9. **Şablon/Bayrak Yama Yasağı ve Alfa Doluluk:** Dairesel bayrak veya amblem yuvalarında kalan boşlukları boyayarak yamamak yasaktır; orijinal şablon kullanılır ve `yuva_kontrol` ile yuvanın `%100` opak (`alpha >= 250`) dolduğu doğrulanır.

---

## E. Ekran Kanıtı ve Tek-Segment Revizyon Döngüsü

1. **Otomatik Kanıt Tablosu (`_kareler.jpg`):**
   - `plan_render.py` her `--onizleme` ve `--master` çalışmasında tüm sahnelerin tam orta karesini çekerek numaralı `<cikti>_kareler.jpg` dosyasını üretir.
   - Kaliko bu dosyayı `read_file` ile bizzat inceleyerek sündürme, siyah kare, bozuk Arapça/RTL yazı veya bayrak hizalama hatası olmadığını doğrular.
2. **SHA-256 Segment Önbelleği ile Nokta Atışı Revizyon:**
   - Her sahne `_segments/master/seg_XX_<sha256>.mp4` olarak önbelleklenir.
   - Cihan *"videoyu baştan yapma, sadece sondaki bayrak kısmını düzelt"* dediğinde yalnızca ilgili sahnenin PNG katmanı veya parametresi güncellenir ve `plan_render.py --master` çalıştırılır; değişmeyen sahneler `0.1 sn`'de önbellekten alınır, sadece değişen sahne yeniden kodlanır.
3. **Sarman Denetim Kanıtları:**
   - Teslimatta `📋 Sarman Denetim Makbuzu` içine `plan_render.py --dogrula` çıktısı (`[GEÇTİ]`) ve `_kareler.jpg` dosya yolu kanıt olarak eklenir.
