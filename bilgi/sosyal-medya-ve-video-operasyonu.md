# Sosyal Medya ve Video Operasyonu Rehberi

> **Okuma Kuralı:** Fihristten ilgili başlığı (`## X.`) bulun ve yalnızca o bölümü okuyun.

## Alfabetik Bölüm ve Metot Fihristi (A-Z)
| Başlık | Satır Aralığı | İçerik Özeti |
| :--- | :--- | :--- |
| [A. Arapça ve RTL Tipografi, Yazı Katmanı ve Supersampling (Pillow & Cairo)](#a-arapça-ve-rtl-tipografi-yazı-katmanı-ve-supersampling-pillow--cairo) | L16-L51 | RTL harf birleştirme, 4x supersampling, emoji yasağı ve kontak sayfası |
| [B. Çerçeveli / Dairesel Yuvalara Görsel Yerleştirme ve Bitiş Kartları](#b-çerçeveli--dairesel-yuvalara-görsel-yerleştirme-ve-bitiş-kartları) | L55-L98 | Autocrop beyaz boşluk yasağı, 4 fotoğraflı delikli şablon ve alt kanal |
| [C. Dikey Video: Araç Dışı FFmpeg Notları ve Premiere XML Köprüsü](#c-dikey-video-araç-dışı-ffmpeg-notları-ve-premiere-xml-köprüsü) | L102-L124 | Standart video-kurgu.md'de; xfade normalizasyonu, prproj ve xmeml koordinatları |
| [D. Meta Business Suite ve Çok Kanallı Müşteri Yanıtlama Otomasyonu](#d-meta-business-suite-ve-çok-kanallı-müşteri-yanıtlama-otomasyonu) | L128-L156 | İki aşamalı Türkçe onay, wa.me yer tutucu, DOM dosya yükleme ve spam kontrolü |
| [E. Sosyal Medya Hesap Güvenliği ve Yerel Kayıt İzolasyonu](#e-sosyal-medya-hesap-güvenliği-ve-yerel-kayıt-izolasyonu) | L160-L168 | Profil doğrulama, git gizlilik duvarı, çift repolu iş kaydı ve global öğrenim ayrımı |

---

## A. Arapça ve RTL Tipografi, Yazı Katmanı ve Supersampling (Pillow & Cairo)

Arapça, Farsça ve İbranice gibi sağdan sola (RTL) dillerde video altyazısı veya şablon grafik üretilirken harf kopması, tenvin kayması ve font render hataları oluşur.

1. **Windows Pillow ve Harf Şekillendirme (`libraqm` Eksikliği Çözümü):**
   - Windows ortamındaki standart `Pillow` derlemelerinde karmaşık metin düzenleme motoru (`libraqm`) varsayılan olarak bulunmaz.
   - Bu eksiklik doğrudan font çizildiğinde harflerin ayrık kutu (`[]` veya `0xFE8D` izole form) olarak çıkmasına yol açar.
   - Çözüm: `arabic_reshaper` ve `python-bidi` kütüphaneleri şu katı parametrelerle birlikte kullanılır:
     ```python
     import arabic_reshaper
     from bidi.algorithm import get_display

     # Tenvin kaymasını (0x064B) ve izole glif hatalarını önleyen yapılandırma
     reshaper_config = {
         'use_unshaped_instead_of_isolated': True,
         'delete_harakat': True,  # Tenvin ve hareke taşmalarını temizler
         'support_ligatures': True
     }
     reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

     def sekillendir_rtl(metin: str) -> str:
         duzeltilmis = reshaper.reshape(metin)
         return get_display(duzeltilmis)
     ```
2. **RTL Satır İçi Latin ve Rakam Bloklama:**
   - RTL cümle içinde geçen telefon numarası, marka adı, Latin harfli kelimeler veya model kodları bidi algoritması tarafından parça parça ters çevrilebilir.
   - Çözüm: Ardışık Latin ve rakam karakterleri tek bir LTR blok olarak birleştirilmeli, aralarına Unicode LTR Mark (`\u200E`) eklenerek sıralama sabitlenmelidir.
3. **4x Supersampling (Kenar Tırtıklanması Önleme):**
   - İnce fontlarda (`Cairo-Light`, `Cairo-Regular`) veya dar rakamlarda pikseller doğrudan tuval boyutunda çizildiğinde kenarlarda aliasing (tırtıklanma) oluşur.
   - Çözüm: Metin şablonu hedef çözünürlüğün 4 katı (`4x`) boyutta çizilir ve ardından yüksek kaliteli `PIL.Image.Resampling.LANCZOS` filtresiyle hedef boyuta küçültülür (supersampling).
   - Otomatik Font Küçültme Sarmalayıcısı: Metin genişliği belirlenen güvenli marjı (`safe_width`) aşıyorsa font boyutu otomatik olarak 2'şer punto düşürülerek sınır içine oturtulur.
4. **Emoji Yasağı ve Doğrulama Protokolü:**
   - Standart metin fontlarında (`Cairo`, `Tahoma`, `Amiri`) renkli emoji glifleri bulunmaz; metin içine konan emojiler siyah kutu, soru işareti veya font hatası üretir.
   - Kural: PNG şablonlarda metin içi Unicode emoji kesinlikle yasaktır. Vektörel süslemeler (yıldız, elmas, onay ikonu) ayrı alfa katmanı olarak eklenir.
   - Noktalama: Üç nokta (`...`) yerine Arapça virgül (`،`) veya nokta kullanılır.
   - Doğrulama: Üretim sonrasında `fontTools.ttLib.TTFont` ile `cmap` tablosunda eksik glif taraması yapılır ve gri zeminli kontak sayfası üretilerek görsel kontrol sağlanır.

---

## B. Çerçeveli / Dairesel Yuvalara Görsel Yerleştirme ve Bitiş Kartları

Video bitiş ekranlarında veya çoklu ürün sahnelerinde dairesel ve çerçeveli alanlara logo, bayrak veya ürün fotoğrafı yerleştirilirken hizalama ve ölçekleme kuralları uygulanır.

1. **Beyaz Boşluk Yasağı (`Autocrop`):**
   - Referans görsellerin etrafındaki beyaz veya şeffaf kenar boşlukları dairesel maskeyi bozar ve logonun yuva içinde küçük kalmasına neden olur.
   - Çözüm: Dairesel yuvaya yerleştirilmeden önce görselin kenar boşlukları `PIL.Image.getbbox()` ile otomatik kırpılır (`autocrop`).
   - Kırpılmış görselin yüksekliği dairesel maskenin çapına (`d_px`) tam oturacak şekilde ölçeklenir (`scale = d_px / cropped_height`):
     ```python
     from PIL import Image, ImageDraw

     def dairesel_yuvaya_yerlestir(kaynak_img: Image.Image, cap_px: int) -> Image.Image:
         # Kenar bosluklarini kirp (beyaz veya seffaf alanlari temizle)
         bbox = kaynak_img.getbbox()
         kirpilmis = kaynak_img.crop(bbox) if bbox else kaynak_img
         
         # Yuvayi tam dolduracak olcek
         olcek = cap_px / max(kirpilmis.size[1], 1)
         yeni_w = int(kirpilmis.size[0] * olcek)
         yeni_h = int(kirpilmis.size[1] * olcek)
         yeniden_boyutlu = kirpilmis.resize((yeni_w, yeni_h), Image.Resampling.LANCZOS)
         
         # Dairesel maske olustur
         maske = Image.new("L", (cap_px, cap_px), 0)
         cizici = ImageDraw.Draw(maske)
         cizici.ellipse((0, 0, cap_px, cap_px), fill=255)
         
         tuval = Image.new("RGBA", (cap_px, cap_px), (0, 0, 0, 0))
         ofset_x = (cap_px - yeni_w) // 2
         ofset_y = (cap_px - yeni_h) // 2
         tuval.paste(yeniden_boyutlu, (ofset_x, ofset_y))
         tuval.putalpha(maske)
         return tuval
     ```
2. **Resmi Bayrak ve Amblem Standardı:**
   - Ülke bayrakları ve resmî amblemler yapay zekâya çizdirilmez (oran, yıldız sayısı veya renk hatası riski).
   - Daima kullanıcının sağladığı doğrulanmış vektör veya yüksek çözünürlüklü raster kaynak dosya kullanılır.
3. **Dört Fotoğraflı Delikli Üst Katman Şablonu:**
   - `2160x3840` dikey şablon tuvali (2x; video çıktısına `bilgi/video-kurgu.md` C'deki boyuta ölçeklenir) üzerinde `960x1280` (3:4 dikey) boyutunda 4 pencere koordinatı:
     - Sol Üst Yuva: `(560, 1360)` merkez koordinatı
     - Sağ Üst Yuva: `(1600, 1360)` merkez koordinatı
     - Sol Alt Yuva: `(560, 2720)` merkez koordinatı
     - Sağ Alt Yuva: `(1600, 2720)` merkez koordinatı
   - Kurgu mimarisi: Üst kanalda delikli şablon PNG'si, alt kanalda ise ilgili zaman damgasında bu koordinatlara oturan ürün fotoğrafları yer alır.

---

## C. Dikey Video: Araç Dışı FFmpeg Notları ve Premiere XML Köprüsü

> Çıktı standardı (1080x1920, 30 fps), kurgu akışı, kilit ve denetim: [`bilgi/video-kurgu.md`](video-kurgu.md) C ve E. Kurgu `tools/video/plan_render.py` ile yapılır; aşağıdaki FFmpeg notları yalnız araç dışı işler içindir.

1. **Araç Dışı Elle Render Notları:** Çözünürlük ve fps standardı `bilgi/video-kurgu.md` C'deki `cikti` alanıdır.
   - **Kodek:** H.264 MP4 (`libx264`).
   - **Ses:** AAC stereo, 320 kbps, 48 kHz örnekleme frekansı.
   - **Renk ve Netlik Filtre Zinciri:** `LANCZOS` yeniden ölçekleme, hafif unsharp (`unsharp=5:5:0.6:5:5:0.0`), kontrast ve doygunluk ayarı (`eq=contrast=1.06:saturation=1.12`) ve müzik vuruşlarında anlık parlama (`beat-flash`).
2. **FFmpeg `xfade` ve Zaman Temeli (Timebase) Normalizasyonu:**
   - Farklı kaynaklardan gelen dikey videolarda timebase veya değişken kare hızı (VFR) `xfade` geçişlerinde ses kaymasına veya donmalara yol açar.
   - Çözüm: Her klip geçiş öncesi şu filtreyle normalize edilir:
     `setpts=PTS-STARTPTS,fps=30,settb=1/30,format=yuv420p`
   - Kısıtlı gömülü ffmpeg derlemeleri yerine `uv run --with imageio-ffmpeg` (`libx264`) motoru kullanılır.
   - Bellek taşmasını önlemek için uzun renderlar parçalanıp `concat -c copy` ile birleştirilir.
   - Dikey 4K (`displaymatrix` `-90°`) kaynaklar `tools/video/analiz.py` ile taranır; kurgu, kilit ve denetim `tools/video/plan_render.py` ve `bilgi/video-kurgu.md` kurallarıyla yürütülür.
3. **Premiere Pro `.prproj` ve XML Kurgu Köprüsü:**
   - Premiere Pro proje dosyası (`.prproj`), gzip ile sıkıştırılmış bir XML belgesidir.
   - Zaman Birimi: `tick / 254016000000 = saniye` formülüyle klip başlangıç ve bitiş zamanları salt-okunur olarak okunur.
   - Bu zaman damgalarına göre otomatik altyazı (`.srt`) ve tam kadraj şeffaf başlık PNG'leri üretilir.
   - FCP7 XML (`xmeml`) içe aktarımında `Basic Motion center` koordinatları sekans boyutuna göre değil, klibin kendi piksel boyutuna göre normalize edilir:
     `horiz = (hedef_x - kare_merkez_x) / klip_genislik`
     `vert = (hedef_y - kare_merkez_y) / klip_yukseklik`
   - Kurgu öncesi açık Premiere Pro sürümü görev çubuğundan / görev yöneticisinden kontrol edilir.

---

## D. Meta Business Suite ve Çok Kanallı Müşteri Yanıtlama Otomasyonu

Sosyal medya mesajlaşma ve yorum yanıtlama süreçlerinde kurumsal güvenlik, iki aşamalı onay ve teknik doğrulama standarttır.

1. **İki Aşamalı Onay Mekanizması:**
   - Otomasyon hiçbir müşteriye doğrudan ve habersiz yanıt göndermez.
   - Önce yöneticiye Türkçe onay tablosu sunulur:
     `| Sıra | Müşteri Adı | Soru Türü | Önerilen Yanıt (Yerel Dil) | Eklenecek Katalog PDF'i |`
   - Yönetici "onay / gönder" demeden mesaj gönderilmez.
2. **RTL Metinlerde WhatsApp Bağlantı Kuralı:**
   - Sağdan sola akan dillerde telefon numarası metin içine asla düz rakam olarak yazılmaz; ters çevrilme ve kopyalama hatası önlenir.
   - Metin içinde yalnızca `{{WHATSAPP_LINK}}` yer tutucusu (`https://wa.me/<ULKE_KODU_NUMARA>`) kullanılır.
   - Fiyat ve özel sipariş ayrıntıları mesajda yazılmaz; `{{WHATSAPP_LINK}}` üzerinden paylaşılır.
3. **Tekil Ek, Başlık ve Buton Doğrulaması:**
   - Konuşma seçildikten sonra sağ paneldeki üst başlığın (müşteri adı) değiştiği DOM üzerinden doğrulanır.
   - Konuşma geçmişinde veya ekleme kutusunda katalog PDF'i zaten mevcutsa ikinci kez eklenmez.
   - Gönder butonu aktif ve tıklanabilir siyah (`rgb(0, 0, 0)`) renge dönmeden tıklama yapılmaz.
   - Gönderim başarısı, konuşma listesinde "Bir dosya eki gönderdin" önizlemesiyle teyit edilir.
4. **DOM Dosya Yükleme Yaması (`input[type=file]`):**
   - Meta arayüzünde dosya yükleme tetiklendiğinde DOM'da biriken eski input elementleri çakışma yaratır.
   - Çözüm: `HTMLInputElement.prototype.click` dinlenerek dinamik input yakalanır ve her işlem öncesinde eski geçici yükleme elementleri DOM'dan temizlenir.
5. **Yorum ve Spam Yönetimi:**
   - Otomatik veya önceden verilmiş yanıtlar ("1 yanıtı gör") kontrol edilir; mükerrer yanıt verilmez.
   - Uygunsuz veya spam yorumlar silinmez; sayfa itibarını korumak için "Gizle" seçeneğiyle gizlenir.
6. **Toplu Yorumlarda Paralel Kopya Ajan ve Tek Sekme Gönderim Mimarisi:**
   - Çok sayıda (ör. 20+) yorum veya mesaj biriktiğinde işlem "Paralel Beyin, Sıralı Parmak" hibrit akışıyla yürütülür.
   - **Adım 1 (Tekil Okuma):** Kaliko açık sekmeden tüm yorumları DOM üzerinden tek seferde toplar ve Tekir'e iletir.
   - **Adım 2 (Geçici Kopya Ajanlarla Paralel Cevap Üretimi):** Tekir yorumları 5–10'arlı gruplara böler ve her grup için geçici `ankara` alt ajan kopyaları (`invoke_subagent`, `Model: "flash"`, `Workspace: "inherit"`) başlatır. Kopyalar aynı anda çalışarak 5 sütunlu onay tablosunu (`# | Soru Arapça | Soru Türkçe | Hazırlanan Cevap Arapça | Cevap Türkçe & Eklenti`) üretir; görev bitince repoya hiçbir iz veya dosya bırakmadan silinirler.
   - **Adım 3 (Tek Sekme ve Doğal Beklemeli Gönderim):** Yönetici onayından sonra **asla çoklu tarayıcı sekmesi açılmaz** (`chrome-devtools` sekme odağı çakışmasını ve Meta anti-bot/spam kilidini önlemek için). Tek bir Kaliko ajanı, tek sekmede sırayla ve her gönderim arasına 3–5 saniye doğal bekleme (jitter) koyarak yanıtları gönderir.

---

## E. Sosyal Medya Hesap Güvenliği ve Yerel Kayıt İzolasyonu

1. **Açık Profil Doğrulaması:**
   - Tarayıcı otomasyonu başlatıldığında profil resmi ve hesap adı kontrol edilir.
   - Kişisel hesapla kurumsal işletme hesabının karışması kesin olarak engellenir; kurumsal profil aktif değilse işlem durdurulur.
2. **Git Gizlilik Duvarı ve Yerel Kayıt İzolasyonu:**
   - Gerçek müşteri isimleri, telefon numaraları, sipariş miktarları ve mesajlaşma günlükleri git reposuna **kesinlikle yazılmaz**.
   - Müşteri verileri yalnızca `.gitignore` altında korunan yerel kayıt klasöründe (`yerel-kayitlar/`) tarihli olarak tutulur.
3. **Çift Repolu Çalışma ve Global Öğrenim Ayrımı:** [`CLAUDE.md` Bölüm 14](../CLAUDE.md#14-öğrenme-ve-hafıza) ("Harici İşletme / Sosyal Medya Reposu ile Birlikte Çalışma").
