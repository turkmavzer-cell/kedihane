# Video Kurgu Rehberi (Plan → Uygulama Akışı)

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o bölümü okuyun. Video çıktı standardının asıl yeri bu dosyanın C bölümüdür. Premiere XML koordinatları, araç dışı FFmpeg notları ve RTL yazı üretimi `bilgi/sosyal-medya-ve-video-operasyonu.md` A ve C bölümlerindedir.

## Bölüm Fihristi
| Başlık | Satır Aralığı | İçerik Özeti |
| :--- | :--- | :--- |
| [A. İş Bölümü: Planı Güçlü Model, Uygulamayı Hafif Model Yapar](#a-iş-bölümü-planı-güçlü-model-uygulamayı-hafif-model-yapar) | L16-L34 | Hangi adım hangi modelde, eksik brief, Argon'a giden tek mesaj |
| [B. Uzun İş Protokolü (Hafif Model)](#b-uzun-iş-protokolü-hafif-model) | L36-L43 | `_calisma/`, durum.md, adım kapısı, plan kilidi, durma koşulu |
| [C. plan.json Şeması](#c-planjson-şeması) | L45-L74 | Video ve görsel planlar, tempo, kadraj, yazı ve yuva, ses, doğrulama |
| [D. Kurgu Dili](#d-kurgu-dili) | L76-L96 | Hook, yapı, tempoya göre geçiş, kesim yeri, ince doku, yazı, ses |
| [E. Kontrol, Kilit ve Denetim](#e-kontrol-kilit-ve-denetim) | L98-L110 | Kodlu kontrol sayfaları, master kilidi, 9 maddelik denetim, Premiere XML, makbuz |

---

## A. İş Bölümü: Planı Güçlü Model, Uygulamayı Hafif Model Yapar

Kurgu kalitesini belirleyen karar (hangi plan, hangi sıra, hangi tempo) tek adımdır ve güçlü modele verilir. Uzun ve mekanik iş hafif modelde yürür. Hafif model ffmpeg komutu yazmaz; yalnız `plan.json` doldurur ve araçları çalıştırır.

| Adım | Ne yapılır | Antigravity | Claude |
|---|---|---|---|
| 1. Analiz | `python tools/video/analiz.py <kaynak_klasor> --muzik <muzik>` → `<kaynak_klasor>/_calisma/` | Gemini 3.8 Flash | Kaliko (sonnet) |
| 2. Plan | `analiz.json` + `_kontak_videolar.jpg` + `_kontak_gorseller.jpg` + brief → yalnız `_calisma/plan.json` | **Gemini Argon** | Kaliko (opus) |
| 3. Önizleme | `python tools/video/plan_render.py _calisma/plan.json --onizleme --analiz _calisma/analiz.json` | Flash | Kaliko (sonnet) |
| 4. Kontrol | E bölümü; teknik düzeltme Flash, yaratıcı düzeltme Argon | Flash (+Argon) | Kaliko |
| 5. Master | aynı komut `--master` ile → PASS → Sarman | Flash | Kaliko → Sarman |

**Eksik brief:** Kaynaklar, hedef süre, platform, müzik ve tempo (hareketli/yavaş) belli değilse Flash tahmin yürütmez, önce Cihan'a sorar.

**Argon'a giden tek mesaj (adım 2):** Ham video gönderilmez. Mesajda şunlar olur: brief, `analiz.json`, iki kontak sayfası, bu dosyanın C ve D bölümleri ve şu talimat: "Yalnız geçerli `plan.json` döndür. Her planın `neden` alanı dolu olsun. Kesimleri müzik vuruşlarına oturt."

Argon kotası bittiyse plan Opus veya Sonnet'e verilir. Hiçbiri yoksa Flash C ve D bölümleriyle planlar ve teslimde "plan hafif modelle yazıldı" diye belirtir.

**ffmpeg:** Araçlar önce `imageio-ffmpeg`'i (tam libx264), yoksa PATH'teki ffmpeg'i kullanır. ffprobe yoksa bilgi `ffmpeg -i` çıktısından okunur. Gerekirse `pip install imageio-ffmpeg`.

## B. Uzun İş Protokolü (Hafif Model)

1. **İş klasörü:** `<kaynak_klasor>/_calisma/` (repo dışı). İçinde `brief.md`, `analiz.json`, `plan.json`, `durum.md` ve çıktılar bulunur. Plandaki göreli yollar bu klasöre göredir (`../klip.mp4`).
2. **durum.md:** Her adım bitince tek satır eklenir ve satır o adımın ürettiği dosyayı adıyla anar. Örnek: `14:20 | adım 3 | kurgu_onizleme.mp4, _kareler.jpg | 2 uyarı`. Bağlam dolarsa iş buradan sürer; sohbet geçmişine güvenilmez.
3. **Eski dosya:** Önceki oturumdan kalan bir ara dosya, `--onizleme` yeniden alınıp kontrol sayfasına bakılmadan kullanılmaz.
4. **Adım kapısı:** Araç `[TAMAM]` yazmadan sonraki adıma geçilmez. `[HATA]` düzeltilmeden render alınmaz. Master kilidi ve denetim (E bölümü) bunu kod düzeyinde uygular.
5. **Plan kilidi:** Flash `plan.json`'da yalnız teknik alanları değiştirebilir: kaynak yolu, `kadraj`, `onay_*` kodları. Vuruş hizalamasını araç kendisi yapar. Plan sırası, plan seçimi, süre ve tempo değişikliği Argon'a gider.
6. **Durma koşulu:** Aynı hata 2 turda çözülmezse Flash durur, `durum.md`'ye yazar ve Argon'a veya Cihan'a bırakır.

## C. plan.json Şeması

```json
{
 "cikti": {"boyut": [1080, 1920], "fps": 30, "ad": "urun_kurgu_v1.mp4", "kapanis_fade": 0.5},
 "hedef_sure": 15, "tempo": "hareketli", "keskinlestir": false,
 "muzik": {"dosya": "../muzik.mp3", "baslangic": 0, "ses_db": 0, "fade_out": 1.5},
 "orijinal_ses": false, "hedef_lufs": -14,
 "planlar": [
  {"kaynak": "../klip1.mp4", "giris": 2.10, "cikis": 3.60, "kadraj": "orta", "neden": "hook: ürün yakın plan"},
  {"kaynak": "../urun.jpg", "sure": 1.5, "kadraj": 0.35, "keskinlestir": true, "neden": "taş detayı"},
  {"kaynak": "../urun2.jpg", "sure": 2.0, "kadraj": "bulanik", "neden": "ürünün tamamı"},
  {"kaynak": "../klip2.mp4", "giris": 4.0, "cikis": 7.0, "tempo": "yavas", "gecis": "fade", "neden": "yavaş kapanış"}
 ],
 "yazilar": [{"png": "bitis.png", "bas": 12.5, "bit": 15, "yuva_kontrol": [{"cx": 330, "cy": 1050, "r": 185}]}],
 "onay_kareler": "", "onay_yazilar": ""
}
```

- **Çıktı standardı:** Dikey master 1080x1920 (9:16), 30 fps, H.264. Kodlama ayarlarını `plan_render.py` belirler; elle değiştirilmez.
- **Video planı:** `kaynak`, `giris`, `cikis` (kaynaktaki saniye) ve `neden` zorunlu. İsteğe bağlı: `hiz` (0,25–4).
- **Görsel planı (jpg/png/webp):** `kaynak`, `sure` ve `neden` zorunlu. Görsel sündürülmez. `keskinlestir` hafif unsharp uygular.
- **`kadraj`:** `orta`/`ust`/`alt` ya da 0–1 arası sayı (0 = üst, 1 = alt) 9:16'ya kırpar. `bulanik` kırpmadan sığdırır, boşluğu aynı görüntünün bulanık hali doldurur. `sigdir` siyah bantla sığdırır.
- **`tempo`:** Üst düzeyde varsayılandır; plan düzeyinde o plana giriş için geçerlidir. Kurallar D bölümünde.
- **`gecis`:** `kesme`, `fade` ya da `fadeblack`. Slide, wipe, circle, PiP, ızgara ve kaydırma (pan) araçta yoktur. `gecis_sure` yazılmazsa tempo varsayılanı kullanılır.
- **Yazılar:** Tam kadraj şeffaf PNG, çıktı boyutuna ölçeklenir. Arapça/RTL yazı üretimi için `sosyal-medya-ve-video-operasyonu.md` A bölümüne bakılır. `yuva_kontrol` (PNG pikseli cinsinden `cx`, `cy`, `r`) bayrak ya da amblem yuvasının tamamen dolu olduğunu denetler; boşluk varsa hata verir. Boşluk boyanmaz; görsel büyütülür.
- **Ses:** `orijinal_ses: true` ise klip sesi `orijinal_ses_db` (varsayılan -6) ile müziğe karışır. Sonda `loudnorm` uygulanır. Kısa videoda tek geçişli `loudnorm` hedefin 2–3 LU altında kalabilir.
- **`--analiz` verilince:** ±0,15 sn içindeki her kesim, önceki planın sonu oynatılarak en yakın vuruşa hizalanır (`[HIZALA]` satırı basılır). Daha uzak kesimler uyarı verir. İki analiz biçimi de okunur (`muzikler[].vuruslar_sn` ve `muzik.vuruslar`).
- **Hata verenler:** eksik alan, boş `neden`, kaynak dosya yok, `cikis` kaynak süresini aşıyor, izinsiz geçiş, tempo aralığı dışındaki `gecis_sure`, dolmamış yuva, eski `sahneler` şeması.
- **Uyarı verenler:** plan 0,4 sn'den kısa, plan tempo sınırından uzun, hareketli bölümde geçişlerin 1/3'ünden fazlası efektli, toplam süre hedeften 1 sn'den fazla sapıyor, yazı güvenli alan dışına taşıyor.

## D. Kurgu Dili

> Genel kurgu ilkeleri ve Cihan'ın işlerinden çıkan derslerdir. Cihan bir sonucu "iyi" ya da "kötü" diye değerlendirdikçe güncellenir (CLAUDE.md Bölüm 14). İlkelerden yalnız C bölümünde "hata/uyarı" diye geçenler araçla denetlenir; diğerleri planı yazanın sorumluluğundadır.

1. **Hook:** İlk plan 1,2–3 sn sürer ve en güçlü ya da en hareketli görüntüyle açılır. Logo, siyah ekran veya yavaş açılışla başlanmaz.
2. **Yapı:** Hook, gelişme (ürün, kullanım, hikâye), doruk, kapanış ve çağrı (son 2–3 sn).
3. **Tempoya göre geçiş:**

| Tempo | Varsayılan geçiş | `gecis_sure` | Plan süresi |
|---|---|---|---|
| `hareketli` | `kesme`, vuruşta; `fade` en fazla 1/3 | 0,15–0,35 sn | 0,8–2,5 sn, en fazla 4 |
| `yavas` | `fade` | 0,35–0,8 sn | 2–5 sn, en fazla 7 |

   Bir videoda iki tempo birlikte olabilir (hareketli gövde, yavaş kapanış gibi). `fadeblack` yalnız bölüm değişiminde kullanılır.

4. **Kesim yeri:** Müzik vuruşunda kesilir. Büyük değişimler (yeni bölüm, yazı girişi) güçlü vuruşa, yani ölçü başına denk getirilir. Hareket varsa hareketin ortasında kesilir.
5. **Sıralama:** Aynı açıdan benzer iki plan arka arkaya konmaz. Geniş ve yakın plan dönüşümlü kullanılır.
6. **İnce doku (taş, strass, sim, nakış):** Görsel tam ekran ve sabit kalır, detay bölgesinden `kadraj` sayısıyla kırpılır ve `keskinlestir` açılır. Küçük kutu, ızgara ya da sündürme kullanılmaz.
7. **Kaynak:** `analiz.json`'daki siyah ve bozuk aralıklar kullanılmaz. Yavaşlatma (`hiz` < 1) yalnız kaynak ≥ 50 fps ise yapılır.
8. **Yazı:** Ekranda kalma süresi kabaca kelime başına 0,3 sn + 1 sn olur. Güvenli alanın (üst %8, alt %17, sağ %13 dışı) içinde kalır.
9. **Ses:** Müzik -14 LUFS'tur. Konuşma varsa müzik konuşmanın yaklaşık 12 dB altında kalır.

## E. Kontrol, Kilit ve Denetim

1. **Kontrol sayfaları:** `--onizleme` iki sayfa üretir. `_kareler.jpg` her planın orta karesini, numarasını ve `neden`ini gösterir. `_yazilar.jpg` yazı PNG'lerini gri zeminde, kırmızı güvenli alan çerçevesiyle gösterir. Her sayfanın üst bandında bir **kod** vardır ve kod terminale yazılmaz.
2. **Kontrol listesi (Flash):**
   1. Her karede konu kadrajda mı? Konu kesiliyorsa `kadraj` değiştirilir (teknik).
   2. Kare `neden`le uyuşuyor mu? Uyuşmuyorsa → Argon.
   3. Yazılar okunuyor mu? Arapça harfler bitişik mi? Bayrak ve amblem yerinde mi?
   4. `[UYARI]` satırları: sıra, süre veya tempo sorunuysa → Argon.
3. **Master kilidi:** Kodlar `onay_kareler` ve `onay_yazilar` alanlarına yazılır. `--master` şu durumlarda çalışmaz: kod yanlışsa, önizleme alınmadıysa ya da plan önizlemeden sonra değiştiyse. Kilit kopyayı pahalılaştırır ama imkânsız kılmaz; kontrol yine de gerçekten yapılmalıdır.
4. **Denetim (otomatik, 9 madde):** çözünürlük, SAR 1:1, sabit fps, döndürme kalıntısı, motor imzası, `faststart`, sürenin planla eşitliği, ses ve görüntü süresinin eşitliği, istenmeyen siyah kare. Master'da **FAIL varsa teslim yasaktır**. Donuk görüntü (yalnız video planlarında) ve düşük netlik uyarı olarak basılır. Elle yazılmış betikle üretilen video imzasız olduğu için FAIL alır.
5. **Premiere XML:** `--master` ayrıca `_premiere.xml` üretir. Dosya kaynak dosyalara bağlı bir kesim listesidir; geçişler kesme olarak, hız 1x olarak gelir. İnce ayar Premiere'de yapılır.
6. **Argon'a düzeltme mesajı:** `plan.json`, uyarılar ve `_kareler.jpg` gönderilir; talimat "yalnız sorunlu planları değiştir". En fazla 2 tur yapılır, sonra Cihan'a sorulur.
7. **Sarman makbuzu:** "Doğrulanan Kanıtlar" alanına denetim satırı (`PASS 9/9`), "kontrol sayfaları görüldü: evet" ve `[HIZALA]`/`[UYARI]` satırları yazılır. "Cihan'ın Kontrol Etmesi Gerekenler" alanına müzik uyumu ve genel ritim yazılır; bunları araç ölçemez.
